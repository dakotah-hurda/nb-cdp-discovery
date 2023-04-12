class scan_cdp_device():

    def retrieve_macaddress(device, local_port, username, password):
        """
        This function is intended to SSH into a switch a retrieve a specific interface's MAC table entries.
        """
        import re
        from netmiko import ConnectHandler
        
        logger.debug(f"Beginning SSH session to {device} to retrieve MAC address from port {local_port}")
        
        connection_details = { 
            "device_type": "cisco_ios",
            "host": device,
            "username": username,
            "password": password,
            }

        try:
        
            with ConnectHandler(**connection_details) as net_connect:
                
                command = f'show mac address-table interface {local_port} | i STATIC|DYNAMIC'

                mac_output = net_connect.send_command(command) # Reference output string: '250    7079.b362.9a7a    STATIC      Gi5/0/7 '
                

                if "STATIC" in mac_output:
                    ap_macaddress = mac_output.split(" STATIC")[0]
                elif "DYNAMIC" in mac_output:
                    ap_macaddress = mac_output.split(" DYNAMIC")[0]

                ap_macaddress = re.sub(' +', ' ', ap_macaddress).strip()

                ap_macaddress = ap_macaddress.split(" ")[1].strip()
                
                logger.debug(f"Returning AP MAC address {ap_macaddress} found through regex parsing.")
                return(ap_macaddress)

        except Exception as e: 
            logger.debug(f"Failed to establish SSH session to {device} to retrieve MAC address from port {local_port} Reason: \n\n {e}")
            return()

    def parse_cdp_nei_data(device, cdp_neighbors_data, username, password):
        """
        This function passes in a device_name and its corresponding CDP Neighbor Data.

        The function parses out the raw CDP data and returns a complete, formatted dictionary of the good stuff.
        """

        cdp_neighbors = {}
        
        cdp_neighbor_list = cdp_neighbors_data.split("-------------------------") # Splitting up the CDP output into something usable

        for cdp_neighbor in cdp_neighbor_list[1:]: # This for-loop parses out the CDP data and collects a few relevant variables, then stores them in a dictionary.
            
            is_ap = False # Sets these variables up so they don't accidentally get passed from one neighbor to the next. 
            is_camera = False
            is_phone = False

            for line in cdp_neighbor.splitlines():
                
                if "Device ID:" in line:
                    device_id = line.split(": ")[1]
                    if '.' in device_id: # Filters out '.domain.com' suffixes
                        device_id = device_id.split('.')[0]
                
                if "Port ID (outgoing port):" in line:
                    remote_port = line.split(",  ")[1].split("Port ID (outgoing port): ")[1]

                if "Interface:" in line:
                    local_port = line.split(",  ")[0].split("Interface: ")[1]
                
                if "IP address:" in line:
                    ip_addr = line.split(",  ")[0].split("IP address: ")[1]

                if "Platform: " in line:
                    if "Platform: cisco" in line:
                        neighbor_platform = line.split("Platform: cisco ")[1]
                    else:
                        neighbor_platform = line.split("Platform: ")[1]
                    
                    neighbor_platform = neighbor_platform.split(",  Capabilities:")[0]
            
            if "Trans-Bridge" in cdp_neighbor:
                logger.debug(f"Setting is_ap flag to TRUE for host {device_id} due to 'Trans-Bridge' being found in its CDP Capabilities.")
                is_ap = True

                ap_macaddress = scan_cdp_device.retrieve_macaddress(device, local_port, username, password)

            else:
                is_ap = False
            
            if "Capabilities: Host Phone" in cdp_neighbor:
                is_phone = True
            else:
                is_phone = False
            
            if "Network Camera" in cdp_neighbor:
                is_camera = True
            else:
                is_camera = False
            
            try: remote_port
            except: remote_port = ''

            try: local_port
            except: local_port = ''

            try: ip_addr
            except: ip_addr = ''

            try: neighbor_platform
            except: neighbor_platform = ''

            try: is_ap
            except: is_ap = False

            try: is_phone
            except: is_phone = False

            try: is_camera
            except: is_camera = False

            cdp_neighbors[device_id] = {}
            cdp_neighbors[device_id]['remote_port'] = remote_port
            cdp_neighbors[device_id]['local_port'] = local_port
            cdp_neighbors[device_id]['ip_addr'] = ip_addr
            cdp_neighbors[device_id]['platform'] = neighbor_platform
            cdp_neighbors[device_id]['is_ap'] = is_ap
            cdp_neighbors[device_id]['is_phone'] = is_phone
            cdp_neighbors[device_id]['is_camera'] = is_camera
            cdp_neighbors[device_id]['scanned'] = False

            if is_ap:
                cdp_neighbors[device_id]['ap_macaddress'] = ap_macaddress
                del ap_macaddress # Prevents this key from getting added to every CDP neighbor through looping logic
        
        return(cdp_neighbors)        

    def ssh_interrogation(device, username, password) -> tuple:
        """
        This function SSHs into the provided device and issues a few 'show' commands. Then, it parses the output data for the desired variables. 

        Returns a tuple. 

        Tuple format: [model_num, serial_num, cdp_output, stp_macaddress, stp_blockedports_list]

        If SSH fails to the device, this function returns a tuple [False, False, False, False, False]
        """

        from netmiko import ConnectHandler

        connection_details = { 
        "device_type": "cisco_ios",
        "host": device,
        "username": username,
        "password": password,
        }

        try:
        
            with ConnectHandler(**connection_details) as net_connect: # Pass the above connection_details dict. Open an SSH session and run multiple commands in order.
                                    
                serial_num_command = 'show version | i Processor board ID'
                serial_num_output = net_connect.send_command(serial_num_command)
                serial_num = serial_num_output.split('Processor board ID ')[1] # ref output: 'Processor board ID FOC1922S481'

                model_num_command = f'show inventory | i {serial_num}'
                model_num_output = net_connect.send_command(model_num_command)
                model_num = model_num_output.split(' , ')[0] # ref output: 'PID: WS-C2960X-48FPS-L , VID: V06  , SN: FOC2127S3M7'
                model_num = model_num.split('PID: ')[1].strip() # ref output: 'PID: ISR4431/K9       ' <-- notice the spaces between model and end-quote. The .strip() function removes these.

                cdp_command = "show cdp entry *" # Retrieves the entire list of CDP neighbors from the device
                cdp_output = net_connect.send_command(cdp_command)

                stp_mac_command = "show spanning-tree bridge address | i VLAN0001"
                stp_mac_output = net_connect.send_command(stp_mac_command)

                if 'VLAN0001         ' in stp_mac_output:

                    stp_macaddress = stp_mac_output.split('VLAN0001         ')[1]
                
                else:
                    stp_macaddress = ''
                    logger.debug(f"Could not determine STP MAC for device {device}")

                stp_blockedports_command = "show spanning-tree blockedports | i VLAN0001"
                stp_blockedports_output = net_connect.send_command(stp_blockedports_command)
                
                if 'VLAN0001             ' in stp_blockedports_output:
                    stp_blockedports_list = []
                    for line in stp_blockedports_output:
                        stp_blocked_port = line.split('VLAN0001             ')[1]
                        stp_blockedports_list.append(stp_blocked_port)
                
                else:
                    stp_blockedports_list = ''
            
            print(f"SSH connection to {device} successful.")
            logger.info(f"SSH connection to {device} successful.")
            
            return(model_num, serial_num, cdp_output, stp_macaddress, stp_blockedports_list)

        except:
            print(f"""SSH connection to {device} failed. 
                Returning FALSE for attributes: model_num, serial_num, cdp_output, stp_macaddress, stp_blockedports_list""")
                
            logger.critical(f"SSH connection to {connection_details['host']} failed inside scan_seed_device.ssh_interrogation.")
            return(False, False, False, False, False) 
    
    def discover_device_data(device, username, password) -> tuple:
        """
        This functions first runs the 'ssh_interrogation' function to gather data via SSH. 

        Then, it parses the retrieved CDP-Neighbor data, and parses it with the 'parse_cdp_nei_data' function.

        Returns a tuple. 

        Tuple format: [platform, serial_num, cdp_neighbors_dict, stp_macaddress, stp_blockedports_list, scanned]

        Note: If SSH scan fails, multiple 'False' values are returned, so it does not continue with CDP neighbor scanning, then returns 'False' for respective variables in tuple. 
        """
        
        platform, serial_num, cdp_neighbors_data, stp_macaddress, stp_blockedports_list = scan_cdp_device.ssh_interrogation(device, username, password)

        if platform != False: # The above function returns 'False' if SSH fails for whatever reason.
            scanned = True
            cdp_neighbors_dict = scan_cdp_device.parse_cdp_nei_data(device, cdp_neighbors_data, username, password)
            return([platform, serial_num, cdp_neighbors_dict, stp_macaddress, stp_blockedports_list, scanned])
        
        else:
            return([False, False, False, False, False, True])  

    def __init__(self, device, username, password):
        global logger
        
        from logger import myLogger
        from dns_resolve_hostname import dns_resolve_hostname

        logger = myLogger(__name__)

        print(f"Scanning {device}...")
        dns_output = dns_resolve_hostname(device)      

        if dns_output.ip_addr == False:
            self.ip_addr = ''
            self.dns_name = ''
        
        else:
            ip_addr = dns_output.ip_addr
            dns_hostname = dns_output.dns_hostname
            
            self.ip_addr = ip_addr
            self.dns_name = dns_hostname

        
        self.platform, self.serial_num, self.cdp_neighbors, self.stp_macaddress, self.stp_blockedports, self.scanned = scan_cdp_device.discover_device_data(device, username, password)
        self.hostname = device
