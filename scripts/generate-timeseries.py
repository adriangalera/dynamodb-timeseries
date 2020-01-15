import argparse
import random
import time
import requests

temperature_ts = "living_room/temperature"
presence_ts = "emergency_exit/presence"
customers_ts = "web/customers"

def submit(exit_presence,living_room_temp,web_customers, api):
    unix_time = int(time.time())
    data = {}

    if living_room_temp:
        data[temperature_ts] = [[unix_time, living_room_temp]]
    
    if web_customers:
        data[customers_ts] = [[unix_time, web_customers]]

    if exit_presence:
        data[presence_ts] = [[unix_time, exit_presence]]
    print(data)
    add_data_endpoint = "/data"
    response = requests.post(api + add_data_endpoint, json=data)

def generateLivingRoomTemperature():
    return random.uniform(18, 25)

def generateEmergenceExitPresence():
    candidate = random.random()
    presence = 0
    if candidate < 0.1:
        return 1

    return None

def generateWebCustomers():
    return random.uniform(200, 400)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Create timeseries data and send it to an API')
    parser.add_argument('--api-url', required=True, help='The API url to send')

    args = parser.parse_args()
    api_url = args.api_url

    while True:
        exit_presence = generateEmergenceExitPresence()
        living_room_temp = generateLivingRoomTemperature()
        web_customers = generateWebCustomers()
        submit(exit_presence,living_room_temp,web_customers, api_url)
        time.sleep(1)

