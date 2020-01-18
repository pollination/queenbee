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
