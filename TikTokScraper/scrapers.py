import requests
from requests_html import HTMLSession
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from itertools import chain
from functools import reduce
import pandas as pd
import numpy as np
import time
import re
import random
from datetime import datetime
from datetime import timedelta
import multiprocessing as mp


def get_driver(**kwargs):
    # Open Chrome Driver and set relevant options
    opts = Options()
    opts.add_argument("user-agent=Googlebot")
    opts.add_argument('--headless')
    driver = webdriver.Chrome(options=opts)
    driver.implicitly_wait(1)

    return (driver)

def get_views_list_multi(profile_list, num_vids_list, max_vids):
    pool = mp.Pool(processes=4)
    results = pool.starmap(get_profile_avg_views_multi, [(p, n, max_vids) for p, n in zip(profile_list, num_vids_list)])

    return(results)

def check_page_status(**kwargs):

    driver = kwargs.get('driver')
    bad_page_string = '<html xmlns="http://www.w3.org/1999/xhtml"><head></head><body></body></html>'
    
    html_source = driver.page_source
    
    if(html_source == bad_page_string):
        bad_page = True
    else:
        bad_page = False

    return(bad_page)

def get_profile_avg_views(**kwargs):

    driver = kwargs.get('driver')
    profile = kwargs.get('profile')
    num_vids = kwargs.get('num_vids')
    max_vids = kwargs.get('max_vids')

    wait = WebDriverWait(driver, 3)
    driver.get(profile)
    time.sleep(2)

    start_time = datetime.now()
    
    num_views_old_set = set()
    num_views_new_set = set()
    num_views_old_list = []
    num_views_new_list = []
    
    bad_page = check_page_status(driver=driver)
    
    if(bad_page):
        print("Error getting page!")
        return(None)
    
    if(len(num_views_new_list) >= num_vids):

        print("No videos for user: %s"%profile)
        views_info_df = pd.DataFrame({'num_vids': [0]
                                     , 'min_views_overall': [0]
                                     , 'max_views_overall': [0]
                                     , 'mean_views_overall': [0]
                                     , 'median_views_overall': [0]
                                     , 'min_views_last10': [0]
                                     , 'max_views_last10': [0]
                                     , 'mean_views_last10': [0]
                                     , 'median_views_last10': [0]
                                     , 'min_views_last50': [0]
                                     , 'max_views_last50': [0]
                                     , 'mean_views_last50': [0]
                                     , 'median_views_last50': [0]})
        return(views_info_df)

    while (len(num_views_new_list) < num_vids):

        time.sleep(1)
        time_elapsed_secs = (datetime.now() - start_time).seconds

        if (time_elapsed_secs >= 3.5 or len(num_views_new_list) > max_vids):
            break
    
        # Create sets to store usernames
        try:
            num_views_new_list = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".video-bottom-info")))
        except Exception as e:
            print("No videos for user: %s"%profile)
            views_info_df = pd.DataFrame({'num_vids': [0]
                                         , 'min_views_overall': [0]
                                         , 'max_views_overall': [0]
                                         , 'mean_views_overall': [0]
                                         , 'median_views_overall': [0]
                                         , 'min_views_last10': [0]
                                         , 'max_views_last10': [0]
                                         , 'mean_views_last10': [0]
                                         , 'median_views_last10': [0]
                                         , 'min_views_last50': [0]
                                         , 'max_views_last50': [0]
                                         , 'mean_views_last50': [0]
                                         , 'median_views_last50': [0]})
            return(views_info_df)
        
        num_views_new_set = set([nv.text for nv in num_views_new_list])
        driver.execute_script("return arguments[0].scrollIntoView();", num_views_new_list[-1])

        while (len(num_views_old_set) < len(num_views_new_set) and len(num_views_new_list) <= max_vids):
            start_time = datetime.now()
            num_views_old_list = wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".video-bottom-info")))
            num_views_old_set = set([nv.text for nv in num_views_old_list])

            driver.execute_script("return arguments[0].scrollIntoView();", num_views_old_list[-1])
            time.sleep(0.1+len(num_views_new_set)/250)

            num_views_new_list = wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".video-bottom-info")))
            num_views_new_set = set([nv.text for nv in num_views_new_list])

    num_views_numeric_list = [eval(nv.replace('K', '*1000').replace('M', '*1000000')) for nv in
                              [nv.text for nv in num_views_new_list]]
    num_vids_actual = len(num_views_numeric_list)
    max_10 = np.min([10, num_vids_actual])
    max_25 = np.min([25, num_vids_actual])
    max_50 = np.min([50, num_vids_actual])

    min_views_overall = np.min(num_views_numeric_list)
    max_views_overall = np.max(num_views_numeric_list)
    mean_views_overall = np.mean(num_views_numeric_list)
    median_views_overall = np.median(num_views_numeric_list)
    min_views_last10 = np.min(num_views_numeric_list[0:max_10])
    max_views_last10 = np.max(num_views_numeric_list[0:max_10])
    mean_views_last10 = np.mean(num_views_numeric_list[0:max_10])
    median_views_last10 = np.median(num_views_numeric_list[0:max_10])
    min_views_last25 = np.min(num_views_numeric_list[0:max_25])
    max_views_last25 = np.max(num_views_numeric_list[0:max_25])
    mean_views_last25 = np.mean(num_views_numeric_list[0:max_25])
    median_views_last25 = np.median(num_views_numeric_list[0:max_25])
    min_views_last50 = np.min(num_views_numeric_list[0:max_50])
    max_views_last50 = np.max(num_views_numeric_list[0:max_50])
    mean_views_last50 = np.mean(num_views_numeric_list[0:max_50])
    median_views_last50 = np.median(num_views_numeric_list[0:max_50])

    views_info_df = pd.DataFrame({'num_vids': [num_vids_actual]
                                     , 'min_views_overall': [min_views_overall]
                                     , 'max_views_overall': [max_views_overall]
                                     , 'mean_views_overall': [mean_views_overall]
                                     , 'median_views_overall': [median_views_overall]
                                     , 'min_views_last10': [min_views_last10]
                                     , 'max_views_last10': [max_views_last10]
                                     , 'mean_views_last10': [mean_views_last10]
                                     , 'median_views_last10': [median_views_last10]
                                     , 'min_views_last25': [min_views_last25]
                                     , 'max_views_last25': [max_views_last25]
                                     , 'mean_views_last25': [mean_views_last25]
                                     , 'median_views_last25': [median_views_last25]
                                     , 'min_views_last50': [min_views_last50]
                                     , 'max_views_last50': [max_views_last50]
                                     , 'mean_views_last50': [mean_views_last50]
                                     , 'median_views_last50': [median_views_last50]})

    return (views_info_df)


def get_profile_avg_views_multi(profile, num_vids, max_vids):
    # driver = kwargs.get('driver')
    # profile = kwargs.get('profile')
    # num_vids = kwargs.get('num_vids')
    # max_vids = kwargs.get('max_vids')

    driver = get_driver()
    wait = WebDriverWait(driver, 3)
    driver.get(profile)
    time.sleep(3)

    start_time = datetime.now()

    num_views_old_set = set()
    num_views_new_set = set()

    while (len(num_views_old_set) < num_vids):

        time.sleep(2)
        time_elapsed_secs = (datetime.now() - start_time).seconds

        if (time_elapsed_secs >= 5 or len(num_views_new_set) > max_vids):
            break

        # Create sets to store usernames
        num_views_new_list = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".video-bottom-info")))
        num_views_new_set = set([nv.text for nv in num_views_new_list])
        driver.execute_script("return arguments[0].scrollIntoView();", num_views_new_list[-1])

        while (len(num_views_old_set) < len(num_views_new_set) and len(num_views_new_set) <= max_vids):
            start_time = datetime.now()
            num_views_old_list = wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".video-bottom-info")))
            num_views_old_set = set([nv.text for nv in num_views_old_list])

            driver.execute_script("return arguments[0].scrollIntoView();", num_views_old_list[-1])
            time.sleep(1)

            num_views_new_list = wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".video-bottom-info")))
            num_views_new_set = set([nv.text for nv in num_views_new_list])

    driver.quit()

    num_views_numeric_list = [eval(nv.replace('K', '*1000').replace('M', '*1000000')) for nv in
                              [nv.text for nv in num_views_new_list]]
    num_vids_actual = len(num_views_numeric_list)

    max_10 = np.max([10, num_vids_actual])
    max_50 = np.max([50, num_vids_actual])

    min_views_overall = np.min(num_views_numeric_list)
    max_views_overall = np.max(num_views_numeric_list)
    mean_views_overall = np.mean(num_views_numeric_list)
    median_views_overall = np.median(num_views_numeric_list)
    min_views_last10 = np.min(num_views_numeric_list[0:max_10])
    max_views_last10 = np.max(num_views_numeric_list[0:max_10])
    mean_views_last10 = np.mean(num_views_numeric_list[0:max_10])
    median_views_last10 = np.median(num_views_numeric_list[0:max_10])
    min_views_last50 = np.min(num_views_numeric_list[0:max_50])
    max_views_last50 = np.max(num_views_numeric_list[0:max_50])
    mean_views_last50 = np.mean(num_views_numeric_list[0:max_50])
    median_views_last50 = np.median(num_views_numeric_list[0:max_50])

    views_info_df = pd.DataFrame({'num_vids': [num_vids_actual]
                                     , 'min_views_overall': [min_views_overall]
                                     , 'max_views_overall': [max_views_overall]
                                     , 'mean_views_overall': [mean_views_overall]
                                     , 'median_views_overall': [median_views_overall]
                                     , 'min_views_last10': [min_views_last10]
                                     , 'max_views_last10': [max_views_last10]
                                     , 'mean_views_last10': [mean_views_last10]
                                     , 'median_views_last10': [median_views_last10]
                                     , 'min_views_last50': [min_views_last50]
                                     , 'max_views_last50': [max_views_last50]
                                     , 'mean_views_last50': [mean_views_last50]
                                     , 'median_views_last50': [median_views_last50]})

    return (views_info_df)
