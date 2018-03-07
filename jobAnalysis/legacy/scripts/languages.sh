#!/usr/bin/env bash
#
# Count the number of terms a programming language is used.
# This is to be used more of a sanity check.
#

# Find out occurrences for each language.
#
# There are dangers in explicitly specifying word boundaries (\b).
# For instance "\bfortran\b" will not pick up fortran95.
#

fortran=`grep -i fortran ../data/jobs.csv| wc -l `
julia=`grep -i julia ../data/jobs.csv| wc -l `
python=`grep -i python ../data/jobs.csv| wc -l `
# Using explicit word boundaries here will stop me picking up "Java"
# which I have seen one case of but don't want to pick up JavaScript.
java=`grep -Ei "[[:punct:]]?java[[:punct:]]?" ../data/jobs.csv| wc -l `
javascript=`grep -i javascript ../data/jobs.csv| wc -l `
html=`grep -i html ../data/jobs.csv| wc -l `
cplusplus=`grep -i c++ ../data/jobs.csv| wc -l `
sas=`grep -i "\bsas\b" ../data/jobs.csv| wc -l `
spss=`grep -i "\bspss\b" ../data/jobs.csv| wc -l `
# Getting some false positives with the reg below, mainly with people's names.
r=`grep  "\bR\b" ../data/jobs.csv| wc -l `
# Bad choice - c use used for "circa", chemical names, etc.
# Get lots and lots of false positives.
# If we search for " C ", there are more false positives:
# "Level C ", "Grade C ",
# "Must also have GCSE English language and Mathematics or equivalent at a minimum of C "
#c=`grep -i "\bc\b" ../data/jobs.csv| wc -l `
pascal=`grep -i pascal ../data/jobs.csv| wc -l `
matlab=`grep -i matlab ../data/jobs.csv| wc -l `
genstat=`grep -i genstat ../data/jobs.csv| wc -l `
php=`grep -i "\bphp\b" ../data/jobs.csv| wc -l `
perl=`grep -i perl ../data/jobs.csv| wc -l `
stata=`grep -i "\bstata\b" ../data/jobs.csv| wc -l `
sql=`grep -i "\bsql\b" ../data/jobs.csv| wc -l `
nosql=`grep -i "\bnosql\b" ../data/jobs.csv| wc -l `
ruby=`grep -i "\bruby\b" ../data/jobs.csv| wc -l `
jquery=`grep -i "\bjquery\b" ../data/jobs.csv| wc -l `
csharp=`grep -i "c#" ../data/jobs.csv| wc -l `
asp=`grep -i "asp.net" ../data/jobs.csv| wc -l `
hadoop=`grep -i "hadoop" ../data/jobs.csv| wc -l `

# Other computing languages: D, Basic, Visual Basic

# Print out the results.
echo
echo Number of jobs that mention Fortran: $fortran
echo Number of jobs that mention Julia: $julia
echo Number of jobs that mention Python: $python
echo Number of jobs that mention Java: $java
echo Number of jobs that mention JavaScript: $javascript
echo Number of jobs that mention html: $html
echo Number of jobs that mention C++: $cplusplus
echo Number of jobs that mention SAS: $sas
echo Number of jobs that mention SPSS: $spss
echo Number of jobs that mention R: $r
echo Number of jobs that mention Genstat: $genstat
echo Number of jobs that mention MATLAB: $matlab
#echo Number of jobs that mention C: $c
echo Number of jobs that mention Pascal: $pascal
echo Number of jobs that mention PHP: $php
echo Number of jobs that mention Perl: $perl
echo Number of jobs that mention Stata: $stata
echo Number of jobs that mention SQL: $sql
echo Number of jobs that mention NoSQL: $nosql
echo Number of jobs that mention Ruby: $ruby
echo Number of jobs that mention Jquery: $jquery 
echo Number of jobs that mention C#: $csharp
echo Number of jobs that mention ASP.Net: $asp
echo Number of jobs that mention Hadoop: $hadoop
echo

