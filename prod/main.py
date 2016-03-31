from vispy import app, gloo, set_log_level
import time
from fractal import FractalProgram
from skeleton_bones import SkeletonBonesProgram
from input import SkeletonInput, FakeInput
from definitions import Definitions
from primesense import openni2, nite2, _nite2


class MainCanvas(app.Canvas):

    def __init__(self, *args, **kwargs):
        self.fake_inputs = kwargs.pop('fake_inputs', False)
        self.draw_bones = kwargs.pop('draw_bones', False)
        super(MainCanvas, self).__init__(*args, **kwargs)
        gloo.set_state(clear_color='black', blend=True, blend_func=('src_alpha', 'one_minus_src_alpha'))

        openni2.initialize()
        nite2.initialize()
        self.user_tracker = nite2.UserTracker(False)
        self.user_tracker.skeleton_smoothing_factor = 0.9

        self.fractal = FractalProgram(Definitions['kfs-test'])
        self.skeleton_bones = SkeletonBonesProgram()
        if self.fake_inputs:
            self.input_manager = FakeInput()
        else:
            self.input_manager = SkeletonInput()

        self._starttime = time.time()

        self.apply_zoom()
        self._timer = app.Timer('auto', connect=self.update, start=True)
        self.show()

    def on_draw(self, event):
        elapsed =  time.time() - self._starttime
        self.fractal['time'] = elapsed
        self.fractal.draw()

        user_tracker_frame = self.user_tracker.read_frame()
        inputs = self.input_manager.inputs(elapsed, self.user_tracker, user_tracker_frame)
        self.fractal.adjust(inputs)

        if self.draw_bones:
            self.skeleton_bones.draw(user_tracker_frame)

    def apply_zoom(self):
        width, height = self.physical_size
        gloo.set_viewport(0, 0, width, height)

        self.fractal['resolution'] = [width, height]
        self.skeleton_bones['resolution'] = [width, height]

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

        print "Setting %s to %s" % (param, self.fractal[param] + adjustment)
        self.fractal[param] += adjustment


if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-W", "--width", type="int", default=800)
    parser.add_option("-H", "--height", type="int", default=600)
    parser.add_option("-f", "--fake", action="store_true")
    parser.add_option("-b", "--bones", action="store_true")

    (options, args) = parser.parse_args()
    set_log_level('INFO')
    gloo.gl.use_gl('gl2 debug')

    canvas = MainCanvas(size=(options.width, options.height), keys='interactive', always_on_top=True, fake_inputs=options.fake, draw_bones=options.bones)
    app.run()
