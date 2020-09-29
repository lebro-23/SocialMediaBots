import sys
import pandas as pd
from scrapers import *
from storage_functions import *

page_links = sys.argv[1]
directory_outpath = sys.argv[2]

#Since command lines arguments are parsed as string, split into list
n = len(page_links)
page_links_list = page_links[1:n-1]
page_links_list = page_links_list.split(',')

#Login
driver = login()

for p in page_links_list:

    #Get followers for specific page
    output_list = get_page_followers(page_link=p,driver=driver)

    #Write to file
    #outpath = directory_outpath + '/' + p + '.csv'
    #pd.Series(list(output_list)).to_csv(outpath)

    outpath = directory_outpath + '/' + p + '.csv'
    df = pd.Series(list(output_list))
    upload_df_to_bucket(credentials_path='../InstagramBot-9cb1dfece602.json', bucket_path='insta-schools-bucket',filepath=outpath, df=df)
