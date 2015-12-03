#!/usr/bin/perl
#
# FetchEvent
#
# Find the most current version at http://service.iris.edu/clients/
#
# Fetch event parameters from web services.  The default web service
# are from the IRIS DMC, other FDSN web services may be specified by
# setting the following environment variables:
#
# SERVICEBASE = the base URI of the service(s) to use (http://service.iris.edu/)
# EVENTWS = complete URI of service (http://service.iris.edu/fdsnws/event/1)
#
# Dependencies: This script should run without problems on Perl
# release 5.10 or newer, older versions of Perl might require the
# installation of the following modules (and their dependencies):
#   XML::SAX
#   Bundle::LWP (libwww-perl)
#
# Installation of the XML::SAX::ExpatXS module can significantly
# speed up the parsing of results returned as XML.
#
# The returned XML event information is parsed and printed to the
# console or a file in the following ways:
#
# The default "parsable" output includes fields separated by vertical
# bars (|) and follows this pattern:
#
# EventID|OriginTime|Latitude|Longitude|Depth/km|Author|Catalog|Contributor,ContribEventID|MagType,MagValue,MagAuthor|MagType,MagValue,MagAuthor|...|EventLocationName
#         OriginTime|Latitude|Longitude|Depth/km|Author|Catalog|Contributor,ContribEventID
#
# The event ID and the primary origin details are all contained on a single
# line along with all magnitude estimates associated with the event.
# Secondary origins, if requested, are listed below and indented to line up
# with the equivalient fields of the primary origin.
#
# The "alternate" output (the -altform option) follows this pattern:
# EVENT <event location name> eventid=<eventID>
#   ORIGIN <origintime>,<lat>,<lon>,<depth>,<author>,<catalog>,<contributor> originid=<originID>
#   ORIGIN <origintime>,<lat>,<lon>,<depth>,<author>,<catalog>,<contributor> originid=<originID>
#   MAGNITUDE <magtype>,<magvalue>,<author> magnitudeid=<magnitudeID>
#   MAGNITUDE <magtype>,<magvalue>,<author> magnitudeid=<magnitudeID>
#
# An EVENT can be followed by multiple ORIGIN lines if the --allorigins
# option is specified and the primary origin is listed first.  An
# EVENT may also be followed by one or more MAGNITUDE lines.
#
# ## Change history ##
#
# 2011.161:
#  - Initial version.
#
# 2011.270:
#  - Allow start and end times to be indenpendently specified.
#  - Reorganize lat, lon, depth and mag range options to compact form that
#     that matches other Fetch scripts.
#  - Add --radius option for selecting a circular region.
#  - Add --magtype option.
#
# 2011.272:
#  - Reorganize default output for easy reading and hopefully easy parsing.
#  - Add the --altform option (unadvertised).
#
# 2011.273:
#  - Fix magnitude selection.
#
# 2011.277:
#  - Remove debugging code.
#
# 2011.337:
#  - Print error message text from service on errors.
#  - Add undocumented -nobs option to prevent printing backspace characters in status.
#  - Remove "query" portion from base URLs, moving them to the service calls.
#  - Include local time in output of DONE line.
#
# 2012.045:
#  - Print "No data available" when return code is 204 in addition to 404.
#  - Support for start/end times specified up to microsecond resolution.
#
# 2012.206:
#  - Parse primary magnitude ID and sort it to front of the mag list
#  - Add -allorigins and -allmags to match new service parameters
#  - Deprecate secondary option: remove from usage message but leave in code
#  - Lower-case some previously CamelCase parameter names for consistency
#
# 2012.221
#  - Add limit argument that takes limit:offset (undocumented, for now)
#
# 2013.077
#  - Use the LWP::UserAgent method env_proxy() to check for and use connection
#  proxy information from environment variables (e.g. http_proxy).
#  - Add checking of environment variables that will override the web
#  service base path (i.e. host name).
#  - Change updated after to take full resolution date and time.
#
# 2013.119
#  - Fix parsing of event, origin & magnitude IDs to make them case insensitive,
#  recent changes in the service changed the case and broke the script.
#  - The event service now returns depths in meters, convert these meters to
#  kilometers to match the previous output and common convention.
#  - Fix positioning of number fields that have no decimal point and adjust widths
#  of fields for expected sizes.
#
# 2013.123
#  - Attempt to parse event, origin and magnitude IDs from patterns other than
#  the one used by the IRIS services.
#  - Check for no origins for an event and print appropriate message on output.
#
# 2013.154
#  - Change (unadvertised) option -eventurl to -eventws to match env. variable.
#
# 2013.162
#  - Parse and store complete publicID for event, origin and magnitude IDs.
#  Add a function to attempt to parse shorter IDs from full public IDs for
#  printing.  This makes the script compatible for services that do not follow
#  the IRIS publicID convention.
#
# 2013.176
#  - Fixed comparisons involving the full public IDs. This had hindered the
#  functionality of -allorigins and -allmags
#  --celso
#
# 2013.197
#  - Fix parsing of element values of "0".
#
# 2013.198
#  - Add test for minimum version of LWP (libwww) module of 5.806.
#
# 2013.316
#  - Allow latitude, longitude, depth, magnitude and geographic ranges
#  to be specified with the value of 0.  Same treatment for the undocumented
#  'limit' option.
#
# 2014.056
#  - Allow gzip'ed HTTP encoding for event data requests if support
#  exists on the local system.
#
# 2014.232
#  - Add "compressed from <size>" to diagnostic message when the server returns
#  gzip'ed content to differentiate the size transmitted versus the result.
#
# 2014.290
#  - Change help message to refer to 'NEIC PDE' intead of just PDE.
#
# 2014.310
#  - Add event ID parsing to include 'evid' token, needed for the ISC service.
#
# Author: Chad Trabant, IRIS Data Management Center

use strict;
use File::Basename;
use Getopt::Long;
use LWP 5.806; # Require minimum version
use LWP::UserAgent;
use HTTP::Status qw(status_message);
use HTTP::Date;
use Time::HiRes;

my $version = "2014.310";

my $scriptname = basename($0);

# Default web service base
my $servicebase = 'http://service.iris.edu';

# Check for environment variable overrides for servicebase
$servicebase = $ENV{'SERVICEBASE'} if ( exists $ENV{'SERVICEBASE'} );

# Web service for events
my $eventservice = "$servicebase/fdsnws/event/1";

# Check for environment variable override for timeseriesservice
$eventservice = $ENV{'EVENTWS'} if ( exists $ENV{'EVENTWS'} );

# HTTP UserAgent reported to web services
my $useragent = "$scriptname/$version Perl/$] " . new LWP::UserAgent->_agent;

my $usage        = undef;
my $verbose      = undef;
my $nobsprint    = undef;

my $starttime    = undef;
my $endtime      = undef;
my @latrange     = ();      # (minlat:maxlat)
my @lonrange     = ();      # (minlon:maxlon)
my @degrange     = ();      # (lat:lon:maxradius[:minradius])
my @deprange     = ();      # (mindepth:maxdepth)
my @magrange     = ();      # (minmag:maxmag)
my $magtype      = undef;
my $catalog      = undef;
my $contributor  = undef;
my $updatedafter = undef;
my $altform      = undef;
my @limitrange   = ();      # (limit:offset)
my $allorigins   = undef;
my $allmags      = undef;
my $orderbymag   = undef;

my $eventid      = undef;
my $originid     = undef;

my $appname      = undef;
my $auth         = undef;
my $outfile      = undef;
my $xmlfile      = undef;

my $eventxml     = undef;

# Event identification tokens for extracting minimal ID from publicID
my @eventidtokens = ("eventid","evid");

my $inflater     = undef;

# If Compress::Raw::Zlib is available configure inflater for RFC 1952 (gzip)
if ( eval("use Compress::Raw::Zlib; 1") ) {
  use Compress::Raw::Zlib;
  $inflater = new Compress::Raw::Zlib::Inflate( -WindowBits => WANT_GZIP,
                                                -ConsumeInput => 0 );
}

# Parse command line arguments
Getopt::Long::Configure ("bundling_override");
my $getoptsret = GetOptions ( 'help|usage|h'      => \$usage,
                              'verbose|v+'        => \$verbose,
                              'nobs'              => \$nobsprint,
			      'starttime|s=s'     => \$starttime,
			      'endtime|e=s'       => \$endtime,
			      'lat=s'             => \@latrange,
                              'lon=s'             => \@lonrange,
                              'radius=s'          => \@degrange,
			      'depth=s'           => \@deprange,
			      'mag=s'             => \@magrange,
			      'magtype=s'         => \$magtype,
                              'catalog|cat=s'     => \$catalog,
                              'contributor|con=s' => \$contributor,
			      'updatedafter|ua=s' => \$updatedafter,
                              'altform'           => \$altform,
			      'limit=s'           => \@limitrange,
                              'allorigins'        => \$allorigins,
                              'allmags'           => \$allmags,
			      'orderbymag'        => \$orderbymag,

			      'eventid|evid=s'    => \$eventid,
			      'originid|orid=s'   => \$originid,

			      'appname|A=s'       => \$appname,
			      'auth|a=s'          => \$auth,
			      'outfile|o=s'       => \$outfile,
			      'xmlfile|X=s'       => \$xmlfile,
			      'eventws=s'         => \$eventservice,
			    );

my $required =  ( defined $starttime || defined $endtime ||
                  scalar @latrange || scalar @lonrange  || scalar @degrange ||
		  scalar @deprange || scalar @magrange ||
                  defined $catalog || defined $contributor ||
                  defined $eventid || defined $originid );

if ( ! $getoptsret || $usage || ! $required ) {
  print "$scriptname: collect event information ($version)\n";
  print "http://service.iris.edu/clients/\n\n";
  print "Usage: $scriptname [options]\n\n";
  print " Options:\n";
  print " -v                More verbosity, may be specified multiple times (-vv, -vvv)\n";
  print "\n";
  print " -s starttime      Limit to origins after time (YYYY-MM-DD,HH:MM:SS.sss)\n";
  print " -e endtime        Limit to origins before time (YYYY-MM-DD,HH:MM:SS.sss)\n";
  print " --lat min:max     Specify a minimum and/or maximum latitude range\n";
  print " --lon min:max     Specify a minimum and/or maximum longitude range\n";
  print " --radius lat:lon:maxradius[:minradius]\n";
  print "                     Specify circular region with optional minimum radius\n";
  print " --depth min:max   Specify a minimum and/or maximum depth in kilometers\n";
  print " --mag min:max     Specify a minimum and/or maximum magnitude\n";
  print " --magtype type    Specify a magnitude type for magnitude range limits\n";
  print " --cat name        Limit to origins from specific catalog (e.g. ISC, 'NEIC PDE', GCMT)\n";
  print " --con name        Limit to origins from specific contributor (e.g. ISC, NEIC)\n";
  print " --ua date         Limit to origins updated after date (YYYY-MM-DD,HH:MM:SS)\n";
  print "\n";
#  print " --altform         Print output in an alternate form, default is more parsable\n";
#  print " --limit max:off   Limit to max events, optionally starting at offset\n";
  print " --allorigins      Return all origins, default is only primary origin per event\n";
  print " --allmags         Return all magnitudes, default is only primary magnitude per event\n";
  print " --orderbymag      Order results by magnitude instead of time\n";
  print "\n";
  print " --evid id         Select a specific event by DMC event ID\n";
  print " --orid id         Select a specific event by DMC origin ID\n";
  print "\n";
  print " -X xmlfile        Write raw returned XML to xmlfile\n";
  print " -A appname        Application/version string for identification\n";
  print "\n";
  print " -o outfile        Write event information to specified file, default: console\n";
  print "\n";
  exit 1;
}

# Print script name and local time string
if ( $verbose ) {
  my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime(time);
  printf STDERR "$scriptname ($version) at %4d-%02d-%02d %02d:%02d:%02d\n", $year+1900, $mon+1, $mday, $hour, $min, $sec;
}

# Normalize time strings
if ( $starttime ) {
  my ($year,$month,$mday,$hour,$min,$sec,$subsec) = split (/[-:,.\s\/T]/, $starttime);
  $starttime = sprintf ("%04d-%02d-%02dT%02d:%02d:%02d", $year, $month, $mday, $hour, $min, $sec);
  $starttime .= ".$subsec" if ( $subsec );
}

if ( $endtime ) {
  my ($year,$month,$mday,$hour,$min,$sec,$subsec) = split (/[-:,.\s\/T]/, $endtime);
  $endtime = sprintf ("%04d-%02d-%02dT%02d:%02d:%02d", $year, $month, $mday, $hour, $min, $sec);
  $endtime .= ".$subsec" if ( $subsec );
}

if ( $updatedafter ) {
  my ($year,$month,$mday,$hour,$min,$sec,$subsec) = split (/[-:,.\s\/T]/, $updatedafter);
  $updatedafter = sprintf ("%04d-%02d-%02dT%02d:%02d:%02d", $year, $month, $mday, $hour, $min, $sec);
  $updatedafter .= ".$subsec" if ( $subsec );
}

# Validate and prepare lat, lon and radius input
if ( scalar @latrange ) {
  @latrange = split (/:/, $latrange[0]);

  if ( defined $latrange[0] && ($latrange[0] < -90.0 || $latrange[0] > 90.0) ) {
    die "Minimum latitude out of range: $latrange[0]\n";
  }
  if ( defined $latrange[1] && ($latrange[1] < -90.0 || $latrange[1] > 90.0) ) {
    die "Maximum latitude out of range: $latrange[1]\n";
  }
}
if ( scalar @lonrange ) {
  @lonrange = split (/\:/, $lonrange[0]);

  if ( defined $lonrange[0] && ($lonrange[0] < -180.0 || $lonrange[0] > 180.0) ) {
    die "Minimum longitude out of range: $lonrange[0]\n";
  }
  if ( defined $lonrange[1] && ($lonrange[1] < -180.0 || $lonrange[1] > 180.0) ) {
    die "Maximum longitude out of range: $lonrange[1]\n";
  }
}
if ( scalar @degrange ) {
  @degrange = split (/\:/, $degrange[0]);

  if ( scalar @degrange < 3 || scalar @degrange > 4 ) {
    die "Unrecognized radius specification: @degrange\n";
  }
  if ( defined $degrange[0] && ($degrange[0] < -90.0 || $degrange[0] > 90.0) ) {
    die "Radius latitude out of range: $degrange[0]\n";
  }
  if ( defined $degrange[1] && ($degrange[1] < -180.0 || $degrange[1] > 180.0) ) {
    die "Radius longitude out of range: $degrange[1]\n";
  }
}
if ( scalar @deprange ) {
  @deprange = split (/\:/, $deprange[0]);

  if ( defined $deprange[0] && ($deprange[0] < -7000 || $deprange[0] > 7000) ) {
    die "Minimum depth out of range: $deprange[0]\n";
  }
  if ( defined $deprange[1] && ($deprange[1] < -7000 || $deprange[1] > 7000) ) {
    die "Maximum depth out of range: $deprange[1]\n";
  }
}
if ( scalar @magrange ) {
  @magrange = split (/\:/, $magrange[0]);

  if ( defined $magrange[0] && ($magrange[0] < -50 || $magrange[0] > 15) ) {
    die "Minimum magnitude out of range: $magrange[0]\n";
  }
  if ( defined $magrange[1] && ($magrange[1] < -50 || $magrange[1] > 15) ) {
    die "Maximum magnitude out of range: $magrange[1]\n";
  }
}
if ( scalar @limitrange ) {
  @limitrange = split (/\:/, $limitrange[0]);

  if ( defined $limitrange[0] && ($limitrange[0] < 1) ) {
    die "Event limit out of range: $limitrange[0]\n";
  }
  if ( defined $limitrange[1] && ($limitrange[1] < 0) ) {
    die "Event count offset out of range: $limitrange[1]\n";
  }
}

# Report data selection criteria
if ( $verbose > 2 ) {
  print STDERR "Latitude range: $latrange[0] : $latrange[1]\n" if ( scalar @latrange );
  print STDERR "Longitude range: $lonrange[0] : $lonrange[1]\n" if ( scalar @lonrange );
  print STDERR "Radius range: $degrange[0] : $degrange[1] : $degrange[2] : $degrange[3]\n" if ( scalar @degrange );
  print STDERR "Depth range: $deprange[0] : $deprange[1]\n" if ( scalar @deprange );
  print STDERR "Magnitude range: $magrange[0] : $magrange[1]\n" if ( scalar @magrange );
  print STDERR "Magnitude range: $limitrange[0] : $limitrange[1]\n" if ( scalar @limitrange );
}

# Containers to hold event, origin and magnitude details
my @eventids = ();
my %eventname = ();
my %eventprime = ();
my %eventprimemag = ();
my %origins = ();
my %mags = ();

my $datasize;

# Fetch events from the web service
&FetchEvents();

my $totalevents = 0;
my $totalorigins = 0;
my $totalmags = 0;

# Write to either specified output file or stdout
my $eventfile = ( $outfile ) ? $outfile : "-";

if ( scalar @eventids <= 0 ) {
  printf STDERR "No events selected\n", scalar @eventids;
}

open (EVENT, ">$eventfile") || die "Cannot open event file '$eventfile': $!\n";

# Write event information to stdout/console or a file if specified
if ( ! defined $altform ) {
  # Parsable lines, one event line with primary origin, fields delimited with '|':
  # EventID|OriginTime|Latitude|Longitude|Depth/km|Author|Catalog|Contributor,ContribEventID|MagType,MagValue,MagAuthor|MagType,MagValue,MagAuthor|...|EventLocationName
  #         OriginTime|Latitude|Longitude|Depth/km|Author|Catalog|Contributor,ContribEventID

  foreach my $eventid ( @eventids ) {
    $totalevents++;

    # Print event ID
    my $printeventid = &ExtractID($eventid, @eventidtokens);
    printf EVENT "%-8s", $printeventid;

    # Generate list of origin IDs with primary origin first and others sorted on ascending time
    my @originids = (exists $origins{$eventid}{$eventprime{$eventid}}) ? ($eventprime{$eventid}) : ();
    foreach my $originid ( sort { ${$origins{$eventid}{$b}}[0] cmp ${$origins{$eventid}{$a}}[0] } keys %{$origins{$eventid}} ) {
      push (@originids, $originid) if ( $originid ne $eventprime{$eventid} );
    }
    $totalorigins += scalar @originids;

    if ( scalar @originids <= 0 ) {
      print EVENT " -- NO ORIGINS\n";
      next;
    }

    # Print first/primary origin
    my ($time,$lat,$lon,$depth,$author,$catalog,$contributor,$contributoreventid) = @{$origins{$eventid}{$originids[0]}};
    printf (EVENT "|%-24s|%-8s|%-9s|%-6s|%s|%s|%s%s",
	    $time,&decimalposition($lat,4),&decimalposition($lon,5),&decimalposition($depth,5),
	    $author,$catalog,$contributor,($contributoreventid)?",$contributoreventid":"");

    # Generate list of magnitude IDs with primary magnitude first and others sorted on ascending value
    my @magids = (exists $mags{$eventid}{$eventprimemag{$eventid}}) ? ($eventprimemag{$eventid}) : ();
    foreach my $magid ( sort { ${$mags{$eventid}{$b}}[1] cmp ${$mags{$eventid}{$a}}[1] } keys %{$mags{$eventid}} ) {
      push (@magids, $magid) if ( $magid ne $eventprimemag{$eventid} );
    }
    $totalmags += scalar @magids;

    # Print magnitudes
    foreach my $magid ( @magids ) {
      my $magstr = join (',', @{$mags{$eventid}{$magid}});
      $magstr =~ s/,*$//;  # Cut trailing commas
      print EVENT "|$magstr";
    }

    # Print event name and newline
    printf EVENT "|$eventname{$eventid}\n";

    # Print secondary origin lines
    foreach my $originid ( @originids[1..$#originids] ) {
      my ($time,$lat,$lon,$depth,$author,$catalog,$contributor,$contributoreventid) = @{$origins{$eventid}{$originid}};
      printf (EVENT "         %-24s|%-8s|%-9s|%-6s|%s|%s|%s%s\n",
	      $time,&decimalposition($lat,4),&decimalposition($lon,5),&decimalposition($depth,5),
	      $author,$catalog,$contributor,($contributoreventid)?",$contributoreventid":"");
    }
  }
}
else {
  # Alternate lines, primary origin is first:
  # EVENT <event location name> eventid=<eventid>
  #   ORIGIN <origintime>,<lat>,<lon>,<depthkm>,<author>,<catalog>,<contributor> originid=<originid>
  #   ORIGIN <origintime>,<lat>,<lon>,<depthkm>,<author>,<catalog>,<contributor> originid=<originid>
  #   MAGNITUDE <magtype>,<magvalue>,<author> magnitudeid=<magnitudeid>
  #   MAGNITUDE <magtype>,<magvalue>,<author> magnitudeid=<magnitudeid>

  foreach my $eventid ( @eventids ) {
    $totalevents++;

    # Print event ID
    my $printeventid = &ExtractID($eventid, @eventidtokens);
    printf EVENT "EVENT $eventname{$eventid} eventid=$printeventid\n";

    # Generate list of origin IDs with primary origin firstand others sorted on ascending time
    my @originids = (exists $origins{$eventid}{$eventprime{$eventid}}) ? ($eventprime{$eventid}) : ();
    foreach my $originid ( sort { ${$origins{$eventid}{$b}}[0] cmp ${$origins{$eventid}{$a}}[0] } keys %{$origins{$eventid}} ) {
      push (@originids, $originid) if ( $originid ne $eventprime{$eventid} );
    }

    # Generate list of magnitude IDs with primary magnitude first and others sorted on ascending value
    my @magids = (exists $mags{$eventid}{$eventprimemag{$eventid}}) ? ($eventprimemag{$eventid}) : ();
    foreach my $magid ( sort { ${$mags{$eventid}{$b}}[1] cmp ${$mags{$eventid}{$a}}[1] } keys %{$mags{$eventid}} ) {
      push (@magids, $magid) if ( $magid ne $eventprimemag{$eventid} );
    }

    # Print origin lines
    foreach my $originid ( @originids ) {
      $totalorigins++;
      my ($time,$lat,$lon,$depth,$author,$catalog,$contributor,$contributoreventid) = @{$origins{$eventid}{$originid}};

      printf EVENT "  ORIGIN %s,%s,%s,%s,%s,%s,%s originid=$originid\n",
	$time,$lat,$lon,$depth,$author,$catalog,$contributor;
    }

    # Print magnitude lines
    foreach my $magid ( @magids ) {
      $totalmags++;
      print EVENT "  MAGNITUDE " . join (',', @{$mags{$eventid}{$magid}}) . " magnitudeid=$magid\n";
    }
  }
}

close EVENT;

if ( $verbose && scalar @eventids > 0 ) {
  printf STDERR "Selected %d events (%d origins, %d magnitudes)\n",
    $totalevents, $totalorigins, $totalmags;
}

my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime(time);
printf STDERR "DONE at %4d-%02d-%02d %02d:%02d:%02d\n", $year+1900, $mon+1, $mday, $hour, $min, $sec;
## End of main


######################################################################
# decimalposition:
#
# Return a string left-padded with spaces such that the decimal is at
# the specified position in the string.
######################################################################
sub decimalposition { # decimalposition (value, position)
  my ($value, $position) = @_;

  my $idx = index ($value, '.');
  my $len = length $value;

  $idx = $len if ( $idx < 0 );

  return sprintf "%*s", ($position - $idx - 1 + $len), $value;

}  # End of decimalposition()


######################################################################
# ExtractID:
#
# Attempt to extract an ID from a full publicID value.  The smaller ID
# value is generally better for printing and is normally usable as the
# value of the eventid service parameter.
#
# An IRIS example for <event publicID= >:
# smi:service.iris.edu/fdsnws/event/1/query?eventid=3954686
#
# An NEIC example for <event publicID= >:
# quakeml://comcat.cr.usgs.gov/fdsnws/event/1/query?eventid=pde20100115001825990_25&amp;format=quakeml
#
# A SeisComP3 example for <event publicID= >:
# smi:scs/0.6/gfz2013hykj
#
# An ISC example for <event publicID= >:
# smi:ISC/evid=15925507
#
######################################################################
sub ExtractID { # ExtractID (publicid, token1[, token2, token3, ..])
  my $publicid = shift;
  my @tokens = @_;

  my $id = undef;
  my $token = undef;

  foreach my $tok ( @tokens ) {
    if ( $publicid =~ /.*${tok}\=[0-9a-zA-Z]+/i ) { # Check for token=ID
      $token = $tok;
      last;
    }
  }
  if ( $token ) {
    ($id) = $publicid =~ /.*${token}\=([0-9a-zA-Z]+)/i;
  }
  elsif ( $publicid =~ /.*\/[^\/:]+$/ ) { # Check for ID following last slash
    ($id) = $publicid =~ /.*\/([^\/:]+)$/;
  }
  else { # Fall back to simply using the full public ID
    $id = $publicid;
  }

  return $id;
}  # End of ExtractID()


######################################################################
# FetchEvents:
#
# Collect event information for selected data set.
#
# Resulting information is placed in the following global structures:
#   @eventids - an array containing the returned event IDs in order
#   %eventname
#   %eventprime
#   %eventprimemag
#   %origins
#   %mags
#
######################################################################
sub FetchEvents {

  # Create HTTP user agent
  my $ua = RequestAgent->new();
  $ua->env_proxy;

  # Create web service URI
  my $uri = "${eventservice}/query?";
  $uri .= "orderby="; $uri .= ($orderbymag) ? "magnitude" : "time";
  $uri .= "&starttime=$starttime" if ( $starttime );
  $uri .= "&endtime=$endtime" if ( $endtime );
  if ( scalar @latrange ) {
    $uri .= "&minlat=$latrange[0]" if ( defined $latrange[0] );
    $uri .= "&maxlat=$latrange[1]" if ( defined $latrange[1] );
  }
  if ( scalar @lonrange ) {
    $uri .= "&minlon=$lonrange[0]" if ( defined $lonrange[0] );
    $uri .= "&maxlon=$lonrange[1]" if ( defined $lonrange[1] );
  }
  if ( scalar @degrange ) {
    $uri .= "&lat=$degrange[0]" if ( defined $degrange[0] );
    $uri .= "&lon=$degrange[1]" if ( defined $degrange[1] );
    $uri .= "&maxradius=$degrange[2]" if ( defined $degrange[2] );
    $uri .= "&minradius=$degrange[3]" if ( defined $degrange[3] );
  }
  if ( scalar @deprange ) {
    $uri .= "&mindepth=$deprange[0]" if ( defined $deprange[0] );
    $uri .= "&maxdepth=$deprange[1]" if ( defined $deprange[1] );
  }
  if ( scalar @magrange ) {
    $uri .= "&minmag=$magrange[0]" if ( defined $magrange[0] );
    $uri .= "&maxmag=$magrange[1]" if ( defined $magrange[1] );
  }
  $uri .= "&magtype=$magtype" if ( $magtype );
  $uri .= "&catalog=$catalog" if ( $catalog );
  $uri .= "&contributor=$contributor" if ( $contributor );
  $uri .= "&updatedafter=$updatedafter" if ( $updatedafter );
  if ( scalar @limitrange ) {
    $uri .= "&limit=$limitrange[0]" if ( defined $limitrange[0] );
    $uri .= "&offset=$limitrange[1]" if ( defined $limitrange[1] );
  }
  $uri .= "&includeallorigins=true" if ( $allorigins );
  $uri .= "&includeallmagnitudes=true" if ( $allmags );

  $uri .= "&eventid=$eventid" if ( $eventid );
  $uri .= "&originid=$originid" if ( $originid );

  my $ftime = Time::HiRes::time;

  print STDERR "Event URI: '$uri'\n" if ( $verbose > 1 );

  print STDERR "Fetching event information :: " if ( $verbose );

  $datasize = 0;
  $eventxml = "";

  # Fetch event information from web service using callback routine
  my $response = ( $inflater ) ?
    $ua->get($uri, 'Accept-Encoding' => 'gzip', ':content_cb' => \&EDCallBack ) :
    $ua->get($uri, ':content_cb' => \&EDCallBack );

  $inflater->inflateReset if ( $inflater );

  if ( $response->code == 404 || $response->code == 204 ) {
    print (STDERR "No data available\n") if ( $verbose );
    return;
  }
  elsif ( ! $response->is_success() ) {
    print (STDERR "Error fetching data: "
	   . $response->code . " :: " . status_message($response->code) . "\n");
    print STDERR "------\n" . $response->decoded_content . "\n------\n";
    print STDERR "  URI: '$uri'\n" if ( $verbose > 1 );
  }
  else {
    printf (STDERR "%s\n", ($nobsprint)?sizestring($datasize):"") if ( $verbose );
  }

  my $duration = Time::HiRes::time - $ftime;
  my $rate = $datasize/(($duration)?$duration:0.000001);
  printf (STDERR "Received %s%s of event information in %.1f seconds (%s/s)\n",
	  sizestring($datasize),
	  ( $response->content_encoding() =~ /gzip/ ) ? sprintf (" (compressed from %s)", sizestring(length $eventxml)) : "",
	  $duration, sizestring($rate));

  # Return if no metadata received
  return if ( length $eventxml <= 0 );

  # Create stream oriented XML parser instance
  use XML::SAX;
  my $parser = new XML::SAX::ParserFactory->parser( Handler => ESHandler->new );

  my $totalevents = 0;
  my $totalorigins = 0;

  my $ptime = Time::HiRes::time;

  print STDERR "Parsing XML event data... " if ( $verbose );

  # Open file to store event XML
  my $eventxmlfile = ( $xmlfile ) ? $xmlfile : "eventdata-$$.xml";
  if ( open (EXML, ">$eventxmlfile") ) {
    # Write XML and close file
    print EXML $eventxml;
    close EXML;

    # Parse XML from file
    $parser->parse_file ($eventxmlfile);

    # Remove temporary XML file
    if ( ! defined $xmlfile ) {
      if ( ! unlink $eventxmlfile ) {
	print STDERR "Cannot remove temporary XML file: $!\n";
      }
    }
  }
  # Otherwise parse the XML in memory
  else {
    printf STDERR " in memory (possibly slow), " if ( $verbose );

    # Parse XML event data from string
    $parser->parse_string ($eventxml);
  }

  printf STDERR "Done (%.1f seconds)\n", Time::HiRes::time - $ptime if ( $verbose );

  my $duration = Time::HiRes::time - $ftime;
  my $rate = $datasize/(($duration)?$duration:0.000001);
  printf (STDERR "Processed event information for $totalevents events, $totalorigins origins in %.1f seconds (%s/s)\n",
	  $duration, sizestring($rate));

  ## End of this routine, below is the XML parsing handler used above

  ## Beginning of SAX ESHandler, event-based streaming XML parsing
  package ESHandler;
  use base qw(XML::SAX::Base);
  use HTTP::Date;

  my $inevent = 0;
  my $inpreferredOriginID = 0;
  my $inpreferredMagnitudeID = 0;
  my $indescription = 0;
  my $intext = 0;
  my $invalue = 0;

  my $inorigin = 0;
  my $intime = 0;
  my $inlat = 0;
  my $inlon = 0;
  my $indepth = 0;
  my $increationInfo = 0;
  my $inauthor = 0;

  my $inmagnitude = 0;
  my $inmag = 0;
  my $intype = 0;

  my $name = undef;

  my ($name,$eventid,$originid,$porigin,$pmagnitude,$time,$lat,$lon,$depth,$author,$catalog,$contributor,$contributoreventid) = (undef) x 13;
  my ($magnitudeid,$mag,$magtype,$magauthor) = (undef) x 4;

  sub start_element {
    my ($self,$element) = @_;

    if ( $element->{Name} eq "event" ) {
      ($name,$eventid,$originid,$porigin,$pmagnitude,$time,$lat,$lon,$depth,$author,$catalog,$contributor,$contributoreventid) = (undef) x 13;
      ($magnitudeid,$mag,$magtype,$magauthor) = (undef) x 4;

      $eventid = $element->{Attributes}->{'{}publicID'}->{Value};

      $inevent = 1;
    }

    if ( $inevent ) {
      if ( $element->{Name} eq "preferredOriginID" ) { $inpreferredOriginID = 1; }
      elsif ( $element->{Name} eq "preferredMagnitudeID" ) { $inpreferredMagnitudeID = 1; }
      elsif ( $element->{Name} eq "description" ) { $indescription = 1; }

      if ( $indescription && $element->{Name} eq "text" ) { $intext = 1; }

      if ( $element->{Name} eq "origin" ) {
	$originid = $element->{Attributes}->{'{}publicID'}->{Value};

	# Search for catalog and contributor from any namespace
	foreach my $key (keys %{$element->{Attributes}}) {
          $catalog = $element->{Attributes}->{$key}->{Value} if ( $key =~ /^\{.*\}catalog$/ );
          $contributor = $element->{Attributes}->{$key}->{Value} if ( $key =~ /^\{.*\}contributor$/ );
          $contributoreventid = $element->{Attributes}->{$key}->{Value} if ( $key =~ /^\{.*\}contributorEventId$/ );
	}

	$inorigin = 1;
      }

      if ( $element->{Name} eq "magnitude" ) {
	$magnitudeid = $element->{Attributes}->{'{}publicID'}->{Value};

	$inmagnitude = 1;
      }
    }

    if ( $inorigin ) {
      if ( $element->{Name} eq "time" ) { $intime = 1; }
      elsif ( $element->{Name} eq "latitude" ) { $inlat = 1; }
      elsif ( $element->{Name} eq "longitude" ) { $inlon = 1; }
      elsif ( $element->{Name} eq "depth" ) { $indepth = 1; }
      elsif ( $element->{Name} eq "creationInfo" ) { $increationInfo = 1; }

      if ( ($intime || $inlat || $inlon || $indepth || $increationInfo) && $element->{Name} eq "value" ) { $invalue = 1; }
      if ( $increationInfo && $element->{Name} eq "author" ) { $inauthor = 1; }
    }

    if ( $inmagnitude ) {
      if ( $element->{Name} eq "mag" ) { $inmag = 1; }
      elsif ( $element->{Name} eq "type" ) { $intype = 1; }
      elsif ( $element->{Name} eq "creationInfo" ) { $increationInfo = 1; }

      if ( $inmag && $element->{Name} eq "value" ) { $invalue = 1; }
      if ( $increationInfo && $element->{Name} eq "author" ) { $inauthor = 1; }
    }
  }

  sub end_element {
    my ($self,$element) = @_;

    if ( $element->{Name} eq "event" ) {
      push (@eventids, $eventid);

      $eventname{$eventid} = $name;
      $eventprime{$eventid} = $porigin;
      $eventprimemag{$eventid} = $pmagnitude;
      $totalevents++;

      ($name,$eventid,$porigin,$pmagnitude) = (undef) x 4;
      $inevent = 0;
    }

    if ( $inevent ) {
      if ( $element->{Name} eq "preferredOriginID" ) {
	$inpreferredOriginID = 0;
      }
      elsif ( $element->{Name} eq "preferredMagnitudeID" ) {
	$inpreferredMagnitudeID = 0;
      }
      elsif ( $element->{Name} eq "description" ) { $indescription = 0; }

      if ( $indescription && $element->{Name} eq "text" ) { $intext = 0; }

      if ( $element->{Name} eq "origin" ) {
	# Convert ISO exchange time to something slightly more readable
	$time =~ s/\-/\//g;
        $time =~ s/T/ /;

	@{$origins{$eventid}{$originid}} = ($time,$lat,$lon,$depth,$author,$catalog,$contributor,$contributoreventid);
        $totalorigins++;

	($originid,$time,$lat,$lon,$depth,$author,$catalog,$contributor,$contributoreventid) = (undef) x 9;
	$inorigin = 0;
      }

      if ( $element->{Name} eq "magnitude" ) {
	@{$mags{$eventid}{$magnitudeid}} = ($magtype,$mag,$magauthor);

	($magnitudeid,$mag,$magtype,$magauthor) = (undef) x 4;
	$inmagnitude = 0;
      }
    }

    if ( $inorigin ) {
      if ( $element->{Name} eq "time" ) { $intime = 0; }
      elsif ( $element->{Name} eq "latitude" ) { $inlat = 0; }
      elsif ( $element->{Name} eq "longitude" ) { $inlon = 0; }
      elsif ( $element->{Name} eq "depth" ) { $indepth = 0; }
      elsif ( $element->{Name} eq "creationInfo" ) { $increationInfo = 0; }

      if ( ($intime || $inlat || $inlon || $indepth || $increationInfo) && $element->{Name} eq "value" ) { $invalue = 0; }
      if ( $increationInfo && $element->{Name} eq "author" ) { $inauthor = 0; }
    }

    if ( $inmagnitude ) {
      if ( $element->{Name} eq "mag" ) { $inmag = 0; }
      elsif ( $element->{Name} eq "type" ) { $intype = 0; }
      elsif ( $element->{Name} eq "creationInfo" ) { $increationInfo = 0; }

      if ( $inmag && $element->{Name} eq "value" ) { $invalue = 0; }
      if ( $increationInfo && $element->{Name} eq "author" ) { $inauthor = 0; }
    }
  }

  sub characters {
    my ($self,$element) = @_;

    if ( defined $element->{Data} && $inevent ) {

      if ( $inpreferredOriginID ) { $porigin .= $element->{Data}; }
      elsif ( $inpreferredMagnitudeID ) { $pmagnitude .= $element->{Data}; }
      elsif ( $indescription && $intext ) { $name .= $element->{Data}; }

      elsif ( $inorigin ) {
	if ( $intime && $invalue ) { $time .= $element->{Data}; }
	elsif ($inlat && $invalue ) { $lat .= $element->{Data}; }
	elsif ($inlon && $invalue ) { $lon .= $element->{Data}; }
	elsif ($indepth && $invalue ) {
	   # Convert QuakeML depth in meters to kilometers
	  $depth .= $element->{Data} / 1000.0;
	}
	elsif ($increationInfo && $inauthor ) { $author .= $element->{Data}; }
      }

      elsif ( $inmagnitude ) {
	if ( $inmag && $invalue ) { $mag .= $element->{Data}; }
	elsif ( $intype ) { $magtype .= $element->{Data}; }
	elsif ( $increationInfo && $inauthor ) { $magauthor .= $element->{Data}; }
      }
    }
  } # End of SAX ESHandler
} # End of FetchMetaData()


######################################################################
# EDCallBack:
#
# A call back for LWP downloading.
#
# Add received data to eventxml string, tally up the received data
# size and print and updated (overwriting) byte count string.
######################################################################
sub EDCallBack {
  my ($data, $response, $protocol) = @_;
  $datasize += length($data);

  if ( $response->content_encoding() =~ /gzip/ ) {
    my $datablock = "";
    $inflater->inflate($data, $datablock);
    $eventxml .= $datablock;
  }
  else {
    $eventxml .= $data;
  }

  if ( $verbose && ! $nobsprint ) {
    printf (STDERR "%-10.10s\b\b\b\b\b\b\b\b\b\b", sizestring($datasize));
  }
}


######################################################################
# sizestring (bytes):
#
# Return a clean size string for a given byte count.
######################################################################
sub sizestring { # sizestring (bytes)
  my $bytes = shift;

  if ( $bytes < 1000 ) {
    return sprintf "%d Bytes", $bytes;
  }
  elsif ( ($bytes / 1024) < 1000 ) {
    return sprintf "%.1f KB", $bytes / 1024;
  }
  elsif ( ($bytes / 1024 / 1024) < 1000 ) {
    return sprintf "%.1f MB", $bytes / 1024 / 1024;
  }
  elsif ( ($bytes / 1024 / 1024 / 1024) < 1000 ) {
    return sprintf "%.1f GB", $bytes / 1024 / 1024 / 1024;
  }
  elsif ( ($bytes / 1024 / 1024 / 1024 / 1024) < 1000 ) {
    return sprintf "%.1f TB", $bytes / 1024 / 1024 / 1024 / 1024;
  }
  else {
    return "";
  }
} # End of sizestring()


######################################################################
#
# Package RequestAgent: a superclass for LWP::UserAgent with override
# of LWP::UserAgent methods to set default user agent and handle
# authentication credentials.
#
######################################################################
BEGIN {
  use LWP;
  package RequestAgent;
  our @ISA = qw(LWP::UserAgent);

  sub new
    {
      my $self = LWP::UserAgent::new(@_);
      my $fulluseragent = $useragent;
      $fulluseragent .= " ($appname)" if ( $appname );
      $self->agent($fulluseragent);
      $self;
    }

  sub get_basic_credentials
    {
      my ($self, $realm, $uri) = @_;

      if ( defined $auth ) {
        return split(':', $auth, 2);
      }
      elsif (-t) {
        my $netloc = $uri->host_port;
        print "\n";
        print "Enter username for $realm at $netloc: ";
        my $user = <STDIN>;
        chomp($user);
        return (undef, undef) unless length $user;
        print "Password: ";
        system("stty -echo");
        my $password = <STDIN>;
        system("stty echo");
        print "\n";  # because we disabled echo
        chomp($password);
        return ($user, $password);
      }
      else {
        return (undef, undef)
      }
    }
} # End of LWP::UserAgent override
