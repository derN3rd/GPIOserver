import SimpleHTTPServer
import SocketServer
import BaseHTTPServer
import time
import RPi.GPIO as GPIO
import cgi

class switch(object):
    def __init__(self, value):
        self.value = value
        self.fall = False

    def __iter__(self):
        """Return the match method once, then stop"""
        yield self.match
        raise StopIteration
    
    def match(self, *args):
        """Indicate whether or not to enter a case suite"""
        if self.fall or not args:
            return True
        elif self.value in args: # changed for v1.5, see below
            self.fall = True
            return True
        else:
            return False

 
class RemoteSwitch(object):
        repeat = 10 # Number of transmissions
        pulselength = 300 # microseconds
        GPIOMode = GPIO.BCM
	GPIO.setwarnings(False)
       
        def __init__(self, device, key=[1,0,1,0,0], pin=17):
                ''' 
                devices: A = 1, B = 2, C = 4, D = 8, E = 16  
                key: according to dipswitches on your Elro receivers
                pin: according to Broadcom pin naming
                '''           
                self.pin = pin
                self.key = key
                self.device = device
                GPIO.setmode(self.GPIOMode)
                GPIO.setup(self.pin, GPIO.OUT)
               
        def switchOn(self):
                self._switch(GPIO.HIGH)
 
        def switchOff(self):
                self._switch(GPIO.LOW)
 
        def _switch(self, switch):
                self.bit = [142, 142, 142, 142, 142, 142, 142, 142, 142, 142, 142, 136, 128, 0, 0, 0]          
 
                for t in range(5):
                        if self.key[t]:
                                self.bit[t]=136
                x=1
                for i in range(1,6):
                        if self.device & x > 0:
                                self.bit[4+i] = 136
                        x = x<<1
 
                if switch == GPIO.HIGH:
                        self.bit[10] = 136
                        self.bit[11] = 142
                               
                bangs = []
                for y in range(16):
                        x = 128
                        for i in range(1,9):
                                b = (self.bit[y] & x > 0) and GPIO.HIGH or GPIO.LOW
                                bangs.append(b)
                                x = x>>1
                               
                GPIO.output(self.pin, GPIO.LOW)
                for z in range(self.repeat):
                        for b in bangs:
                                GPIO.output(self.pin, b)
                                time.sleep(self.pulselength/1000000.)

PORT = 80
Handler = BaseHTTPServer.BaseHTTPRequestHandler

class MyRequestHandler(Handler):
	def do_GET(self):
		#print self.path
		ausgabe = "Ok"
		for case in switch(self.path):
			if case("/1/0"):
				RemoteSwitch(1).switchOff()
				break
			if case("/1/1"):
				RemoteSwitch(1).switchOn()
				break
			if case("/2/0"):
				RemoteSwitch(2).switchOff()
				break
			if case("/2/1"):
				RemoteSwitch(2).switchOn()
				break
			if case("/3/0"):
				RemoteSwitch(3).switchOff()
				break
			if case("/3/1"):
				RemoteSwitch(3).switchOn()
				break
			if case():
				ausgabe = "unknown request"
				# kein request fuer die lampen :c
		# send response
		self.send_response(200, "Ok")
		self.send_header("Content-type", "text/plain")
		self.end_headers()
		self.wfile.write(ausgabe)
		self.wfile.close()
	def do_POST(self):
		MyRequestHandler.do_GET(self)
	#def do_POST(self):
	#	ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
	#	if ctype == 'multipart/form-data':
	#		postvars = cgi.parse_multipart(self.rfile, pdict)
	#	elif ctype == 'application/x-www-form-urlencoded':
	#		length = int(self.headers.getheader('content-length'))
	#		postvars = cgi.parse_qs(self.rfile.read(length), keep_blank_values=1)
	#	else:
	#		postvars = {}
	#	print "POST: ", postvars
	#	#do_GET(self)


try:
	httpd = SocketServer.TCPServer(("", PORT), MyRequestHandler)

	print "serving at port", PORT
	httpd.serve_forever()
except KeyboardInterrupt:
	print "Shut down"
	httpd.socket.close()
