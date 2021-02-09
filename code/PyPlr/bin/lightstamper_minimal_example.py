from time import sleep

from pupil import PupilCore, LightStamper, PupilGrabber, new_trigger

# set up pupil
pupil = PupilCore()

# make trigger
trigger = new_trigger('LIGHT_ON')

# start LightStamper
lst = LightStamper(pupil, trigger, threshold=15, wait_time=10.)
pgr = PupilGrabber(pupil, topic='pupil.1.3d', secs=10.)
lst.start()
pgr.start()
sleep(10)

# administer light stimulus

