
from sqlalchemy import (Table, Column, Integer, Boolean,
    String, MetaData, ForeignKey)

meta = MetaData()
members = Table('members', meta,
        Column('id', Integer, primary_key=True),
        Column('name', String),
        Column('indemnity_form', String, ForeignKey('indemnity_forms.id')),
    )

tokens = Table('tokens', meta,
    Column('id', Integer, primary_key=True),
    Column('member_id', Integer, ForeignKey('members.id')),
    Column('timestamp', Integer),
    Column('valid', Boolean),
)

subscriptions = Table('subscriptions', meta,
    Column('id', Integer, primary_key=True),
    Column('member_id', Integer, ForeignKey('members.id')),
    Column('type', String), # either 'before4' or 'normal'
    Column('start_timestamp', Integer),
    Column('end_timestamp', Integer),
)

entries = Table('entries', meta,
    Column('id', Integer, primary_key=True),
    Column('timestamp', Integer),
    Column('token_id', String), # might have a field in members
)

indemnity_forms = Table('indemnity_forms', meta,
    Column('id', Integer, primary_key=True),
    Column('name', String),
    Column('id_number', String),
    Column('email', String),
    Column('spam_consent', Boolean),
#    Column(), XXX find out what we want here
    Column('signature_filename', String),
)
