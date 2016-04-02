from vispy import gloo
import numpy as np
from utils import read_shader
from primesense import _nite2


class SkeletonBonesProgram(gloo.Program):

    def __init__(self):
        super(SkeletonBonesProgram, self).__init__(read_shader('skeleton_bones.vert'), read_shader('skeleton_bones.frag'))
        self['a_position'] = gloo.VertexBuffer()

    def draw(self, user_tracker_frame):
        for user in user_tracker_frame.users:
            joint_positions = np.asarray(list((joint.position.x / 1000.0, joint.position.y / 1000.0, 0) for joint in user.skeleton.joints), dtype=np.float32)
            self['a_position'] = gloo.VertexBuffer(joint_positions)

        super(SkeletonBonesProgram, self).draw('points')
