"""Script to put data into the database via API"""
import requests
import argparse
import json
import time

api = 'yourapihere'

parser = argparse.ArgumentParser()
parser.add_argument("timeserie", help="Timeserie name")
args = parser.parse_args()
timeserie = args.timeserie

now = time.time()
now = long(((now / 60) * 60))
index = 0
while True:
    cur = now + index
    times = [cur]
    values = [1]
    list_values = zip(times, values)
    request_body = {timeserie: list_values}

    print 'Sending: %s to %s' % (json.dumps(request_body), api + "/data")
    before = time.time()
    response = requests.post(api + "/data", data=json.dumps(request_body))

    print 'It takes %d seconds to store' % (now - before)
    print response.status_code, response.text

    # each minute
    time.sleep(60)
    index += 60
