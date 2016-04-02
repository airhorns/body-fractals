from vispy import gloo
import numpy as np
from utils import normalize, read_shader
import random


class FractalProgram(gloo.Program):

    def __init__(self, definition):
        super(FractalProgram, self).__init__(read_shader('fractal.vert'), read_shader('fractal.frag'))

        self.definition = definition

        # Fill screen with single quad, fragment shader does all the real work
        self["position"] = [(-1, -1), (-1, 1), (1, 1),
                            (-1, -1), (1, 1), (1, -1)]

        self['time'] = 0

        self['cameraPos'] = (0.0, 9.0, -12.0)
        self['cameraLookat'] = (0.0, -3.0, 0.0)
        self['lightDir'] = normalize(np.array((1, 1, -1.5)))  # needs to be normalized
        self['diffuse'] = (1, 1, 1)
        self['ambientFactor'] = 0.45
        self['resolution'] = [10, 10]
        self['distanceEstimatorFunction'] = self.definition['distance_estimator']
        self['trapFunction'] = random.choice(self.definition['trap_functions'])

        for param, param_description in self.definition['params'].iteritems():
            self[param] = param_description['initial']

    def adjust(self, adjustments):
        for key, value in adjustments.iteritems():
            param = self.definition['params'][key]['min'] + self.definition['params'][key]['delta'] * value
            # print "Setting %s to %s, adjustment: %s, min: %s delta: %s" % (key, param, value, self.definition['params'][key]['min'], self.definition['params'][key]['delta'])
            self[key] = param

    def _initial_definition_value(value):
        if isinstance(value, dict):
            return value.get('initial', value['min'])
        else:
            return value
