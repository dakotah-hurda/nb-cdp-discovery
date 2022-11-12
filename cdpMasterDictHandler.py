import os
import time
import logging, logging.handlers
from pprint import pprint
from netmiko import ConnectHandler
from scan_cdp_device import scan_cdp_device
from scan_cdp_AP_neighbor import scan_cdp_AP_neighbor
from logger import myLogger

class cdpMasterDictHandler():
    """
    This is the main class that will handle all actions related to editing the master dictionary. 
    
    All other classes and functions are only used to collect or parse the data to be put into the master_dictionary.
    """

    def scan_cdp_neighbors(site_data, site, cdp_nei_scan_list):
        """
        This function scans CDP neighbors that are not APs, phones, or cameras, and edits the site_data dict.
        """

        for cdp_neighbor in cdp_nei_scan_list:
            logger.debug(f"Evaluating cdp_neighbor {cdp_neighbor}...")
            
            if cdp_neighbor not in site_data[site]['device_scan_data'].keys(): # If the neighbor is NOT in the master_dict already
                logger.debug(f"CDP neighbor {cdp_neighbor} not found in device_scan_data keys. Initializing device_scan_data key for neighbor.")

                site_data[site]['device_scan_data'][cdp_neighbor] = {}

                logger.debug(f"Beginning CDP neighbor-scan on {cdp_neighbor}")
                cdp_device_data = scan_cdp_device(cdp_neighbor, username, password)
                
                logger.debug(f"CDP neighbor scan completed for {cdp_neighbor}. Adding data to its device_scan_data key entry.")
                site_data[site]['device_scan_data'][cdp_neighbor]['ip_addr'] = cdp_device_data.ip_addr
                site_data[site]['device_scan_data'][cdp_neighbor]['hostname'] = cdp_device_data.hostname
                site_data[site]['device_scan_data'][cdp_neighbor]['dns_name'] = cdp_device_data.dns_name
                site_data[site]['device_scan_data'][cdp_neighbor]['platform'] = cdp_device_data.platform
                site_data[site]['device_scan_data'][cdp_neighbor]['stp_macaddress'] = cdp_device_data.stp_macaddress
                site_data[site]['device_scan_data'][cdp_neighbor]['stp_blockedports'] = cdp_device_data.stp_blockedports
                site_data[site]['device_scan_data'][cdp_neighbor]['serial_num'] = cdp_device_data.serial_num
                site_data[site]['device_scan_data'][cdp_neighbor]['cdp_neighbors'] = cdp_device_data.cdp_neighbors
                site_data[site]['device_scan_data'][cdp_neighbor]['scanned'] = cdp_device_data.scanned    

            elif cdp_neighbor in site_data[site]['device_scan_data'].keys(): # If the neighbor IS in the master_dict already
                logger.debug(f"CDP neighbor {cdp_neighbor} found in device_scan_data keys. Evaluating 'scanned' flag.")
                
                if site_data[site]['device_scan_data'][cdp_neighbor]['scanned'] == True: # If the 'scanned' key is set to TRUE, skip the host. 
                    logger.debug(f"'scanned' flag set to TRUE. Skipping neighbor {cdp_neighbor}")
                    continue
                
                else: # And the 'scanned' flag is set to FALSE...
                    logger.debug(f"'scanned' flag set to FALSE. Scanning neighbor.")
                    cdp_device_data = scan_cdp_device(cdp_neighbor, username, password)

                    logger.debug(f"CDP neighbor scan completed for {cdp_neighbor}. Adding data to its device_scan_data key entry.")
                    site_data[site]['device_scan_data'][cdp_neighbor]['ip_addr'] = cdp_device_data.ip_addr
                    site_data[site]['device_scan_data'][cdp_neighbor]['hostname'] = cdp_device_data.hostname
                    site_data[site]['device_scan_data'][cdp_neighbor]['dns_name'] = cdp_device_data.dns_name
                    site_data[site]['device_scan_data'][cdp_neighbor]['platform'] = cdp_device_data.platform
                    site_data[site]['device_scan_data'][cdp_neighbor]['platform'] = cdp_device_data.platform
                    site_data[site]['device_scan_data'][cdp_neighbor]['serial_num'] = cdp_device_data.serial_num
                    site_data[site]['device_scan_data'][cdp_neighbor]['cdp_neighbors'] = cdp_device_data.cdp_neighbors
                    site_data[site]['device_scan_data'][cdp_neighbor]['scanned'] = cdp_device_data.scanned         
            
            pprint(site_data[site]['device_scan_data'][cdp_neighbor])

    def ssh_credential_test(username, password) -> bool:
    
        credential_test_connection_details = { 
            "device_type": "cisco_ios",
            "host": "S_CHG2AC9500_User1", # How can we remove this hard-coded variable?
            "username": username,
            "password": password,

        }

        try:
            
            with ConnectHandler(**credential_test_connection_details) as net_connect: 
                net_connect.find_prompt()
                time.sleep(1)
                logger.info(f"Credential test on device {credential_test_connection_details['host']} successful. Proceeding with script.")
                
                return True

        except Exception as e:
            logger.critical(e)
            return False
    
    def __init__(self, site_data):
        
        global master_dictionary, username, password, cdp_scan_depth, logger, failed_ssh_devices # This makes passing these variables into functions much easier.

        logger = myLogger(__name__)

        username = os.environ.get('SSH-USERNAME') # SSH username
        password = os.environ.get('SSH-PASSWORD') # SSH password 
        cdp_scan_depth = os.environ.get('CDP-SCAN-DEPTH') # This line can be edited to change how many levels deep you want CDP scanning to occur.
        failed_ssh_devices = []

        if cdpMasterDictHandler.ssh_credential_test(username, password): # Runs credential_test function to ensure no accidental account lockouts if you typed your password in wrong.         
            logger.debug('SSH credential test has passed. Moving onto scanning functions.')

            site_list = []
            
            for site in site_data.keys():
                site_list.append(site)

            for site in site_list:
                
                site_data[site]['device_scan_data'] = {}

                cdp_seed_device = site_data[site]['cdp_seed_device']
                site_data[site]['device_scan_data'][cdp_seed_device] = {}
                
                #############################################################################
                logger.debug(f"Beginning seed-device scan on {cdp_seed_device} for site {site}...")
                print(f"Beginning seed-device scan on {cdp_seed_device} for site {site}...")

                seed_device_data = scan_cdp_device(cdp_seed_device, username, password)
                
                print(f"Seed-device scan completed on {cdp_seed_device}.")
                logger.debug(f"Seed-device scan completed on {cdp_seed_device}.")
                #############################################################################
                
                site_data[site]['device_scan_data'][cdp_seed_device]['ip_addr'] =          seed_device_data.ip_addr
                site_data[site]['device_scan_data'][cdp_seed_device]['platform'] =         seed_device_data.platform
                site_data[site]['device_scan_data'][cdp_seed_device]['serial_num'] =       seed_device_data.serial_num
                site_data[site]['device_scan_data'][cdp_seed_device]['stp_macaddress'] =   seed_device_data.stp_macaddress
                site_data[site]['device_scan_data'][cdp_seed_device]['stp_blockedports'] = seed_device_data.stp_blockedports
                site_data[site]['device_scan_data'][cdp_seed_device]['cdp_neighbors'] =    seed_device_data.cdp_neighbors
                site_data[site]['device_scan_data'][cdp_seed_device]['scanned'] =          seed_device_data.scanned

                # At this point, the site's seed device is fully scanned and stored in the site_data dictionary. 
                # Now, we can start looping through the seed device's CDP neighbors and scanning them. 
                
                ap_scan_list = [] # Since APs are scanned differently, we make a separate list for them. 
                unfound_aps_list = []
                iter_count = 0
                
                logger.info(f"Scan depth set to {cdp_scan_depth}. This can be changed in the .env file.")
                for _ in range(int(cdp_scan_depth) - 1 ): # The _ is a throwaway variable. Loop through the "range" of the cdp_scan_depth variable, but since it starts from 0, subtract 1 to equal user input.
                    
                    iter_count += 1 # Just for visually tracking the loop progress. Not needed for any other reason.
                    
                    print("\n" + ("*" * 80))
                    print(f"iter count: {iter_count}")
                    print(("*" * 80) + "\n")
                    
                    cdp_nei_scan_list = [] # This list will be used to store all devices that will be scanned like a switch or router. 

                    for device in site_data[site]['device_scan_data'].keys():
                        if site_data[site]['device_scan_data'][device]['platform'] == False:
                            continue

                        else:
                            for cdp_neighbor in site_data[site]['device_scan_data'][device]['cdp_neighbors'].keys():
                            
                                if site_data[site]['device_scan_data'][device]['cdp_neighbors'][cdp_neighbor]['is_ap'] == True:
                                    logger.debug(f"Adding CDP-Neighbor {cdp_neighbor} to AP scan_list due to AP flag set to TRUE")
                                    ap_scan_list.append([device, cdp_neighbor]) # Use a tuple to track what device the AP is connected to. Collect data about all APs then pass to scan_cdp_AP_neighbor class outside of scan_depth loop.

                                elif site_data[site]['device_scan_data'][device]['cdp_neighbors'][cdp_neighbor]['is_ap'] == False:
                                    if site_data[site]['device_scan_data'][device]['cdp_neighbors'][cdp_neighbor]['is_camera'] == False:
                                        if site_data[site]['device_scan_data'][device]['cdp_neighbors'][cdp_neighbor]['is_phone'] == False:
                                            logger.debug(f"Adding CDP-Neighbor {cdp_neighbor} to scan_list due to AP, camera, and phone flags set to FALSE")
                                            cdp_nei_scan_list.append(cdp_neighbor)
                    
                    cdpMasterDictHandler.scan_cdp_neighbors(site_data, site, cdp_nei_scan_list)
                
                ap_output = scan_cdp_AP_neighbor(site_data, site, ap_scan_list, username, password) # All discovered APs were added to the 'ap_scan_list' as a tuple with their corresponding switch as the opposite value in the tuple.
                for unfound_ap in ap_output.unfound_aps:
                    unfound_aps_list.append(unfound_ap)

        for site in site_data.keys():
            for device in site_data[site]['device_scan_data'].keys():
                if site_data[site]['device_scan_data'][device]['platform'] == False:
                    failed_ssh_devices.append(device)
        
        if len(failed_ssh_devices) >= 1:
            logger.critical(f"""
            The following devices were unable to be SSH'd into. Please evaluate their connectivity and try scanning again:

            {failed_ssh_devices}
            """)
        
        if len(unfound_aps_list) >= 1:
            logger.critical(f"""
            The following APs were not found on either the 5k or the 9k controllers:

            {unfound_aps_list}
            """)

        self.site_data_dict = site_data