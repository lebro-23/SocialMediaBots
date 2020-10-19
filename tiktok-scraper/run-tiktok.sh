#!/bin/bash

while getopts t: flag
do
    case "${flag}" in
        t) tag=${OPTARG};;
    esac
done

echo "Getting users for tag ${tag}"
source ../../tiktok-env/bin/activate
python3 run_tags_1.py $tag
deactivate

lines=$(wc -l "${tag}_profiles.csv" | sed 's/[^0-9]//g') 
echo "Finished. Now getting user info for ${lines} users"
source ../../tiktok-env-2/bin/activate

rm -f "${tag}_profiles_info_df.csv"
rm -f "${tag}_profiles_error_df.csv"

count=0

while [ $lines -gt 1 ]
do
   count=$(($count+1))
   python3 run_tags_2.py $tag
   lines=$(wc -l "${tag}_profiles.csv" | sed 's/[^0-9]//g')
   echo "Finished doing ${count} iterations.\nEstimated ${lines} records left"
done

deactivate
