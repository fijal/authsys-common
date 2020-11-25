
import sys
from os import environ

from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
from autobahn.wamp import auth

from twisted.internet.serialport import SerialPort
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
from twisted.protocols.basic import LineReceiver
from twisted.python import log

log.startLogging(sys.stdout)

def reconnect_to_brain():
    print "RECONNECTING"
    d = runner.run(TokenComponent, start_reactor=False)
    d.addErrback(lambda *args: reactor.callLater(1.0, reconnect_to_brain))

class TokenComponent(ApplicationSession):
    def print_mandate(self, *args):
        print("printing mandate")

    def onJoin(self, details):
        print "CONNECTED"
        line_protocol.feedback = self

    def onConnect(self):
        self.join(self.config.realm, [u"wampcra"], u"frontdesk")

    def onChallenge(self, challenge):
        if challenge.method != u'wampcra':
            raise Exception("invalid auth method " + challenge.method)
        if u'salt' in challenge.extra:
            raise Exception("salt unimplemented")
        return auth.compute_wcs(environ.get("AUTOBAHN_SECRET", None),
                                challenge.extra['challenge'])


    def onDisconnect(self):
        print "DISCONNECTED"
        reactor.callLater(1.0, reconnect_to_brain)

    def auth_token(self, data):
        return self.call('com.members.register_token', data)

class P(LineReceiver):
    delimiter = '\n'
    feedback = None
    connected = False

    def connectionMade(self):
        self.connected = True
        reactor.callLater(1.0, self.health_check_feedback)

    def health_check_feedback(self):
        if not self.connected:
            return
        reactor.callLater(1.0, self.health_check_feedback)
        if not self.feedback:
            return
        try:
            self.feedback.call('com.members.reader_visible', 0)
        except:
            pass

    def lineReceived(self, data):
        def errb(*args):
            print "errback:", args
            self.transport.write("n")

        def cb(r):
            if r:
                print "y", r
                self.transport.write("y")
            else:
                print "n", r
                self.transport.write("n")

        if self.feedback is None:
            return # ignore
        d = self.feedback.auth_token(data)
        d.addCallbacks(cb, errb)

    def connectionLost(self, err):
        self.connected = False
        reactor.callLater(1.0, reconnect)

def reconnect():
    if line_protocol.connected:
        return
    try:
        SerialPort(line_protocol, '/dev/ttyACM0', reactor, 9600)
    except:
        reactor.callLater(1.0, reconnect) # in case that one fails
        raise

line_protocol = P()

if __name__ == '__main__':
    try:
        reconnect()
    except:
        pass # eat the exception, reconnection in progress
    runner = ApplicationRunner(
        environ.get("AUTOBAHN_ROUTER", u"ws://127.0.0.1:8087/ws"),
        u"authsys",
        extra={
            'authentication': {
                'wampcra': {
                    'authid': 'frontdesk',
                    'secret': '12345'
                }
            }
        }
    )
    reconnect_to_brain()
    reactor.run()
