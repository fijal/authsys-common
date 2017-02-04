
from sqlalchemy import (Table, Column, Integer, Boolean,
    String, MetaData, ForeignKey)

meta = MetaData()

tokens = Table('tokens', meta,
    Column('id', String, primary_key=True),
    Column('member_id', Integer, ForeignKey('members.id')),
    Column('timestamp', Integer),
    Column('valid', Boolean),
)

subscriptions = Table('subscriptions', meta,
    Column('id', Integer, primary_key=True),
    Column('member_id', Integer, ForeignKey('members.id')),
    Column('type', String), # either 'before4' or 'regular'
    Column('start_timestamp', Integer),
    Column('end_timestamp', Integer),
)

entries = Table('entries', meta,
    Column('id', Integer, primary_key=True),
    Column('timestamp', Integer),
    Column('token_id', String, ForeignKey("tokens.id")),
)

members = Table('members', meta,
    Column('id', Integer, primary_key=True),
    Column('name', String),
    Column('id_number', String),
    Column('email', String),
    Column('spam_consent', Boolean),
#    Column(), XXX find out what we want here
    Column('signature_filename', String),
    Column('timestamp', Integer),
)

daily_passes = Table('daily_passes', meta,
    Column('id', Integer, primary_key=True),
    Column('member_id', Integer, ForeignKey('members.id')),
    Column('timestamp', Integer))

tables = {
    'tokens': tokens,
    'subscriptions': subscriptions,
    'entries': entries,
    'members': members,
    'daily_passes': daily_passes
    }
