
import os, sys
from ConfigParser import ConfigParser

from sqlalchemy import create_engine

from .model import meta, members, entries, tokens, subscriptions

config = None

def get_config():
    global config

    if config is None:
        if os.getenv('AUTHSYS_INI') is None:
            print "Error, set AUTHSYS_INI env variable to your config"
            sys.exit(2) # maaaybe raise an exception instead

        config = ConfigParser()
        config.read(os.getenv('AUTHSYS_INI'))
    return config

def get_db_url():
    cp = get_config()
    return cp.get('db', 'url')

def get_email_conf():
    cp = get_config()
    return cp.get('email', 'username'), cp.get('email', 'password')

def create_db(url):
    eng = create_engine(url)

    with eng.connect():
        meta.create_all(eng)
    return eng

def populate_with_test_data(con):
    ins = members.insert()
    con.execute(ins.values([
        [1, "One Two", "1234", "a@b.com", False, "filename", 1234],
        [2, "John One", "12345", "b@com", True, "file2", 1235],
        [3, "Brad Two", "11111", "x@com", True, "filex", 1236],
        [4, "Jim Three", "xyz", "aaa@gmail.com", False, "file8", 1237],
    ]))
    ins = entries.insert()
    t0 = 10000
    con.execute(ins.values([
        [1, t0, 0, "AAAAAA08"],
        [2, t0 + 5, 0, "AAAAAA08"],
        [3, t0 + 10, 0, "BBBBBB08"],
        [4, t0 + 20, 0, "CCCCCC08"],
        [5, t0 + 30, 0, "DDDDDD08"],
        [6, t0 + 40, 0, "BBBBBB08"],
        ]))
    ins = tokens.insert()
    con.execute(ins.values([
        ["BBBBBB08", 2, 0, True],
        ["CCCCCC08", 2, 0, False],
        ]))
    ins = subscriptions.insert()
    con.execute(ins.values([
        [0, 2, "regular", t0, t0 + 20],
        [2, 2, "before4", t0 - 20, t0 + 20],
        [1, 2, "regular", 0, 2000],
        ]))
