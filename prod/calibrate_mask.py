from vispy import app, gloo, set_log_level
import time
from mask import MaskProgram

class MainCanvas(app.Canvas):

    def __init__(self, *args, **kwargs):
        super(MainCanvas, self).__init__(*args, **kwargs)
        gloo.set_state(clear_color='black', blend=True, blend_func=('src_alpha', 'one_minus_src_alpha'))

        self.mask = MaskProgram(bg=(0, 0, 0, 1), fg=(1, 1, 1, 1))

        self.apply_zoom()
        self._timer = app.Timer('auto', connect=self.update, start=True)
        self.show()

    def on_draw(self, event):
        self.mask.draw()

    def on_resize(self, event):
        self.apply_zoom()

    def apply_zoom(self):
        width, height = self.physical_size
        gloo.set_viewport(0, 0, width, height)

        self.mask['resolution'] = [width, height]

    def on_key_press(self, event):
        params = [('triangleA', 0), ('triangleA', 1), ('triangleB', 0), ('triangleB', 1), ('triangleC', 0), ('triangleC', 1)]
        top_keys = ('a', 's', 'd', 'f', 'g', 'h', 'j')
        bottom_keys = ('z', 'x', 'c', 'v', 'b', 'n', 'm')

        adjustment = 0.005
        if event.text in top_keys:
            param, index = params[top_keys.index(event.text)]
        elif event.text in bottom_keys:
            param, index = params[bottom_keys.index(event.text)]
            adjustment *= -1
        else:
            return

        value = self.mask[param][index] + adjustment
        if value > 1 or value < 0:
            print "Not setting %s, max range" % (param)
        else:
            print "Setting %s to %s" % (param, value)
            tup = list(self.mask[param])
            tup[index] = value
            self.mask[param] = tup

        for key in ('triangleA', 'triangleB', 'triangleC'):
            print "%s: %s" % (key, self.mask[key])


if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-W", "--width", type="int", default=800)
    parser.add_option("-H", "--height", type="int", default=600)

    (options, args) = parser.parse_args()
    set_log_level('INFO')
    gloo.gl.use_gl('gl2 debug')

    canvas = MainCanvas(size=(options.width, options.height),
                        keys='interactive',
                        always_on_top=True,
                        resizable=True)
    app.run()
