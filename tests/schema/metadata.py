from queenbee.schema.metadata import MetaData

single_author = {
    'description': 'test metadata',
    'author': {
        'name': 'John Dao',
        'email': 'jd@example.com'
    }
}

multi_authors = {
    'description': 'test metadata',
    'author': [
        {'name': 'John Smith', 'email': 'jos@example.com'},
        {'name': 'Jane Smith', 'email': 'jas@example.com'},
    ]
}


def test_load_single_author():
    MetaData.parse_obj(single_author)


def test_load_multi_authors():
    MetaData.parse_obj(multi_authors)
