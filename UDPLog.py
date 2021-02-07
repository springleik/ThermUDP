#!/usr/bin/env python3
# UDP client to log temperature data
# M. Williamsen, Quantum Design.  2/6/2021

import socket, time, json

# set up socket port
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
host = '192.168.178.38'
port = 43210

# log to file forever
with open('data.log', 'w') as logFile:
	while True:
		sock.sendto('measure'.encode('utf-8'), (host, port))
		data, addr = sock.recvfrom(1024)
		repl = json.loads(data.decode('utf-8'))
		print (repl['hiResC'])
		logFile.write('{0}\n'.format(repl['hiResC']))
		time.sleep(6.0)
