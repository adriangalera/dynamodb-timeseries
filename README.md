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
