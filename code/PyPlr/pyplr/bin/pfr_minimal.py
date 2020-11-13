from time import sleep
from pyplr.pupil import PupilCore, LightStamper, new_trigger

p = PupilCore()
p.command('R')
sleep(5.)
trigger = new_trigger('LIGHT_ON')
lst = LightStamper(p, trigger, threshold=15, wait_time=.10)
lst.start() 
# shine a light here
sleep(20.)
p.command('r') 


