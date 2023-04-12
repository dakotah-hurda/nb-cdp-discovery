import os
import pprint
import logging, logging.handlers
import pynetbox
import yaml
from logger import myLogger

from cdpMasterDictHandler import cdpMasterDictHandler
from netbox_data_handler import netbox_data_handler
from dotenv import load_dotenv

def nb_retrieve_all_sites(netbox_access_token) -> list:
    """
    This function makes an API call to Netbox, grabs all sites, then returns a tuple for each site.

    Tuple format: [site_id, site_seed_device]
    """
    logger = myLogger(__name__)

    site_data = {}

    netbox_url = 'https://NETBOX-URL-GOES-HERE'
    nb = pynetbox.api(netbox_url, token=netbox_access_token)
    
    sites = nb.dcim.sites.all()
    
    for site in sites: # This loops through all the sites from Netbox and builds a small dictionary for use. This dictionary will be passed to the cdpDiscoveryFunctions module later.
        
        # Verify that the cdp_seed_device custom field actually exists at the site object. This SHOULD never fail.
        if 'cdp_seed_device' in site.custom_fields.keys(): 
            logger.debug(f'Found cdp_seed_device KEY for site {site}')
            
            # Verify that there is data in the cdp_seed_device return value.
            if site.custom_fields['cdp_seed_device'] is not None: 
                logger.debug(f'Found cdp_seed_device DATA for site {site}')
                
                # Finally, verify that the cdp_seed_device has a name.
                if site.custom_fields['cdp_seed_device']['name'] is not None: 
                    logger.debug(f'Found cdp_seed_device NAME for site {site}, adding to site_list')
                    
                    # Successfully extracted name from Netbox, add to site_list.
                    
                    site_data[site.name] = {}
                    site_data[site.name]['cdp_seed_device'] = {}
                    site_data[site.name]['cdp_seed_device'] = site.custom_fields['cdp_seed_device']['name']
                    site_data[site.name]['site_id'] = site.id
                
                # If no device_name is present with the cdp_seed_device data...
                else: 
                    logger.error(f'No device_name present in cdp_seed_device data for site {site}. This indicates that the data in the "custom field" is incomplete.')
            
            # If no CDP data exists within the site key...
            else: 
                logger.error(f'No CDP Seed Device data for site {site}. This indicates that you need to fill in the "custom field" for the site in Netbox.')
        
        # If the CDP device key isn't even found for the site...
        else: 
            logger.error(f'No CDP device key found for site {site}. This indicates a Netbox API issue.')

    logger.info("\n" + (f'Created site data: {site_data}'))
    return(site_data)

def welcomeMessage():

    print(r"""
           /^\/^\
         _|__|  O|
\/     /~     \_/ \
 \____|__________/  \
        \_______      \
                `\     \                 \
                  |     |                  \
                 /      /                    \
                /     /                       \\
              /      /                         \ \
             /     /                            \  \
           /     /             _----_            \   \
          /     /           _-~      ~-_         |   |
         (      (        _-~    _--_    ~-_     _/   |
          \      ~-____-~    _-~    ~-_    ~-_-~    /
            ~-_           _-~          ~-_       _-~
               ~--______-~                ~-___-~
    
_________  ________  __________          _________                         .__                  
\_   ___ \ \______ \ \______   \         \_   ___ \_______ _____  __  _  __|  |    ____ _______ 
/    \  \/  |    |  \ |     ___/  ______ /    \  \/\_  __ \\__  \ \ \/ \/ /|  |  _/ __ \\_  __ \
\     \____ |    `   \|    |     /_____/ \     \____|  | \/ / __ \_\     / |  |__\  ___/ |  | \/
 \______  //_______  /|____|              \______  /|__|   (____  / \/\_/  |____/ \___  >|__|   
        \/         \/                            \/             \/                    \/            
    """)

    print("\n\n#" + ("-" * 100) + "#\n\n")
    print(" - CDP-CRAWLER v1.2.0 by Dakotah Hurda.")
    print(" - This script will CDP-crawl from each of the sites' seed devices as defined in Netbox.")
    print(" - Hold CTRL+C at any time to force the program to close.")
    print("\n\n#" + ("-" * 100) + "#\n\n")
    print()
    input("Press ENTER to continue with script.")

welcomeMessage()

logger = myLogger(__name__)

load_dotenv() # This loads in all environment variables. You should have a .env file configured with the necessary API tokens and whatnot.

netbox_access_token = os.environ.get('NETBOX-ACCESS-TOKEN') # netbox_access_token is equal to the environment variable set in the .env file.

site_data = nb_retrieve_all_sites(netbox_access_token) # Netbox script to grab a list of all sites' seed-devices from Netbox thru API.

all_site_CDP_data = cdpMasterDictHandler(site_data) # Pass the site_data to the cdpDiscoveryFunctions module.

with open('.\output\cdp-dump.yml', 'w+') as outfile:
    yaml.dump(all_site_CDP_data.site_data_dict, outfile)
    print("Stored device scan-data in .\output\cdp-dump.yml")

netbox_data_handler(all_site_CDP_data.site_data_dict)
