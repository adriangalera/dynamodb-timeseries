"""Script to put data into the database via API"""
import requests
import argparse
import json
import time

api = 'yourapihere'
timeserie1 = 'timeserie1'
timeserie2 = 'timeserie2'

parser = argparse.ArgumentParser()
parser.add_argument("timeserie", help="Timeserie name")
parser.add_argument("start", help="Unix timestamp start")
parser.add_argument("end", help="Unix timestamp end")
args = parser.parse_args()
timeserie = args.timeserie
start = int(args.start)
end = int(args.end)

total = (end - start)
times = range(start, end)
print 'Creating %d items ...' % total
# values = [random.uniform(-100, 100) for __ in xrange(total)]
values = [1 for __ in xrange(total)]
list_values = zip(times, values)
request_body = {timeserie: list_values}

print 'Sending: %s to %s' % (json.dumps(request_body), api + "/data")
before = time.time()
response = requests.post(api + "/data", data=json.dumps(request_body))
now = time.time()
print 'It takes %d seconds to store' % (now - before)
print response.status_code, response.text
