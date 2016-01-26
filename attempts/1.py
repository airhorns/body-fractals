from vispy import app, gloo, set_log_level
import os.path
import time


set_log_level('INFO')
gloo.gl.use_gl('gl2 debug')


class Canvas(app.Canvas):

    def __init__(self, *args, **kwargs):
        app.Canvas.__init__(self, *args, **kwargs)
        self.program = gloo.Program(self.read_shader('1.vert'), self.read_shader('1.frag'))

        # Fill screen with single quad, fragment shader does all the real work
        self.program["position"] = [(-1, -1), (-1, 1), (1, 1),
                                    (-1, -1), (1, 1), (1, -1)]

        self._starttime = time.time()
        self.program['time'] = 0

        self.program['cameraPos'] = (0.0, 3.0, -6.0)
        self.program['cameraLookat'] = (0.0, -0.85, 0.5)
        self.program['lightDir'] = (-1.4, 0.8, -1.0)  # needs to be normalized
        self.program['lightColour'] = (3.0, 1.4, 0.3)
        self.program['diffuse'] = (0.3, 0.3, 0.3)
        self.program['ambientFactor'] = 0.35
        self.program['rotateWorld'] = 1
        self.program['ao'] = True
        self.program['shadows'] = True
        self.program['antialias'] = False  # mutually exclusive with dof

        self.apply_zoom()

        gloo.set_clear_color(color='black')
        self._timer = app.Timer('auto', connect=self.update, start=True)
        self.show()

    def on_draw(self, event):
        gloo.clear()
        self.program['time'] = time.time() - self._starttime
        self.program.draw()

    def read_shader(self, name):
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), name)) as f:
            return f.read()

    def apply_zoom(self):
        width, height = self.physical_size
        gloo.set_viewport(0, 0, width, height)
        self.program['resolution'] = [width, height]

if __name__ == '__main__':
    canvas = Canvas(size=(1000, 800), keys='interactive')
    app.run()
