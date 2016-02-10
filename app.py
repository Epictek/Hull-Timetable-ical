#!/usr/bin/python
# -*- coding: utf-8 -*-
import requests
import time
from datetime import datetime
import sys
from ics import Calendar, Event
import progressbar
import logging
import sys
import os

debug = False
if os.isatty(sys.stdin.fileno()):
    debug = True
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    pass
else:
    debug = False
    logging.basicConfig(stream=sys.stderr, level=logging.WARNING)
    pass

username = ''
password = ''

#location of the ics file, it's recommended to write to a web folder
ical_loc = '/var/www/kieran/'

r = requests.post('https://hull.ombiel.co.uk/campusm/ldap/282',
                  params={'username': username, 'password': password})
cookie = dict(a=r.cookies['a'], __a=r.cookies['__a'])
r = r.json()
surname = r['surname']
if surname[-1] != "s":
    surname = surname + "'s"
else:
    surname = surname + "'"

student_name = r['firstname'] + ' ' + surname

logging.info('Downloading timetable for: ' + student_name)

c = Calendar()
cyear = datetime.today().year
endyear = 2016
ids = []
cday = datetime.today().timetuple().tm_yday
day = cday - cday % 7 + 5
#day = 4

totaldays = (endyear - cyear + 1) * 372

if debug:
    bar = progressbar.ProgressBar(max_value=totaldays,
                                  redirect_stdout=True)

prog = day
year = cyear
while year <= endyear:
    logging.debug('Day: ' + str(day) + ' Year: ' + str(year))
    if debug:
        bar.update(prog)
    date = str(year) + str(day).zfill(3)
    url = 'https://hull.ombiel.co.uk/campusm/sso/calendar/course_timetable/' + date
    r = requests.get(url, cookies=cookie)
    r = r.json()
    day = day + 7
    prog = prog + 7
    if day > 364:
        day = 4
        year += 1
    locode = ''
    i = 1
    for event in r['events']:
        if event['id'] not in ids:
            e = Event()
            i = i + 1
            ids.append(event['id'])

#this code is really bad, like I don't even, Should probably refactor this in to something better, It basically finds events with the same time and merges them 

            locode = event['locCode']
            if locode[-1:] == "." and locode[-2:-1].isalpha():
                locode = locode[:-2]
            if locode[:-1].isalpha():
                locode = locode[:-1]
            x = 1
            length = len(r['events'])
            if i + 1 < length:
                for otherevent in r['events']:
                    if (event['locCode'][:-2] == otherevent['locCode'][:-2]  
                        and event['desc2'] == otherevent['desc2'] \
                        and event['start'] == otherevent['start'] \
                        and event['locCode'] != otherevent['locCode']):
                            locode = locode + otherevent['locCode'][-2:-1]
                            ids.append(otherevent['id'])

            #I wanted to add the tye of lecture to the start of the title, Again this could probably be improved
            if "[" in event['desc2']:
                class_name = event['desc2'].split('[')
                e.name = '[' + class_name[1] + ' ' \
                    + (class_name[0])[:-2] + ' (' + event['desc1'] + ')'
            else:
                class_name = event['desc2']
                e.name = class_name + ' (' + event['desc1'] + ')'
#That mess of a code is over now, lets just add everything to the event now

            logging.debug(e.name + ' - ' + locode)
            e.begin = event['start']
            e.end = event['end']
            e.description = event.get('teacherName', '')
            e.location = locode
            c.events.append(e)


#write it all to file
icalfile = ical_loc + username + '.ics'
open(icalfile, 'w').writelines(c)
with open(icalfile, 'r') as file:
    lines = file.readlines()
    lines[1] = lines[1] + 'X-WR-CALNAME: ' + student_name \
        + ' Uni Timetable\nX-PUBLISHED-TTL:PT12H'

with open(icalfile, 'w') as file:
    for line in lines:
        file.write(line)

if debug:
    bar.update(totaldays)
