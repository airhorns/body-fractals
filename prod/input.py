from primesense import _nite2, nite2, openni2
import numpy as np
from utils import joint_to_array, LowConfidenceException

JT = _nite2.NiteJointType

user_tracker = None


class Input(object):

    def __init__(self):
        self.count = 0

    def on_key_press(self, event):
        pass

    def inputs(self, elapsed):
        self.count += 1
        if self.count % 60 == 0:
            print self.smoothed_inputs


class FakeInput(Input):

    def __init__(self, sweep=True):
        super(FakeInput, self).__init__()
        self.sweep = sweep
        self.smoothed_inputs = {
            'angleA': 0,
            'angleB': 0,
            'angleC': 0,
            'iterationScale': 0.5,
            'iterationOffsetX': 0.5,
            'iterationOffsetY': 0.5,
            'iterationOffsetZ': 0.5,
            'trapWidth': 0
        }

    def on_key_press(self, event):
        params = [('iterationScale', 0.1), ('iterationOffsetX', 0.1), ('iterationOffsetY', 0.1), ('trapWidth', 1.1), ('angleA', 0.01), ('angleB', 0.01)]
        top_keys = ('a', 's', 'd', 'f', 'g', 'h', 'j')
        bottom_keys = ('z', 'x', 'c', 'v', 'b', 'n', 'm')

        if event.text in top_keys:
            param, adjustment = params[top_keys.index(event.text)]
        elif event.text in bottom_keys:
            param, adjustment = params[bottom_keys.index(event.text)]
            adjustment *= -1
        else:
            return

        value = self.smoothed_inputs[param] + adjustment
        if value > 1 or value < 0:
            print "Not setting %s, max range" % (param)
        else:
            print "Setting %s to %s" % (param, value)
            self.smoothed_inputs[param] = value

    def inputs(self, elapsed):
        super(FakeInput, self).inputs(elapsed)

        if self.sweep:
            self.smoothed_inputs.update({
                'angleA': 0.5 + np.sin(self.count / 3000.0) / 2,
                'angleB': 0.5 + np.sin(self.count / 4000.0) / 2,
                'angleC': 0.5 + np.sin(self.count / 5000.0) / 2,
                'iterationOffsetX': 0.5 + np.sin(self.count / 6000.0) / 2,
                'iterationOffsetY': 0.5 + np.sin(self.count / 7000.0) / 2,
            })

        return self.smoothed_inputs


# MAX_DIFFERENCE = 0.05

class SmoothInputs(dict):

    def __init__(self, *args, **kwargs):
        super(SmoothInputs, self).__init__(*args, **kwargs)
        self._previous = {}

    def smooth_update(self, attributes):
        for key, value in attributes.iteritems():
            self.smooth_set(key, value)

    def smooth_set(self, key, value_func):
        previous = self._previous.get(key, 0)
        try:
            value = value_func()
        except LowConfidenceException:
            value = previous
            pass

        # difference = value - previous
        # if abs(difference) > MAX_DIFFERENCE:
        #     print "key: %s, value: %s, previous: %s, difference: %s" % (key, value, previous, difference)
        #     value = previous + np.sign(difference) * MAX_DIFFERENCE

        self._previous[key] = self.get(key, 0)
        self[key] = value


class SkeletonInput(Input):

    def __init__(self):
        super(SkeletonInput, self).__init__()
        if user_tracker is None:
            openni2.initialize()
            nite2.initialize()

        self.smoothed_inputs = SmoothInputs()
        self.reset_user_tracker()

    def reset_user_tracker(self):
        global user_tracker
        user_tracker = nite2.UserTracker(False)
        user_tracker.skeleton_smoothing_factor = 0.8

    def inputs(self, elapsed):
        super(SkeletonInput, self).inputs(elapsed)

        global user_tracker
        frame = user_tracker.read_frame()
        for user in frame.users:
            if user.is_new():
                user_tracker.start_skeleton_tracking(user.id)

            if user.is_lost():
                user_tracker.stop_skeleton_tracking(user.id)

            if self.count % 30 == 0:
                print "%s: new: %s, visible: %s, lost: %s, skeleton state: %s" % (user.id, user.is_new(), user.is_visible(), user.is_lost(), user.skeleton.state)

            if user.skeleton.state == _nite2.NiteSkeletonState.NITE_SKELETON_TRACKED and user.is_visible():
                joints = user.skeleton.joints

                try:
                    user_height = self.joint_distance_in_space(joints[JT.NITE_JOINT_HEAD], joints[JT.NITE_JOINT_LEFT_FOOT])
                except LowConfidenceException:
                    user_height = 10000000

                self.smoothed_inputs.smooth_update({
                    'angleA': lambda: self.joint_line_angle_relative_to_plane(joints[JT.NITE_JOINT_LEFT_ELBOW], joints[JT.NITE_JOINT_RIGHT_ELBOW], np.array((0, 0, 1))),
                    'angleB': lambda: self.joint_angle_relative_to_joint(joints[JT.NITE_JOINT_RIGHT_ELBOW], joints[JT.NITE_JOINT_RIGHT_SHOULDER], joints[JT.NITE_JOINT_RIGHT_HAND]),
                    'angleC': lambda: self.joint_angle_relative_to_joint(joints[JT.NITE_JOINT_LEFT_ELBOW], joints[JT.NITE_JOINT_LEFT_SHOULDER], joints[JT.NITE_JOINT_LEFT_HAND]),
                    'iterationScale': lambda: self.joint_angle_relative_to_joint(joints[JT.NITE_JOINT_LEFT_SHOULDER], joints[JT.NITE_JOINT_LEFT_HIP], joints[JT.NITE_JOINT_LEFT_ELBOW]),
                    'iterationOffsetX': lambda: self.joint_angle_relative_to_joint(joints[JT.NITE_JOINT_RIGHT_SHOULDER], joints[JT.NITE_JOINT_RIGHT_HIP], joints[JT.NITE_JOINT_RIGHT_ELBOW]),
                    'iterationOffsetY': lambda: self.joint_angle_relative_to_joint(joints[JT.NITE_JOINT_RIGHT_SHOULDER], joints[JT.NITE_JOINT_RIGHT_HIP], joints[JT.NITE_JOINT_RIGHT_ELBOW]),
                    'iterationOffsetZ': lambda: self.joint_angle_relative_to_joint(joints[JT.NITE_JOINT_RIGHT_SHOULDER], joints[JT.NITE_JOINT_RIGHT_HIP], joints[JT.NITE_JOINT_RIGHT_ELBOW]),
                    'trapWidth': lambda: self.joint_angle_relative_to_joint(joints[JT.NITE_JOINT_RIGHT_ELBOW], joints[JT.NITE_JOINT_RIGHT_SHOULDER], joints[JT.NITE_JOINT_RIGHT_HAND])
                })

                return self.smoothed_inputs

        self.smoothed_inputs.smooth_update({
            'angleA': lambda: 0,
            'angleB': lambda: 0,
            'angleC': lambda: 0,
            'iterationScale': lambda: 0,
            'iterationOffsetX': lambda: 0,
            'iterationOffsetY': lambda: 0,
            'iterationOffsetZ': lambda: 0,
            'trapWidth': lambda: 0
        })

        return self.smoothed_inputs

    def joint_distance_relative_to_reference_joint_distance(self, joint_a, joint_b, reference_joint_a, reference_joint_b, max_multiplier):
        variable_distance = self.joint_distance_in_space(joint_a, joint_b)
        reference_distance = self.joint_distance_in_space(reference_joint_a, reference_joint_b)

        return np.clip((variable_distance / reference_distance) / max_multiplier, 0, 1)

    def joint_angle_relative_to_joint(self, root, appendage_a, appendage_b):
        # inverse of cosine law -- translate the vectors to the root by subtracting out the root, then using an inverted dot product forumla isolating for the angle
        root = joint_to_array(root)
        a = joint_to_array(appendage_a) - root
        b = joint_to_array(appendage_b) - root
        return np.arccos(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))) / np.pi

    def joint_distance_in_space(self, joint_a, joint_b):
        return np.linalg.norm(joint_to_array(joint_a) - joint_to_array(joint_b))

    def normalized_joint_distance_in_space(self, joint_a, joint_b, expected_lower_bound, expected_upper_bound):
        return np.clip((self.joint_distance_in_space(joint_a, joint_b) - expected_lower_bound) / expected_upper_bound, 0, 1)

    def joint_line_angle_relative_to_plane(self, joint_a, joint_b, plane_normal):
        # http://www.vitutor.com/geometry/distance/line_plane.html
        line = joint_to_array(joint_b) - joint_to_array(joint_a)
        return np.arcsin(np.dot(line, plane_normal) / (np.linalg.norm(line) * np.linalg.norm(plane_normal))) / np.pi

    def joint_angle_relative_to_screen(self, joint):
        pass

    def on_key_press(self, event):
        if event.text == ' ':
            self.reset_user_tracker()


class GroupBodyInputTracker(SkeletonInput):

    def __init__(self, *args, **kwargs):
        super(GroupBodyInputTracker, self).__init__(*args, **kwargs)
        self.min = 700
        self.max = 1500

    def inputs(self, elapsed):
        Input.inputs(self, elapsed)

        global user_tracker
        frame = user_tracker.read_frame()
        positions = []

        for user in frame.users:
            if self.count % 30 == 0:
                print "%s: new: %s, visible: %s, lost: %s" % (user.id, user.is_new(), user.is_visible(), user.is_lost())

            if user.is_visible():
                positions.append(user.centerOfMass.z)

        if len(positions) > 0:
            self.min = min(self.min, min(positions))
            self.max = max(self.max, max(positions))
            position_range = float(self.max - self.min)

            normalized_positions = {i: np.clip(value, 0, 1) for i, value in enumerate(map(lambda p: (p - self.min) / position_range, positions))}
        else:
            normalized_positions = {}

        self.smoothed_inputs.smooth_update({
            'angleA': lambda: normalized_positions.get(1, 0),
            'angleB': lambda: normalized_positions.get(0, 0),
            'angleC': lambda: normalized_positions.get(3, 0.5 + np.sin(self.count / 400.0) / 2),
            'iterationScale': lambda: normalized_positions.get(2, 0),
            'iterationOffsetX': lambda: normalized_positions.get(1, 0.5 + np.sin(self.count / 600.0) / 2),
            'iterationOffsetY': lambda: normalized_positions.get(1, 0.5 + np.sin(self.count / 600.0) / 2),
            'iterationOffsetZ': lambda: normalized_positions.get(1, 0.5 + np.sin(self.count / 600.0) / 2),
            'trapWidth': lambda: 0.5 + np.sin(self.count / 600.0) / 2,
        })

        return self.smoothed_inputs


class MicrosoftSkeletonInput(SkeletonInput):

    def __init__(self):
        from pykinect2 import PyKinectV2
        from pykinect2.PyKinectV2 import *
        from pykinect2 import PyKinectRuntime

        self.count = 1
        self.kinect = PyKinectRuntime.PyKinectRuntime(PyKinectV2.FrameSourceTypes_Body)

    def inputs(self, elapsed):
        if self._kinect.has_new_body_frame():
            frame = self._kinect.get_last_body_frame()

        for body in frame:
            if not body.is_tracked:
                continue

            if self.count % 30 == 0:
                print body

        return {
            'angleA': 0,
            'angleB': 0,
            'iterationScale': 0,
            'iterationOffsetX': 0,
            'iterationOffsetY': 0,
            'iterationOffsetZ': 0,
            'trapWidth': 0
        }
