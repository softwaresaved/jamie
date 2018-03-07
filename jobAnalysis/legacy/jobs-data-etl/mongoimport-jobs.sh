#!/bin/bash

# config file
CONFIG=$1

# filename of cleaned jobs CSV file to import
FILE=$2

read pass < "$CONFIG"

mongoimport -v -u jobsDBuser -p $pass --authenticationDatabase jobsDB --db jobsDB --collection jobs --type csv --headerline --stopOnError --maintainInsertionOrder --numInsertionWorkers 1 --file "$FILE"