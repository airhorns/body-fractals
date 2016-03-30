from primesense import openni2, nite2, _nite2

openni2.initialize()
nite2.initialize()

dev = openni2.Device.open_any()

print dev.get_device_info()

user_tracker = nite2.UserTracker(False)

while True:
    frame = user_tracker.read_frame()
    for user in frame.users:
        if user.is_new():
            user_tracker.start_skeleton_tracking(user.id)

        if user.is_lost():
            user_tracker.stop_skeleton_tracking(user.id)

        print "%s: new: %s, visible: %s, lost: %s, skeleton state: %s" % (user.id, user.is_new(), user.is_visible(), user.is_lost(), user.skeleton.state)
        if user.skeleton.state == _nite2.NiteSkeletonState.NITE_SKELETON_TRACKED:
            print user.skeleton.joints


openni2.unload()
