#!/usr/bin/python
# Copyright 1999-2005 Gentoo Foundation
# $Header$

# Temporary script to find package versions and slot for revdep-rebuild

import sys

sys.path.insert(0, "/usr/lib/gentoolkit/pym")
import gentoolkit

for pkgname in sys.argv[1:]:
	matches = gentoolkit.find_packages(pkgname)
	for pkg in matches:
		(cat, name, ver, rev) = gentoolkit.split_package_name(pkg.get_cpv())
		slot = pkg.get_env_var("SLOT")
		if rev == "r0":
			fullversion = ver
		else:
			fullversion = ver + "-" + rev
		
		print name + " " + fullversion + " (" + slot + ")"
