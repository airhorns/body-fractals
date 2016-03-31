from vispy import app, gloo, set_log_level
import time
from fractal import FractalProgram
from skeleton_bones import SkeletonBonesProgram
from skeleton_input import SkeletonInput
from definitions import Definitions
from primesense import openni2, nite2, _nite2


class MainCanvas(app.Canvas):

    def __init__(self, *args, **kwargs):
        super(MainCanvas, self).__init__(*args, **kwargs)
        gloo.set_viewport(0, 0, width, height)
        gloo.set_state(clear_color='black', blend=True, blend_func=('src_alpha', 'one_minus_src_alpha'))

        openni2.initialize()
        nite2.initialize()
        self.user_tracker = nite2.UserTracker(False)
        self.user_tracker.skeleton_smoothing_factor = 0.8

        self.fractal = FractalProgram(Definitions['kfs-test'])
        self.skeleton_bones = SkeletonBonesProgram()
        self.skeleton_input = SkeletonInput()

        self._starttime = time.time()
        self._count = 0

        self.apply_zoom()
        self._timer = app.Timer('auto', connect=self.update, start=True)
        self.show()

    def on_draw(self, event):
        self._count += 1
        self.fractal['time'] = time.time() - self._starttime
        self.fractal.draw()

        user_tracker_frame = self.user_tracker.read_frame()

        for user in user_tracker_frame.users:
            if user.is_new():
                self.user_tracker.start_skeleton_tracking(user.id)

            if user.is_lost():
                self.user_tracker.stop_skeleton_tracking(user.id)

            if self._count % 30 == 0:
                print "%s: new: %s, visible: %s, lost: %s, skeleton state: %s" % (user.id, user.is_new(), user.is_visible(), user.is_lost(), user.skeleton.state)

            if user.skeleton.state == _nite2.NiteSkeletonState.NITE_SKELETON_TRACKED:
                inputs = self.skeleton_input.inputs(user)
                print inputs
                self.fractal.adjust(inputs)

        # self.skeleton_bones.draw(user_tracker_frame)

    def apply_zoom(self):
        width, height = self.physical_size
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
    width = 400
    height = 400
    set_log_level('INFO')
    gloo.gl.use_gl('gl2 debug')

    canvas = MainCanvas(size=(width, height), keys='interactive', always_on_top=True)
    app.run()
