project(
    'gentoolkit',
    'c',
    version : '0.6.5',
    license : 'GPL-2.0-or-later',
    meson_version : '>=0.64.0'
)

py_mod = import('python')
py = py_mod.find_installation(pure : true)

system_wide = get_option('system-wide')

eprefix = get_option('eprefix')
prefixdir = get_option('prefix')
datadir = get_option('datadir')
docdir = get_option('docdir')

sysconfdir = system_wide ? get_option('sysconfdir') \
                         : datadir / 'etc'

if docdir == ''
    docdir = system_wide ? datadir / 'doc' / 'gentoolkit' \
                         : datadir / 'share' / 'gentoolkit' / 'doc'
endif

conf_data = configuration_data({
    'VERSION' : meson.project_version()
})

if system_wide
    conf_data.set('INSTALL_TYPE', 'SYSTEM')
    conf_data.set('EPREFIX', eprefix)
else
    conf_data.set('INSTALL_TYPE', 'MODULE')
    conf_data.set('EPREFIX', '')
endif

subdir('bin')
subdir('pym')

test(
    'python-unittest',
    py,
    args : ['-m', 'unittest', 'discover', meson.current_source_dir() / 'pym'],
    timeout : 0
)

if get_option('code-only')
    subdir_done()
endif

subdir('data')

install_data(
    [
        'NEWS',
    ],
    install_dir : docdir
)

if not system_wide
    subdir_done()
endif

subdir('man')
