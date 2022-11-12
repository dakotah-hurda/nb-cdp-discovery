import logging, logging.handlers

from logger import myLogger
from netmiko import ConnectHandler
from pprint import pprint
from dns_resolve_hostname import dns_resolve_hostname


class scan_cdp_AP_neighbor():
    """
    This class is intended to discover data about CDP-discovered APs.
    """
    
    def wlc_5k_ssh(ap_list, username, password) -> str:
        """
        This function SSHs into the 5k WLC and retrieves serial_number info for the provide ap_name.

        Returns as a string.
        """
        controller = 'wlc_mer_5520'
        logger.debug(f"Beginning SSH scan on {controller}.")      

        connection_details = { 
            "device_type": "cisco_wlc_ssh",
            "host": controller,
            "username": username,
            "password": password,
            }
        
        with ConnectHandler(**connection_details) as net_connect:
            for ap in ap_list:
                command = f'show ap inventory {ap}'
                output = net_connect.send_command(command)
                found = False
                
                for line in output.splitlines():
                
                    if 'SN: ' in line: 
                        found = True
                        ap_serialnum = line.split('SN: ')[1]
                        logger.debug(f"Found serial_num {ap_serialnum} for {ap} on {controller}")
                        output_list.append([ap, ap_serialnum])                    
                    else:
                        continue 
                
                if not found:
                    wlc9k_search_list.append(ap)
            
    def wlc_9k_ssh(wlc9k_search_list, username, password) -> str:
        """
        This function SSHs into the 9k WLC and retrieves serial_number info for the provide ap_name.

        Returns as a string.
        """
        controller = 'cjf-mer-conversion-wlc01_mgmt'
        logger.debug(f"Beginning SSH scan on {controller}.")      

        connection_details = { 
            "device_type": "cisco_wlc_ssh",
            "host": controller,
            "username": username,
            "password": password,
            }

        with ConnectHandler(**connection_details) as net_connect:
            for ap in wlc9k_search_list:
                command = f'show ap name {ap} inventory'
                output = net_connect.send_command(command)
                found = False
                
                for line in output.splitlines():
                
                    if 'SN: ' in line: 
                        found = True
                        ap_serialnum = line.split('SN: ')[1]
                        logger.debug(f"Found serial_num {ap_serialnum} for {ap} on {controller}")
                        output_list.append([ap, ap_serialnum])                    
                    else:
                        continue 
                
                if not found:
                    unfound_AP_list.append(ap)

    def ap_serial_discovery(ap_name, username, password):
        """
        This function is intended to discover the serial number of a given AP. 
        
        It works by calling other sub-functions that make SSH sessions with all WLCs and search them for serial info for the provided AP. 
        """

        ap_serialnum = scan_cdp_AP_neighbor.wlc_5k_ssh(ap_name, username, password) # Check the 5k WLC for the AP info first. 

        if ap_serialnum == False: # If the 5k returns 'False', that means the AP was not found on the WLC.
            ap_serialnum = scan_cdp_AP_neighbor.wlc_9k_ssh(ap_name, username, password) # Pass the info to the 9k WLC for secondary discovery.
            
            if ap_serialnum == False: # If the serial still isn't found on the 9k, return 'NOTFOUND'
                return('NOTFOUND')
            else:
                return(ap_serialnum)
        else: 
            return(ap_serialnum)

    def format_apmacaddress(unformatted_macaddress) -> str:
        """
        This function formats 'Cisco'-style MACs into normalized MACs.

        e.g. aaaa.bbbb.cccc -> aa:aa:bb:bb:cc:cc
        """
        mac_string = unformatted_macaddress.replace('.', '') # Removes the dots in the MAC string.

        formatted_mac = ':'.join(mac_string[i:i+2] for i in range(0,12,2)) # Places colons in the correct places. 
        logger.debug(f"Raw MAC: {unformatted_macaddress} Formatted MAC: {formatted_mac}")
        return(formatted_mac)

    def discoverApSerialNumbers(ap_list, username, password) -> list:
        """
        Takes in a list of AP names and returns a list of tuples. 

        Tuple format: [ap_name, serial]
        """
        global output_list, wlc9k_search_list, unfound_AP_list

        output_list = []
        wlc9k_search_list = []
        unfound_AP_list = []
        
        print("\nBeginning AP discovery on both wireless-controllers...\n")
        
        # Start an SSH session with the 5k and look for serials. If found, append to output_list. If not found, do nothing?
        scan_cdp_AP_neighbor.wlc_5k_ssh(ap_list, username, password)

        if len(wlc9k_search_list) >= 1:
            scan_cdp_AP_neighbor.wlc_9k_ssh(wlc9k_search_list, username, password)

        if len(unfound_AP_list) >= 1:
            logger.critical(f"APs not found on either controller:\n\n{unfound_AP_list}\n\n")

        return(output_list, unfound_AP_list)

    def __init__(self, site_data, site, ap_scan_list, username, password):
        
        global logger
        
        logger = myLogger(__name__)

        ap_list = []
        unfound_aps = []
        for ap in ap_scan_list:

            parent_switch = ap[0]
            ap = ap[1]
            ap_list.append(ap)

            # pprint(site_data[site]['device_scan_data'][parent_switch]['cdp_neighbors'][ap]) <-- Use this to show that the dictionary data is being successfully passed to this module.

            ip_addr =       site_data[site]['device_scan_data'][parent_switch]['cdp_neighbors'][ap]['ip_addr']
            platform =      site_data[site]['device_scan_data'][parent_switch]['cdp_neighbors'][ap]['platform']
            ap_port =       site_data[site]['device_scan_data'][parent_switch]['cdp_neighbors'][ap]['remote_port']
            switch =        parent_switch
            switchport =    site_data[site]['device_scan_data'][parent_switch]['cdp_neighbors'][ap]['local_port']
            ap_macaddress = scan_cdp_AP_neighbor.format_apmacaddress(site_data[site]['device_scan_data'][parent_switch]['cdp_neighbors'][ap]['ap_macaddress'])
            
            dns_output = dns_resolve_hostname(ap)
            dns_name = dns_output.dns_hostname

            if '.' in dns_name:
                dns_name = dns_name.split('.')[0]
            
            site_data[site]['device_scan_data'][ap] = {}
            site_data[site]['device_scan_data'][ap]['hostname'] =      ap
            site_data[site]['device_scan_data'][ap]['ip_addr'] =       ip_addr
            site_data[site]['device_scan_data'][ap]['platform'] =      platform
            site_data[site]['device_scan_data'][ap]['ap_port'] =       ap_port
            site_data[site]['device_scan_data'][ap]['switch'] =        switch
            site_data[site]['device_scan_data'][ap]['switchport'] =    switchport
            site_data[site]['device_scan_data'][ap]['ap_macaddress'] = ap_macaddress
           
            if ap == dns_name:
                site_data[site]['device_scan_data'][ap]['dns_hostname'] = dns_name
            else:
                site_data[site]['device_scan_data'][ap]['dns_hostname'] = ''
                logger.error(f'DNS name does match hostname for {ap} {ip_addr}')
        
        # Here we'll make a list of all the AP names, then pass them ALL into an SSH session with the 5k and 9k WLCs for faster discovery.
        ap_serial_data = scan_cdp_AP_neighbor.discoverApSerialNumbers(ap_list, username, password)
        
        for ap in ap_serial_data[0]:
            ap_name =    ap[0]
            serial_num = ap[1]

            site_data[site]['device_scan_data'][ap_name]['serial_num'] = serial_num
        
        for unfound_ap in ap_serial_data[1]:
            unfound_aps.append(unfound_ap)

        self.unfound_aps = unfound_aps
