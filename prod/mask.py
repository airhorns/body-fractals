from vispy import gloo
import numpy as np
from utils import read_shader


class MaskProgram(gloo.Program):

    def __init__(self, fg=(1,1,1,0), bg=(0,0,0,1)):
        super(MaskProgram, self).__init__(read_shader('mask.vert'), read_shader('mask.frag'))

        self["tipColorSelector"] = 0

        self["position"] = [(-1, -1), (-1, 1), (1, 1),
                            (-1, -1), (1, 1), (1, -1)]

        self["foregroundColor"] = fg
        self["backgroundColor"] = bg
        self["triangleA"] = (0.00, 1.0)
        self["triangleB"] = (1.0, 1.0)
        self["triangleC"] = (0.51, 0.00)
