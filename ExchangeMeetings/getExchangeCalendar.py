#!/usr/bin/env python3

import json
import os
from pprint import pprint
from datetime import datetime, timedelta
import pytz
import re
import time
import yaml
from exchangelib import Credentials, Account, EWSTimeZone, EWSDateTime # https://github.com/ecederstrand/exchangelib

days_to_fetch = 3
cache_time_to_live = 900  # cache exchange data for 15 minutes, configurable in yaml file
max_cache_age = 43200  # dont cache for more than 12 hours

def get_config(filename):
    with open(filename) as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
    cache_time_to_live = config['ttl']
    return config

def main(days, filename='ExchangeMeetings/ExchangeMeetings_config.yml'):
    config=get_config(filename)
    data = fetch_from_exchange(days, config)
    return data

def fetch_from_exchange(days, config):
    now = datetime.now(tz=pytz.UTC)
    credentials = Credentials(config['email'], config['password'])
    a = Account('trice@cisco.com', credentials=credentials, autodiscover=True)
    today = datetime.today()
    tomorrow = today + timedelta(days=1)
    if tomorrow.weekday() >= 5:
        # ensure Monday is included Fri-Sun
        tomorrow = today + timedelta(days=8-tomorrow.weekday())

    try:
        tz =a.default_timezone
    except:
        tz = EWSTimeZone.timezone(config['tz'])
    start = a.default_timezone.localize(EWSDateTime(today.year, today.month, today.day))
    end = a.default_timezone.localize(EWSDateTime(tomorrow.year, tomorrow.month, tomorrow.day))
    items = a.calendar.view(start=start, end=end).only('uid', 'start', 'end', 'duration', 'subject', 'text_body',
                                                       'my_response_type', 'organizer', 'importance', 'is_cancelled',
                                                       'is_all_day', 'is_recurring', 'location', 'optional_attendees',
                                                       'required_attendees')
    results = []

    for item in items:
        duration = item.end - item.start
        optional = []
        required = []
        if item.optional_attendees:
            for optional_attendee in item.optional_attendees:
                optional.append(optional_attendee.mailbox.name)
        if item.required_attendees:
            for required_attendee in item.required_attendees:
                required.append(required_attendee.mailbox.name)

        #dt = new Date "February 19, 2016 23:15:00"
        datefmt='%B %d, %Y %H:%M'
        try:
            start = item.start.astimezone(tz).strftime(datefmt)
            end = item.end.astimezone(tz).strftime(datefmt)
        except:
            start = item.start.strftime(datefmt)
            end = item.end.strftime(datefmt)
        result = {'start': start,
                  'end': end,
                  'subject': item.subject,
                  'response': item.my_response_type,
                  'recurring': item.is_recurring,
                  'cancelled': item.is_cancelled,
                  'uid': item.uid,
                  'url': None,
                  'url_type': None,
                  'location': item.location,
                  'duration_seconds': duration.seconds,
                  'duration_min': int(duration.seconds / 20),
                  'text_body': item.text_body,
                  'organizer': item.organizer.name,
                  'zoom': {'url': None,
                           'url_host': None,
                           'access_code': None,
                           'password': None,
                           'password_numeric': None,
                           },
                  'webex': {'url': None,
                            'url_host': None,
                            'access_code': None,
                            'password': None,
                            'password_numeric': None,
                            },
                  'required_attendees': required,
                  'optional_attendees': optional,
                  }
        webex_parse(item, result)
        zoom_parse(item, result)
        tv_parse(item, result)
        goto_parse(item, result)
        results.append(result)

    return sorted(results, key = lambda i: (i['start'], i['end']))

def zoom_parse(item, result):
    if type(item.text_body) is str:
        zoom_meeting_number = re.search("Meeting ID:\n([0-9]+)\n", item.text_body, re.IGNORECASE)
        zoom_password = re.search('Password:\n([0-9]+)\n', item.text_body, re.IGNORECASE)
        zoom_url_join = re.search('Join Zoom Meeting\<(.+)\>', item.text_body, re.IGNORECASE)
        if zoom_meeting_number:
            result['zoom']['access_code'] = zoom_meeting_number.group(1)
        if zoom_password:
                             result['zoom']['password'] = zoom_password.group(1)
                             result['zoom']['password_numeric'] = zoom_password.group(1)
        if zoom_url_join:
            result['zoom']['url'] = zoom_url_join.group(1)
            result['url_type'] = 'zoom'


def goto_parse(item, result):
    if type(item.text_body) is str:
        foo = item.text_body
        goto_url_join = re.search('\<(https*://(.*)goto.com.*)\>', item.text_body, re.IGNORECASE)
        if goto_url_join:
            foo = goto_url_join.group(1)
            result['url'] = goto_url_join.group(1)
            result['url_type'] = 'goto'

def tv_parse(item, result):
    if type(item.text_body) is str:
        foo = item.text_body
        livestream_url_join = re.search('\<(https://livestreaming.cisco.com.*)\>', item.text_body, re.IGNORECASE)
        if livestream_url_join:
            foo = livestream_url_join.group(1)
            result['url'] = livestream_url_join.group(1)
            result['url_type'] = 'tv'

def webex_parse(item, result):
    if type(item.text_body) is str:
        webex_meeting_number = re.search('Meeting number \(access code\): ([\s0-9]+)', item.text_body, re.IGNORECASE)
        webex_password = re.search('Meeting password: (\w+) \((\d+) from phones', item.text_body, re.IGNORECASE)
        webex_url_join = re.search('Join meeting\<(.+)\>', item.text_body, re.IGNORECASE)
        webex_url_host = re.search('If you are a host, click here\<(.+)\>', item.text_body, re.IGNORECASE)
        if webex_meeting_number:
            result['webex']['access_code'] = webex_meeting_number.group(1)
        if webex_password:
                              result['webex']['password'] = webex_password.group(1)
                              result['webex']['password_numeric'] = webex_password.group(2)
        if webex_url_host:
            result['webex']['url_host'] = webex_url_host.group(1)
        if webex_url_join:
            result['webex']['url'] = webex_url_join.group(1)
            result['url_type'] = 'webex'

if __name__ == '__main__':
    filename_data = 'ExchangeMeetings/meetings.json'
    filename_config = 'ExchangeMeetings/ExchangeMeetings_config.yml'
    filename_data = 'meetings.json'
    filename_config = 'ExchangeMeetings_config.yml'
    # cache_time_to_live = 1
    if os.path.isfile(filename_data):
        st = os.stat(filename_data)
        fileage = time.time() - st.st_mtime
    else:
        fileage = cache_time_to_live + 1
    if fileage > cache_time_to_live:
        try:
            meetings = main(days_to_fetch, filename=filename_config)
            with open(filename_data, 'w') as text_file:
                json.dump({'meetings': meetings}, text_file, indent=4)
            pprint(meetings)
        except Exception as e:
            raise
            pass  # Exchange API is unreliable, fall back to cache
    if os.path.isfile(filename_data):
        with open(filename_data, 'r') as text_file:
            print(text_file.read())
    else:
        print(json.dumps({"error": f"data file {filename_data} not found"}))
