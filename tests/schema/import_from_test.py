from queenbee.schema.parser import parse_file


def test_parser():
    """Test recursive import of data from files."""
    fp = './tests/assets/import_from/base.yaml'
    data = parse_file(fp)
    assert 'operators' in data
    assert len(data['operators']) == 1
    # check operator itself
    operator = data['operators'][0]
    assert operator['name'] == 'radiance-operator'
    assert 'image' in operator
    assert operator['image'] == 'ladybugtools/radiance:5.2'
    assert 'local' in operator
    assert 'app' in operator['local']
    # check if app is loaded correctly
    app = operator['local']['app'][0]
    assert app['name'] == 'radiance'
    assert app['version'] == ">=5.2"
    assert app['command'] == 'rtrace -version'
    assert app['pattern'] == "r'\\d+\\.\\d+'"
