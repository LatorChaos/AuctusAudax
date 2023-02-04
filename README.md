# Auctus Audax
A resource and warchest automation, production calculation, and auditing script for the MMO Politics &amp; War

![imperial gelt](https://user-images.githubusercontent.com/119812496/205515999-a0faa8c4-7b81-4f22-974f-cf998eb03a6f.png)

Usage Instructions
1. Install Python 3 https://www.python.org/downloads/
2. Open cmd.exe and use pip to install the dependences
      Example: pip install bs4
      Module dependences as of typing: requests, json, math, time, copy, datetime, bs4
3. Right click on Auctus_Audax.py and click, "Edit with IDLE"
4. Configure settings and set variables as desired and needed
    a. api_tax_dict, dump_to_offshore, offshore_name, top_off, send_WC, send_war_WC, wc_money_multipler, days_of_supply, send_food_and_uranium_buffer, food_and_uranium_buffer_multiplier, run_audit, user_email, user_password, user_alliance_id, sender_api_key, headers
    b. The script is NOT ready to run out of the box and NEEDS to be configured with proper variables set
5. I recommend not engaging this script wrecklessly and not starting it too close to a turn change as it will fail if it runs into a turn change
6. When you are ready to start, at the top of the IDLE window, click Run -> Run Module to start. Alternatively press the F5 key
7. The script will ask for user input to begin the process of sending resources, simply enter 'Y' to continue or 'N' to end the script
    a. Please note that it is up to the user to ensure there's enough resources in the bank for sends to successfully complete
    b. Each send needs to be confirmed by a human
8. Give praise to the Omnissiah and his many forms
