
imlate_py = configure_file(
    input : 'imlate.py',
    output : 'imlate.py',
    configuration : conf_data
)

py.install_sources(
    [
        '__init__.py',
        imlate_py,
    ],
    subdir : 'gentoolkit/imlate'
)
