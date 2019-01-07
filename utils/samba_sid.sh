#!/bin/bash
sambaSID=
for num in 1 2 3 ;do
    randNum=$(od -vAn -N4 -tu4 < /dev/urandom | sed -e 's/ //g')
    if [ -z     "$sambaSID" ];then
        sambaSID="S-1-5-21-$randNum"
    else
        sambaSID="${sambaSID}-${randNum}"
    fi
done
echo $sambaSID
