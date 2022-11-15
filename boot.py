import os

import pycom
from machine import SD

pycom.heartbeat(True)

sd = SD()
os.mount(sd, '/sd')
