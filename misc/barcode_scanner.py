
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
import sys
from twisted.internet import reactor



CHARMAP_LOWERCASE = {4: 'a', 5: 'b', 6: 'c', 7: 'd', 8: 'e', 9: 'f', 10: 'g', 11: 'h', 12: 'i', 13: 'j', 14: 'k',
                                          15: 'l', 16: 'm', 17: 'n', 18: 'o', 19: 'p', 20: 'q', 21: 'r', 22: 's', 23: 't', 24: 'u', 25: 'v',
                                          26: 'w', 27: 'x', 28: 'y', 29: 'z', 30: '1', 31: '2', 32: '3', 33: '4', 34: '5', 35: '6', 36: '7',
                                          37: '8', 38: '9', 39: '0', 44: ' ', 45: '-', 46: '=', 47: '[', 48: ']', 49: '\\', 51: ';', 86: '-',
                                          52: '\'', 53: '~', 54: ',', 55: '.', 56: '/'}
CHARMAP_UPPERCASE = {4: 'A', 5: 'B', 6: 'C', 7: 'D', 8: 'E', 9: 'F', 10: 'G', 11: 'H', 12: 'I', 13: 'J', 14: 'K',
                                          15: 'L', 16: 'M', 17: 'N', 18: 'O', 19: 'P', 20: 'Q', 21: 'R', 22: 'S', 23: 'T', 24: 'U', 25: 'V',
                                          26: 'W', 27: 'X', 28: 'Y', 29: 'Z', 30: '!', 31: '@', 32: '#', 33: '$', 34: '%', 35: '^', 36: '&',
                                          37: '*', 38: '(', 39: ')', 44: ' ', 45: '_', 46: '+', 47: '{', 48: '}', 49: '|', 51: ':', 52: '"',
                                          53: '~', 54: '<', 55: '>', 56: '?'}
CR_CHAR = 40
SHIFT_CHAR = 2

#def barcode_reader():
#   barcode_string_output = ''
#   # barcode can have a 'shift' character; this switches the character set
#   # from the lower to upper case variant for the next character only.
#   CHARMAP = CHARMAP_LOWERCASE
#   with open('/dev/hidraw0', 'rb') as fp:
#      while True:
#         # step through returned character codes, ignore zeroes
#         for char_code in [element for element in fp.read(8) if element > 0]:
#            if char_code == CR_CHAR:
#               # all barcodes end with a carriage return
#               return barcode_string_output
#            if char_code == SHIFT_CHAR:
#               # use uppercase character set next time
#               CHARMAP = CHARMAP_UPPERCASE
#            else:
#               # if the charcode isn't recognized, add ?
#               barcode_string_output += CHARMAP.get(char_code, '?')
#               # reset to lowercase character map
#               CHARMAP = CHARMAP_LOWERCASE


import usb.core
import usb.util
import time
import threading

VENDOR_ID = 0x1eab
PRODUCT_ID = 0x8303

device = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)

reattach = False
if device.is_kernel_driver_active(0):
   reattach = True
   device.detach_kernel_driver(0)

class State(object):
   stop = False
   item = None
   feedback = None

state = State()

class Component(ApplicationSession):
   def onJoin(self, details):
      state.feedback = self
      print "CONNECTED"

   def onDisconnect(self):
      state.feedback = None
      print "DISCONNECTED"


def main(device):
   device.set_configuration()
   cfg = device.get_active_configuration()
   intf = cfg[(0, 0)]
   endpoint = device[0][(0, 0)][0]

   msg = ''
   while not state.stop:
      try:
         ar = device.read(endpoint.bEndpointAddress, endpoint.wMaxPacketSize)
         if ar[0] == 2:
            charmap = CHARMAP_UPPERCASE
         else:
            charmap = CHARMAP_LOWERCASE
         if ar[2] == 0:
            continue
         elif ar[2] == CR_CHAR:
            state.item = msg
            if state.feedback is not None:
               state.feedback.publish('com.vouchers.scan', msg)
            msg = ''
         else:
            msg += charmap.get(ar[2], '?')
      except usb.core.USBError as e:
         if e.args[0] == 110:
            continue
         raise


try:
   t = threading.Thread(target=main, args=(device,))
   t.start()
   runner = ApplicationRunner(
       u"ws://127.0.0.1:8080/ws",
       u"authsys",
   )
   d = runner.run(Component, start_reactor=False)

   reactor.run()
finally:
   usb.util.dispose_resources(device)

   # It may raise USBError if there's e.g. no kernel driver loaded at all
   if reattach:
      device.attach_kernel_driver(0)
