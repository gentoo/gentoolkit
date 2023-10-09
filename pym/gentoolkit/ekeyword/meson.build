
ekeyword_py = configure_file(
    input : 'ekeyword.py',
    output : 'ekeyword.py',
    configuration : conf_data
)

py.install_sources(
    [
        '__init__.py',
        ekeyword_py,
        'test_ekeyword.py',
    ],
    subdir : 'gentoolkit/ekeyword'
)

install_data(
    [
        'Makefile',
        'README',
        'pytest.ini',
    ],
    install_dir : py.get_install_dir() / 'gentoolkit' / 'ekeyword'
)

subdir('tests')
