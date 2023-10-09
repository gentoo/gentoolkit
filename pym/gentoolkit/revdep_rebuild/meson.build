
__init__py = configure_file(
    input : '__init__.py',
    output : '__init__.py',
    configuration : conf_data
)

py.install_sources(
    [
        __init__py,
        'analyse.py',
        'assign.py',
        'cache.py',
        'collect.py',
        'rebuild.py',
        'runner.py',
        'settings.py',
        'stuff.py',
    ],
    subdir : 'gentoolkit/revdep_rebuild'
)
