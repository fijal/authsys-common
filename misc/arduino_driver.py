
from os import environ

from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner

from twisted.internet.serialport import SerialPort
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
from twisted.protocols.basic import LineReceiver

def reconnect_to_brain():
    print "RECONNECTING"
    d = runner.run(TokenComponent, start_reactor=False)
    d.addErrback(lambda *args: reactor.callLater(1.0, reconnect))

class TokenComponent(ApplicationSession):
    def onJoin(self, details):
        print "CONNECTED"
        line_protocol.feedback = self

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
        SerialPort(line_protocol, '/dev/tty.usbmodem1411', reactor, 9600)
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
        environ.get("AUTOBAHN_DEMO_ROUTER", u"ws://127.0.0.1:8080/ws"),
        u"authsys",
    )
    reconnect_to_brain()
    reactor.run()
