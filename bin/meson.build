py_bins = [
    'eclean',
    'eclean-dist',
    'eclean-pkg',
    'ekeyword',
    'enalyze',
    'epkginfo',
    'equery',
    'eread',
    'eshowkw',
    'imlate',
    'merge-driver-ekeyword',
    'revdep-rebuild',
]

ebump = configure_file(
    input : 'ebump',
    output : 'ebump',
    configuration : conf_data
)

euse = configure_file(
    input : 'euse',
    output : 'euse',
    configuration : conf_data
)

revdep_rebuild_sh = configure_file(
    input : 'revdep-rebuild.sh',
    output : 'revdep-rebuild.sh',
    configuration : conf_data
)

other_bins = [
    ebump,
    euse,
    revdep_rebuild_sh,
]

# It might seem sensible to use py.install_sources() to install the Python
# scripts, but it's really just a wrapper around install_data that forces the
# install_dir. Meson 1.2.0 and later also optimize to bytecode, but Gentoo does
# this in the ebuild.

install_data(
    py_bins,
    install_dir : get_option('bindir'),
    install_mode : 'rwxr-xr-x',
)

install_data(
    other_bins,
    install_dir : get_option('bindir'),
    install_mode : 'rwxr-xr-x',
)
