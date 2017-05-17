
import treq
from authsys_common.scripts import get_config
from authsys_common import queries as q

def recurring_payment(con, payment_id, no, tp, callback):
    conf = get_config()
    if tp == "before4":
        price = conf.get("price", "before4")
    elif tp == "youth":
        price = conf.get("price", "youth")
    else:
        price = conf.get("price", "regular")
    url = conf.get('payment', 'base') + '/v1/registrations/' + payment_id + '/payments'
    print url
    data = {
            'authentication.userId' : conf.get('payment', 'userId'),
            'authentication.password' : conf.get('payment', 'password'),
            'authentication.entityId' : conf.get('payment', 'recurringEntityId'),
            'amount' : price + ".00",
            'currency' : 'ZAR',
            'paymentType' : 'DB',
            'recurringType': 'REPEATED',
#            'merchantTransactionId': "foobarbaz" + str(q.max_id_of_payment_history(con)),
            }
    d = treq.post(url, data)
    d.addCallback(callback, no)
