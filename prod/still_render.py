from vispy import app, gloo, set_log_level
import random
import sys
from fractal import FractalProgram
from input import RandomInput, FileStoredInput
from definitions import Definitions
from vispy.io import write_png
from vispy.gloo.util import _screenshot
import yaml


class StillCanvas(app.Canvas):

    def __init__(self, *args, **kwargs):
        self.exit = kwargs.pop('exit', False)
        self.inputs_path = kwargs.pop('inputs_path', None)
        super(StillCanvas, self).__init__(*args, **kwargs)
        gloo.set_state(clear_color='black', blend=True, blend_func=('src_alpha', 'one_minus_src_alpha'))

        self.inputs = None

        if self.inputs_path is not None:
            self.input_manager = FileStoredInput(self.inputs_path)
            self.time = self.input_manager.stored_time
            definition = Definitions[self.input_manager.stored_definition_name]
        else:
            self.input_manager = RandomInput()
            self.time = float(random.randint(0, 345212312))
            definition = Definitions[random.choice(Definitions.keys())]

        self.fractal = FractalProgram(definition, mask=False)

        self.apply_zoom()
        self._timer = app.Timer(1.0 / 5, connect=self.update, start=True)
        if self.exit:
            app.Timer(1, connect=self.write_and_exit, start=True, iterations=1)
        # self.update(None)
        # self.update(None)
        self.show()
        # self.write_and_exit()

    def write(self):
        image = _screenshot(alpha=True)
        write_png('covers2/%s.png' % self.time, image)

        data = {}
        data.update(self.input_manager.smoothed_inputs)
        data['time'] = self.time
        data['definition'] = self.fractal.definition['name']

        with open('covers2/%s.yml' % self.time, 'w') as f:
            yaml.dump(data, stream=f)

        print "Wrote image and data for %s" % self.time

    def write_and_exit(self, event=None):
        self.write()
        sys.exit(0)

    def on_draw(self, event):
        self.input_manager.time = self.time
        self.fractal['time'] = self.time
        self.fractal.draw()
        self.inputs = self.input_manager.inputs(self.time)
        self.fractal.adjust(self.inputs)

    def on_resize(self, event):
        self.apply_zoom()

    def apply_zoom(self):
        width, height = self.physical_size
        gloo.set_viewport(0, 0, width, height)

        self.fractal['resolution'] = [width, height]

    def on_key_press(self, event):
        if event.text == 'w':
            self.write()
        else:
            self.input_manager.on_key_press(event)
            print self.inputs
            self.update()


if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-W", "--width", type="int", default=800)
    parser.add_option("-H", "--height", type="int", default=600)
    parser.add_option("-e", "--exit", action="store_true")
    parser.add_option("-l", "--path", type="string")

    (options, args) = parser.parse_args()
    set_log_level('INFO')
    gloo.gl.use_gl('gl2 debug')

    canvas = StillCanvas(size=(options.width, options.height),
                         keys='interactive',
                         resizable=True,
                         inputs_path=options.path,
                         exit=options.exit)
    app.run()
