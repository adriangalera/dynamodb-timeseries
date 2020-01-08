# Dynamo DB Timeseries

This project provides the implementation of a timeseries database over DynamoDB tables.

There's one table per granularity.

## Granularities:
- second
- minute
- hour
- day
- month
- year

From hour to year, the aggregation process required the usage of timezone to perform 
the aggregations; to compute the start of the periods.

## Aggregation methods:
- sum
- last
- max
- min
- max abs
- min abs
- average
- count

## Build kinesisconsumer:
From the root directory

```
docker build -f kinesisconsumer/Dockerfile -t kinesisconsumer:latest .
```

## API 

### Create timeserie configuration

POST /configuration
```json
{
        "timeserie" : "test2",
        "aggregation_method" : "sum",
        "retentions" : [],
        "timezone" : "Europe/Madrid"
}
```

### Get timeserie configuration
GET /configuration

```json
[
  {
    "aggregation_method": "average",
    "timezone": "Europe/Madrid",
    "default": false,
    "retentions": {
      "hour": 16070400,
      "month": 96422400,
      "second": 259200,
      "year": 321408000,
      "day": 32140800,
      "minute": 2678400
    },
    "timeserie": "test-manual"
  }
]
```

### Get timeseries data
GET /data/{timeseries}/{granularity}?start=0&end=1571157752

```json
{
  "test-manual": [
    [
      1571147701,
      62
    ],
    [
      1571147712,
      69
    ],
    [
      1571147722,
      -47
    ],
    [
      1571147732,
      60
    ],
    [
      1571147742,
      91
    ],
    [
      1571147752,
      53
    ]
  ]
}
```
## Add timeseries data
POST /data
```json
{
    "test-manual" : [
            [1,100],
            [2,120],
            [3,120]
        ]
}
```
