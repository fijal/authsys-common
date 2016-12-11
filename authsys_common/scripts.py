
import os, sys
from ConfigParser import ConfigParser

from sqlalchemy import create_engine

from .model import meta, members

def get_db_url():
    if os.getenv('AUTHSYS_INI') is None:
        print "Error, set AUTHSYS_INI env variable to your config"
        sys.exit(2) # maaaybe raise an exception instead

    cp = ConfigParser()
    cp.read(os.getenv('AUTHSYS_INI'))
    return cp.get('db', 'url')

def create_db(url):
    eng = create_engine(url)

    with eng.connect():
        meta.create_all(eng)
    return eng

def populate_with_test_data(con):
    ins = members.insert()
    con.execute(ins.values([
        {'name': "John One"},
        {'name': "Brad Two"},
        {'name': "Jim Three"}]))
