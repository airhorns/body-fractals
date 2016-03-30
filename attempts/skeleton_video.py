from vispy import app, gloo, set_log_level
from vispy.util.transforms import perspective, translate, scale

import numpy as np
from utils import read_shader
from primesense import openni2, nite2, _nite2
import sys
import pickle


set_log_level('INFO')
gloo.gl.use_gl('gl2 debug')


class Canvas(app.Canvas):

    def __init__(self, *args, **kwargs):
        app.Canvas.__init__(self, *args, **kwargs)
        self.raw_depth_program = gloo.Program(read_shader('1.vert'), read_shader('skeleton_video.frag'))
        self.skeleton_program = gloo.Program(read_shader('skeleton_bones.vert'), read_shader('skeleton_bones.frag'))

        # Fill screen with single quad, fragment shader does all the real work
        self.raw_depth_program["position"] = [(-1, -1), (-1, 1), (1, 1),
                                    (-1, -1), (1, 1), (1, -1)]
        self.raw_depth_program["frame"] = gloo.Texture2D(shape=(480, 640, 2), format='luminance_alpha')

        width, height = self.physical_size
        gloo.set_viewport(0, 0, width, height)
        self.raw_depth_program['resolution'] = [width, height]

        # Set uniform and attribute
        self.skeleton_program['a_position'] = gloo.VertexBuffer()

        openni2.initialize()
        nite2.initialize()
        self.user_tracker = nite2.UserTracker(False)

        gloo.set_state(clear_color='black', blend=True, blend_func=('src_alpha', 'one_minus_src_alpha'))
        self._timer = app.Timer('auto', connect=self.update, start=True)
        self.show()

    def on_draw(self, event):
        frame = self.user_tracker.read_frame()
        frame_data = np.array(frame.get_depth_frame().get_buffer_as_uint8(), dtype=np.uint8)
        frame_data.shape = (480, 640, 2)

        for user in frame.users:
            if user.is_new():
                print "%s: new: %s, visible: %s, lost: %s, skeleton state: %s" % (user.id, user.is_new(), user.is_visible(), user.is_lost(), user.skeleton.state)
                self.user_tracker.start_skeleton_tracking(user.id)

            if user.is_lost():
                self.user_tracker.stop_skeleton_tracking(user.id)
                print "%s: new: %s, visible: %s, lost: %s, skeleton state: %s" % (user.id, user.is_new(), user.is_visible(), user.is_lost(), user.skeleton.state)

            if user.skeleton.state == _nite2.NiteSkeletonState.NITE_SKELETON_TRACKED:
                joint_positions = np.asarray(list((joint.position.x / 1000.0, joint.position.y / 1000.0, 0) for joint in user.skeleton.joints), dtype=np.float32)
                self.skeleton_program['a_position'] = gloo.VertexBuffer(joint_positions)

        gloo.clear(color=True, depth=True)
        self.raw_depth_program["frame"].set_data(frame_data[::-1])
        self.raw_depth_program.draw()
        self.skeleton_program.draw('points')

if __name__ == '__main__':
    canvas = Canvas(size=(400, 400), keys='interactive', always_on_top=True)
    app.run()
