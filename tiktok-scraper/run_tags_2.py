import pandas as pd
import numpy as np
import os
import sys
from TikTokAPI import TikTokAPI
from datetime import datetime

search_term = sys.argv[1]

time_start = datetime.now()
hdr2 = False if os.path.isfile("%s_profiles_error_df.csv"%search_term) else True

profiles_df = pd.read_csv("%s_profiles.csv"%search_term)
profiles_df.drop('Unnamed: 0',axis=1,inplace=True)

first_run = False if os.path.isfile("%s_profiles_original.csv"%search_term) else True

if first_run:
    profiles_df_original = profiles_df.copy()
    profiles_df_original.to_csv("%s_profiles_original.csv"%search_term)

profiles_df.columns = ['name','tag']

api = TikTokAPI()
output_df = pd.DataFrame(columns=['tag','followingCount', 'followerCount', 'heartCount', 'videoCount','diggCount', 'heart', 'bio','nickname', 'link', 'median_views_25','median_views_50'])

count = 0
check_count = 0
error_list = []
user_list = []

for p in profiles_df['name']:
    
    hdr1 = False if os.path.isfile("%s_profiles_info_df.csv"%search_term) else True

    if count >= 100:
        break
    count = count + 1
    
    profiles_df_filtered = profiles_df.iloc[count:,:]

    try:
        user_videos = api.getVideosByUserName(p,count=50)
        check_count = 0
        user_views = [uv['stats']['playCount'] for uv in user_videos['items']]
        max_25 = np.min([len(user_views),25])
        median_views_25 = np.median(user_views[0:max_25])
        median_views_50 = np.median(user_views)
    
    except Exception as e:
        print("Error getting info for user: %s"%p)
        check_count = check_count + 1
        error_list.append(p)
        if check_count >= 3:
            print("Breaking cause there seems to be something wrong :/")
            break
        else:
            continue
    
    if median_views_50 >= 15000 or median_views_25 >= 15000:
        user_info = api.getUserByName(p)
        stats = user_info['userInfo']['stats']
        user_info_df = pd.DataFrame(stats,index=[p])
        user_info_df['name'] = profiles_df['name'].iloc[count-1]
        user_info_df['tag'] = profiles_df['tag'].iloc[count-1]
        
        try:
            user_info_df['bio'] = user_info['userInfo']['user']['signature']
        except Exception as e:
            user_info_df['bio'] = ""
        try:
            user_info_df['nickname'] = user_info['userInfo']['user']['nickname']
        except Exception as e:
            user_info_df['nickname'] = ""
        try:
            user_info_df['link'] = user_info['userInfo']['user']['bioLink']['link']
        except Exception as e:
            user_info_df['link'] = ""

        user_info_df['median_views_25'] = median_views_25
        user_info_df['median_views_50'] = median_views_50
        output_df = output_df.append(user_info_df)
        user_list.append(user_info_df)

    if count%10 == 0:
        output_df.to_csv("%s_profiles_info_df.csv"%search_term, mode='a', header=hdr1)
        rows_out = pd.read_csv("%s_profiles_info_df.csv"%search_term).shape[0]
        time_elapsed = (datetime.now() - time_start).seconds/60
        print("Finished writing %s eligible records out of %s processed in %f minutes"%(rows_out,count, time_elapsed))
        output_df = pd.DataFrame(columns=['tag','followingCount', 'followerCount', 'heartCount', 'videoCount','diggCount', 'heart', 'bio','nickname', 'link', 'median_views_25','median_views_50'])

output_df.to_csv("%s_profiles_info_df.csv"%search_term,mode='a', header=hdr1)
pd.DataFrame(error_list).to_csv("%s_profiles_error_df.csv"%search_term, mode='a', header=hdr2)
profiles_df_filtered.to_csv("%s_profiles.csv"%search_term)
time_elapsed = (datetime.now() - time_start).seconds/60
print("Finished writing %s eligible records out of %s processed in %f minutes"%(output_df.shape[0],count, time_elapsed))

