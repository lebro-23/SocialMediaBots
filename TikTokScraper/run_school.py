import sys
import pandas as pd
from scrapers import *
from storage_functions import *

file_inpath = sys.argv[1]
file_outpath = sys.argv[2]
multi = sys.argv[3]
max_vids = int(sys.argv[4])

if multi == 'True':
    multi = True
elif multi == 'False':
    multi = False
else:
    print("Please enter valid option 3 (Parallel/Serial)")

#tags_profiles_df = download_df_from_bucket(credentials_path='../InstagramBot-9cb1dfece602.json',bucket_path='insta-schools-bucket', filepath=file_inpath)
tags_profiles_df = pd.read_csv(file_inpath)

#Login
driver = get_driver()

start_time = datetime.now()
count = 0
error_count = 0
num_profiles = 5

full_df = pd.DataFrame(columns=['num_vids', 'min_views_overall', 'max_views_overall', 'mean_views_overall','median_views_overall','min_views_last10', 'max_views_last10', 'mean_views_last10', 'median_views_last10','min_views_last25','max_views_last25', 'mean_views_last25', 'median_views_last25','min_views_last50','max_views_last50', 'mean_views_last50', 'median_views_last50','profile'])
error_user_list = []
num_records = tags_profiles_df['username'].shape[0]
print(num_records)

num_iterations = int(np.floor(num_records/num_profiles))

if multi:
    print("Running parralel with multiple cpus!")
    for i in range(0,num_iterations):

        if(i == num_iterations-1):
            i_end = num_records-1
        else:
            i_end = i+num_profiles-1

        profile_list = tags_profiles_df['username'].iloc[i:i_end]
        num_vids_list = tags_profiles_df['videoCount'].iloc[i:i_end]

        multi_results = get_views_list_multi(profile_list,num_vids_list,max_vids)

        full_df = full_df.append(pd.concat(multi_results))
        count = count + (count+1)*num_profiles

        if count > 0 and count % 1 == 0:
            time_elapsed = (datetime.now() - start_time).seconds / 60
            estimated_finish_time = datetime.now() + timedelta(minutes=(num_records / count) * time_elapsed)
            print("Finished %s of %s records in %s minutes. %s Records remaining, estimated to finish at: %s" % (
            count, num_records, time_elapsed, num_records - count, estimated_finish_time))
            #upload_df_to_bucket(credentials_path='../InstagramBot-9cb1dfece602.json', bucket_path='insta-schools-bucket',filepath=file_outpath, df=full_df)
            full_df.to_csv(file_outpath)

else:
    print("Running serially!")
    for profile in tags_profiles_df['username']:
        
        try:
            num_vids = tags_profiles_df['videoCount'].iloc[count]
            row_df = get_profile_avg_views(driver=driver, profile=profile, num_vids=num_vids, max_vids=max_vids)
            row_df['profile'] = profile
            error_count = 0
            #print("Finished getting user: %s, number of videos = %s" % (profile, row_df['num_vids'][0]))

        except Exception as e:
            if(error_count >= 10):
                error_user_list.append(profile)
                error_count = 0
                full_df.to_csv(file_outpath)
                pd.Series(error_user_list).to_csv(file_outpath+'_errorlist.csv')
                print("Blocked")
                break

            row_df = pd.DataFrame(columns=['num_vids', 'min_views_overall', 'max_views_overall', 'mean_views_overall','median_views_overall','min_views_last10', 'max_views_last10', 'mean_views_last10', 'median_views_last10','min_views_last25','max_views_last25', 'mean_views_last25', 'median_views_last25','min_views_last50','max_views_last50', 'mean_views_last50', 'median_views_last50','profile'])
            error_count = error_count + 1
            error_user_list.append(profile)
            print("Error writing getting: %s" % (profile))

        full_df = full_df.append(row_df)
        count = count + 1

        if count % 10 == 0:
            time_elapsed = (datetime.now() - start_time).seconds / 60
            estimated_finish_time = datetime.now() + timedelta(minutes=(num_records / count) * time_elapsed)
            print("Finished %s of %s records in %s minutes. %s Records remaining, estimated to finish at: %s" % (
            count, num_records, time_elapsed, num_records - count, estimated_finish_time))
            #upload_df_to_bucket(credentials_path='../InstagramBot-9cb1dfece602.json', bucket_path='insta-schools-bucket',filepath=file_outpath, df=full_df)
            full_df.to_csv(file_outpath)
