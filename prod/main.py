from vispy import app, gloo, set_log_level
import time
from fractal import FractalProgram
from skeleton_bones import SkeletonBonesProgram
from mask import MaskProgram
from input import SkeletonInput, MicrosoftSkeletonInput, FakeInput, FakeUserTracker
from definitions import Definitions


class MainCanvas(app.Canvas):

    def __init__(self, *args, **kwargs):
        self.fake_inputs = kwargs.pop('fake_inputs', False)
        self.draw_bones = kwargs.pop('draw_bones', False)
        self.kiosk_interval = kwargs.pop('kiosk_interval', 0)
        self.start_definition = kwargs.pop('start_definition', 0)
        super(MainCanvas, self).__init__(*args, **kwargs)
        gloo.set_state(clear_color='black', blend=True, blend_func=('src_alpha', 'one_minus_src_alpha'))

        self.skeleton_bones = SkeletonBonesProgram()
        self.mask = MaskProgram()

        self.inputs = None
        if self.fake_inputs:
            self.input_manager = FakeInput(sweep=True)
        else:
            self.input_manager = SkeletonInput()

        self._starttime = time.time()

        self.definition_position = self.start_definition
        self.rotate()
        if self.kiosk_interval > 0:
            self.kiosk_timer = app.Timer(self.kiosk_interval, connect=self.rotate, start=True)

        self._timer = app.Timer('auto', connect=self.update, start=True)
        self.show()

    def rotate(self, event=None):
        definition = Definitions[Definitions.keys()[self.definition_position % len(Definitions.keys())]]
        self.fractal = FractalProgram(definition)

        if self.inputs:
            self.fractal.adjust(self.inputs)
        self.apply_zoom()

        self.definition_position += 1

    def on_draw(self, event):
        elapsed = time.time() - self._starttime
        self.fractal['time'] = elapsed
        self.fractal.draw()

        self.inputs = self.input_manager.inputs(elapsed)
        self.fractal.adjust(self.inputs)

        if not self.fake_inputs and self.draw_bones and hasattr(self.input_manager, 'user_tracker'):
            self.skeleton_bones.draw(self.input_manager.user_tracker.read_frame())

        self.mask.draw()

    def on_resize(self, event):
        self.apply_zoom()

    def apply_zoom(self):
        width, height = self.physical_size
        gloo.set_viewport(0, 0, width, height)

        self.fractal['resolution'] = [width, height]
        self.skeleton_bones['resolution'] = [width, height]
        self.mask['resolution'] = [width, height]

    def on_key_press(self, event):
        self.input_manager.on_key_press(event)


if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-W", "--width", type="int", default=800)
    parser.add_option("-H", "--height", type="int", default=600)
    parser.add_option("-k", "--kiosk", type="int", default=0)
    parser.add_option("-d", "--start", type="int", default=0)
    parser.add_option("-f", "--fake", action="store_true")
    parser.add_option("-b", "--bones", action="store_true")

    (options, args) = parser.parse_args()
    set_log_level('INFO')
    gloo.gl.use_gl('gl2 debug')

    canvas = MainCanvas(size=(options.width, options.height),
                        keys='interactive',
                        always_on_top=True,
                        resizable=True,
                        fake_inputs=options.fake,
                        draw_bones=options.bones,
                        kiosk_interval=options.kiosk,
                        start_definition=options.start)
    app.run()
