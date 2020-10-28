#!/usr/bin/env python3
import sys, string, socket, datetime
import time, json, asyncio

# ----------------------------------------------------------
# command line arguments
print ('ThermAsyncio.py reads temperature from Maxim/Dallas DS1621')
print ('thermometer connected by I2C to Raspberry Pi computer.')
print ('M. Williamsen, 10/26/2020, https://github.com/springleik')
print ('Usage: python3 ThermAsyncio.py [arg names and values]')
print ('  arg name | arg value')
print ('  ---------|----------')
print ('  -port    | socket port number   (default is 43210)')
print ('  -host    | socket host address  (default is any)')
print ('  -addr    | DS1621 I2C address   (default is 0x48)')

# set defaults
thePort = 43210
theHost = '0.0.0.0'
ds1621Addr = 0x48

# check for user inputs on command line
args = iter(sys.argv)
print ('Running script: "{0}"\n  in Python: {1}'.format(next(args), sys.version))
for arg in args:
	if '-port' == arg:
		thePort = int(next(args, thePort), 0)
	elif '-host' == arg:
		theHost = next(args, theHost)
	elif '-addr' == arg:
		ds1621Addr = int(next(args, ds1621Addr), 0)
	else:
		print ('Unexpected argument: {0}'.format(arg))

# ----------------------------------------------------------
# i2c bus interface
# DS1621 register addresses
stopConv   = 0x22
accessTH   = 0xa1
accessTL   = 0xa2
readCount  = 0xa8
readSlope  = 0xa9
readTemp   = 0xaa
accessCfg  = 0xac
startConv  = 0xee

# enable interface in one-shot mode
try:
	import smbus
	i2cBus = smbus.SMBus(bus = 1)
	cfg = i2cBus.read_byte_data(ds1621Addr, accessCfg)
	if 0 == (cfg & 0x01):
		cfg |= 0x01	# set one-shot bit
		print ('Writing config register: {0}'.format(hex(cfg)))
		i2cBus.write_byte_data(ds1621Addr, accessCfg, cfg)
		time.sleep(0.01)
	print ('DS1621 intialized at addr: {0}'.format(hex(ds1621Addr)))

except (IOError, OSError, ImportError) as e:
	i2cBus = None
	print ('Failed to initialize hardware: {0}'.format(e))
	print ('   Running in simulation mode.')

# function to read and report temperature
def getDataPoint():
	if not i2cBus:
		message = {'message':'Simulation mode enabled.'}
		print(message)
		return message
		
	# start a temperature conversion
	i2cBus.write_byte_data(ds1621Addr, startConv, 0)

	# wait up to 1.5 sec. for completion
	done = False
	timeout = 15
	while (not done) and (timeout > 0):
		time.sleep(0.1)
		rslt = i2cBus.read_byte_data(ds1621Addr, accessCfg)
		if rslt & 0x80: done = True
		timeout -= 1
		
	if not timeout:
		error = {'error':'Conversion timed out.'}
		print (error)
		return error

	# read standard (1/2-deg) resolution
	therm = i2cBus.read_word_data(ds1621Addr, readTemp)
	loRes  = (therm << 1) & 0x1fe
	loRes |= (therm >> 15) & 0x01
	if loRes > 255: loRes -= 512
	loRes /= 2.0

	# read high (1/16-deg) resolution
	count = i2cBus.read_byte_data(ds1621Addr, readCount)
	slope = i2cBus.read_byte_data(ds1621Addr, readSlope)
	temp = therm & 0xff
	if temp > 127: temp -= 256
	hiRes = temp - 0.25 + (slope - count) / slope

	# build data point structure
	now = datetime.datetime.now()
	point = {'loResC': loRes,
		'hiResC': hiRes,
		'hiResF': 32.0 + hiRes * 9.0 / 5.0,
		'date': now.strftime('%m/%d/%Y'),
		'time': now.strftime('%H:%M:%S')
		}
	
	print (point)
	return point

# ----------------------------------------------------------
# implement UDP socket server
# https://docs.python.org/3/library/asyncio-protocol.html#udp-echo-server
class myProtocol:
	def connection_made(self, transport):
		self.transport = transport

	def datagram_received(self, data, addr):
		if data:
			msg = data.decode().strip()
			if len(msg):
				print('msg: {0}'.format(msg))
		self.transport.sendto((json.dumps(getDataPoint()) + '\n').encode('utf-8'), addr)
		
	def connection_lost(self, exc):
		pass
		
# define main loop
async def main():
	print('Main loop started.')
	theLoop = asyncio.get_running_loop()
	transport, protocol = await theLoop.create_datagram_endpoint(lambda: myProtocol(), local_addr=(theHost, thePort))
	while True: await asyncio.sleep(1)

# run main loop
try:
	asyncio.run(main())
except (KeyboardInterrupt):
	print('  User exit request.')
