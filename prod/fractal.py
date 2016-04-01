from vispy import gloo
import numpy as np
from utils import normalize, read_shader


class FractalProgram(gloo.Program):

    def __init__(self, definition):
        super(FractalProgram, self).__init__(read_shader('fractal.vert'), read_shader('fractal.frag'))

        self.definition = definition

        # Fill screen with single quad, fragment shader does all the real work
        self["position"] = [(-1, -1), (-1, 1), (1, 1),
                            (-1, -1), (1, 1), (1, -1)]

        self['time'] = 0

        self['cameraPos'] = (0.0, 3.0, -6.0)
        self['cameraLookat'] = (0.0, 0.0, 0.0)
        self['lightDir'] = normalize(np.array((1, 1, -1.5)))  # needs to be normalized
        self['diffuse'] = (1, 1, 1)
        self['ambientFactor'] = 0.45
        self['resolution'] = [10, 10]
        self['modelScale'] = 1
        self['distanceEstimatorFunction'] = self.definition['distance_estimator']

        for param, param_description in self.definition['params'].iteritems():
            self[param] = param_description['initial']

    def adjust(self, adjustments):
        for key, value in adjustments.iteritems():
            self[key] = self.definition['params'][key]['min'] + self.definition['params'][key]['delta'] * value

    def _initial_definition_value(value):
        if isinstance(value, dict):
            return value.get('initial', value['min'])
        else:
            return value
