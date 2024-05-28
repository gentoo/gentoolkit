TESTS = \
	single-KEYWORDS-conflict \
	multiple-KEYWORDS-conflict \
	conflict-near-KEYWORDS \
	non-KEYWORDS-conflict \
	$(NULL)

.PHONY: $(TESTS)

all: $(TESTS)

GENTOO-is-set:
	@if [ -z "$(GENTOO)" ]; then \
		echo GENTOO must be set to the path to gentoo.git; \
		exit 1; \
	fi

single-KEYWORDS-conflict: GENTOO-is-set
	mkdir -p $@
	git -C "$(GENTOO)" show 27aaf96d86ce53c80c967130a31cf0bec5a07c27:x11-apps/xconsole/xconsole-1.1.0.ebuild > $@/common-ancestor.ebuild
	sed -e 's/~arm ~arm64/arm ~arm64/' $@/common-ancestor.ebuild > $@/A.ebuild
	sed -e 's/~arm ~arm64/~arm arm64/' $@/common-ancestor.ebuild > $@/B.ebuild
	sed -e 's/~arm ~arm64/arm arm64/'  $@/common-ancestor.ebuild > $@/expected.ebuild

multiple-KEYWORDS-conflict: GENTOO-is-set
	mkdir -p $@
	git -C "$(GENTOO)" show 27aaf96d86ce53c80c967130a31cf0bec5a07c27:x11-apps/xconsole/xconsole-1.1.0.ebuild > $@/common-ancestor.ebuild
	sed -e 's/~arm64/arm64/' -e 's/~ppc64/ppc64/' $@/common-ancestor.ebuild > $@/A.ebuild
	sed -e 's/~amd64/amd64/' -e 's/~sparc/sparc/' $@/common-ancestor.ebuild > $@/B.ebuild
	sed -e 's/~arm64/arm64/' -e 's/~ppc64/ppc64/' -e 's/~amd64/amd64/' -e 's/~sparc/sparc/' $@/common-ancestor.ebuild > $@/expected.ebuild

conflict-near-KEYWORDS: GENTOO-is-set
	mkdir -p $@
	git -C "$(GENTOO)" show 128496a4717fb4085ea09066b92f53ae47e0341a:sys-fs/squashfs-tools-ng/squashfs-tools-ng-1.3.0.ebuild > $@/common-ancestor.ebuild
	git -C "$(GENTOO)" show 2c5cd6c4e004dc5037761c4a7a64fe956cac4bc4:sys-fs/squashfs-tools-ng/squashfs-tools-ng-1.3.0.ebuild > $@/A.ebuild
	git -C "$(GENTOO)" show 84e655a1f462a58154b701b9b8077ebf3071e82f:sys-fs/squashfs-tools-ng/squashfs-tools-ng-1.3.0.ebuild > $@/B.ebuild
	git -C "$(GENTOO)" show 7579afbd4aa1f2356b8de3c2870df2c49ab68d5f:sys-fs/squashfs-tools-ng/squashfs-tools-ng-1.3.0.ebuild > $@/expected.ebuild

non-KEYWORDS-conflict: GENTOO-is-set
	mkdir -p $@
	git -C "$(GENTOO)" show f1689f39c7bc6245f7f4fc8083d41bc82f4621d9:media-gfx/eog-plugins/eog-plugins-44.0-r2.ebuild > $@/common-ancestor.ebuild
	sed -e 's/{9..11}/{9..12}/'  $@/common-ancestor.ebuild > $@/A.ebuild
	sed -e 's/{9..11}/{10..11}/' $@/common-ancestor.ebuild > $@/B.ebuild
	# No expected.ebuild
