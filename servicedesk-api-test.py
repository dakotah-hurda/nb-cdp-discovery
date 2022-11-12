"""
This script is meant to be used after you have generated your relevant API tokens. 

See ./servicedesk-token-generator.py if you need to generate tokens. 

Also, wiki doc: http://633-fl11-netlab-wiki-sv01.mke.cnty/books/how-to-guides/page/how-to-create-a-servicedesk-api-key

"""

import os
import json
import time
import yaml
import pprint
import requests
import urllib.parse
from dotenv import load_dotenv
import servicedeskApiTokenGenerator

# ---------------------------------------------------------------------------- #

class HTTP401Exception(Exception): # This class is only used for handling HTTP401 errors during API calls. 
    pass

# ---------------------------------------------------------------------------- #

def retrieve_all_asset_id(start_index) -> json:
    """
    This function retrieves all asset metadata from ManageEngine. 
    
    It grabs 100 assets starting from the start_index number passed in, and returns the full data for parsing. 
    """

    url = 'https://imsdservicedesk.milwaukeecountywi.gov/api/v3/assets'

    payload = {

        'input_data': json.dumps( # This is a nested dict, which requests does not like. Convert the nested dict to a string first with json.dumps(): https://stackoverflow.com/questions/43600125/nested-dictionaries-to-json-for-the-post-request-python
            { 
            'list_info' : {
                
                'row_count': 100, 
                'start_index': start_index, 
                'fields_required': [""],
                
                }
            }
        ) 
    }

    headers = {
        'Authorization': 'Zoho-oauthtoken ' + access_token,
        'Accept': 'application/vnd.manageengine.sdp.v3+json',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.request("GET", url, headers=headers, params=payload)
    
    if response.status_code == 401:

        raise HTTP401Exception("ERROR: HTTP401")

    response = json.loads(response.text)

    return(response)

# ---------------------------------------------------------------------------- #

def walk_asset_data() -> list:

    start_index = 1
    asset_list = []

    while True: # This loop uses the retrieve_all_asset_id function to retrieve all asset IDs on ManageEngine.
        
        print(f"Starting API call at start_index number {start_index}")
        try:
            response = retrieve_all_asset_id(start_index)
        except(HTTP401Exception):

            access_token = servicedeskApiTokenGenerator.RefreshAccessToken(client_id, client_secret, refresh_token)
            access_token = access_token['access_token']

            response = retrieve_all_asset_id(start_index)

        if response['list_info']['has_more_rows'] == True:
            
            for asset in response['assets']:
                asset_list.append(asset['id'])
            
            start_index += 100
            
        else: 
            
            for asset in response['assets']:
                asset_list.append(asset['id'])
            
            return(asset_list)

            break

# ---------------------------------------------------------------------------- #

def asset_tag_serial_binding(asset_id, access_token) -> dict:

    """
    Now that all of the Asset IDs are collected and stored in the asset_list object, 

    we can loop through them and build an index of their asset tags and serials for reference. 

    This function will loop through all asset_list data and parse out the serial and asset tag for each asset, 

    then combine the asset_id, asset_tag, and serial_number as a dictionary. All dictionaries will be stored in a master dictionary.
    """
    
    asset_dict = {} # Instantiate the main dictionary. 

    url = f'https://imsdservicedesk.milwaukeecountywi.gov/api/v3/assets/{asset_id}'

    headers = {
        'Authorization': 'Zoho-oauthtoken ' + access_token,
        'Accept': 'application/vnd.manageengine.sdp.v3+json',
        'Content-Type': 'application/x-www-form-urlencoded'
        }
    
    response = requests.request("GET", url, headers=headers)

    # print(type(response.status_code))
    if response.status_code == 401:

        raise HTTP401Exception("ERROR: HTTP401")

    response = json.loads(response.text)

    asset_tag = response['asset']['asset_tag']
    serial_number = response['asset']['serial_number']

    asset_dict[serial_number] = {
        'asset_tag': asset_tag,
        'asset_id': asset_id
        }
        
    return(asset_dict)

# ---------------------------------------------------------------------------- #

load_dotenv()

global access_token # Needed because certain 'downstream' functions can update the access_token upon HTTP401 error detection.

asset_list = []
asset_master_dict = {}
client_id = os.environ.get('ZOHO-CLIENT-ID')
client_secret = os.environ.get('ZOHO-CLIENT-SECRET')
access_token = os.environ.get('ZOHO-ACCESS-TOKEN')
refresh_token = os.environ.get('ZOHO-REFRESH-TOKEN')

# ---------------------------------------------------------------------------- #

# with open('asset_list.txt', 'r') as f: # This section is just for speeding up testing, and can be removed for final release.
#     for asset in f.readlines():
#         asset_list.append(asset.rstrip())

# ---------------------------------------------------------------------------- #


try:
    asset_list = walk_asset_data()

except(HTTP401Exception): # This section is used when authentication fails with our provided access_token. If we receive a 401, we regenerate the access token and try again.
        
        # print(f"status code was 401, running access_token regeneration")
        # input()
        # print(f"Old access token: {access_token}")
        
        access_token = servicedeskApiTokenGenerator.RefreshAccessToken(client_id, client_secret, refresh_token)
        access_token = access_token['access_token']

        asset_list = walk_asset_data()

start_time = time.perf_counter()

# print(asset_list)

for pos, asset_id in enumerate(asset_list):

    # print(f"Starting new iteration with access_token {access_token}")
    api_time_start = time.perf_counter()

    try:
        asset_dict = asset_tag_serial_binding(asset_id, access_token)

    except(HTTP401Exception): # This section is used when authentication fails with our provided access_token. If we receive a 401, we regenerate the access token and try again.
        
        # print(f"status code was 401, running access_token regeneration")
        # input()
        # print(f"Old access token: {access_token}")
        
        access_token = servicedeskApiTokenGenerator.RefreshAccessToken(client_id, client_secret, refresh_token)
        access_token = access_token['access_token']        
        
        # print(f"New access token: {access_token}")
        # input(f"Running new API request with new token {access_token}, hit ENTER")

        try:
            asset_dict = asset_tag_serial_binding(asset_id, access_token) # Retry the API call with a new access token. 
        except:
            continue # If it fails at this point, just ignore it and move on. 

    api_time_end = time.perf_counter()
    asset_master_dict.update(asset_dict)

    current_time = time.perf_counter()

    print()
    print("*" * 80)
    print(f"The script is running. Current position is: {pos} / {len(asset_list)}")
    print(f"API Latency: {round(api_time_end - api_time_start, 2)} seconds")
    print(f"Total elapsed time: {round(current_time - start_time, 2)} seconds")
    print("*" * 80)
    print()

# ---------------------------------------------------------------------------- #

"""
Caching the data so we don't have to re-make this API call all the time. 
 
FUTURE: Build in a function that stores a date-time and compares with current date-time with script? 
    e.g. If data is more than a week old, run the whole API data collection process again. 
"""

with open("./asset-data-cache.yaml", 'w+') as file: 
    yaml.dump(asset_master_dict, file)

# ---------------------------------------------------------------------------- #