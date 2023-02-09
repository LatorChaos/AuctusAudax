import requests, json, math, time, copy
import datetime as dt
from bs4 import BeautifulSoup

api_tax_dict = {'APIKEYHERE' : 11656} #api key : tax bracket id - api key must have access to gov of corresponding tax id

dump_to_offshore = True #True means dump bank contents to offshore when sending is done
offshore_name = 'Rain' #Name of the offshore

top_off = True #Top off True means bring targets to specified days of supply, False means just send them however many days of supplies is specified

send_WC = False #True sends WC, False sends no WC
send_war_WC = False #True sends war time WC as defined later in the script, False means regular WC is sent as it is defined
wc_money_multipler = 2.0 #Multiplies WC money requirement by this number

days_of_supply = 3.0 #Targeted days of supplies
send_food_and_uranium_buffer = True #True means the food and uranium buffer multipler will be applied
food_and_uranium_buffer_multiplier = 2.0 #Multiplies food and uranium supply by this number

run_audit = True #If True, a basic audit will be supplied

user_email = 'anEmail@mail.com' #User email of the sender
user_password = 'SENDERpasswordHERE' #User password of the sender
user_alliance_id = '6088' #Alliance ID of the sender
sender_api_key = 'APIKEYHERE'

headers = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36' #Periodcally update this with the most common user agent

def bank_withdraw(net_rev, session):
    #given net_rev and authorized login session, send corresponding leader_name corresponding resources
    r = session.get('https://politicsandwar.com/alliance/id=' + user_alliance_id + '&display=bank')
    soup = BeautifulSoup(r.content, 'html.parser')
    token = soup.find('input', {'name':'token'})['value']
    
    send_message_payload = {'withmoney':net_rev['money'],
                            'withfood':net_rev['food'],
                            'withcoal':net_rev['coal'],
                            'withoil':net_rev['oil'],
                            'withuranium':net_rev['uranium'],
                            'withlead':net_rev['lead'],
                            'withiron':net_rev['iron'],
                            'withbauxite':net_rev['bauxite'],
                            'withgasoline':net_rev['gasoline'],
                            'withmunitions':net_rev['munitions'],
                            'withsteel':net_rev['steel'],
                            'withaluminum':net_rev['aluminum'],
                            "withtype": "Nation",
                            "withrecipient": net_rev['nation_name'],
                            "withnote": "Covid Relief Funds 4u - love Malleator",
                            "withsubmit": "Withdraw",
                            "token": token}
    print(send_message_payload)
    send_message_url = 'https://politicsandwar.com/alliance/id=' + user_alliance_id + '&display=bank'
    res = session.post(send_message_url, data=send_message_payload)

    return session

def login(email, password):
    #given email and password, login to pnw website and return session s
    #print("\nLogging in...")
    with requests.Session() as s:
        s.headers['User-Agent'] = headers
        login_payload = {'email':email, 'password':password, 'loginform':'Login'}
        url = 'https://politicsandwar.com/login/'
        s.post(url, data=login_payload)
        #print("Logged in.\n")

        return s

def send_resources(list_of_net_revenues):
    #given list of net revs, iterate through each item and send resources to corresponding target, asking the user for each
    session = login(user_email, user_password)
    for net_rev in list_of_net_revenues:
        if net_rev['send']:
            print(net_rev)
            user_input = input('Send? (Y/N)').replace(' ','').replace('Y','y')
            if user_input == 'y':
                session = bank_withdraw(net_rev, session)

def sum_of_net_revs(list_of_net_revenues):
    return {k: sum(net_rev[k] for net_rev in list_of_net_revenues if k in net_rev and k) for k in set(k for d in list_of_net_revenues for k in d if k not in ('nation', 'nation_name', 'send'))}
    

def audit_given_nations(api_data):
    #given API data, give basic audit
    nation_flags_dict_list = []
    for data_set in api_data:
        for nation in data_set['data']['nations']['data']:
            nation_flags_dict = {'nation_link': f'https://politicsandwar.com/nation/id={nation["id"]}'}

            for city in nation['cities']:
                city['crime'], city['disease'], city['population'], city['commerce'], city['age'], city['pollution'] = calculate_city_stats(city, nation)

            if nation['aircraft'] < (nation['num_cities'] * 75):
                nation_flags_dict['unmaxed_air'] = 1
            if nation['war_policy'] != 'Fortress':
                nation_flags_dict['wrong_war_policy'] = 1
            if ["" for x in [[v for k, v in city.items() if k in ("oil_refinery", "steel_mill", "aluminum_refinery", "munitions_factory") and v not in (0, 5)] for city in nation['cities']] if len(x)]:
                nation_flags_dict['manu_incorrect'] = 1
            if ["" for x in [[v for k, v in city.items() if k in ("lead_mine", "iron_mine", "bauxite_mine", "coal_mine", "oil_well") and v not in (0, 10)] for city in nation['cities']] if len(x)] or [x for x in [[v for k, v in city.items() if k is "uranium_mine" and v not in (0, 5)] for city in nation['cities']] if len(x)] or [x for x in [[v for k, v in city.items() if k is "farm" and v not in (0, 20)] for city in nation['cities']] if len(x)]:
                nation_flags_dict['raws_incorrect'] = 1
            if any([int(city["infrastructure"] / 50) - sum([v for k, v in city.items() if k in ("coal_power","oil_power","nuclear_power","wind_power","bauxite_mine","uranium_mine","farm","oil_refinery","steel_mill","aluminum_refinery","munitions_factory","police_station","hospital","recycling_center","subway","supermarket","bank","shopping_mall","stadium","barracks","factory","hangar","drydock")]) for city in nation['cities']]):
                nation_flags_dict['unused_slots'] = 1
            if ["" for city in nation["cities"] if city["powered"] is "No"]:
                nation_flags_dict['cities_unpowered'] = 1
            if ["" for city in nation["cities"] if city["infrastructure"] >= 1500 and city["commerce"] < 100] or (["" for city in nation["cities"] if city["infrastructure"] >= 1500 and city["commerce"] < 114] and nation['international_trade_center']):
                nation_flags_dict['needs_more_commerce'] = 1
            if ["" for city in nation["cities"] if city["crime"] > 0.05 and city["infrastructure"] >= 1500]:
                nation_flags_dict['too_much_crime'] = 1
            if nation["num_cities"] >= 10 and ["" for city in nation["cities"] if city["barracks"]>0 or city["factory"]>3 or city["drydock"]>0 or city["hangar"]<4]:
                nation_flags_dict['incorrect_mil_improvs'] = 1
            if ["" for city in nation["cities"] if city["infrastructure"]<1000 and city["commerce"]>0]:
                nation_flags_dict['too_much_commerce'] = 1
            if ["" for city in nation["cities"] if city["disease"]>0.02]:
                nation_flags_dict['too_much_disease'] = 1
            if ["" for city in nation["cities"] if city["infrastructure"]>=1500 and city["pollution"]>=70 and city["recycling_center"]<3 and city["disease"]>=3.5]:
                nation_flags_dict['needs_recycling_center'] = 1
            if ["" for city in nation["cities"] if city["infrastructure"]>=1500 and city["pollution"]>=45 and city["subway"]<1 and city["disease"]>=2.25]:
                nation_flags_dict['needs_subway'] = 1
            if ["" for city in nation["cities"] if city["infrastructure"]>=1500 and city["hospital"]<5 and city["disease"]>=2.5]:
                nation_flags_dict['needs_hospital'] = 1
            if ["" for city in nation["cities"] if city["oil_refinery"]*nation["emergency_gasoline_reserve"]!=city["oil_refinery"] or city["steel_mill"]*nation["iron_works"]!=city["steel_mill"] or city["aluminum_refinery"]*nation["bauxite_works"]!=city["aluminum_refinery"] or city["munitions_factory"]*nation["arms_stockpile"]!=city["munitions_factory"]]:
                nation_flags_dict['refining_without_project'] = 1
            if ["" for city in nation["cities"] if int(city["farm"]) and int(city["land"])<3000]:
                nation_flags_dict['farming_with_low_land'] = 1
            if ["" for city in nation["cities"] if city["infrastructure"] % 50 != 0]:
                nation_flags_dict['odd_infra'] = 1
            if ["" for city in nation["cities"] if city["land"] % 100 != 0]:
                nation_flags_dict['odd_land'] = 1
            if ["" for city in nation["cities"] if int(city["coal_power"]) or int(city["oil_power"])]:
                nation_flags_dict['using_oilcoal_power'] = 1
            if ["" for city in nation["cities"] if int(city["wind_power"])>1]:
                nation_flags_dict['too_much_wind'] = 1

            match nation['num_cities']:
                case range(1, 10):
                    for city in nation['cities']:
                        if int(city['infrastructure']) > 1500:
                            nation_flags_dict['infra_too_high'] = 1
                case range(10, 16):
                    for city in nation['cities']:
                        if int(city['infrastructure']) > 2000:
                            nation_flags_dict['infra_too_high'] = 1
                case range(16, 20):
                    for city in nation['cities']:
                        if int(city['infrastructure']) > 2250:
                            nation_flags_dict['infra_too_high'] = 1
                case range(20, 26):
                    for city in nation['cities']:
                        if int(city['infrastructure']) > 2500:
                            nation_flags_dict['infra_too_high'] = 1
                case range(26, 30):
                    for city in nation['cities']:
                        if int(city['infrastructure']) > 2700:
                            nation_flags_dict['infra_too_high'] = 1
                case range(30, 35):
                    for city in nation['cities']:
                        if int(city['infrastructure']) > 3000:
                            nation_flags_dict['infra_too_high'] = 1
                case range(35, 40):
                    for city in nation['cities']:
                        if int(city['infrastructure']) > 3300:
                            nation_flags_dict['infra_too_high'] = 1
                case _:
                    for city in nation['cities']:
                        if int(city['infrastructure']) > 3300:
                            nation_flags_dict['infra_too_high'] = 1

            nation_flags_dict_list.append(nation_flags_dict)
    return nation_flags_dict_list

def mod_net_revenues(list_of_net_revenues):
    #given list of net revenues, modifiy them based off settings and clean them up
    for net_rev in list_of_net_revenues:
        for key, value in net_rev.items():
            if key != 'nation':
                if value >= 0:
                    net_rev[key] = 0
                else:
                    net_rev[key] *= days_of_supply
                    if key == 'food' or key == 'uranium':
                        net_rev[key] *= food_and_uranium_buffer_multiplier
                    net_rev[key] *= -1
                    net_rev[key] = int(math.ceil(net_rev[key]))
                    if top_off:
                        net_rev[key] -= net_rev['nation'][key]
                        if value <= 0:
                            net_rev[key] = 0
    return list_of_net_revenues

def clean_net_revenues(list_of_net_revenues):
    #given list of net revenues, clean them up
    for net_rev in list_of_net_revenues:
        net_rev['nation_name'] = net_rev['nation']['nation_name']
        net_rev['send'] = False
        net_rev.pop('nation', None)
        for key, value in net_rev.items():
            if key != 'nation_name':
                if value <= 0:
                    net_rev[key] = 0
                else:
                    net_rev['send'] = True
                    net_rev[key] = int(math.ceil(net_rev[key]))
                
                
    return list_of_net_revenues

def mod_net_revs_for_wc(list_of_net_revenues):
    #given list of net_revs, modify to add WC
    for net_rev in list_of_net_revenues:
        if net_rev['nation']['num_cities'] < 20:
            if send_war_WC:
                if net_rev['food'] < net_rev['nation']['num_cities'] * 3000 - net_rev['nation']['food']:
                    net_rev['food'] = (net_rev['nation']['num_cities'] * 3000) - net_rev['nation']['food']
                if net_rev['uranium'] < net_rev['nation']['num_cities'] * 50 - net_rev['nation']['uranium']:
                    net_rev['uranium'] = (net_rev['nation']['num_cities'] * 50) - net_rev['nation']['uranium']
                if net_rev['nation']['aluminum'] < net_rev['nation']['num_cities'] * 400:
                    net_rev['aluminum'] += (net_rev['nation']['num_cities'] * 400) - net_rev['nation']['aluminum']
                if net_rev['nation']['steel'] < net_rev['nation']['num_cities'] * 750:
                    net_rev['steel'] += (net_rev['nation']['num_cities'] * 750) - net_rev['nation']['steel']
                if net_rev['nation']['munitions'] < net_rev['nation']['num_cities'] * 650:
                    net_rev['munitions'] += (net_rev['nation']['num_cities'] * 650) - net_rev['nation']['munitions']
                if net_rev['nation']['gasoline'] < net_rev['nation']['num_cities'] * 625:
                    net_rev['gasoline'] += (net_rev['nation']['num_cities'] * 625) - net_rev['nation']['gasoline']
                if net_rev['nation']['money'] < net_rev['nation']['num_cities'] * 500000 * wc_money_multipler:
                    net_rev['money'] += (net_rev['nation']['num_cities'] * 500000 * wc_money_multipler) - net_rev['nation']['money']
                    
            else:
                if net_rev['food'] < net_rev['nation']['num_cities'] * 1500 - net_rev['nation']['food']:
                    net_rev['food'] = (net_rev['nation']['num_cities'] * 1500) - net_rev['nation']['food']
                if net_rev['uranium'] < net_rev['nation']['num_cities'] * 25 - net_rev['nation']['uranium']:
                    net_rev['uranium'] = (net_rev['nation']['num_cities'] * 25) - net_rev['nation']['uranium']
                if net_rev['nation']['aluminum'] < net_rev['nation']['num_cities'] * 200:
                    net_rev['aluminum'] += (net_rev['nation']['num_cities'] * 200) - net_rev['nation']['aluminum']
                if net_rev['nation']['steel'] < net_rev['nation']['num_cities'] * 375:
                    net_rev['steel'] += (net_rev['nation']['num_cities'] * 375) - net_rev['nation']['steel']
                if net_rev['nation']['munitions'] < net_rev['nation']['num_cities'] * 325:
                    net_rev['munitions'] += (net_rev['nation']['num_cities'] * 325) - net_rev['nation']['munitions']
                if net_rev['nation']['gasoline'] < net_rev['nation']['num_cities'] * 313:
                    net_rev['gasoline'] += (net_rev['nation']['num_cities'] * 313) - net_rev['nation']['gasoline']
                if net_rev['nation']['money'] < net_rev['nation']['num_cities'] * 250000 * wc_money_multipler:
                    net_rev['money'] += (net_rev['nation']['num_cities'] * 250000 * wc_money_multipler) - net_rev['nation']['money']
                    

        else:
            if send_war_WC:
                if net_rev['food'] < net_rev['nation']['num_cities'] * 3000 - net_rev['nation']['food']:
                    net_rev['food'] = (net_rev['nation']['num_cities'] * 3000) - net_rev['nation']['food']
                if net_rev['uranium'] < net_rev['nation']['num_cities'] * 100 - net_rev['nation']['uranium']:
                    net_rev['uranium'] = (net_rev['nation']['num_cities'] * 100) - net_rev['nation']['uranium']
                if net_rev['nation']['aluminum'] < net_rev['nation']['num_cities'] * 500:
                    net_rev['aluminum'] += (net_rev['nation']['num_cities'] * 500) - net_rev['nation']['aluminum']
                if net_rev['nation']['steel'] < net_rev['nation']['num_cities'] * 750:
                    net_rev['steel'] += (net_rev['nation']['num_cities'] * 750) - net_rev['nation']['steel']
                if net_rev['nation']['munitions'] < net_rev['nation']['num_cities'] * 700:
                    net_rev['munitions'] += (net_rev['nation']['num_cities'] * 700) - net_rev['nation']['munitions']
                if net_rev['nation']['gasoline'] < net_rev['nation']['num_cities'] * 675:
                    net_rev['gasoline'] += (net_rev['nation']['num_cities'] * 675) - net_rev['nation']['gasoline']
                if net_rev['nation']['money'] < net_rev['nation']['num_cities'] * 750000 * wc_money_multipler:
                    net_rev['money'] += (net_rev['nation']['num_cities'] * 750000 * wc_money_multipler) - net_rev['nation']['money']
                    
            else:
                if net_rev['food'] < net_rev['nation']['num_cities'] * 1500 - net_rev['nation']['food']:
                    net_rev['food'] = (net_rev['nation']['num_cities'] * 1500) - net_rev['nation']['food']
                if net_rev['uranium'] < net_rev['nation']['num_cities'] * 50 - net_rev['nation']['uranium']:
                    net_rev['uranium'] = (net_rev['nation']['num_cities'] * 50) - net_rev['nation']['uranium']
                if net_rev['nation']['aluminum'] < net_rev['nation']['num_cities'] * 250:
                    net_rev['aluminum'] += (net_rev['nation']['num_cities'] * 250) - net_rev['nation']['aluminum']
                if net_rev['nation']['steel'] < net_rev['nation']['num_cities'] * 375:
                    net_rev['steel'] += (net_rev['nation']['num_cities'] * 375) - net_rev['nation']['steel']
                if net_rev['nation']['munitions'] < net_rev['nation']['num_cities'] * 350:
                    net_rev['munitions'] += (net_rev['nation']['num_cities'] * 350) - net_rev['nation']['munitions']
                if net_rev['nation']['gasoline'] < net_rev['nation']['num_cities'] * 338:
                    net_rev['gasoline'] += (net_rev['nation']['num_cities'] * 338) - net_rev['nation']['gasoline']
                if net_rev['nation']['money'] < net_rev['nation']['num_cities'] * 300000 * wc_money_multipler:
                    net_rev['money'] += (net_rev['nation']['num_cities'] * 300000 * wc_money_multipler) - net_rev['nation']['money']
    return list_of_net_revenues

def get_data_from_api():
    #given dict of apikey:taxid, return needed api data for each pair in the form of a list with each item being an entire set of data
    responses = []
    
    for API_key, tax_bracket in api_tax_dict.items():
        url = 'https://api.politicsandwar.com/graphql?api_key=' + str(API_key)
        #payload = {"query": "{nations(tax_id: " + str(tax_bracket) + ") { data {emergency_gasoline_reserve}}}"}
        payload = {"query": "{  game_info{radiation{global}radiation{north_america}radiation{south_america}radiation{europe}radiation{africa}radiation{asia}radiation{australia}radiation{antarctica}}  nations(tax_id: 11656) {    data {      id      nation_name      leader_name      continent      war_policy      population      soldiers      tanks      aircraft      ships      wars(active:true){att_id}      iron_works      bauxite_works      arms_stockpile      emergency_gasoline_reserve      mass_irrigation      international_trade_center      uranium_enrichment_program      recycling_initiative      telecommunications_satellite      green_technologies      clinical_research_center      specialized_police_training_program        coal        oil        uranium        lead        iron        bauxite        gasoline        munitions        steel        aluminum        food        money          num_cities      cities {          id          infrastructure        land          date          powered        oil_power        wind_power        coal_power        nuclear_power        coal_mine        oil_well        uranium_mine        barracks        farm        police_station        hospital        recycling_center        subway        supermarket        bank        shopping_mall        stadium        lead_mine        iron_mine        bauxite_mine        oil_refinery        aluminum_refinery        steel_mill        munitions_factory        factory        hangar        drydock         }    }  }}"}

        response = requests.post(url, json = payload)

        responses.append(json.loads(response.text))
        
    return responses

def determine_nation_radiation(continent, radiation_data):
    #given continent and radiation data, return corresponding regional radiation to continent
    if continent == 'sa':
        return radiation_data['south_america']
    elif continent == 'na':
        return radiation_data['north_america']
    elif continent == 'af':
        return radiation_data['africa']
    elif continent == 'eu':
        return radiation_data['europe']
    elif continent == 'au':
        return radiation_data['australia']
    elif continent == 'as':
        return radiation_data['asia']
    elif continent == 'an':
        return radiation_data['antarctica']

def calculate_city_stats(city, nation):
    #thanks putmir
    base_pop = city["infrastructure"] * 100

    age = (dt.datetime.today() - dt.datetime(int(city['date'][0:4]),int(city['date'][5:7]),int(city['date'][8:10]))).days
    if age <= 0:
        age = 1

    commerce = ((city['subway']*8)+(city['supermarket']*3)+(city['bank']*5)+(city['shopping_mall']*9)+(city['stadium']*12))
    if nation["telecommunications_satellite"]:
        commerce += 2
    if commerce > 100:
        if nation["telecommunications_satellite"]:
            if commerce > 125:
                commerce = 125
        elif nation["international_trade_center"]:
            if commerce > 115:
                commerce = 115
        else:
            commerce = 100

    crime = max(((((103 - commerce) ** 2) + (city["infrastructure"] + 250) * 100)/ 11111111) - (city["police_station"] * (3.5 if nation["specialized_police_training_program"] else 2.5)), 0,)

    pol_index = ((city["coal_power"] * 8)+ (city["oil_power"] * 6)+ ((city["coal_mine"]+ city["iron_mine"]+ city["oil_well"]+ city["bauxite_mine"]+ city["lead_mine"])* 12)+ (city["uranium_mine"] * 20)+ ((city["farm"] * 2) * (0.5 if nation["green_technologies"] else 1))+ (((city["munitions_factory"] + city["oil_refinery"]) * 32)+ ((city["steel_mill"] + city["aluminum_refinery"]) * 40))* (0.75 if nation["green_technologies"] else 1)+ (city["police_station"])+ (city["hospital"] * 4)+ (city["recycling_center"]* -(75 if nation["recycling_initiative"] else 70))+ (city["subway"] * -(70 if nation["green_technologies"] else 45))+ (city["shopping_mall"] * 2)+ (city["stadium"] * 5)) * 0.05
    
    disease = ((((((base_pop / city["land"]) ** 2) * 0.01) - 25) / 100) + (base_pop / 100000) + pol_index - (3.5 if nation["clinical_research_center"] else 2.5) * city["hospital"])

    if disease < 0:
        disease = 0
        
    population = round((base_pop - (disease * base_pop) - max(((crime / 10) * base_pop - 25), 0)) * (1 + math.log(age) / 15))

    return crime, disease, population, commerce, age, pol_index

def calculate_production_per_day(improvCount, improvCap, baseRate):
    #given improvement data, return its daily production
    bonus = 1 + ((0.5 * (int(improvCount) - 1)) / (int(improvCap) - 1))
    production = (int(improvCount) * bonus * float(baseRate)) * 12
    if production <= 0:
        production = 0
    return production

def calculate_net_revenue(api_data):
    #given api_data, give dict of each leader name with his or hers corresponding national net revenue per turn
    list_of_net_revenues = []
    for data_set in api_data:
        for nation in data_set['data']['nations']['data']:
            nation_net_rev = {"nation" : nation, "money" : 0, "coal": 0, "oil": 0, "uranium": 0, "lead": 0, "iron": 0, "bauxite": 0, "gasoline": 0, "munitions": 0, "steel": 0, "aluminum": 0, "food": 0}
            
            nation['radiation'] = determine_nation_radiation(nation['continent'], data_set['data']['game_info']['radiation'])
            
            foodRadMultipler = 1 - ((nation['radiation'] + data_set['data']['game_info']['radiation']['global'])/1000)

            for city in nation['cities']:
                city['crime'], city['disease'], city['population'], city['commerce'], city['age'], city['pollution'] = calculate_city_stats(city, nation)
                
                nation_net_rev['money'] += ((((city['commerce']/50) * 0.725) + 0.725) * city['population'])

                nation_net_rev['money'] -= (city['coal_mine']*400)
                nation_net_rev['money'] -= (city['oil_well']*600)
                nation_net_rev['money'] -= (city['bauxite_mine']*1600)
                nation_net_rev['money'] -= (city['iron_mine']*1600)
                nation_net_rev['money'] -= (city['lead_mine']*1500)
                nation_net_rev['money'] -= (city['uranium_mine']*5000)
                nation_net_rev['money'] -= (city['farm']*300)

                nation_net_rev['money'] -= (city['coal_power']*1200)
                nation_net_rev['money'] -= (city['oil_power']*1800)
                nation_net_rev['money'] -= (city['nuclear_power']*10500)
                nation_net_rev['money'] -= (city['wind_power']*500)

                nation_net_rev['money'] -= (city['oil_refinery']*4000)
                nation_net_rev['money'] -= (city['steel_mill']*4000)
                nation_net_rev['money'] -= (city['aluminum_refinery']*2500)
                nation_net_rev['money'] -= (city['munitions_factory']*3500)

                nation_net_rev['money'] -= (city['police_station']*750)
                nation_net_rev['money'] -= (city['hospital']*1000)
                nation_net_rev['money'] -= (city['recycling_center']*2500)
                nation_net_rev['money'] -= (city['subway']*3250)
                nation_net_rev['money'] -= (city['supermarket']*600)
                nation_net_rev['money'] -= (city['bank']*1800)
                nation_net_rev['money'] -= (city['shopping_mall']*5400)
                nation_net_rev['money'] -= (city['stadium']*12150)
                
                nation_net_rev['coal'] += calculate_production_per_day(city['coal_mine'], 10, 0.25)
                nation_net_rev['oil'] += calculate_production_per_day(city['oil_well'], 10, 0.25)
                nation_net_rev['lead'] += calculate_production_per_day(city['lead_mine'], 10, 0.25)
                nation_net_rev['iron'] += calculate_production_per_day(city['iron_mine'], 10, 0.25)
                nation_net_rev['bauxite'] += calculate_production_per_day(city['bauxite_mine'], 10, 0.25)

                if nation['continent'] == 'an':
                    if nation['mass_irrigation']:
                        if ((calculate_production_per_day(city['farm'], 20, (float(city['land'])/400)))*0.5*foodRadMultipler) > 0:
                            nation_net_rev['food'] += (calculate_production_per_day(city['farm'], 20, (float(city['land'])/400)))*0.5*foodRadMultipler
                    else:
                        if ((calculate_production_per_day(city['farm'], 20, (float(city['land'])/500)))*0.5*foodRadMultipler) > 0:
                            nation_net_rev['food'] += (calculate_production_per_day(city['farm'], 20, (float(city['land'])/500)))*0.5*foodRadMultipler
                else:
                    if nation['mass_irrigation']:
                        if (calculate_production_per_day(city['farm'], 20, (float(city['land'])/400))*foodRadMultipler) > 0:
                            nation_net_rev['food'] += calculate_production_per_day(city['farm'], 20, (float(city['land'])/400))*foodRadMultipler#*foodSeasonMultipler
                    else:
                        if (calculate_production_per_day(city['farm'], 20, (float(city['land'])/500))*foodRadMultipler) > 0:
                            nation_net_rev['food'] += calculate_production_per_day(city['farm'], 20, (float(city['land'])/500))*foodRadMultipler#*foodSeasonMultipler
                        
                if nation['uranium_enrichment_program']:
                    nation_net_rev['uranium'] += calculate_production_per_day(city['uranium_mine'], 5, 0.5)
                else:
                    nation_net_rev['uranium'] += calculate_production_per_day(city['uranium_mine'], 5, 0.25)
                    
                cityInfraCounter, nukePower, oil_power, coal_power, wind_power = city['infrastructure'], city['nuclear_power'], city['oil_power'], city['coal_power'], city['wind_power']
                while cityInfraCounter > 0:
                    if wind_power > 0:
                        cityInfraCounter -= 250
                        wind_power -= 1
                    elif nukePower > 0:
                        nuke_infra_batches = cityInfraCounter / 1000
                        if nuke_infra_batches > 1:
                            cityInfraCounter -= 2000
                            nation_net_rev['uranium'] -= 2.4
                        else:
                            cityInfraCounter -= 1000 #nuke_infra_batches * 
                            nation_net_rev['uranium'] -= 1.2 #nuke_infra_batches * 
                        nukePower -= 1
                    elif oil_power > 0:
                        decrease = min(cityInfraCounter, 500)
                        cityInfraCounter -= decrease
                        nation_net_rev['oil'] -= math.ceil(decrease / 100) * 1.2
                        oil_power -= 1
                    elif coal_power > 0:
                        decrease = min(cityInfraCounter, 500)
                        cityInfraCounter -= decrease
                        nation_net_rev['coal'] -= math.ceil(decrease / 100) * 1.2
                        coal_power -= 1
                    elif nukePower  + oil_power + coal_power + wind_power <= 0:
                        cityInfraCounter = 0
                
                
                if nation['emergency_gasoline_reserve']:
                    resourceProductAmount = calculate_production_per_day(city['oil_refinery'], 5, 1)
                    nation_net_rev['gasoline'] += resourceProductAmount
                    nation_net_rev['oil'] -= resourceProductAmount / 2
                else:
                    resourceProductAmount = calculate_production_per_day(city['oil_refinery'], 5, 0.5)
                    nation_net_rev['gasoline'] += resourceProductAmount
                    nation_net_rev['oil'] -= resourceProductAmount / 2
                    
                if nation['arms_stockpile']:
                    resourceProductAmount = calculate_production_per_day(city['munitions_factory'], 5, 2.01)
                    nation_net_rev['munitions'] += resourceProductAmount
                    nation_net_rev['lead'] -= resourceProductAmount / 3
                else:
                    resourceProductAmount = calculate_production_per_day(city['munitions_factory'], 5, 1.5)
                    nation_net_rev['munitions'] += resourceProductAmount
                    nation_net_rev['lead'] -= resourceProductAmount / 3
                    
                if nation['iron_works']:
                    resourceProductAmount = calculate_production_per_day(city['steel_mill'], 5, 1.02)
                    nation_net_rev['steel'] += resourceProductAmount
                    nation_net_rev['iron'] -= resourceProductAmount / 3
                    nation_net_rev['coal'] -= resourceProductAmount / 3
                else:
                    resourceProductAmount = calculate_production_per_day(city['steel_mill'], 5, 0.75)
                    nation_net_rev['steel'] += resourceProductAmount
                    nation_net_rev['iron'] -= resourceProductAmount / 3
                    nation_net_rev['coal'] -= resourceProductAmount / 3

                if nation['bauxite_works']:
                    resourceProductAmount = calculate_production_per_day(city['aluminum_refinery'], 5, 1.02)
                    nation_net_rev['aluminum'] += resourceProductAmount
                    nation_net_rev['bauxite'] -= resourceProductAmount / 3
                else:
                    resourceProductAmount = calculate_production_per_day(city['aluminum_refinery'], 5, 0.75)
                    nation_net_rev['aluminum'] += resourceProductAmount
                    nation_net_rev['bauxite'] -= resourceProductAmount / 3

            list_of_net_revenues.append(nation_net_rev)
            
    return list_of_net_revenues
                
                
def main():
    #main script body
    print("MACHINA SPIRITIBUS BENEDICITE NOBIS TUA BENEVOLENTIAE\n")
    print(dt.datetime.today())
    start_time = time.time()
    
    api_data = get_data_from_api()#getting all the API data we'll need

    if run_audit:
        audit_results = audit_given_nations(api_data)
        print("\n")
        print('AUDIT RESULTS:')
        print(audit_results)

    list_of_net_revenues = calculate_net_revenue(api_data) #calculating each nation's net change in resources and money
    
    print("\nPROGRAMEE DATA:")
    print(list_of_net_revenues)
    print("\nPROGRAM DAILY NET PRODUCTION:")
    print(sum_of_net_revs(list_of_net_revenues))
    
    list_of_net_revenues = mod_net_revenues(list_of_net_revenues) #calculating what and how much to send
    
    if send_WC:
        list_of_net_revenues = mod_net_revs_for_wc(list_of_net_revenues) #making sure everything is within WC parameters
    list_of_net_revenues = clean_net_revenues(list_of_net_revenues) #final cleaning/slimming of data

    print("\nAMOUNT TO BE SENT TO EACH PROGRAMEE:")
    print(list_of_net_revenues)
    
    print("\nCURRENT BANK CONTENTS:")
    print(json.loads(requests.post('https://politicsandwar.com/api/alliance-bank/?allianceid=' + user_alliance_id + '&key=' + sender_api_key).text)['alliance_bank_contents'][0])

    print("\nTOTAL TO BE SENT THIS CYCLE:")
    print(sum_of_net_revs(list_of_net_revenues))
    print("Calculations elapsed time (sec): " + str(time.time() - start_time))

    user_input = input("\nBegin sending resources? (Y/N)").replace(' ','').replace('Y','y')
    if user_input == 'y':
        send_resources(list_of_net_revenues)

    

    print("\nTotal elapsed time (sec): " + str(time.time() - start_time))
    print(dt.datetime.today())
    print("\n\nMACHINATIO SPIRITUUM CETERA, GRATIAS TIBI DAMUS")

if __name__ == "__main__":
    main()
