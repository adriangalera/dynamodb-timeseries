"""Granularities module"""
import logging
import os
import datetime
from dateutil import tz
import calendar
import constants
from dateutil.relativedelta import relativedelta

LOGGER = logging.getLogger(__name__)

SECOND = 'second'
MINUTE = 'minute'
HOUR = 'hour'
DAY = 'day'
MONTH = 'month'
YEAR = 'year'

# GRANULARITIES = [SECOND, MINUTE, HOUR, DAY, MONTH, YEAR]
# GRANULARITIES = [SECOND, MINUTE]
GRANULARITIES = [SECOND, MINUTE, HOUR, DAY, MONTH, YEAR]

GRANULARITY_TABLE = {
    SECOND: "timeseries_second",
    MINUTE: "timeseries_minute",
    HOUR: "timeseries_hour",
    DAY: "timeseries_day",
    MONTH: "timeseries_month",
    YEAR: "timeseries_year",
}

GRANULARITY_VALUE_TEXT = {
    0: SECOND,
    1: MINUTE,
    2: HOUR,
    3: DAY,
    4: MONTH,
    5: YEAR
}

GRANULARITY_TEXT_VALUE = {v: k for k, v in GRANULARITY_VALUE_TEXT.iteritems()}
TABLE_GRANULARITY = {v: k for k, v in GRANULARITY_TABLE.iteritems()}

SECONDS_IN_MINUTE = 60
SECONDS_IN_HOUR = SECONDS_IN_MINUTE * 60
SECONDS_IN_DAY = SECONDS_IN_HOUR * 24

RETENTIONS_GRANULARITY = {
    SECOND: 3 * 24 * 3600,  # 3 days
    MINUTE: 1 * 31 * 24 * 3600,  # 1 months
    HOUR: 6 * 31 * 24 * 3600,  # 6 months
    DAY: 1 * 12 * 31 * 24 * 3600,  # 1 year
    MONTH: 3 * 12 * 31 * 24 * 3600,  # 3 years
    YEAR: 10 * 12 * 31 * 24 * 3600,  # 10 years
}

DEFAULT_TIMEZONE = 'Europe/Madrid'


def get_interval(gran_value, start, timezone=None):
    """Given a granularity compute the start and end instants for a unit period. For
    instance if gran_value = 1 (minute) and start = 1513608098, this will return [
    1513608098, 1513608098 + 60] = [1513608098, 1513608158]. For some granularity
    timezone might be required"""

    gran_text = GRANULARITY_VALUE_TEXT[gran_value]

    LOGGER.debug('Passed granularity value %s -> %s', gran_value, gran_text)
    LOGGER.debug('start %s with timezone %s', start, timezone)

    if gran_text == MINUTE:
        return [start, start + SECONDS_IN_MINUTE]
    if gran_text == HOUR:
        return [start, start + SECONDS_IN_HOUR]
    if gran_text == DAY:
        return [start, start + SECONDS_IN_DAY]
    elif gran_text == MONTH:
        # compute start of month
        # compute end of month
        gmt_date = datetime.datetime.utcfromtimestamp(long(start))
        gmt_date = gmt_date.replace(tzinfo=tz.gettz('UTC'))
        start_date = replace_date(gmt_date, day=1, hour=0, minute=0, second=0,
                                  microsecond=0, tzinfo=tz.gettz(timezone))
        end_date = start_date + relativedelta(months=1) - relativedelta(microsecond=1)
        start = calendar.timegm(start_date.utctimetuple())
        end = calendar.timegm(end_date.utctimetuple())
        return [start, end]
    elif gran_text == YEAR:
        # compute start of year
        # compute end of year
        gmt_date = datetime.datetime.utcfromtimestamp(long(start))
        gmt_date = gmt_date.replace(tzinfo=tz.gettz('UTC'))
        start_date = replace_date(gmt_date, month=1, day=1, hour=0, minute=0, second=0,
                                  microsecond=0, tzinfo=tz.gettz(timezone))
        end_date = start_date + relativedelta(years=1) - relativedelta(microsecond=1)
        start = calendar.timegm(start_date.utctimetuple())
        end = calendar.timegm(end_date.utctimetuple())
        return [start, end]

    else:
        raise NotImplementedError('Not implemented')


def get_granularity_table(granularity_value):
    """Get granularity table from granularity value"""
    gran_text = GRANULARITY_VALUE_TEXT.get(granularity_value, None)
    table = None
    if gran_text:
        table = GRANULARITY_TABLE.get(gran_text, None)
        # Table modification on presence of environment variable
        if table and constants.TABLE_PREFIX_ENV_VAR in os.environ:
            table = os.environ.get(constants.TABLE_PREFIX_ENV_VAR, "") + "_" + table
    return table


def get_granularity_table_text(granularity_text):
    """Get granularity table from granularity value"""
    table = GRANULARITY_TABLE.get(granularity_text, None)
    # Table modification on presence of environment variable
    if table and constants.TABLE_PREFIX_ENV_VAR in os.environ:
        table = os.environ.get(constants.TABLE_PREFIX_ENV_VAR, "") + "_" + table
    return table


def seconds_to_minute(seconds, __tz__):
    """Convert from seconds to minutes"""
    return (int(seconds) / SECONDS_IN_MINUTE) * SECONDS_IN_MINUTE


def seconds_to_hour(seconds, __tz):
    """Convert from seconds to hours"""
    return (int(seconds) / SECONDS_IN_HOUR) * SECONDS_IN_HOUR


def replace_date(gmt_date, hour=None, minute=None, second=None, microsecond=None,
                 tzinfo=None, day=None, month=None):
    """Replace the date"""
    tz_date = gmt_date
    # Convert to local timezone to make calculus
    if tzinfo is not None:
        tz_date = tz_date.astimezone(tzinfo)

    if hour is not None:
        tz_date = tz_date.replace(hour=hour)
    if minute is not None:
        tz_date = tz_date.replace(minute=minute)
    if second is not None:
        tz_date = tz_date.replace(second=second)
    if microsecond is not None:
        tz_date = tz_date.replace(microsecond=microsecond)
    if day is not None:
        tz_date = tz_date.replace(day=day)
    if month is not None:
        tz_date = tz_date.replace(month=month)

    return tz_date


def convert_with_timezone(seconds, timezone, granularity):
    """Generic method to convert """
    gmt_date = datetime.datetime.utcfromtimestamp(long(seconds))
    gmt_date = gmt_date.replace(tzinfo=tz.gettz('UTC'))
    LOGGER.debug('%s -> %s', seconds, gmt_date)
    tz_date = None
    if granularity == DAY:
        tz_date = replace_date(gmt_date, hour=0, minute=0, second=0, microsecond=0,
                               tzinfo=tz.gettz(timezone))
    if granularity == MONTH:
        tz_date = replace_date(gmt_date, hour=0, minute=0, second=0, microsecond=0, day=1,
                               tzinfo=tz.gettz(timezone))
    if granularity == YEAR:
        tz_date = replace_date(gmt_date, hour=0, minute=0, second=0, microsecond=0,
                               day=1, month=1, tzinfo=tz.gettz(timezone))
    LOGGER.debug('%s -> %s', gmt_date, tz_date)

    # Very important to use utc time tuple because timegm is timezone naive
    new_time = calendar.timegm(tz_date.utctimetuple())
    LOGGER.debug('%s -> %s', tz_date, new_time)
    return new_time


def seconds_to_day(seconds, timezone):
    """Convert from seconds to day"""
    return convert_with_timezone(seconds, timezone, DAY)


def seconds_to_month(seconds, timezone):
    """Convert from seconds to month"""
    return convert_with_timezone(seconds, timezone, MONTH)


def seconds_to_year(seconds, timezone):
    """Convert from seconds to year"""
    return convert_with_timezone(seconds, timezone, YEAR)


def convert_time(granularity, time_value, timezone=None):
    """Convert the time to the requested granularity"""
    func = GRANULARITY_GET_TIME_FUNC_DICT.get(granularity, None)
    if not func:
        raise ValueError('No function associated to %s', granularity)
    return func(time_value, timezone)


def seconds_to_second(time_value, __tz):
    """Seconds to second"""
    return time_value


GRANULARITY_GET_TIME_FUNC_DICT = {
    SECOND: seconds_to_second,
    MINUTE: seconds_to_minute,
    HOUR: seconds_to_hour,
    DAY: seconds_to_day,
    MONTH: seconds_to_month,
    YEAR: seconds_to_year
}


def enable_all_granularities():
    """Enables all the granularities (for testing purposes)"""
    global GRANULARITIES
    GRANULARITIES = [SECOND, MINUTE, HOUR, DAY, MONTH, YEAR]


if constants.ENABLE_ALL_GRAN_ENV_VAR in os.environ:
    LOGGER.info('Enabling all granularities!')
    enable_all_granularities()
