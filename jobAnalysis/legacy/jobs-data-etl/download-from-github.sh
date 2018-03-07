#!/bin/bash

# repository parameters
OWNER='softwaresaved'
REPO='jobs-analysis'

# user access token
OAUTH_TOKEN='INSERTACCESSTOKENHERE'

# files to download from GitHub

# file 1
REPOFILEPATH1=DataCleaning/jobsCsvCleaner.py
REF1=master
LOCALFILENAME1=jobsCsvCleaner.py
URL1="https://api.github.com/repos/$OWNER/$REPO/contents/$REPOFILEPATH1?ref=$REF1"

# file 2
REPOFILEPATH2=
REF2=
LOCALFILENAME2=
URL2="https://api.github.com/repos/$OWNER/$REPO/contents/$REPOFILEPATH2?ref=$REF2"

# file 3
REPOFILEPATH3=
REF3=
LOCALFILENAME3=
URL3="https://api.github.com/repos/$OWNER/$REPO/contents/$REPOFILEPATH3?ref=$REF3"

# Get file contents
curl -H "Authorization: token $OAUTH_TOKEN" -H 'Accept: application/vnd.github.v3.raw' -o $LOCALFILENAME1 -L $URL1
#curl -H "Authorization: token $OAUTH_TOKEN" -H 'Accept: application/vnd.github.v3.raw' -o $LOCALFILENAME2 -L $URL2
#curl -H "Authorization: token $OAUTH_TOKEN" -H 'Accept: application/vnd.github.v3.raw' -o $LOCALFILENAME3 -L $URL3