import pynetbox
import os
import yaml
from dotenv import load_dotenv
from pprint import pprint
import re
from netmiko import ConnectHandler

load_dotenv()

netbox_url = 'https://633-fl11-netbox-sv01'
netbox_access_token = os.environ.get('NETBOX-ACCESS-TOKEN')

nb = pynetbox.api(netbox_url, token=netbox_access_token)

sites = nb.dcim.sites.all()
locations = nb.dcim.locations.all()
netracks = nb.dcim.racks.all()
devices = nb.dcim.devices.all()


for device in devices:
    print(device.interfaces)

    input()

# loc_dict = {}

# for site in sites:
#     loc_dict[site.slug] = {}
#     loc_dict[site.slug]['locations'] = {}

# for loc in locations:
#     if loc.site.slug in loc_dict.keys():
#         loc_dict[loc.site.slug]['locations'][loc.slug] = {}
#         loc_dict[loc.site.slug]['locations'][loc.slug]['netracks'] = {}

# for rack in netracks:
#     if rack.site.slug in loc_dict.keys():
#         if rack.location.slug in loc_dict[rack.site.slug]['locations'].keys():
#             loc_dict[rack.site.slug]['locations'][rack.location.slug]['netracks'][rack] = {}

# pprint(loc_dict)