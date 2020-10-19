import sys
import asyncio
import time
import re
import pandas as pd
import numpy as np
from datetime import datetime
from pyppeteer import launch
from pyppeteer_stealth import stealth

username = sys.argv[1]

output_df = pd.DataFrame(columns=['followingCount', 'followerCount', 'heartCount', 'videoCount',
                                  'diggCount', 'bio', 'name', 'median_views_25',
                                  'median_views_50'])

def get_video_views(html):
    start_string = '<div class="tt-feed">'
    end_string = 'href="https://wa.me/'
    html_start = html[html.find(start_string):]
    html_end = html_start[:html_start.find(end_string)]
    video_counts = re.findall( r'video-count\">.*?<', html_end)
    video_counts_clean = [eval(vc[len('video-count">'):-1].replace('K','000').replace('M','000000')) for vc in video_counts]

    return video_counts_clean

def get_user_stats(html):
    user_stats = re.findall(r'\"stats\":.*?}', html)
    user_stats_clean = user_stats[0][len('"stats":'):]
    
    return eval(user_stats_clean)

def get_user_info(html):
    user_info = re.findall(r'\"user\":.*?}', html)
    user_info_clean = user_info[0][len('"user":'):]
    user_info_clean = user_info_clean.replace('false','False').replace('true','True')
    
    return eval(user_info_clean)

async def main(username):
    check_count = 0
    usernames_list = []
    browser = await launch(headless=True)
    page = await browser.newPage()
    await stealth(page)
    
    await page.goto('https://tiktok.com/@%s'%username)
    time.sleep(1)
    await page.evaluate("""{window.scrollBy(0, document.body.scrollHeight);}""")
    time.sleep(1)
    
    html = await page.evaluate("""() => new XMLSerializer().serializeToString(document)""")
    video_counts = get_video_views(html)
    user_stats = get_user_stats(html)
    user_info = get_user_info(html)
    
    max_25 = np.min([len(video_counts),25])
    median_views_25 = np.median(video_counts[0:max_25])
    median_views_50 = np.median(video_counts)
    
    user_info_df = pd.DataFrame(user_stats,index=[username])
    user_info_df['bio'] = user_info['signature']
    user_info_df['name'] = user_info['nickname']
    user_info_df['median_views_25'] = median_views_25
    user_info_df['median_views_50'] = median_views_50
    
    if len(video_counts) == 0 and html.find('<meta name="keywords" content="TikTok security verification" />') != -1:
        print("Security captcha! Waiting 10 seconds")
        time.sleep(10)
        page = await browser.newPage()
        await stealth(page)
    
    return user_info_df

def byUsername(username):
    return asyncio.get_event_loop().run_until_complete(main(username))

user_info_df = byUsername(username)
print(user_info_df)
print(user_info_df.columns)
