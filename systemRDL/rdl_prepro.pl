#! /usr/bin/perl -w
#############################################################################
#        SystemRDL  Preprocess Script                                       #
#        Author: Xinwei Gong                                                #
#        Mail:   gxwcxl2010@gmail.com                                       #
#        Github URL: https://github.com/gxwcxl2010/System-RDL-preprocess    #
#############################################################################
use Getopt::Long;
use Data::Dumper;
use strict;

my $argEval       = undef;
my @incdirs       = ();
my @cmdLineMacros = ();
my $debug         = 0;
my $help          = undef;
my $outdir        = undef;
my $noenv         = undef;

my $optHash = {
    "outdir|od=s"  => \$outdir,
    "incdir|I=s"   => \@incdirs,
    "D=s"          => \@cmdLineMacros,
    "eval|e=s"     => \$argEval,
    "debug=i"      => \$debug,
    "help|h"       => \$help,
    "noenv"        => \$noenv
};

sub Usage {
    my $HELP_STR = << 'END_STR';
  rdl_prepro.pl [-outdir <output dir>][-I include_dir] [-e "perl eval code"] [-debug <N>] [-D <MACRO>] <rdl_file.rdl>

  -----------------------------------------------------------------------------------------
  #Description:
     Process perl preprocess code that defined in SystemRDL. (<% some perl code %> or <%= some perl express%>)
     Process directive macros, current support ones: `ifdef, `ifndef, `else, `endif, `define, `undef
  -----------------------------------------------------------------------------------------
  #Options:
  -outdir|o <outdir> Specify the output direcotry of preprocess. If not specified, 
                       it will be the same as source file.
  -incdir|I  <dir>     Specify the include dirs for preprocess script.
  -eval|e              Add some perl code that will be execute before the preprocess.
  -debug               Show more message for debug.
  -D         <macro>   Define a preprocess macro.
  -noenv               Don't push current env to perl preprocess
  -help                Show this message for help.

END_STR
    print $HELP_STR, "\n";
    exit 1;
}

GetOptions(%{$optHash}) or die "Unknown option!\n";
if(defined $help){
    &Usage();
}
#push incdir
push @incdirs, @INC;

my $appendEnv = "";
if(not defined $noenv){
    $appendEnv = "BEGIN{";
    foreach(keys %ENV){
        $appendEnv .= "\$ENV{$_}='$ENV{$_}';";
    }
    $appendEnv .="};";
}
foreach(@incdirs){
  print "incidr:",$_,"\n" if $debug > 1;
}
foreach(@ARGV){
  print "ARGV:$_\n" if $debug > 1;
}
print "process rdl file number:",scalar(@ARGV) , "\n";
die "ERROR! No file to process!\n" if scalar(@ARGV) < 1;

#Flags for macro processing
my $definedMacros             = undef;
my @waitingMacros             = ();
my $directiveDepth            = 0;
my $ignore_this_line          = 0;
my $ignore_till_else_or_endif = 0;
my $ignore_till_endif         = 0;
my $ignore_depth              = 0;

foreach my $f (@ARGV){
    &pre_preproc($f);
    &do_preproc($f,undef);
    &post_preproc($f);
}

sub pre_preproc {
    $definedMacros             = undef;
    @waitingMacros             = ();
    $directiveDepth            = 0;
    $ignore_this_line          = 0;
    $ignore_till_else_or_endif = 0;
    $ignore_till_endif         = 0;
    $ignore_depth              = 0;
    #push predefined macros
    foreach(@cmdLineMacros){
        $definedMacros->{$_} = 1;
    }
}

sub post_preproc {
    my $file = shift @_;
    #check directive parse ending
    print "directiveDepth = $directiveDepth\n" if $debug > 1;
    if($directiveDepth != 0){
        die "`endif missed for macro:@waitingMacros of file $file !\n";
    }
    #check preprocess output file
    my $rdl_ppp_final = "$file\.pp.final";
    if(not -e $rdl_ppp_final){
        die "ERROR! rdl preprocess fail, expected file $rdl_ppp_final does not exist!\n";
    }
    #move to outfile if defined
    if(defined $outdir){
        system("mv $rdl_ppp_final $outdir");
        $rdl_ppp_final =~ s@^.*/@@;
        print "rdl_ppp_final = $rdl_ppp_final\n";
        $rdl_ppp_final = "$outdir/$rdl_ppp_final";
        $rdl_ppp_final =~ s@/+@/@g;
        if(not -e $rdl_ppp_final){
            die "ERROR! write file failed for $rdl_ppp_final!\n";
        }
    }
    print "Generated file $rdl_ppp_final\n";
}


#process macros, current support ones: `ifdef, `ifndef, `else, `endif, `define, `undef
sub proc_macros {
    my $file      = shift @_;
    my $parent_fh = shift @_;
    
    print "enter proc_macros for $file!\n" if $debug > 1;

    my $line      = 0;
    open (my $fh, '<', $file) or die "$! File:$file\n";
    while(<$fh>){
        my $tmp       = $_;
        my $macroline = 0;
        $line++;
        $ignore_this_line = 0;
        if($ignore_till_else_or_endif ==1 or $ignore_till_endif == 1){
            $ignore_this_line = 1;
        }
        if(m/^\s*\t*`define[\s\t]+\b(\w+)\b([\s\t]+\b(\w+)\b)*/){
            $ignore_this_line    = 1;
            $definedMacros->{$1} = defined $3 ? $3 : 1;
            print "define macro: $1 at $file:$line!\n" if $debug > 1;
        }
        elsif(m/^\s*\t*`undef[\s\t]+\b(\w+)\b/){
            $ignore_this_line    = 1;
            $definedMacros->{$1} = 0;
            delete $definedMacros->{$1};
        }
        elsif(m/^\s*\t*`ifdef[\s\t]+\b(\w+)\b/){
            $ignore_this_line = 1;
            $directiveDepth++;
            my $macrosRef;
            $macrosRef->{hit_if_branch} = 0;
            push @{$macrosRef->{macros}}, $1;
            push @waitingMacros, $macrosRef;
            if($ignore_till_else_or_endif == 0 and $ignore_till_endif == 0){
                if(not exists $definedMacros->{$1}){
                    $ignore_till_else_or_endif = 1;
                    $ignore_depth              = $directiveDepth;
                    print " Start `ifdef ingore for $waitingMacros[-1], ignore_depth=$ignore_depth at $file:$line!\n" if $debug > 1;
                    print Dumper("definedMacros",$definedMacros) if $debug > 1;
                }
                else {
                    $macrosRef->{hit_if_branch} = 1;
                }
            }
        }
        elsif(m/^\s*\t*`ifndef[\s\t]+\b(\w+)\b/){
            $ignore_this_line = 1;
            $directiveDepth++;
            my $macrosRef;
            $macrosRef->{hit_if_branch} = 0;
            push @{$macrosRef->{macros}}, $1;
            push @waitingMacros, $macrosRef;
            if($ignore_till_else_or_endif == 0 and $ignore_till_endif == 0){
                if(exists $definedMacros->{$1}){
                    $ignore_till_else_or_endif = 1;
                    $ignore_depth = $directiveDepth;
                    print " Start `ifndef ingore for $macrosRef->{macros}[-1], ignore_depth=$ignore_depth at $file:$line!\n" if $debug > 1;
                    print Dumper("definedMacros",$definedMacros) if $debug > 1;
                }
                else {
                    $macrosRef->{hit_if_branch} = 1;
                }
            }
        }
        elsif(m/^\s*\t*`endif\b/){
            $ignore_this_line = 1;
            if($ignore_till_else_or_endif ==1 && $directiveDepth == $ignore_depth){
                $ignore_till_else_or_endif = 0;
                print " find `endif for @{$waitingMacros[-1]->{macros}}!\n" if $debug > 1;
            }
            if($ignore_till_endif ==1 && $directiveDepth == $ignore_depth){
                $ignore_till_endif = 0;
                print " find `endif for @{$waitingMacros[-1]->{macros}}!\n" if $debug > 1;
            }
            $directiveDepth--;
            pop @waitingMacros;
        }
        elsif(m/^\s*\t*`else\b/){
            $ignore_this_line = 1;
            my $macrosRef;
            if( scalar(@waitingMacros) < 1){
                die "ERROR! There is no `ifdef or `ifndef for `else at $file:$line!\n";
            }
            else {
                $macrosRef = $waitingMacros[-1];
            }
            if($ignore_till_else_or_endif == 1 && $directiveDepth == $ignore_depth){
                $ignore_till_else_or_endif = 0;
                print " find `else for \[@{$macrosRef->{macros}}\] at $file:$line!\n" if $debug > 1;
            }
            print "Before check `else ignore_till_else_or_endif:$ignore_till_else_or_endif,ignore_till_endif:$ignore_till_endif,waitingMacros:\[@{$macrosRef->{macros}}\], hit_if_branch=$macrosRef->{hit_if_branch}\n" if $debug > 1;
            if(($ignore_till_else_or_endif == 0 and $ignore_till_endif == 0) and
                $macrosRef->{hit_if_branch} == 1){
                $ignore_till_endif = 1;
                $ignore_depth      = $directiveDepth;
                print " Start `else ingore for \[@{$macrosRef->{macros}}\], ignore_depth=$ignore_depth at $file:$line!\n" if $debug > 1;
            }
        }
        elsif(m/^\s*\t*`elsif[\s\t]+\b(\w+)\b/){
            $ignore_this_line = 1;
            my $testMacroPre  = undef;
            my $testMacroCur  = $1;
            if( scalar(@waitingMacros) < 1){
                die "ERROR! There is no `ifdef or `ifndef for `else at $file:$line!\n";
            }
            else {
                $testMacroPre = $waitingMacros[-1]->{macros}[-1];
            }
            my $macrosRef = $waitingMacros[-1];
            push @{$macrosRef->{macros}}, $1;
            if($ignore_till_else_or_endif == 1 && $directiveDepth == $ignore_depth){
                $ignore_till_else_or_endif = 0;
                print " find `elsif for $testMacroPre at $file:$line!\n" if $debug > 1;
            }
            if($ignore_till_else_or_endif == 0 and $ignore_till_endif == 0){
                if($macrosRef->{hit_if_branch} == 1 or (not exists $definedMacros->{$testMacroCur})){
                    $ignore_till_else_or_endif = 1;
                    $ignore_depth      = $directiveDepth;
                    print " Start `elsif ingore for $testMacroCur, ignore_depth=$ignore_depth at $file:$line!\n" if $debug > 1;
                }
                else {
                    $macrosRef->{hit_if_branch} = 1;
                }
            }
        }
        if(m/`/){
            $macroline = 1;
        }
        #deny illegal or bad directive macro style
        if($macroline == 1){
            if(m/`.*`/){
                die "ERROR! $file:$line has used multi directive macros in one line! Error line: $_\n";
            }
            if(m/^.*\w+.*`/){
                die "ERROR! $file:$line has words before directive macro! Please move directive macro to stand alone line or fix typo! Error line:$_\n";
            }
            if(m/`(else|endif|(ifdef|ifndef|elsif)[\s\t]+\w+)[\s\t]+([^\s\t]+)/){
                die "ERROR! $file:$line has words after directive macro! Please move directive macro to stand alone line or fix typo! Error line:$_\n";
            }
            if( not m/`(ifdef|ifndef|else|elsif|end|include|define|undef)/){
                die "ERROR! $file:$line has unknow directive macro! Error line: $_\n";
            }
        }
        print "ignore_this_line = $ignore_this_line\n" if $debug > 8;
        if($ignore_this_line == 1){
            next;
        }
        if(m/^([\s\t]*)`include[\s\t]+"([^ ]*)"(.*)$/){
            my $inc_file = $2;
            my $found    = 0;
            foreach my $dir(@incdirs){
                my $test_file = "$dir/$inc_file";
                if(-f "$test_file"){
                    print "processing include file $test_file in $file ....\n" if $debug>-1;
                    &do_preproc($test_file,$parent_fh);
                    $found = 1;
                    last;
                }
            }
            die "Cannot find $inc_file in $file! incdirs:@incdirs\n" if $found == 0;
            print $parent_fh "\n",$3;
        }
        else {
            print $parent_fh $_;
        }
    }
    close $fh;
}

sub do_preproc {
    my $file      = shift @_;
    my $parent_fh = shift @_;
    if(defined $parent_fh){
        print "do_preproc: $file, parent_fh used!\n" if $debug > 1;
    }
    else {
        print "do_preproc: $file, null\n" if $debug > 1;
    }
    my $pl_file = $file.".pl";
    open (my $plfh, '>', $pl_file) or die $!;
    if(defined $argEval){
        print $plfh $argEval,"\n";
    }
    print $plfh $appendEnv,"\n";
    open (my $fh, '<', $file) or die $!;
    {
        local $/;
        my $context = <$fh>;

        while(length($context)>0){
            if($context =~ m@^((.*?\n*?)*?.*?)<%@){
                #print not perl code
                my $match=$1;
                my $len = length($match);
                $match =~ s/\\/\\\\/g;
                $match =~ s/'/\\'/g;
                print $plfh "print '$match';\n";
                $context = substr($context,$len+2);
                my $exe = 0;
                if($context =~ m@^=@){
                    print $plfh "print ";
                    $context = substr($context,1);
                    $exe =1;
                }
                if($context =~ m@^((.*?\n*?)*?.*?)%>@){
                    #keep perl code
                    my $match=$1;
                    my $len = length($match);
                    print $plfh $match;
                    $context = substr($context,$len+2);
                    if($exe == 1){
                        print $plfh ' ;';
                    }
                    print $plfh "\n";
                }
                else {
                    print STDERR "context:\n",$context, "\n";
                    die "Error! More '%>' is needed as '<%' is found at substr $len!\n";
                }
            }
            else {
                $context =~ s/\\/\\\\/g;
                $context =~ s/'/\\'/g;
                print $plfh "print '$context';";
                $context = '';
            }
        }
    }
    close $fh;
    close $plfh;
    my $rdl_ppp = $file.".post_pp.init";
    my $plcmd = "perl ";
    foreach my $dir (@incdirs){
        $plcmd .= "-I$dir ";
    }
    $plcmd .= " $pl_file > $rdl_ppp";
    #print STDERR "plcmd=$plcmd\n";
    my $cmd_status = system("$plcmd");
    die "ERROR! perl code preprocess status: $cmd_status, plcmd = $plcmd\n" if $cmd_status > 0;
    print "perl code preprocess status: $cmd_status, plcmd = $plcmd\n" if $debug > 4;
    #delete comments
    system('sed -i \'s%//.*$%%\' '."$rdl_ppp");
    #delete empty lines
    system('sed -i \'/^\s*$/d\' '."$rdl_ppp");
    #delete temp files
    system("rm $pl_file") if $debug == 0 and $cmd_status == 0;

    my $rdl_ppp_final = "$file\.pp.final";
    open (my $pp_final_fh, '>', $rdl_ppp_final) or die $!;
    &proc_macros($rdl_ppp,$pp_final_fh);
    close $pp_final_fh;


    if(defined $parent_fh){
        print "Define parent_fh for $rdl_ppp\n" if $debug > 1;
        my $pp_inc_str = `cat $rdl_ppp_final`;
        print $parent_fh $pp_inc_str;
        system("rm $rdl_ppp_final") if $debug == 0;
    }
    system("rm $rdl_ppp") if $debug == 0;
}


