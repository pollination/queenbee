from queenbee.schema.operator import Operator, LocalRequirements
import yaml


def test_load_operator():
    fp = './tests/assets/operator.yaml'
    operator = Operator.from_file(fp)

    assert operator.name == 'honeybee-radiance'
    
    # check image
    image = operator.image
    image == 'ladybugtools/honeybee-radiance-workflow:latest'
    
    # more checks is not really helpful as successful load to Pydantic object means
    # the object has been loaded correctly.


def test_create_operator():
    operator_dict = {
        'name': 'honeybee-radiance',
        'image': 'ladybugtools/honeybee-radiance-workflow:latest',
        'local': {
            'app': [
                {
                    'name': 'radiance',
                    'version': '>=5.2',
                    'command': 'rtrace -version',
                    'pattern': "r'\\d+\\.\\d+'"
                }
            ],
        'pip': [
            {
                'name': 'lbt-honeybee',
                'version': '>=0.4.3'
            },
            {
                'name': 'honeybee-radiance-workflow'
            }],
        'language': [
            {
                'name': 'python',
                'version': '>=3.6'
            }],
        'platform': [
            'Windows',
            'Mac'
            ]
        }
    }

    operator = Operator.parse_obj(operator_dict)

    operator_file = './tests/assets/temp/operator.yaml'
    operator.to_yaml(operator_file)

    # parse the yaml file and compare the two
    with open(operator_file) as inf:
        obj = yaml.safe_load(inf.read())

    assert obj == operator.to_dict()

