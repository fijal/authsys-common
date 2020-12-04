
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
    if line_protocol.feedback is not None:
        return
    print "RECONNECTING"
    line_protocol.connecting = True
    runner.run(TokenComponent, start_reactor=False)
    reactor.callLater(1.0, reconnect_to_brain)

class TokenComponent(ApplicationSession):
    def print_mandate(self, *args):
        print("printing mandate")

    def onJoin(self, details):
        print "CONNECTED"
        if line_protocol.feedback is not None:
            self.disconnect()
            return
        line_protocol.feedback = self

    def onConnect(self):
        self.join(self.config.realm, [u"wampcra"], u"frontdesk")

    def onChallenge(self, challenge):
        if challenge.method != u'wampcra':
            raise Exception("invalid auth method " + challenge.method)
        if u'salt' in challenge.extra:
            raise Exception("salt unimplemented")
        return auth.compute_wcs(environ.get("AUTOBAHN_SECRET", None),
                                challenge.extra[u'challenge'])


    def onDisconnect(self):
        print "DISCONNECTED"
        if line_protocol.feedback is self:
            line_protocol.feedback = None
            reactor.callLater(1.0, reconnect_to_brain)

    def auth_token(self, data):
        return self.call(u'com.members.register_token', data, environ.get('AUTOBAHN_GYM_ID', "3"))

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
        self.feedback.call(u'com.members.reader_visible', int(environ.get('AUTOBAHN_GYM_ID', "3")))

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
        SerialPort(line_protocol, '/dev/ttyACM0', reactor, 9600) # linux
        #SerialPort(line_protocol, '/dev/tty.usbmodem14101', reactor, 9600) # OS X
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
        unicode(environ.get("AUTOBAHN_ROUTER", u"ws://127.0.0.1:8087/ws")),
        u"authsys"
    )
    reconnect_to_brain()
    reactor.run()
