
from sqlalchemy import (Table, Column, Integer, Boolean,
    String, MetaData, ForeignKey, create_engine)


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
    Column('subscription_type', String), # yoga, regular, before4, youth, yogaclimbing
    Column('extra_notes', String),
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

vouchers = Table('vouchers', meta,
    Column('number', Integer, primary_key=True),
    Column('unique_id', String),
    Column('fullname', String),
    Column('reason', String),
    Column('extra', String),
    Column('timestamp', Integer),
    Column('used', Boolean)
)

covid_indemnity = Table('covid_indemnity', meta,
    Column('id', Integer, primary_key=True),
    Column('timestamp', Integer),
    Column('member_id', Integer, ForeignKey('members.id'))
)


tables = {
    'tokens': tokens,
    'subscriptions': subscriptions,
    'entries': entries,
    'members': members,
    'daily_passes': daily_passes,
    'payment_history': payment_history,
    'free_passes': free_passes,
    'league': league,
    'vouchers': vouchers,
    'covid_indemnity': covid_indemnity
    }

if __name__ == '__main__':
    def metadata_dump(sql, *multiparams, **params):
        # print or write to log or file etc
        print(sql.compile(dialect=engine.dialect))

    engine = create_engine('sqlite:///:memory:', strategy='mock', executor=metadata_dump)
    meta.create_all(engine)
