from vispy import app, gloo, set_log_level
import os.path
import numpy as np
import time
from utils import normalize


set_log_level('INFO')
gloo.gl.use_gl('gl2 debug')


class Canvas(app.Canvas):

    def __init__(self, *args, **kwargs):
        app.Canvas.__init__(self, *args, **kwargs)
        self.program = gloo.Program(self.read_shader('1.vert'), self.read_shader('4.frag'))

        # Fill screen with single quad, fragment shader does all the real work
        self.program["position"] = [(-1, -1), (-1, 1), (1, 1),
                                    (-1, -1), (1, 1), (1, -1)]

        self._starttime = time.time()
        self.program['time'] = 0

        self.program['cameraPos'] = (0.0, 3.0, -6.0)
        self.program['cameraLookat'] = (0.0, 0.0, 0.0)
        self.program['lightDir'] = normalize(np.array((1, 1, -1.5)))  # needs to be normalized
        self.program['diffuse'] = (1, 1, 1)
        self.program['ambientFactor'] = 0.45
        self.program['rotateWorld'] = True
        self.program['modelScale'] = 1.0
        self.program['iterationScale'] = 1.5
        self.program['iterationOffset'] = 1.8
        self.program['iterations'] = 14
        self.program['cubeWidth'] = 1
        self.program['angleA'] = 1
        self.program['angleB'] = 1

        self.apply_zoom()

        gloo.set_clear_color(color='black')
        self._timer = app.Timer('auto', connect=self.update, start=True)
        self.show()

    def on_draw(self, event):
        self.program['time'] = time.time() - self._starttime
        self.program.draw()

    def read_shader(self, name):
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), name)) as f:
            return f.read()

    def apply_zoom(self):
        width, height = self.physical_size
        gloo.set_viewport(0, 0, width, height)
        self.program['resolution'] = [width, height]

    def on_key_press(self, event):
        params = [('iterationScale', 0.1), ('iterationOffset', 0.1), ('iterations', 1), ('cubeWidth', 0.1), ('angleA', 0.01), ('angleB', 0.01), ('modelScale', 0.1)]
        top_keys = ('a', 's', 'd', 'f', 'g', 'h', 'j')
        bottom_keys = ('z', 'x', 'c', 'v', 'b', 'n', 'm')

        if event.text in top_keys:
            param, adjustment = params[top_keys.index(event.text)]
        elif event.text in bottom_keys:
            param, adjustment = params[bottom_keys.index(event.text)]
            adjustment *= -1
        else:
            return

        print "Setting %s to %s" % (param, self.program[param] + adjustment)
        self.program[param] += adjustment

if __name__ == '__main__':
    canvas = Canvas(size=(400, 400), keys='interactive', always_on_top=True)
    app.run()
