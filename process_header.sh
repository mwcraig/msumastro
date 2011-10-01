#!/usr/local/bin/bash

# use the local version to ensure bash >4, which includes associative arrays.

# for now, force the working version of wcstools:

WCSTOOLS=wcstools-local/bin


function subcolon 
{
    echo ${1//_/:}
    return
}

# usage:

if [ $# = 0 ] 
then
    echo "Moron!"
    exit 1
fi

# DO NOT MODIFY SOURCE FILE...operate only on the copy.
origFile=$1
newFile=${1/.fit/_new.fit}
cp $origFile $newFile

# Do some basic processing of FITS headers from feder observatory:

# Reformat Lat/Lon/RA/Dec to use colon as separator instead of space

# MaxImDL 4 keywords for lat/long
latlong=$(echo SITE{LAT,LONG})

for key in $latlong "RA" "DEC"
do
    origKeyValue=$(gethead -b $key $origFile)
    newKeyValue=$(subcolon $origKeyValue )
    if [[ $origKeyValue != $newKeyValue ]] 
    then
	echo "Would have changed, in $newFile ..."
	echo $key $origKeyValue $newKeyValue
	echo	"$WCSTOOLS/sethead -h $newFile $key=$newKeyValue"
	$WCSTOOLS/sethead -h $newFile $key=$newKeyValue
    fi

done

