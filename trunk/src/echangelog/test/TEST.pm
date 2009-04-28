#
#===============================================================================
#
#         FILE:  POSIX.pm
#
#  DESCRIPTION:  
#
#        FILES:  ---
#         BUGS:  ---
#        NOTES:  ---
#       AUTHOR:  YOUR NAME (), 
#      COMPANY:  
#      VERSION:  1.0
#      CREATED:  04/28/2009 01:24:13 PM
#     REVISION:  ---
#===============================================================================

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
