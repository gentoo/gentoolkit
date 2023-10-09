
cli_py = configure_file(
    input : 'cli.py',
    output : 'cli.py',
    configuration : conf_data
)

py.install_sources(
    [
        '__init__.py',
        'clean.py',
        cli_py,
        'exclude.py',
        'output.py',
        'search.py',
    ],
    subdir : 'gentoolkit/eclean'
)
