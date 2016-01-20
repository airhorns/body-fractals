from vispy import app, gloo
import os.path


# vispy Canvas
# -----------------------------------------------------------------------------
class Canvas(app.Canvas):

    def __init__(self, *args, **kwargs):
        app.Canvas.__init__(self, *args, **kwargs)
        self.program = gloo.Program(self.read_shader('1.vert'), self.read_shader('1.frag'))
        gloo.set_clear_color(color='black')
        self._timer = app.Timer('auto', connect=self.update, start=True)
        self.show()

    def on_draw(self, event):
        self.program.draw()

    def read_shader(self, name):
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), name)) as f:
            return f.read()


if __name__ == '__main__':
    canvas = Canvas(size=(800, 800), keys='interactive')
    app.run()
