
__init__py = configure_file(
    input : '__init__.py',
    output : '__init__.py',
    configuration : conf_data
)

py.install_sources(
    [
        __init__py,
        'belongs.py',
        'check.py',
        'depends.py',
        'depgraph.py',
        'files.py',
        'has.py',
        'hasuse.py',
        'keywords.py',
        'list_.py',
        'meta.py',
        'size.py',
        'uses.py',
        'which.py',
    ],
    subdir : 'gentoolkit/equery'
)
