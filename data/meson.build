install_data(
    [
        '99gentoolkit-env',
    ],
    install_dir : sysconfdir / 'env.d'
)

install_data(
    [
        'eclean/packages.exclude',
        'eclean/distfiles.exclude',
        'revdep-rebuild/99revdep-rebuild',
    ],
    install_dir: sysconfdir,
    preserve_path: true
)

if not system_wide
    subdir_done()
endif
