man_pages_out = []
man_pages_in = [
    'ebump.1',
    'eclean.1',
    'enalyze.1',
    'epkginfo.1',
    'equery.1',
    'eread.1',
    'eshowkw.1',
    'euse.1',
    'imlate.1',
    'revdep-rebuild.1',
]

foreach man_page : man_pages_in
    man_pages_out += configure_file(
        input : man_page,
        output : man_page,
        configuration : conf_data
    )
endforeach

install_man(man_pages_out)
