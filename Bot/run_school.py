import sys
import random
import pandas as pd
from datetime import datetime
from datetime import timedelta
from itertools import chain
from actions import *
from storage_functions import *

#Command line arguments
#Get file location of csv with list of usernames to action
username = sys.argv[1]
password = sys.argv[2]
filenames = sys.argv[3]
directory_inpath = sys.argv[4]
#directory_outpath = sys.argv[5]
max_follows = sys.argv[5]
max_likes = sys.argv[6]

#Since command lines arguments are parsed as string, split into list
n = len(filenames)
filenames_list = filenames[1:n-1]
filenames_list = filenames_list.split(',')
full_input_list = []
num_likes = 0
num_follows = 0

#Get full list of users
for f in filenames_list:

    #Get filepath
    file_inpath = directory_inpath + '/' + f

    #Read csv file with list of usernames
    #input_series = pd.read_csv(file_inpath)
    input_series = download_df_from_bucket(credentials_path='../InstagramBot-9cb1dfece602.json', bucket_path='insta-schools-bucket',filepath=file_inpath)
    input_list = input_series.iloc[:,1]

    #Create combined list
    full_input_list.append(input_list)

#Print number of unique users
full_input_list = list(set(chain.from_iterable(full_input_list)))
print("Number of unique users %s"%(len(full_input_list)))

#Print estimated finish time
max_mins = (min(int(max_follows),len(full_input_list))/2)*(1+5/60)
max_finish_time = datetime.now() + timedelta(minutes=max_mins)
print("Estimated finish time %s"%(max_finish_time))

#Login with details
driver = login(username=username,password=password)
print("Logged in successfully for account: %s"%username)
time.sleep(10)

#Run actions with given time breaks
secs = 60
user_list = full_input_list

liked_list = []
followed_list = []

error_liked_list = []
error_followed_list = []

count = 0

for user in user_list:

    count = count + 1

    if (count % 3) == 1:

        try:
            #Follow account
            already_followed,private_account,blocked,blocked_text = follow_user(username=user, driver=driver)

            #If Blocked then break loop
            if(blocked and blocked_text == 'Action Blocked'):
                print("Blocked! :(")
                print(blocked_text)
                break

            #If not blocked then add to list
            followed_list.append(user)

            if(already_followed):
                print("Already followed %s" % user)
            else:
                if(private_account):
                    print("Successfully followed private account %s" % user)
                else:
                    print("Successfully followed public account %s" % user)
                num_follows = num_follows + 1

        except Exception as e:
            error_followed_list.append(user)
            print("Couldn't follow user %s" % user)

    if (count % 3) == 2:

        try:
            already_liked, blocked = like_latest_posts(username=user, num_posts=1, driver=driver)

            # If Blocked then break loop
            if(blocked and blocked_text == 'Action Blocked'):
                print("Blocked! :(")
                print(blocked_text)
                break

            # If not blocked then add to list
            liked_list.append(user)

            if(already_liked):
                print("Already liked post by %s" % user)
            else:
                print("Successfully liked post by %s" % user)
                num_likes = num_likes + 1

        except Exception as e:
            error_liked_list.append(user)
            print("Couldn't like latest post by user %s" % user)

    if (count % 3) == 0:

        try:
            # Follow account
            already_followed,private_account,blocked,blocked_text = follow_user(username=user, driver=driver)

            #If Blocked then break loop
            if(blocked and blocked_text == 'Action Blocked'):
                print("Blocked! :(")
                print(blocked_text)
                break

            #If not blocked then add to list
            followed_list.append(user)

            if(already_followed):
                print("Already followed %s" % user)
            else:
                if(private_account):
                    print("Successfully followed private account %s" % user)
                else:
                    print("Successfully followed public account %s" % user)
                num_follows = num_follows + 1

        except Exception as e:
            error_followed_list.append(user)
            print("Couldn't follow user %s" % user)

    time.sleep(random.randint(5, 15))

    # Write to file each 2 attempted follows in case of early stopping
    complete_list = followed_list + liked_list
    incomplete_list = list(set(full_input_list) - set(complete_list))

    schoolname = directory_inpath
    base_outpath = directory_inpath + '/' + schoolname
    complete_outpath = base_outpath + '_complete.csv'
    incomplete_outpath = base_outpath + '_incomplete.csv'

    upload_df_to_bucket(credentials_path='../InstagramBot-9cb1dfece602.json', bucket_path='insta-schools-bucket',
                        filepath=complete_outpath, df=pd.Series(list(complete_list)))
    upload_df_to_bucket(credentials_path='../InstagramBot-9cb1dfece602.json', bucket_path='insta-schools-bucket',
                        filepath=incomplete_outpath, df=pd.Series(list(incomplete_list)))

    if (num_follows > int(max_follows) or num_likes > int(max_likes)):
        break

complete_list = followed_list + liked_list
incomplete_list = list(set(full_input_list) - set(complete_list))

#Get schoolname
#filename_split = directory_inpath.split('/')
#schoolname = filename_split[len(filename_split)-1]
schoolname = directory_inpath
#csv_filename = csv_filename.replace('.csv','')

# Write to file
#base_outpath = directory_outpath + '/' + schoolname
base_outpath = directory_inpath + '/' + schoolname
complete_outpath = base_outpath + '_complete_full.csv'
incomplete_outpath = base_outpath + '_incomplete_full.csv'
follows_outpath = base_outpath + '_followed_full.csv'
likes_outpath = base_outpath + '_liked_full.csv'
error_follows_outpath = base_outpath + '_error_followed_full.csv'
error_likes_outpath = base_outpath + '_error_liked_full.csv'

#pd.Series(list(complete_list)).to_csv(complete_outpath)
#pd.Series(list(incomplete_list)).to_csv(incomplete_outpath)
#pd.Series(list(followed_list)).to_csv(follows_outpath)
#pd.Series(list(liked_list)).to_csv(likes_outpath)
#pd.Series(list(error_followed_list)).to_csv(error_follows_outpath)
#pd.Series(list(error_liked_list)).to_csv(error_likes_outpath)

upload_df_to_bucket(credentials_path='../InstagramBot-9cb1dfece602.json', bucket_path='insta-schools-bucket',filepath=complete_outpath, df=pd.Series(list(complete_list)))
upload_df_to_bucket(credentials_path='../InstagramBot-9cb1dfece602.json', bucket_path='insta-schools-bucket',filepath=incomplete_outpath, df=pd.Series(list(incomplete_list)))