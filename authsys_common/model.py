
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
    Column('renewal_id', Integer),
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
    Column('phone', String),
    Column('emergency_phone', String),
    Column('show_up_reason', String),
    Column('signature_filename', String),
    Column('timestamp', Integer),
    Column('member_type', String), # can be 'ondemand', 'recurring', null or 'perpetual'
    Column('credit_card_id', Integer),
)

payment_history = Table('payment_history', meta,
    Column('id', Integer, primary_key=True),
    Column('member_id', Integer, ForeignKey('members.id')),
    Column('timestamp', Integer),
    Column('type', String),
    Column('out_code', String),
    Column('out_description', String),
    Column('price', Integer),
    Column('membership_type', String),
    Column('token_id', Integer),
)

daily_passes = Table('daily_passes', meta,
    Column('id', Integer, primary_key=True),
    Column('member_id', Integer, ForeignKey('members.id')),
    Column('timestamp', Integer))

free_passes = Table('free_passes', meta,
    Column('id', Integer, primary_key=True),
    Column('member_id', Integer, ForeignKey('members.id')),
    Column('timestamp', Integer))

league = Table('league', meta,
    Column('id', Integer, primary_key=True),
    Column('member_id', Integer, ForeignKey('members.id')),
    Column('timestamp', Integer))

tables = {
    'tokens': tokens,
    'subscriptions': subscriptions,
    'entries': entries,
    'members': members,
    'daily_passes': daily_passes,
    'payment_history': payment_history,
    'free_passes': free_passes,
    'league': league,
    }
