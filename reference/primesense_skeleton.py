from primesense import openni2, nite2

openni2.initialize()
nite2.initialize()

# dev = openni2.Device.open_any()

user_tracker = nite2.UserTracker(False)

import ipdb; ipdb.set_trace()
while True:
    frame = user_tracker.read_frame()
    print frame.users

openni2.unload()
