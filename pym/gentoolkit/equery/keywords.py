#	vim:fileencoding=utf-8
# Copyright 2010 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

import sys
from gentoolkit.eshowkw import main as emain

# we have equery as first argument instead of the scriptname
# so we will just ommit it
emain(sys.argv)
