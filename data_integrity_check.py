import os
import re
import pynetbox

from pprint import pprint
from logger import myLogger
from dotenv import load_dotenv

class data_integrity_check():
    
    def dns_check(hostname, ip_addr) -> tuple:
        """
        This function takes in a hostname and an IP address, then checks DNS for accuracy.

        Returns [RESULT, error_message]

        The RESULT indicates that all DNS checks return TRUE:
            - Hostname resolves to a single IP
            - Resolved IP == Given IP
            - Given IP resolves to a single hostname
            - Resolved hostname == Given hostname

        The error_message describes what the issue is, so other functions can perform cleanup actions based on the result. 
        """
        from dns_resolve_hostname import dns_resolve_hostname

        def hostname_check(hostname):
            """
            This function evaluates the given hostname for DNS accuracy. 

            The hostname must resolve to a single address, and the address must match the original IP. 

            The IP must resolve to a single hostname, and the hostname must match the original hostname. 
            """
            hostname_dns_type = dns_resolve_hostname.dns_determiner(hostname)
            hostname_dns_output = dns_resolve_hostname.dns_reporter(hostname, hostname_dns_type)    

            if len(hostname_dns_output) == 1: # A single DNS entry is found for the given hostname. This is the desired outcome. 
                hostname_answer = hostname_dns_output[0] # This gives us the IP address found in DNS for the hostname. 
                # print(f"DNS answer found for {hostname}: {hostname_answer}")
                logger.debug(f"DNS answer found for {hostname}: {hostname_answer}")

                hostname_reversion_check = dns_resolve_hostname.dns_determiner(hostname_answer) # This takes the IP address we found, and resolves it to check if it matches the original hostname. 
                hostname_reversion_check = dns_resolve_hostname.dns_reporter(hostname_answer, hostname_reversion_check)

                # print(f"DEBUG: {hostname_reversion_check}")

                if len(hostname_reversion_check) >= 1:
                    if '.' in hostname_reversion_check:
                        hostname_reversion_check = hostname_reversion_check.split('.')[0] # Removes the .mke.cnty suffix for easier comparison
                
                else: # This is used if there are many values in the returned hostname check.
                    # print(f"DEBUG-FAILURE: {hostname_reversion_check}")
                    hostname_reversion_check = False

                print(f"Hostname: {hostname} Reversion_check: {hostname_reversion_check}")

                if hostname_reversion_check == hostname:
                    return([hostname_answer, True])
                else:
                    return([hostname_answer, False])

            elif len(hostname_dns_output) > 1: # Multiple DNS entries detected for the given hostname. 
                hostname_answer = hostname_dns_output
                print(f"Multiple DNS entries found for hostname {hostname}: {hostname_answer}")
                logger.error(f"Multiple DNS entries found for hostname {hostname}: {hostname_answer}")
                return(hostname_answer, False)
                
            else: # No DNS entries found for the given hostname. 
                hostname_answer = 'NOTFOUND'
                print(f"No DNS entry found for hostname {hostname}")
                logger.error(f"No DNS entry found for hostname {hostname}")
                return(hostname_answer, False)
        
        def ip_check(ip_addr):
            """
            This function evaluates the given ip_addr for DNS accuracy. 
            """
            # print(f"DEBUG: {ip_addr}")
            ip_dns_type = dns_resolve_hostname.dns_determiner(ip_addr) # Gives us the hostname(s) associated with the IP in DNS. 
            # print(f"DEBUG: {ip_dns_type}")
            ip_dns_output = dns_resolve_hostname.dns_reporter(ip_addr, ip_dns_type)
            
            # print(f"DEBUG: {ip_dns_output}")
            if len(ip_dns_output) >= 1: # A single DNS entry is found for the given hostname. This is the desired outcome. 
                ip_answer = ip_dns_output # This gives us the hostname(s) found in DNS for the IP address.
                # print(f"DEBUG1: {ip_answer}")
                if '.' in ip_answer: 
                    ip_answer = ip_answer.split('.')[0]
                # print(f"DEBUG2: {ip_answer}")
                print(f"DNS answer found for IP {ip_addr}: {ip_answer}")
                logger.debug(f"DNS answer found for IP {ip_addr}: {ip_answer}")

                ip_reversion_check = dns_resolve_hostname.dns_determiner(ip_answer) # This takes the hostname we found, and resolves it to check if it matches the original hostname. 
                ip_reversion_check = dns_resolve_hostname.dns_reporter(ip_answer, ip_reversion_check)
                
                print(f"IP: {ip_addr} Reversion_check: {ip_reversion_check[0]}")
                
                if len(ip_reversion_check) >= 1:
                    # if '.' in ip_reversion_check[0]:
                    #     ip_reversion_check = ip_reversion_check[0].split('.')[0]
                    
                        if ip_reversion_check[0] == ip_addr:
                            # print(f"DEBUG3-SUCCESS: {ip_reversion_check}, {ip_addr}")
                            return(ip_answer, True)
                        else:
                            # print(f"DEBUG3-FAIL: {ip_reversion_check}, {ip_addr}")
                            return(ip_answer, False)

                elif len(ip_reversion_check) == 2: # Useful for parsing out values like ['hostname', 'hostname.domain.com']
                    item1 = ip_reversion_check[0]
                    item2 = ip_reversion_check[1]

                    if '.' in item1:
                        item1 = item1.split('.')[0]

                    if '.' in item2:
                        item2 = item2.split('.')[0]

                    if item1 == item2:
                        ip_reversion_check = item1
                    
                    else:
                        ip_reversion_check = False
                
                else: # This is used if there are many values in the returned hostname check.
                    ip_reversion_check = False
                
                
            else: # No DNS entries found for the given hostname. 
                ip_answer = 'NOTFOUND'
                print(f"No DNS entry found for hostname {hostname}")
                logger.error(f"No DNS entry found for hostname {hostname}")
                return(ip_answer, False)
        
        print(f"Checking {hostname}, {ip_addr}")
        hostname_answer, hostname_dns_integrity = hostname_check(hostname)
        
        if len(ip_addr) >= 1:
            ip_answer, ip_dns_integrity = ip_check(ip_addr)
        else:
            print(f"No IP address provided for hostname {hostname}")
            logger.critical(f"No IP address provided for hostname {hostname}")
            ip_answer, ip_dns_integrity = 'NOTPROVIDED', False

        # print(hostname_answer, hostname_dns_integrity)
        # print(ip_answer, ip_dns_integrity)
        
        if ip_answer == 'NOTPROVIDED':
            error_message = 'ip_not_provided'
            return(False, error_message)

        if hostname_answer == ip_addr:
            if ip_answer == hostname:
                if hostname_dns_integrity == True:
                    if ip_dns_integrity == True:
                        error_message = 'NONE'
                        print(f"DNS successfully validated, all values look good. Details: PROVIDED_HOSTNAME: {hostname} , PROVIDED_IP_ADDR: {ip_addr} , HOSTNAME_DNS_ANSWER: {hostname_answer} , IP_DNS_ANSWER: {ip_answer}")
                        logger.debug(f"DNS successfully validated, all values look good. Details: PROVIDED_HOSTNAME: {hostname} , PROVIDED_IP_ADDR: {ip_addr} , HOSTNAME_DNS_ANSWER: {hostname_answer} , IP_DNS_ANSWER: {ip_answer}")
                        return(True, error_message)

                    else: 
                        error_message = 'ip_dns_integrity == FALSE'
                        print(f"IP DNS integrity is FALSE. Details: PROVIDED_HOSTNAME: {hostname} , PROVIDED_IP_ADDR: {ip_addr} , HOSTNAME_DNS_ANSWER: {hostname_answer} , IP_DNS_ANSWER: {ip_answer}")
                        logger.error(f"IP DNS integrity is FALSE. Details: PROVIDED_HOSTNAME: {hostname} , PROVIDED_IP_ADDR: {ip_addr} , HOSTNAME_DNS_ANSWER: {hostname_answer} , IP_DNS_ANSWER: {ip_answer}")
                        return(False, error_message)
                else:
                    error_message = 'hostname_dns_integrity == FALSE'
                    print(f"Hostname DNS integrity is FALSE. Details: PROVIDED_HOSTNAME: {hostname} , PROVIDED_IP_ADDR: {ip_addr} , HOSTNAME_DNS_ANSWER: {hostname_answer} , IP_DNS_ANSWER: {ip_answer}")
                    logger.error(f"Hostname DNS integrity is FALSE. Details: PROVIDED_HOSTNAME: {hostname} , PROVIDED_IP_ADDR: {ip_addr} , HOSTNAME_DNS_ANSWER: {hostname_answer} , IP_DNS_ANSWER: {ip_answer}")
                    return(False, error_message)
            else:
                error_message = 'dns_ip_answer != hostname'
                print(f"DNS IP answer != provided hostname. Details: PROVIDED_HOSTNAME: {hostname} , PROVIDED_IP_ADDR: {ip_addr} , HOSTNAME_DNS_ANSWER: {hostname_answer} , IP_DNS_ANSWER: {ip_answer}")
                logger.error(f"DNS IP answer != provided hostname. Details: PROVIDED_HOSTNAME: {hostname} , PROVIDED_IP_ADDR: {ip_addr} , HOSTNAME_DNS_ANSWER: {hostname_answer} , IP_DNS_ANSWER: {ip_answer}")
                return(False, error_message)
        else:
            error_message = "dns_hostname_answer != ip_addr"
            print(f"DNS Hostname answer != provided IP addr. Details: PROVIDED_HOSTNAME: {hostname} , PROVIDED_IP_ADDR: {ip_addr} , HOSTNAME_DNS_ANSWER: {hostname_answer} , IP_DNS_ANSWER: {ip_answer}")
            logger.error(f"DNS Hostname answer != provided IP addr. Details: PROVIDED_HOSTNAME: {hostname} , PROVIDED_IP_ADDR: {ip_addr} , HOSTNAME_DNS_ANSWER: {hostname_answer} , IP_DNS_ANSWER: {ip_answer}")
            return(False, error_message)

    def hostname_check(hostname, site) -> tuple:
        """
        This function will evaluate the given hostname to answer TRUE/FALSE if it matches Connectivity's naming standards. 

        Returns [RESULT, error_message]

        The RESULT will be TRUE if the following conditions are TRUE:
            - Meets hyphenated-field check
            - Each hyphenated field matches its specific regex

        The error_message indicates what issue is found, so other scripts can take corrective action.
        """
    # --- Defining a few starter variables. --- #

        name_hyphen_check = hostname.split("-")
        hyphen_check_bool = False # Used for checking how many hyphenated fields are in the name. 
        name_test_bool = False # Used for checking each of the hyphenated fields in the name for accuracy. 

    # --- This section is for checking hyphenated fields --- #

        if len(name_hyphen_check) <= 3:
            # print(f"Name {hostname} fails due to not enough hyphenated fields.")
            error_message = 'not_enough_fields'
            logger.error(f"Hostname {hostname} failed hostname_check. Details: {error_message}")
            hyphen_check_bool = False

        if len(name_hyphen_check) == 4 or len(name_hyphen_check) == 5:
            # print(f"Name {hostname} succeeds number of hyphenated fields.")
            error_message = "None"
            logger.debug(f"Hostname {hostname} succeeded hyphenated-fields hostname_check.")
            hyphen_check_bool = True
        
        if len(name_hyphen_check) >= 6:
            # print(f"Name {hostname} fails due to too many hyphenated fields.")
            error_message = 'too_many_fields'
            logger.error(f"Hostname {hostname} failed hostname_check. Details: {error_message}")
            hyphen_check_bool = False
        
    # --- This section is for checking the hostname to see if it matches a regex check --- # 

        if hyphen_check_bool == True: # If the name passes the hyphenated fields check, we can start our regex check on it. 
            
            site = site # Redundantly defined here for better visibility. 
            location_list = [] # If a matching site is found, another API call to Netbox to retrieve only the potential buildings for that site in Netbox            
            rack_list = [] # If matching locations are found, pull all the netracks associated with that location. 
                
            for loc in loc_dict[site]['locations'].keys():
                location_list.append(loc)

                for rack in loc_dict[site]['locations'][loc]['netracks'].keys():
                    rack_list.append(rack)
            
            if len(name_hyphen_check) == 4: # Example hostname: ch-fl01-nr01-sw01
                
                field1, field1_check = name_hyphen_check[0], False # ch
                field2, field2_check = name_hyphen_check[1], False # fl01
                field3, field3_check = name_hyphen_check[2], False # nr01
                field4, field4_check = name_hyphen_check[3], False # sw01

            # --- Checking the first hyphenated field to see if it matches its site. --- # 
                if field1 == site:
                    field1_check = True
                    if error_message == "None":
                        error_message = "None"
                else:
                    if error_message == "None":
                        error_message = f"Hostname {hostname} failed field1 check: field1 does not match site_name"
                    else:
                        error_message = error_message
                
            # --- Checking the second hyphenated field to see if it matches its site's locations. --- #
                if field2 in location_list:
                    field2_check = True
                    if error_message == "None":
                        error_message = 'None'
                else:
                    if error_message == "None":
                        error_message = f"Hostname {hostname} failed field2 check: field2 does not match any locations for its site"
                    else:
                        error_message = error_message

            # --- Checking the third hyphenated field to see if it matches its location's netracks. --- #
                if field3 in rack_list:
                    field3_check = True
                    if error_message == "None":
                        error_message = 'None'
                else:
                    if error_message == "None":
                        error_message = f"Hostname {hostname} failed field3 check: field3 does not match any netracks for its location"
                    else:
                        error_message = error_message

            # --- Checking the fourth hyphenated field to see if it matches a simple regex for the device type + number. --- # 
                regex_pattern = "sw|ds|rt|ap\d\d" # Examples: sw01, ds01, rt02, ap12, etc. 
                if re.match(regex_pattern, field4):
                    field4_check = True
                    if error_message == "None":
                        error_message = 'None'
                else:
                    if error_message == "None":
                        error_message = f"Hostname {hostname} failed field4 check: field4 does not match regex pattern"
                    else:
                        error_message = error_message
                
            # --- Final evaluation of all checks. --- # 
                if field1_check == True:
                    if field2_check == True:
                        if field3_check == True:
                            if field4_check == True:
                                return(True, 'pass')
                            else:
                                return(False, error_message)
                        else:
                            return(False, error_message)
                    else:
                        return(False, error_message)
                else:
                    return(False, error_message)

            # if len(name_hyphen_check) == 5:
            #     if len(name_hyphen_check) == 4:
                
            #         field1, field1_check = name_hyphen_check[0], False
            #         field2, field2_check = name_hyphen_check[1], False
            #         field3, field3_check = name_hyphen_check[2], False
            #         field4, field4_check = name_hyphen_check[3], False
            #         field5, field5_check = name_hyphen_check[4], False

            #         if field1 == site:
            #             field1_check = True
            #             field1_error_message = 'None'
            #         else:
            #             field1_error_message = f"Hostname {hostname} failed field1 check -- field1 does not match any site"
                    
            #         if field2 in location_list:
            #             field2_check = True
            #             field2_error_message = 'None'
            #         else:
            #             field2_error_message = f"Hostname {hostname} failed field2 check -- field2 does not match any location for its site"

            #         if field3 in rack_list:
            #             field3_check = True
            #             field3_error_message = 'None'
            #         else:
            #             field3_error_message = f"Hostname {hostname} failed field3 check -- field3 does not match any netrack for its location"
        
        elif hyphen_check_bool == False: # If the name fails, return the specific fail message. 
            
            return(False, error_message)

    def compile_site_locations() -> dict:
        """
        This function retrieves all sites and their respective locations from Netbox, then stores them in a usable dictionary. 
        """
        sites = nb.dcim.sites.all()
        locations = nb.dcim.locations.all()
        netracks = nb.dcim.racks.all()

        loc_dict = {}

        for site in sites:
            loc_dict[site.slug] = {}
            loc_dict[site.slug]['locations'] = {}

        for loc in locations:
            if loc.site.slug in loc_dict.keys():
                
                loc_name = loc.slug
                loc_name = loc_name.split("-")[1]

                loc_dict[loc.site.slug]['locations'][loc_name] = {}
                loc_dict[loc.site.slug]['locations'][loc_name]['netracks'] = {}

        for rack in netracks:
            if rack.site.slug in loc_dict.keys():
                if rack.location.slug in loc_dict[rack.site.slug]['locations'].keys():
                    loc_dict[rack.site.slug]['locations'][rack.location.slug]['netracks'][rack] = {}

        return(loc_dict)

    def __init__(self, device, device_data_dict, site):
        global logger, netbox_access_token, netbox_url, nb, loc_dict, site_name
        logger = myLogger(__name__)
        
        load_dotenv()
        site_name = site
        netbox_access_token = os.environ.get('NETBOX-ACCESS-TOKEN')
        netbox_url = 'https://NETBOX-URL-GOES-HERE'
        nb = pynetbox.api(netbox_url, token=netbox_access_token)

        loc_dict = data_integrity_check.compile_site_locations()

        # self.dns_check, self.dns_check_message = data_integrity_check.dns_check(device, device_data_dict['ip_addr'])
        # print(self.dns_check, self.dns_check_message) TO-DO: Create functions with the associated error messages to make fixes or create tickets accordingly. 


        self.hostname_check, self.hostname_check_message = data_integrity_check.hostname_check(device, site)

        print(device, self.hostname_check, self.hostname_check_error)
