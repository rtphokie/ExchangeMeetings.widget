# uebersicht-widget-Exchange

ExchangeMeetings fetches upcoming meetings and appointments on your Exchange calendar and displays them in a brief [Übersicht](http://tracesof.net/uebersicht/) widget. 

![screenshot.png](screenshot.png?raw=true "ExchangeMeetings")

## Requirements
* [Python3](https://www.python.org/downloads/mac-osx/)

## Features
* Clickable shortcut ([in Übersicht preferences](http://tracesof.net/blog/2015/11/29/clickable-widgets-experiment/)) to join WebEx/Zoom meetings
* Exchange calendar entries for today and tomorrow
* meeting subject, duration, duration, number of attendees (required and optional)
* WebEx and Zoom meetings are identified with icons and are clickable to join
* past meetings are dimmed, next upcoming meeting is highlighted

## Installation
The virtual environment the Python3 script runs inside is easy to setup
1. place in your widgets folder
1. open a terminal that folder, run the following commands to create the environment and install the required python modules

        python3 -m venv ExchangeMeetings/venv
        source ExchangeMeetings/venv/bin/activate ; pip install -r ExchangeMeetings/requirements.txt

1. add your userid (email address) and password to ExchangeMeetings/ExchangeMeetings_config.yml

