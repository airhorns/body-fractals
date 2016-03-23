from vispy import app, gloo, set_log_level
import os.path
import numpy as np
import sys
import time
from utils import normalize
from primesense import openni2, nite2


set_log_level('INFO')
gloo.gl.use_gl('gl2 debug')


class Canvas(app.Canvas):

    def __init__(self, *args, **kwargs):
        app.Canvas.__init__(self, *args, **kwargs)
        self.program = gloo.Program(self.read_shader('1.vert'), self.read_shader('skeleton_video.frag'))

        # Fill screen with single quad, fragment shader does all the real work
        self.program["position"] = [(-1, -1), (-1, 1), (1, 1),
                                    (-1, -1), (1, 1), (1, -1)]
        self.program["frame"] = gloo.Texture2D(shape=(480, 640, 2), format='luminance_alpha')

        width, height = self.physical_size
        gloo.set_viewport(0, 0, width, height)
        self.program['resolution'] = [width, height]
        openni2.initialize()
        nite2.initialize()
        self.user_tracker = nite2.UserTracker(False)

        gloo.set_clear_color(color='black')
        self._timer = app.Timer('auto', connect=self.update, start=True)
        self.show()

    def read_shader(self, name):
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), name)) as f:
            return f.read()

    def on_draw(self, event):
        self.program.draw()
        frame_data = np.array(self.user_tracker.read_frame().get_depth_frame().get_buffer_as_uint8(), dtype=np.uint8)
        frame_data.shape = (480, 640, 2)
        self.program["frame"].set_data(frame_data[::-1])

if __name__ == '__main__':
    canvas = Canvas(size=(400, 400), keys='interactive')
    app.run()
