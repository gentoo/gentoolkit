
merge_driver_ekeyword_py = configure_file(
    input : 'merge_driver_ekeyword.py',
    output : 'merge_driver_ekeyword.py',
    configuration : conf_data
)

py.install_sources(
    [
        '__init__.py',
        merge_driver_ekeyword_py,
        'test_merge_driver_ekeyword.py',
    ],
    subdir : 'gentoolkit/merge_driver_ekeyword'
)

install_data(
    [
        'pytest.ini',
    ],
    install_dir : py.get_install_dir() / 'gentoolkit' / 'merge_driver_ekeyword'
)

subdir('tests')
