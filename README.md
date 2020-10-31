# ThermUDP
UDP Server for DS1621 Thermometer, running in Python 3 on a Raspberry Pi.  Typical UDP reply packet follows:
```JSON
{"loResC": 25.5, "hiResC": 25.375, "hiResF": 77.675, "date": "10/19/2020", "time": "17:09:58"}
```
The DS1621 is a self-contained thermometer and thermostat made by [Maxim](https://www.maximintegrated.com/en/products/sensors/DS1621.html) and available at [DigiKey](https://www.digikey.com/en/products/detail/maxim-integrated/DS1621/956905).  It interfaces with I<sup>2</sup>C, and its power supply range includes both 3.3V and 5.0V, so you can either connect it directly to the RasPi [GPIO header](https://www.raspberrypi.org/documentation/usage/gpio/) with 3.3V levels, or use a [level shifter](https://www.nxp.com/docs/en/application-note/AN10441.pdf) to operate at 5.0V.  In my application I used a level shifter implemented with an [FDC6301N](https://www.onsemi.com/products/discretes-drivers/mosfets/fdc6301n) dual FET, as suggested by [AB Electronics](https://www.abelectronics.co.uk/kb/article/1049/logic-level-converter).  You'll have to do some setup to get the RasPi talking with I<sup>2</sup>C, and details may vary depending on which RasPi you have.  I found the [SparkFun tutorial](https://learn.sparkfun.com/tutorials/raspberry-pi-spi-and-i2c-tutorial#i2c-on-pi) to be helpful.

The UDP temperature server posted here uses the [smbus](https://pypi.org/project/smbus2/) library to let Python 3 talk to the DS1621.  This library has the nice property that it allows multiple processes on the RasPi to interact with the I<sup>2</sup>C bus at the same time.  Obviously the accesses are serialized behind the scenes.  Interestingly, this works even if different processes try to access the same I<sup>2</sup>C address, which is to say the same chip.  So you can run two instances of the UPD server posted here at the same time, so long as they use different UDP port numbers.  Following is an unecessarily complicated example of how this can be done, using optional command line arguments to modify the server settings.  The [netcat](https://www.commandlinux.com/man-page/man1/nc.1.html) command line utility is used as the UDP client here.

```SH
pi@raspberrypi:~/Projects/ThermAsync $ ./ThermAsyncio.py -port 40000 &
[1] 1312
pi@raspberrypi:~/Projects/ThermAsync $ ThermAsyncio.py reads temperature from Maxim/Dallas DS1621
thermometer connected by I2C to Raspberry Pi computer.
M. Williamsen, 10/26/2020, https://github.com/springleik
Usage: python3 ThermAsyncio.py [arg names and values]
  arg name | arg value
  ---------|----------
  -port    | socket port number   (default is 43210)
  -host    | socket host address  (default is any)
  -addr    | DS1621 I2C address   (default is 0x48)
Running script: "./ThermAsyncio.py"
  in Python: 3.7.3 (default, Apr  3 2019, 05:39:12) 
[GCC 8.2.0]
DS1621 intialized at addr: 0x48
Main loop started.
./ThermAsyncio.py -port 40001 &
[2] 1313
pi@raspberrypi:~/Projects/ThermAsync $ ThermAsyncio.py reads temperature from Maxim/Dallas DS1621
thermometer connected by I2C to Raspberry Pi computer.
M. Williamsen, 10/26/2020, https://github.com/springleik
Usage: python3 ThermAsyncio.py [arg names and values]
  arg name | arg value
  ---------|----------
  -port    | socket port number   (default is 43210)
  -host    | socket host address  (default is any)
  -addr    | DS1621 I2C address   (default is 0x48)
Running script: "./ThermAsyncio.py"
  in Python: 3.7.3 (default, Apr  3 2019, 05:39:12) 
[GCC 8.2.0]
DS1621 intialized at addr: 0x48
Main loop started.
jobs
[1]-  Running                 ./ThermAsyncio.py -port 40000 &
[2]+  Running                 ./ThermAsyncio.py -port 40001 &
pi@raspberrypi:~/Projects/ThermAsync $ nc -u 127.0.0.1 40000

{'loResC': 23.5, 'hiResC': 23.5, 'hiResF': 74.3, 'date': '10/31/2020', 'time': '11:29:34'}
{"loResC": 23.5, "hiResC": 23.5, "hiResF": 74.3, "date": "10/31/2020", "time": "11:29:34"}
^C
pi@raspberrypi:~/Projects/ThermAsync $ nc -u 127.0.0.1 40001

{'loResC': 23.5, 'hiResC': 23.5, 'hiResF': 74.3, 'date': '10/31/2020', 'time': '11:29:41'}
{"loResC": 23.5, "hiResC": 23.5, "hiResF": 74.3, "date": "10/31/2020", "time": "11:29:41"}
^C
pi@raspberrypi:~/Projects/ThermAsync $ 
```

There are various ways for the UDP server to start itself at boot time.  My favorite is [daemontools](https://cr.yp.to/daemontools.html).
