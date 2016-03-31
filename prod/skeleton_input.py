from primesense import _nite2
import numpy as np
from utils import joint_to_array


JOINT_TYPES = _nite2.NiteJointType


class SkeletonInput(object):

    def inputs(self, user):
        joints = user.skeleton.joints

        return {
            'angleA': self.joint_angle_relative_to_joint(joints[JOINT_TYPES.NITE_JOINT_LEFT_ELBOW], joints[JOINT_TYPES.NITE_JOINT_LEFT_SHOULDER], joints[JOINT_TYPES.NITE_JOINT_LEFT_HAND]),
            'angleB': self.joint_angle_relative_to_joint(joints[JOINT_TYPES.NITE_JOINT_RIGHT_ELBOW], joints[JOINT_TYPES.NITE_JOINT_RIGHT_SHOULDER], joints[JOINT_TYPES.NITE_JOINT_RIGHT_HAND]),
            # 'modelScale': self.joint_distance_in_space(joints[JOINT_TYPES.NITE_JOINT_LEFT_HAND], joints[JOINT_TYPES.NITE_JOINT_RIGHT_HAND], 180, 800)
        }

    def joint_angle_relative_to_joint(self, root, appendage_a, appendage_b):
        # inverse of cosine law -- translate the vectors to the root by subtracting out the root, then using an inverted dot product forumla isolating for the angle
        root = joint_to_array(root)
        a = joint_to_array(appendage_a) - root
        b = joint_to_array(appendage_b) - root
        return np.arccos(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))) / np.pi

    def joint_distance_in_space(self, joint_a, joint_b, lower_bound, upper_bound):
        raw_distance = np.linalg.norm(joint_to_array(joint_a) - joint_to_array(joint_b))
        return np.clip((raw_distance - lower_bound) / upper_bound, 0, 1)

    def joint_angle_relative_to_screen(self, joint):
        pass
