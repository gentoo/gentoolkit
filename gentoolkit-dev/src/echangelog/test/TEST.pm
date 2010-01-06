# We just return a static/predefined date because we're working with
# static md5 checksums.

package TEST;

use strict;
use warnings;

BEGIN {
	use Exporter();
	our ($VERSION, @ISA, @EXPORT, @EXPORT_OK, %EXPORT_TAGS);
	
	$VERSION     = 1.00;

	@ISA         = qw(Exporter);
	@EXPORT      = qw(&strftime);
	%EXPORT_TAGS = ( );
	@EXPORT_OK   = qw();
}
our @EXPORT_OK;

sub strftime {
	return "01 Jan 2009";
}

1;
