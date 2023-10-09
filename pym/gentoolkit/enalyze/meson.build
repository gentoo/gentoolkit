
__init__py = configure_file(
    input : '__init__.py',
    output : '__init__.py',
    configuration : conf_data
)

py.install_sources(
    [
		__init__py,
		'analyze.py',
		'lib.py',
		'output.py',
		'rebuild.py',
    ],
    subdir : 'gentoolkit/enalyze'
)
