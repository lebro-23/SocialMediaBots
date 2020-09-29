import itertools
import sys
from datetime import datetime
from datetime import timedelta

import pandas as pd
from scrapers_bots import *
from storage_functions import *

username = sys.argv[1]
password = sys.argv[2]
followed_list_path = sys.argv[3]
following_list_path = sys.argv[4]
unfollowed_list_path = sys.argv[4]
directory_outpath = sys.argv[5]
max_unfollows = int(sys.argv[6])

#Since command lines arguments are parsed as string, split into list
n = len(followed_list_path)
followed_list_files = followed_list_path[1:n-1]
followed_list_files = followed_list_files.split(',')

full_followed_list = []

if(unfollowed_list_path != ''):
    unfollowed_series = download_df_from_bucket(credentials_path='../InstagramBot-9cb1dfece602.json',bucket_path='insta-schools-bucket', filepath=unfollowed_list_path)

#Get list of users followed by us
for flf in followed_list_files:
    followed_filename = (flf + '/' + 'post_followed_list.csv').strip()
    followed_series = download_df_from_bucket(credentials_path='../InstagramBot-9cb1dfece602.json',bucket_path='insta-schools-bucket', filepath=followed_filename)
    followed_list = list(followed_series.iloc[:, 1])
    full_followed_list.append(followed_list)

#Flatten list
full_followed_list = list(itertools.chain.from_iterable(full_followed_list))

#Get list of users following us
full_following_series = download_df_from_bucket(credentials_path='../InstagramBot-9cb1dfece602.json',bucket_path='insta-schools-bucket', filepath=following_list_path)
full_following_list = list(full_following_series.iloc[:, 1])

#Get users who we have followed but haven't followed us back and exclude users already unfollowed
unfollow_user_list = (set(full_followed_list) - set(full_following_list)) - set(unfollowed_series)

#Login
driver = login(username=username,password=password)

# Print number of unique users
full_input_list = list(unfollow_user_list)
print("Number of unique users %s" % (len(full_input_list)))

# Print estimated finish time
max_mins = (min(int(max_unfollows), len(full_input_list)) / 2) * (1 + 5 / 60)
max_finish_time = datetime.now() + timedelta(minutes=max_mins)
print("Estimated finish time %s" % (max_finish_time))

# Run actions with given time breaks
secs = 60

full_list = []
unfollowed_list = []
error_unfollowed_list = []

count = 0

for user in full_input_list:

    count = count + 1

    if(count >= max_unfollows):
        break

    try:
        # Follow account
        not_followed, blocked, blocked_text = unfollow_user(username=user, driver=driver)

        # If Blocked then break loop
        if (blocked and blocked_text == 'Action Blocked'):
            print("Blocked! :(")
            print(blocked_text)
            break

        if (not_followed):
            print("Not following %s" % user)
        else:
            print("Successfully unfollowed account %s" % user)
            unfollowed_list.append(user)

        full_list.append(user)

    except Exception as e:
        error_unfollowed_list.append(user)
        print("Couldn't follow user %s" % user)

    #Write to file every 5 rows
    if(count%5 == 0):
        full_outpath = directory_outpath + '/' + username + '_full_list.csv'
        outpath = directory_outpath + '/' + username + '_unfollowed.csv'
        error_outpath = directory_outpath + '/' + username + 'error_unfollowed.csv'
        full_df = pd.Series(list(full_list))
        df = pd.Series(list(unfollowed_list))
        df_error = pd.Series(list(error_unfollowed_list))
        upload_df_to_bucket(credentials_path='../InstagramBot-9cb1dfece602.json', bucket_path='insta-schools-bucket',filepath=full_outpath, df=full_df)
        upload_df_to_bucket(credentials_path='../InstagramBot-9cb1dfece602.json', bucket_path='insta-schools-bucket',filepath=outpath, df=df)
        upload_df_to_bucket(credentials_path='../InstagramBot-9cb1dfece602.json', bucket_path='insta-schools-bucket',filepath=error_outpath, df=df_error)
