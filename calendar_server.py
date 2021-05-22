
import csv
from datetime import datetime
from io import StringIO
from flask import Flask, request
from flask.templating import render_template

app = Flask(__name__)

@app.route('/')
def hello():
    return render_template('index.html')

def get_hours(day, what):
    day = day.lower()
    if what == 'Beginner south' or what == 'Beginner north':
        return (9, 0), (13, 0)
    if what == 'Front am' or what == 'Cafe am':
        if day in ['public holiday', 'sunday', 'saturday']:
            return (8, 0), (19, 0)
        elif day in ['tuesday', 'thursday']:
            return (7, 0), (15, 0)
        else:
            return (8, 0), (15, 0)
    if what == 'Front pm' or what == 'Cafe pm':
        return (14, 30), (22, 0)
    if what == 'South am':
        if day in ['public holiday', 'sunday', 'saturday']:
            return (8, 0), (19, 0)
        elif day in ['monday', 'wednesday']:
            return (7, 0), (15, 0)
        else:
            return (8, 0), (15, 0)
    if what == 'South pm':
        if day == 'monday':
            return (14, 0), (22, 0)
        return (14, 30), (22, 0)
    if what == 'Admin':
        return (8, 0), (16, 0)
    if what == 'setting':
        return (7, 0), (15, 0)
    assert False, what

def timediff(start, stop):
    h_s, m_s = start
    h_t, m_t = stop
    return ((h_t * 60 + m_t) - h_s * 60 + m_s) / 60.

def process_rows(rows):
    assert rows[0][:17] == ['', '', 'morning shift', 'evening shift', 'cafe shift am', 'cafe shift pm', 'Beginners class', '',
                        'south shift am', 'south shift pm', 'Beginners class South', 'setting south', 'setting north',
                        'South Cafe pm', 'Admin', 'Cleaning PE', 'Cleaning South'], rows[0][:17]

    rows = rows[1:]
    problems = []
    hours = {}
    weekends = {}
    setting = {}
    beginner = {}
    evening = {}
    morning = {}

    def check(condition, day, what, extra_val=""):
        if not condition:
            problems.append("%s - %s, %s" % (day, what, extra_val))

    def add_hours(who, day, what):
        if who.strip() == '':
            return
        if who not in hours:
            hours[who] = 0
        if day.lower() in ['saturday', 'sunday', 'public holiday']:
            weekends[who] = weekends.get(who, 0) + 1
        if what == 'setting':
            setting[who] = setting.get(who, 0) + 1
        if 'Beginner' in what:
            beginner[who] = beginner.get(who, 0) + 1
        if ' am' in what:
            morning[who] = morning.get(who, 0) + 1
        if ' pm' in what:
            evening[who] = evening.get(who, 0) + 1
        start, stop = get_hours(day, what)
        hours[who] = timediff(start, stop) + hours[who]

    for i in range(len(rows)):
        row = rows[i][:15]
        day, day_of_the_week, front_am, front_pm, cafe_am, cafe_pm, beg_north, _, south_am, south_pm, south_cafe_pm, beg_south, set_south, set_north, admin = row

        l1 = [x for x in row[2:] if x != '']

        def expand(item):
            if '(' not in item and ',' not in item:
                return [item]
            return [x.strip(" ") for x in item[:item.find('(')].split(',')]

        l = []
        for item in l1:
            l += expand(item)
        check(len(l) == len(dict.fromkeys(l)), day, "?", "repetition on the same day")
        add_hours(front_am, day_of_the_week, "Front am")
        add_hours(front_pm, day_of_the_week, "Front pm")
        add_hours(cafe_am, day_of_the_week, "Cafe am")
        add_hours(cafe_pm, day_of_the_week, "Cafe pm")
        add_hours(south_am, day_of_the_week, "South am")
        add_hours(south_pm, day_of_the_week, "South pm")
        add_hours(beg_south, day_of_the_week, "Beginner south")
        add_hours(beg_north, day_of_the_week, "Beginner north")
        add_hours(south_cafe_pm, day_of_the_week, "Cafe pm")
        if '(' in admin:
            admin_person = admin[:admin.find('(')].strip(" ")
        else:
            admin_person = admin
        add_hours(admin_person, day_of_the_week, "Admin")

        for item in expand(set_south):
            add_hours(item, day_of_the_week, "setting")
        for item in expand(set_north):
            add_hours(item, day_of_the_week, "setting")

        # check for problems

        if day_of_the_week == 'Friday' and i != len(rows) - 1:
            for item in front_pm, cafe_pm, south_pm:
                check(item not in rows[i + 1][:12], day, item, "friday shift followed by weekend am")
        # no evening into morning
        if i != len(rows) - 1:
            _, _, next_front_am, next_front_pm, next_cafe_am, next_cafe_pm, _, _, next_south_am, next_south_pm = rows[i + 1][:10]
            if front_pm != '':
                check(cafe_pm != '', day, "?", "front on, but cafe off")
                check(south_pm != '', day, "?", "front on but south off")
                check(front_pm not in (next_front_am, next_cafe_am, next_south_am), day, front_pm, "front pm repeated next day am")
                check(cafe_pm not in (next_front_am, next_cafe_am, next_south_am), day, cafe_pm, "cafe pm repeated next day am")
                check(south_pm not in (next_front_am, next_cafe_am, next_south_am), day, south_pm, "south pm repeated next day am")
            else:
                assert cafe_pm == ''
            if day_of_the_week == 'Sunday':
                check(front_am not in (next_front_am, next_cafe_am, next_south_am), day, front_am, "front sunday repeated monday am")
                check(cafe_am not in (next_front_am, next_cafe_am, next_south_am), day, cafe_am, "cafe front sunday repeated monday am")
                check(south_am not in (next_front_am, next_cafe_am, next_south_am), day, south_am, "south am sunday repeated monday am")


    return {'problems': problems, 'hours': sorted(hours.items()), 'weekends': weekends, 'setting': setting, 'upload': True,
            'beginner': beginner, 'morning': morning, 'evening': evening}

@app.route('/upload', methods=['POST', 'GET'])
def upload():
    f = request.files.items()
    for name, contents in f:
        cont = contents.read().decode('utf8')
        res = process_rows(list(csv.reader(StringIO(cont))))
    return render_template('index.html', **res)

app.run(port=5007)
