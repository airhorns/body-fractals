import numpy as np
import os.path


def joint_to_array(joint):
    return np.asarray((joint.position.x, joint.position.y, joint.position.z))


def normalize(v):
    norm = np.linalg.norm(v)
    if norm == 0:
        return v
    return v / norm


def read_shader(name):
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), name)) as f:
        return f.read()
