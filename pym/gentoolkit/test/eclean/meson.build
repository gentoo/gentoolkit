py.install_sources(
    [
        '__init__.py',
        'creator.py',
        'distsupport.py',
        'test_clean.py',
        'test_search.py',
    ],
    subdir : 'gentoolkit/test/eclean'
)

install_data(
    [
        'Packages',
        'distfiles.exclude',
        'testdistfiles.tar.gz',
    ],
    preserve_path: true,
    install_dir : py.get_install_dir() / 'gentoolkit' / 'test' / 'eclean'
)
