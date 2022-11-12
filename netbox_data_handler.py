import os
import re
import yaml
import pynetbox
from logger import myLogger
from pprint import pprint
from dotenv import load_dotenv
from netmiko import ConnectHandler
from data_integrity_check import data_integrity_check

class netbox_data_handler():

    def __init__(self, site_data_dict):
        logger = myLogger(__name__)
        for site in site_data_dict.keys():
            
            seed_device = site_data_dict[site]['cdp_seed_device']
            device_scan_data = site_data_dict[site]['device_scan_data']
            site_id = site_data_dict[site]['site_id']

            for device in device_scan_data.keys():
                integrity_check_result = data_integrity_check(device, device_scan_data[device], site)

    def nbCreateHost(refined_host):

        netbox_url = 'https://633-fl11-netbox-sv01'
        nb = pynetbox.api(netbox_url, token=netbox_access_token)

        devices = nb.dcim.devices.all()

        found = False
        
        for device in devices: 
            if refined_host.serial == device.serial: # If a matching serial is found in Netbox, update the device.
                found = True
                print(f"A serial has been found that matches {refined_host.serial} in Netbox. An update API call must be made.")
            
            if refined_host.asset_tag == device.asset_tag: # BE CAREFUL HERE!! Asset-tag 'None' can cause false-positives. 
                found = True
                print(f"An asset tag has been found that matches {refined_host.asset_tag} in Netbox. An update API call must be made.")
        
        if not found: # If no matching serial is found in Netbox, create a new device.
                    
            nb.dcim.devices.create(
                
                asset_tag = refined_host.asset_tag,
                device_role = refined_host.device_role,
                device_type = refined_host.device_type,
                ip_addr = refined_host.ip_addr,
                tags = refined_host.tags,
                # location = refined_host.location,
                manufacturer = refined_host.manufacturer,
                name = refined_host.name,
                # rack = refined_host.rack,
                serial = refined_host.serial,
                site = refined_host.site,
                status = refined_host.status,

                )
