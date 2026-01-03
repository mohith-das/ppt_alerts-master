from glob import glob
from config import in_production
from datetime import timedelta, datetime
import pytz


def get_yesterday(cl_timezone):
    if in_production:
        yesterday_f = datetime.now(pytz.timezone(cl_timezone)) - timedelta(days=1)
    else:
        yesterday_f = datetime.now(pytz.timezone(cl_timezone)) - timedelta(days=1)
    return yesterday_f

def get_year_ago(cl_timezone):
    return datetime.now(pytz.timezone(cl_timezone)) - timedelta(days=365)

def get_six_months_ago(cl_timezone):
    return datetime.now(pytz.timezone(cl_timezone)) - timedelta(days=6*30)

def get_three_months_ago(cl_timezone):
    return datetime.now(pytz.timezone(cl_timezone)) - timedelta(days=3*30)

def get_sdlw(cl_timezone):
    return  get_yesterday(cl_timezone) - timedelta(days=7)

def get_hourly_date_start(cl_timezone):
    return datetime.now(pytz.timezone(cl_timezone)) - timedelta(days=3)

def get_current_date(cl_timezone):
    return datetime.now(pytz.timezone(cl_timezone)).date()

def init_time(cl_timezone):
    global yesterday, year_ago, six_months_ago, three_months_ago, sdlw, hourly_date_start, current_date
    yesterday = get_yesterday(cl_timezone)
    year_ago = get_year_ago(cl_timezone)
    six_months_ago = get_six_months_ago(cl_timezone)
    three_months_ago = get_three_months_ago(cl_timezone)
    sdlw = get_sdlw(cl_timezone)
    hourly_date_start = get_hourly_date_start(cl_timezone)
    current_date = get_current_date(cl_timezone)
    # print(yesterday, year_ago, six_months_ago, three_months_ago, sdlw, hourly_date_start, current_date)


def get_current_timestamp(cl_timezone):
    return int(datetime.now(pytz.timezone(cl_timezone)).timestamp())


def get_previous_week_start_date_end_date(current_date, weekday=6):

    end_date = current_date - timedelta(days=1)
    start_date = end_date - timedelta(days=6)

    while start_date.weekday() != weekday:
        end_date = end_date - timedelta(days=1)
        start_date = end_date - timedelta(days=6)

    return start_date, end_date

