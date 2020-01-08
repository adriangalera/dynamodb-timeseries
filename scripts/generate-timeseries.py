import requests
import random
import time
import requests

api = "https://mgyt0nb2f0.execute-api.eu-west-1.amazonaws.com/dev"
temperature_ts = "living_room/temperature"
presence_ts = "emergency_exit/presence"
customers_ts = "web/customers"

def submit(exit_presence,living_room_temp,web_customers):
    unix_time = int(time.time())
    data = {
        temperature_ts : [[unix_time, living_room_temp]],
        presence_ts: [[unix_time, exit_presence]],
        customers_ts: [[unix_time, web_customers]]
    }
    print(data)
    add_data_endpoint = "/data"
    response = requests.post(api + add_data_endpoint, json=data)

def generateLivingRoomTemperature():
    return random.uniform(18, 25)

def generateEmergenceExitPresence():
    candidate = random.random()
    presence = 0
    if candidate < 0.1:
        presence = 1

    return presence

def generateWebCustomers():
    return random.uniform(200, 400)

if __name__ == "__main__":

    while True:
        exit_presence = generateEmergenceExitPresence()
        living_room_temp = generateLivingRoomTemperature()
        web_customers = generateWebCustomers()
        submit(exit_presence,living_room_temp,web_customers)
        time.sleep(1)

