from TikTokApi import TikTokApi
import sys
import time
from datetime import datetime
import numpy as np
import pandas as pd
import sys
import asyncio
import time
import re
import pandas as pd
from datetime import datetime
from pyppeteer import launch
from pyppeteer_stealth import stealth

search_term = sys.argv[1]
time_start = datetime.now()

async def get_usernames(browser,page):
    html = await page.evaluate("""() => new XMLSerializer().serializeToString(document)""")
    start_string = '<div class="tt-feed">'
    end_string = 'href="https://wa.me/'
    html_start = html[html.find(start_string):]
    html_end = html_start[:html_start.find(end_string)]
    urls = re.findall( r'href=\".*?\"', html_end)
    if len(urls) == 0 and html.find('<meta name="keywords" content="TikTok security verification" />') != -1:
        print("Security captcha! Waiting 10 seconds")
        time.sleep(10)
        page = await browser.newPage()
        await stealth(page)
    
    return page,urls

async def getHashtag(tag_name):
    scrolls = 0
    check_count = 0
    usernames_list = []
    browser = await launch(headless=True)
    page = await browser.newPage()
    await stealth(page)
    await page.goto('https://tiktok.com/tag/%s'%tag_name)
    time.sleep(1)
    
    videos_list_old = await page.querySelectorAll('.video-card-mask')
    videos_list_old_set = set(videos_list_old)
    
    await page.evaluate("""{window.scrollBy(0, document.body.scrollHeight);}""")
    time.sleep(1)
    videos_list_new = await page.querySelectorAll('.video-card-mask')
    videos_list_new_set = set(videos_list_new) | videos_list_old_set
    
    time_break = False
    
    
    while len(videos_list_old_set) <= len(videos_list_new_set):
        #Get video elements
        videos_list_old = await page.querySelectorAll('.video-card-mask')
        videos_list_old_set = videos_list_new_set | set(videos_list_old)
        
        page,usernames = await get_usernames(browser,page)
        new_usernames = set(usernames) - set(usernames_list)
        usernames_list = usernames_list + list(new_usernames)
        
        if len(new_usernames) == 0:
            if check_count > 5:
                break
            check_count = check_count + 1
            time.sleep(3)
        else:
            check_count = 0
        scrolls = scrolls + 1
        
        df = pd.DataFrame(usernames_list)
        df.to_csv("%s_usernames_df.csv"%tag_name)
        time_elapsed = (datetime.now() - time_start).seconds/60
        print("Finished %s records in %f minutes"%(df.shape[0],time_elapsed))
        await page.evaluate("""{window.scrollBy(0, document.body.scrollHeight);}""")
        time.sleep(1)
        videos_list_new = await page.querySelectorAll('.video-card-mask')
        videos_list_new_set = set(videos_list_new) | videos_list_old_set
    
    page = await browser.newPage()
    
    return usernames_list

def byHashtag(input_tag):
    return asyncio.get_event_loop().run_until_complete(getHashtag(input_tag))

time_start = datetime.now()
api = TikTokApi()

hashtags = api.search_for_hashtags(search_term,count=500)
hashtags_unique = list(set([h['challenge']['title'] for h in hashtags]))

print("Found %s distinct hashtags related to search term!"%len(hashtags_unique))
pd.DataFrame(hashtags_unique).to_csv("%s_hashtags.csv"%search_term)
videos_list_full = []

for h in hashtags_unique:
    videos_list = byHashtag(h)
    videos_tups_list = [(v,h) for v in videos_list]
    videos_list_full = videos_list_full + videos_tups_list

videos_list_clean = list(set([(re.search(r'@.*?/',v).group(0)[1:-1],t) for (v,t) in videos_list_full if v != 'href="/feedback?lang=en"' and re.search(r'@.*?/',v) is not None]))

print("Found %s distinct profiles based on hashtags!"%len(videos_list_clean))

search_users = api.search_for_users(search_term, count=1000)
search_users_list = list(set([se['user']['uniqueId'] for se in search_users]))
search_users_tups_list = [(su,'Unknown') for su in search_users_list]

usernames_full = videos_list_clean + search_users_tups_list

print("Found %s distinct profiles related to search term!"%len(usernames_full))
pd.DataFrame(usernames_full).to_csv("%s_profiles.csv"%search_term)
