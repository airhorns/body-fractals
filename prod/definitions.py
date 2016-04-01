import yaml
import os.path

with open(os.path.join(os.path.dirname(__file__), 'fractal_definitions.yml'), 'r') as f:
    _definitions = yaml.load(f)

Definitions = {}

for name, input_definition in _definitions.iteritems():
    definition = {
        'name': name,
        'distance_estimator': input_definition['distance_estimator'],
        'params': {}
    }

    for param, param_description in input_definition['params'].iteritems():
        definition['params'][param] = {
            'min': param_description['min'] if isinstance(param_description, dict) else param_description,
            'max': param_description['max'] if isinstance(param_description, dict) else param_description,
            'initial': param_description.get('initial', param_description['min']) if isinstance(param_description, dict) else param_description
        }

        definition['params'][param]['delta'] = definition['params'][param]['max'] - definition['params'][param]['min']

    Definitions[name] = definition
