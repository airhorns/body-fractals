from primesense import _nite2
import numpy as np
from utils import joint_to_array

JT = _nite2.NiteJointType


class Input(object):

    def __init__(self):
        self.count = 0


class FakeInput(Input):

    def __init__(self, sweep=False):
        super(FakeInput, self).__init__()
        self.sweep = sweep
        self._inputs = {
            'angleA': 0,
            'angleB': 0,
            'iterationScale': 0.5,
            'iterationOffset': 0.5,
            'trapWidth': 0
        }

    def on_key_press(self, event):
        params = [('iterationScale', 0.1), ('iterationOffset', 0.1), ('trapWidth', 1.1), ('angleA', 0.01), ('angleB', 0.01)]
        top_keys = ('a', 's', 'd', 'f', 'g', 'h', 'j')
        bottom_keys = ('z', 'x', 'c', 'v', 'b', 'n', 'm')

        if event.text in top_keys:
            param, adjustment = params[top_keys.index(event.text)]
        elif event.text in bottom_keys:
            param, adjustment = params[bottom_keys.index(event.text)]
            adjustment *= -1
        else:
            return

        value = self._inputs[param] + adjustment
        if value > 1 or value < 0:
            print "Not setting %s, max range" % (param)
        else:
            print "Setting %s to %s" % (param, value)
            self._inputs[param] = value

    def inputs(self, elapsed, user_tracker, user_tracker_frame):
        self.count += 1
        if self.sweep:
            self.inputs.update({
                'angleA': 0.5 + np.sin(self.count / 180.0),
                'angleB': 0.5 + np.sin(self.count / 120.0),
            })

        return self._inputs


class FakeUserTracker(object):

    def read_frame(self):
        return None


class SkeletonInput(Input):

    def inputs(self, elapsed, user_tracker, user_tracker_frame):
        self.count += 1

        for user in user_tracker_frame.users:
            if user.is_new():
                user_tracker.start_skeleton_tracking(user.id)

            if user.is_lost():
                user_tracker.stop_skeleton_tracking(user.id)

            if self.count % 30 == 0:
                print "%s: new: %s, visible: %s, lost: %s, skeleton state: %s" % (user.id, user.is_new(), user.is_visible(), user.is_lost(), user.skeleton.state)

            if user.skeleton.state == _nite2.NiteSkeletonState.NITE_SKELETON_TRACKED:
                joints = user.skeleton.joints

                user_height = self.joint_distance_in_space(joints[JT.NITE_JOINT_HEAD], joints[JT.NITE_JOINT_LEFT_FOOT])

                return {
                    'angleA': self.joint_angle_relative_to_joint(joints[JT.NITE_JOINT_LEFT_ELBOW], joints[JT.NITE_JOINT_LEFT_SHOULDER], joints[JT.NITE_JOINT_LEFT_HAND]),
                    'angleB': self.joint_angle_relative_to_joint(joints[JT.NITE_JOINT_RIGHT_ELBOW], joints[JT.NITE_JOINT_RIGHT_SHOULDER], joints[JT.NITE_JOINT_RIGHT_HAND]),
                    'iterationScale': self.joint_angle_relative_to_joint(joints[JT.NITE_JOINT_LEFT_SHOULDER], joints[JT.NITE_JOINT_LEFT_HIP], joints[JT.NITE_JOINT_LEFT_ELBOW]),
                    'iterationOffset': self.joint_angle_relative_to_joint(joints[JT.NITE_JOINT_RIGHT_SHOULDER], joints[JT.NITE_JOINT_RIGHT_HIP], joints[JT.NITE_JOINT_RIGHT_ELBOW]),
                    'trapWidth': self.normalized_joint_distance_in_space(joints[JT.NITE_JOINT_RIGHT_HIP], joints[JT.NITE_JOINT_RIGHT_FOOT], user_height / 2, user_height)
                }

        return {
            'angleA': 0,
            'angleB': 0,
            'iterationScale': 0,
            'iterationOffset': 0,
            'trapWidth': 0
        }

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

    def joint_angle_relative_to_screen(self, joint):
        pass
