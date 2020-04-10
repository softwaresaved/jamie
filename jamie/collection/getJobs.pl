#!/usr/bin/env perl
#
# Author: Mario Antonioletti (mario@epcc.ed.ac.uk)
#
######################################################################
# Perl script to pull off jobs from www.jobs.ac.uk. Require:
#
# o Perl 5.10 or greater
# o Mojo Perl module (http://mojolicio.us/)
#
# Can install Mojo by running as a privileged user (on a mac add sudo 
# in front of the first line below):
#
# perl -MCPAN -e shell
# install Mojo
# quit
#
# Hopefully all of that should go without a hitch.
# This script works in two phases:
#
# 1. Get a page in www.jobs.ac.uk that lists all the
#    jobs. Can do this by using their search mechanism:
#    (in 2018 they changed show -> pageSize, changed accordingly in 
#     the parts that matter)
#
#    http://www.jobs.ac.uk/search/?keywords=*&sort=re&s=1&show=10
#
#    Note the show=N at the end. N=10 is good for testing. You
#    can also have N=all which will list all the jobs. The "all"
#    keyword defaults to the maximum per page which is 100. If
#    you look at the search page it will tell you how many jobs
#    they actually have. For now you can put show=4215 or whatever
#    is the current max but I am sure they will get on to this
#    as well.
#
#    One has to get all the job links from this page. Job links are
#    embedded in a piece of html that has:
#
#    <div class="text">
#      <a href="JobRelUrl">Job Name</a>
#      ...
#    </div>
#
#   The JobRelUrl are of the format:
#
#   /job/JobID/JobName
#
#   Need to extract all the JobRelUrl from this page. Collect 
#   all of these.
#  
# 2. Once we have each JobRelUrl we make this into a full URL,
#    visit each URL and extract the job information. The main
#    part of the job details are embedded in a bit of html:
#    
#    <div class="content">
#     ... we want all the stuff that is here ...
#    </div>
#
#   Save this as an html fragment as this contains semantical
#   information that makes it easier for subsequent analysis.
#   Save each fragment as JobID_JobName.
#   
#   Some ads have the type:
#
#   <div id="enhanced-content">
#     ... this stuff does nto follow a generic format so cannot
#         easily parse but we just save these files anyhow.
#   </div>
#
######################################################################

# Let the interpreter warn us of any problems.
use strict;
use warnings;

# Load up the Mojo user agent stuff.
use Mojo::UserAgent;
use Mojo::DOM;

# Use perl 5.10 features.
use v5.10;

# Define an output directory either  at the command line or
# defaults to JobsAcUK.
my $outdir = "";

if(exists($ARGV[0])){     # Grab the first command line arg
    $outdir = $ARGV[0];
}else{
   $outdir = "JobsAcUk"; # or use this default if non provided.
}
   
# Define the base web site URL.
my $baseurl = "https://www.jobs.ac.uk";

# Keep track of the jobs that have already been downloaded.
my %GotJob;

# Number of jobs available.
my $NumJobs=6000;

# Define the web site URL to operate on.
# URL expands to: 
#
# http://www.jobs.ac.uk/search/?keywords=*&sort=re&s=1&show=6000
#
# They later changed this to:
#
# https://www.jobs.ac.uk/search/?keywords=*&sort=re&s=1&pageSize=6000
#
# It is going to list 6000 jobs if as many as those are
# available before it starts paginating. It will only
# take new ones.
my $ws = "$baseurl/search/?keywords=*&sort=re&s=1&pageSize=$NumJobs";


##############################################
# First check what job files have already been
# downloaded. Do this by examining what files
# have been downloaded. The file names correspond
# to the job ids.

# Check whether an output job directory exists.
if( -d $outdir){

    # Read existing jobs and keep the job ids.
    print "Directory $outdir already exists.\n";
    print "Collecting information about jobs already downloaded.\n";

    # Get a listing of the files already in the output directory 
    # excluding the "." and ".." directory listings. The filenames
    # correspond to the job ids.
    opendir(DIR,$outdir) or 
           die("Could not open the output directory $outdir: $!.\n");
    my @jobs = grep(!/^\./,readdir(DIR));
    closedir(DIR) or 
           die("Could not close the output directory $outdir: $!\n");

    # Now grab the existing job ids
    foreach my $job (@jobs){
      $GotJob{"$job"} = 1;  
    }
}else{ # directory for scraped jobs does not exist.

    mkdir($outdir) or die("Could not create directory $outdir: $!.\n");
}

# Subroutine to write results to file.
sub WriteResults{

    # Get the arguments
    my ($outfile,$content) = @_;

    # Open the output file for this job.
    open(OUT,">:encoding(UTF-8)",$outfile) or die("Could not open the output file $outfile: $!.\n");

    print OUT $content;

    # Close the output file
    close(OUT) or die("Could not close $outfile:$!.\n");

}

##############################################
# Download the jobs.
#
# For debugging it is useful to run:
#
# mojo version
#
# to get versioning information and set the 
# environment variable:
#
# export MOJO_CLIENT_DEBUG=1
#
# to get extra information.
#

# Now we start...
print "Downloading new jobs...\n";

# Create a new user agent.
my $ua = Mojo::UserAgent->new;

# Start a transaction. 
#    Fetch a web site. 
#    Specify to the web server: Do Not Track (DNT).
my $tx = $ua->get($ws => {DNT => 1});

# Check for an error in the transaction.
if($tx->result->is_error){
   say("Getting the job page $ws failed",$tx->result->message);
   exit(1);
}elsif($tx->result->is_success){
#   say("Success in getting top level search page ...");
}else{
   say("Unknown result ...");
}

# Set a counter for the number of jobs downloaded.
my $jobcount=1;
my $missedjobs=0; # Counting jobs missed by missing css identifier.

# Create a dom object for the page.
my $dom = $tx->result->dom;

#print "URL: $ws\n";

# Go to the web site and look for all the bits that have the html:
#
# <div class="j-search-result__text"><a href="JobRelUrl">...</a>...</div>
#
# Extract each JobRelUrl which points to a job.
#for my $JobRelUrl ($dom->find("div.text a[href]")->map(attr=>'href')->each){
for my $JobRelUrl ($dom->find("div.j-search-result__text a[href]")->map(attr=>'href')->each){

       #print "URL: $JobRelUrl\n";
       # Parse out the jobid and jobname from the JobRelUrl
       # have for path resource the /job/UniqueId/NameForJob
       $JobRelUrl  =~ m^/job/(\w+)/([\w-]+)/?^;
       my $jobid   = $1;
       my $jobname = $2;

       # Check that the JobRelUrl is correctly parsed. If this is
       # triggered off then the regular expressions to grab the 
       # jobid and jobname need to be revised.
       if(not defined($jobid) or not defined($jobname)){
           print "WARNING: failed to parse $JobRelUrl correctly.\n";
	   print "         For the jobid have $jobid.\n";
	   print "         For the jobname have: $jobname.\n";
	   exit(1);
       }

       # Check whether we already have this job id.
       if(defined $GotJob{"$jobid"}){
	   #print "Already have job $jobid, skipping ...\n";
           next;
       }

       # Create a new URL from the relative URL.
       my $joburl = "$baseurl"."$JobRelUrl";

       # Now we need to get the job content. 
       # Generate a URL for the job.
       my $w = Mojo::URL->new($joburl);

       #print("Going for: $w.\n");
       # Start a transaction to get the job content.
       #    Specify to the web server: Do Not Track (DNT).
       my $subtx = $ua->get($w => {DNT => 1});

       # Check for an error in the job download.
       if($subtx->result->is_error){
          say("Getting job $joburl failed ",$tx->result->message);
          exit(1);
       }elsif($subtx->result->is_success){
       #    say("Success in getting $joburl ...");
       }else{
           say("Unknown result for $joburl.");
	   say("Output message: ",$tx->result->message);
	   next;
       }

       # Create a dom object for this page.
       my $jdom = $subtx->res->dom;

       # Find out what type of content we have and 
       # print it to file.
       my $content; 

       # Create an output filename including the output directory.
       my $outfile = "$outdir/$jobid";

       # Seem to have utf8 characters so inform Perl to expect this.
       #binmode(OUT, ":utf8");

       # If this is an enhanced content page just directly out.
       if(defined($content = $jdom->at("div#enhanced-content"))){ 

	      WriteResults($outfile,$content);

       }elsif(defined($content=$jdom->at("div.sub-grid.column-1.edge-span-2-mobile"))){ # A normal content page.

	      WriteResults($outfile,$content);

       }elsif(defined($content=$jdom->at("div.sub-grid"))){ # This is another type

	      WriteResults($outfile,$content);

       }elsif(defined($content=$jdom->at("div.row.body-text.jobPost"))){ # And yet another type

	      WriteResults($outfile,$content);

       }elsif(defined($content=$jdom->at("div.col-lg-12"))){ # And yet another type

	      WriteResults($outfile,$content);

       }elsif(defined($content=$jdom->at("div.left-content"))){ # And yet another type

	      WriteResults($outfile,$content);

       }elsif(defined($content=$jdom->at("div#left-content"))){ # id="left-content"

	      WriteResults($outfile,$content);

       }elsif(defined($content=$jdom->at("div.mainBody.jobsPage"))){ # New job container 4/6/19

	      WriteResults($outfile,$content);

       }else{
	  say("WARNING: Could not get content for job: $jobid ($joburl).");
	  $missedjobs++;
       }


       # Increment the job counter.
       $jobcount++;

} # End loop over $JobRelUrl 

# Seem to overcount by 1 so subract one job.
$jobcount--;

# State how many jobs were downloaded.
print "Downloaded $jobcount jobs from $baseurl. Missing $missedjobs  jobs.\n\n";

