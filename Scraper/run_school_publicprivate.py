import sys
import pandas as pd
from scrapers import *
from storage_functions import *
import time
from datetime import datetime
from datetime import timedelta

filenames = sys.argv[1]
directory_inpath = sys.argv[2]
outname = sys.argv[3]

#Since command lines arguments are parsed as string, split into list
n = len(filenames)
filenames_list = filenames[1:n-1]
filenames_list = filenames_list.split(',')
full_input_list = []

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
max_mins = (len(full_input_list)*13)
max_finish_time = datetime.now() + timedelta(minutes=max_mins)
print("Estimated finish time %s"%(max_finish_time))

#Login with details
driver = login()
print("Logged in successfully for account")
time.sleep(10)

#Dataframe to store output
full_user_out_df = pd.DataFrame(columns=['username', 'status'])

# Set output name
outpath = directory_inpath + '/' + outname + '.csv'
incomplete_outpath = directory_inpath + '/' + outname + '_incomplete.csv'

user_list = []
count = 0
start_time = time.time()

#Loop through list of users
for u in full_input_list:
    count = count + 1

    #Get status for specific user
    user_status = get_private_public_user_nologin(username=u,driver=driver)

    #Break if error/blocked most likely
    if user_status  == 'Error':
        print("Blocked!")
        break

    user_dict = {'username': ['https://www.instagram.com/' + u], 'status': [user_status]}
    user_out_df = pd.DataFrame(user_dict)
    user_list.append(u)
    full_user_out_df = full_user_out_df.append(user_out_df)

    #Print
    elapsed_time = (time.time() - start_time)/60
    print("Finished writing record %s for user %s in %s mins"%(count,u,elapsed_time))

    #Get list of remaining users
    incomplete_list = list(set(full_input_list) - set(user_list))

    #Write to bucket every iteration in case of early stopping
    upload_df_to_bucket(credentials_path='../InstagramBot-9cb1dfece602.json', bucket_path='insta-schools-bucket',filepath=outpath, df=full_user_out_df)
    upload_df_to_bucket(credentials_path='../InstagramBot-9cb1dfece602.json', bucket_path='insta-schools-bucket',
                        filepath=incomplete_outpath, df=pd.Series(list(incomplete_list)))