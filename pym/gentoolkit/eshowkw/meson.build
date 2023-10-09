
__init__py = configure_file(
    input : '__init__.py',
    output : '__init__.py',
    configuration : conf_data
)

py.install_sources(
    [
        __init__py,
        'display_pretty.py',
        'keywords_content.py',
        'keywords_header.py'
    ],
    subdir : 'gentoolkit/eshowkw'
)
