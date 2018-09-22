FROM alpine
RUN apk add --no-cache python py-pip curl
RUN pip install boto3 pytz

ENV TABLE_PREFIX xxx
ENV AWS_DEFAULT_REGION eu-west-1

CMD mkdir consumer
ADD kinesisconsumer/__init__.py consumer/__init__.py
ADD kinesisconsumer/consumer.py consumer/consumer.py
ADD kinesisconsumer/parameters.json consumer/parameters.json
COPY rollup consumer/rollup
ENTRYPOINT ["python", "consumer/consumer.py"]
