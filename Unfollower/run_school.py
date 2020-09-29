import sys
import pandas as pd
from scrapers_bots import *
from storage_functions import *
import itertools

username = sys.argv[1]
password = sys.argv[2]
followed_list_path = sys.argv[3]
following_list_path = sys.argv[4]
directory_outpath = sys.argv[5]

#Since command lines arguments are parsed as string, split into list
n = len(followed_list_path)
followed_list_files = followed_list_path[1:n-1]
followed_list_files = followed_list_files.split(',')

full_followed_list = []

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

#Get users who we have followed but haven't followed us back
unfollow_user_list = set(full_followed_list) - set(full_following_list)

#Login
driver = login(username=username,password=password)

#Get followers for specific page
output_list,error_output_list = unfollow_users(page_link=username,driver=driver,unfollow_list=unfollow_user_list)

#Write to file
#outpath = directory_outpath + '/' + p + '.csv'
#pd.Series(list(output_list)).to_csv(outpath)

outpath = directory_outpath + '/' + username + '_unfollowed.csv'
error_outpath = directory_outpath + '/' + username + 'error_unfollowed.csv'
df = pd.Series(list(output_list))
df_error = pd.Series(list(error_output_list))
upload_df_to_bucket(credentials_path='../InstagramBot-9cb1dfece602.json', bucket_path='insta-schools-bucket',filepath=outpath, df=df)
upload_df_to_bucket(credentials_path='../InstagramBot-9cb1dfece602.json', bucket_path='insta-schools-bucket',filepath=error_outpath, df=df_error)
