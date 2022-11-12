"""
This script houses multiple functions related to interacting with the ServiceDesk/ManageEngine/Zoho API.

See documentation at http://633-fl11-netlab-wiki-sv01.mke.cnty/books/how-to-guides/page/how-to-create-a-servicedesk-api-key

"""


import os
import sys
from dotenv import load_dotenv
import requests
import json
from pathlib import Path

def SetupEnvFile():

    with open('.env', 'w+') as env:
        
        env.write(f'''ZOHO-CLIENT-ID=""
ZOHO-CLIENT-SECRET=""
ZOHO-REFRESH-TOKEN=""
ZOHO-ACCESS-TOKEN=""''')

    EditEnvFile()

def EditEnvFile(client_id=None, client_secret=None, refresh_token=None, access_token=None):
    
    environment_data_file = Path(".env")

    if environment_data_file.is_file():
        
        with open('.env', 'r') as env:

            env_data = env.readlines()
                    
        with open('.env', 'w') as env:

            for pos, line in enumerate(env_data):

                if 'ZOHO-CLIENT-ID' in line:
                    env_data[pos] = f'ZOHO-CLIENT-ID="{client_id}"'
                
                if 'ZOHO-CLIENT-SECRET' in line:
                    env_data[pos] = f'ZOHO-CLIENT-SECRET="{client_secret}"'
                
                if 'ZOHO-REFRESH-TOKEN' in line:
                    env_data[pos] = f'ZOHO-REFRESH-TOKEN="{refresh_token}"'
                
                if 'ZOHO-ACCESS-TOKEN' in line:
                    env_data[pos] = f'ZOHO-ACCESS-TOKEN="{access_token}"'
            
            for line in env_data:
                env.write(line + "\n")
            
    else:
    
        SetupEnvFile()

def AuthorizationRequest(client_id, client_secret, authorization_code): # This function returns the access_token and refresh_token as a single dictionary. 
    
    output = {}

    url = 'https://accounts.zoho.com/oauth/v2/token'

    payload = {
        'redirect_uri': 'https://www.zoho.com',
        'code': authorization_code,
        'grant_type': 'authorization_code',
        'client_id': client_id,
        'client_secret': client_secret,
    }


    response = requests.request("POST", url, data = payload)

    response = json.loads(response.text)

    output['access_token'] = response['access_token']
    output['refresh_token'] = response['refresh_token']

    return(output) # The output is returned as an easily accessible dictionary. 

def RefreshAccessToken(client_id, client_secret, refresh_token): # This function returns a brand-new access token by using the provided refresh token to generate a new one. 
    
    output = {}

    url = 'https://accounts.zoho.com/oauth/v2/token'

    payload = {
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token',
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': 'https://www.zoho.com',
        
    }


    response = requests.request("POST", url, data = payload)
    
    response = json.loads(response.text)

    output['access_token'] = response['access_token']

    return(output)

def interactiveFunction():

    print()
    print("Starting script. If you need to exit the script at any time, use CTRL+C to stop the script.")
    print("\n NOTE: If you run into ANY problems with this script, the easiest way to troubleshoot it is to simply delete the '.env' file in this script's directory and run it again!\n")
    input("Hit ENTER to continue.")
    try:
        
        environment_data_file = Path(".env")

        load_dotenv()
        client_id = os.environ['ZOHO-CLIENT-ID']
        client_secret = os.environ['ZOHO-CLIENT-SECRET']
        refresh_token = os.environ['ZOHO-REFRESH-TOKEN']
        access_token = os.environ['ZOHO-ACCESS-TOKEN']

        print(f"\nYour environment variables have been discovered in the file {environment_data_file}\n")
        print("If you are continuing to have issues with these credentials, try deleting the file and run this script again.")
    
    except KeyError:  # This error is raised if any of the above environmental variables are not found. 
        
        print("There was an issue calling one of your environmental variables. Starting cleanup step.\n")
        EditEnvFile()

        print("Your environment variables have been reinitialized. Please answer the following questions: \n")

        refresh_input = input("Do you need to generate a new REFRESH TOKEN? [Y|N] ").lower()
        access_input = input("Do you need to generate a new ACCESS TOKEN? [Y|N] ").lower()
        client_id = input("Paste your CLIENT ID: ")
        client_secret = input("Paste your CLIENT SECRET: ")

        if refresh_input == "y":
        
            authorization_code = input("Paste your AUTHORIZATION CODE: ")
            
            print("\nTrying your credentials...")
            
            try:

                authRequest = AuthorizationRequest(client_id, client_secret, authorization_code)
                
                access_token = authRequest['access_token']
                refresh_token = authRequest['refresh_token']

                EditEnvFile(client_id, client_secret, refresh_token, access_token)

                print("Your new environment variables have been generated and may be viewed in the local '.env' file.\n")
                print("Closing script.")                
        
                sys.exit(0)
            
            except Exception as e: 
            
                print("!" + "~"*80 + "!")
                print()
                print("Something failed when trying to execute the Authorization Request.")
                print("Double-check your Client-ID, Client-Secret, and Authorization-Code, then run this script again.")
            
                sys.exit(0)

        if refresh_input == "n" and access_input == "y":

            refresh_token = input("Paste your REFRESH TOKEN: ")
            
            try:
                refreshRequest = RefreshAccessToken(client_id, client_secret, refresh_token)

                access_token = refreshRequest['access_token']

                EditEnvFile(client_id, client_secret, refresh_token, access_token)

                print("Your new environment variables have been generated and may be viewed in the local '.env' file.\n")
                print("Closing script.")

                sys.exit(0) 

            except Exception as e:
                print(e)
                print("Something failed when trying to execute the Refresh Access-Code Request.")
                print("Double-check your Client-ID, Client-Secret, and Refresh-Code, then run this script again.")
                sys.exit(0)

# interactiveFunction()