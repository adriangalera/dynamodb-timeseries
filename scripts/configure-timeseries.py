import random
import requests

temperature_ts = "living_room/temperature","average"
presence_ts = "emergency_exit/presence","count"
customers_ts = "web/customers","sum"

timeseries = [temperature_ts, presence_ts, customers_ts]

def configure_timeserie(timeserie_name, aggregation, api):
    configuration = {
        "aggregation_method": aggregation,
        "timezone": "Europe/Madrid",
        "retentions": {
            "hour": 16070400,
            "month": 96422400,
            "second": 259200,
            "year": 321408000,
            "day": 32140800,
            "minute": 2678400
        },
        "timeserie": timeserie_name
    }
    configuration_endpoint = "/configuration"
    response = requests.post(api + configuration_endpoint, json=configuration)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Configure the timeseries database')
    parser.add_argument('--api-url', required=True, help='The API url to send')

    args = parser.parse_args()
    api_url = args.api_url

    for ts in timeseries:
        name, aggregation = ts    
        configure_timeserie(name, aggregation, api_url)