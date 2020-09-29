import requests
from requests_html import HTMLSession
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import StaleElementReferenceException
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

def login(**kwargs):

    # Input arguments - instagram username + password
    username = kwargs.get('username')
    password = kwargs.get('password')

    #Set Chrome Options to look like a real person
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'
    chrome_options = Options()
    #chrome_options.add_argument("--headless")
    chrome_options.add_argument(f'user-agent={user_agent}')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--profile-directory=Default')
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--disable-plugins-discovery")
    #chrome_options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=chrome_options,executable_path='../chromedriver')
    #driver = webdriver.Chrome(options=chrome_options)
    driver.delete_all_cookies()
    #driver.set_window_size(800, 800)
    #driver.set_window_position(0, 0)

    #Use Chrome Driver & login in to instagram
    wait = WebDriverWait(driver, 120)

    driver.get('https://www.instagram.com/')

    user_input = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "label input")))

    #Get details if supplied otherwise use mine
    if('username' in kwargs and username is not None):
        user_input[0].send_keys(username)
    else:
        user_input[0].send_keys('nishant.patra1@gmail.com')

    if('password' in kwargs and password is not None):
        user_input[1].send_keys(password)
    else:
        user_input[1].send_keys('levron')

    #Login with supplied details
    login_button = driver.find_element_by_css_selector(".DhRcB")
    login_button.click()
    time.sleep(3)

    #Check and remove popup if there
    popup = check_popup(driver=driver)
    if(popup):
        print("Popup Removed")

    time.sleep(3)

    #Check and remove notifications popup
    notification = check_notification(driver=driver)
    if(notification):
        print("Notification Removed")

    return(driver)

def check_blocked(**kwargs):
    #Input argument - driver
    driver = kwargs.get('driver')

    wait = WebDriverWait(driver, 3)
    #Check if blocked
    try:
        blocked_notification = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "_08v79")))
        blocked_text = blocked_notification.find_element_by_tag_name("h3").text
        blocked = True
    except Exception as e:
        blocked = False
        blocked_text = 'Not Blocked :)'

    return(blocked,blocked_text)


def check_notification(**kwargs):
    # Input argument - driver
    driver = kwargs.get('driver')

    wait = WebDriverWait(driver, 3)

    # Check if popup, click ok to continue if so
    try:
        browser_notification = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "aOOlW")))
        notification_button_off = browser_notification[len(browser_notification) - 1]
        notification_button_off.click()
        notification = True

    except Exception as e:
        notification = False

    return(notification)

def check_popup(**kwargs):
    # Input argument - driver
    driver = kwargs.get('driver')

    wait = WebDriverWait(driver, 3)

    # Check if popup, click ok to continue if so
    try:
        browser_notification = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "cmbtv")))
        browser_notification_button = browser_notification.find_element_by_class_name("sqdOP")
        popup = True

        if (browser_notification_button.text == 'Not Now'):
            browser_notification_button.click()
    except Exception as e:
        popup = False

    return (popup)

def unfollow_user_2(**kwargs):

    # Input arguments - instagram username + driver
    driver = kwargs.get('driver')
    following_element = kwargs.get('following_element')

    wait = WebDriverWait(driver, 10)

    #Click following and confirm unfollow
    following_element.click()
    unfollow_button = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'aOOlW')))
    unfollow_button.click()

    return(driver)


def unfollow_users(**kwargs):
    # Input arguments - instagram username + driver
    driver = kwargs.get('driver')
    page_link = kwargs.get('page_link')
    unfollow_list = kwargs.get('unfollow_list')

    # Set wait time for expected conditions and implicit wait
    wait = WebDriverWait(driver, 10)
    driver.implicitly_wait(2)
    start_time = time.time()

    # Go to webpage
    base_url = 'https://www.instagram.com/'
    full_url = base_url + page_link
    driver.get(full_url)

    # Create sets to store usernames
    following_user_old_set = set()
    following_user_new_set = set()
    following_elements_old_set = set()
    following_elements_new_set = set()

    unfollowed_list = []
    error_unfollowed_list = []

    # Open followers popup
    buttons_list = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, '-nal3 ')))
    following_popup = buttons_list[2]
    num_following = int(reduce(lambda x, y: x + y, re.findall(r'\d+', following_popup.text)))
    following_popup.click()

    while (len(following_user_new_set) <= num_following):

         # Get initial elements
        followers_frame = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'isgrP')))
        elements_old = followers_frame.find_elements_by_tag_name('li')

        following_user_old_list = [e.find_elements_by_tag_name("div")[0].text[0:e.find_elements_by_tag_name("div")[0].text.find('\n')] for e in elements_old]
        following_user_old_set.update(following_user_old_list)
        following_user_new_set.update(following_user_old_list)

        for e in elements_old:
            start_time = time.time()
            unfollow_username = e.find_elements_by_tag_name("div")[0].text[0:e.find_elements_by_tag_name("div")[0].text.find('\n')]
            following_button = e.find_elements_by_tag_name("div")[len(e.find_elements_by_tag_name("div")) - 1]

            if(unfollow_username in unfollow_list and unfollow_username not in unfollowed_list):
                try:
                    unfollow_user_2(driver=driver,following_element=following_button)
                    unfollowed_list.append(unfollow_username)
                    print("Unfollowed %s"%unfollow_username)
                    time.sleep(1)
                except StaleElementReferenceException as see:
                    error_unfollowed_list.append(unfollow_username)
                    print("Error unfollowing %s" % unfollow_username)
                    time.sleep(1)


        # Scroll down to load new followers
        driver.execute_script('arguments[0].scrollTop = arguments[0].scrollTop + arguments[0].offsetHeight;',followers_frame)
        time.sleep(2)

        # Get new elements and update new set only!
        followers_frame = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'isgrP')))
        elements_new = followers_frame.find_elements_by_tag_name('li')
        following_user_new_list = [e.find_elements_by_tag_name("div")[0].text[0:e.find_elements_by_tag_name("div")[0].text.find('\n')] for e in elements_old]
        following_user_new_set.update(following_user_new_list)

        #print(len(following_user_new_set))

        # Break loop if no more scrolls available
        if (len(following_user_new_set) >= num_following):
            print("End break")
            break

        # Break loop if timeout
        if (time.time() - start_time > 600):
            print("Time break")
            break

        while (len(following_user_new_set) > len(following_user_old_set)):

            following_user_old_set.update(following_user_new_set)
            following_elements_old_set.update(following_elements_new_set)

            # Scroll down to load new followers
            driver.execute_script("return arguments[0].scrollIntoView();", elements_new[-1])
            time.sleep(3)

            # Get new elements
            followers_frame = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'isgrP')))
            elements_new = followers_frame.find_elements_by_tag_name('li')
            following_user_new_list = [e.find_elements_by_tag_name("div")[0].text[0:e.find_elements_by_tag_name("div")[0].text.find('\n')] for e in elements_old]
            following_user_new_set.update(following_user_new_list)
            following_elements_new_set.update(elements_new)

            delta_elements = following_elements_new_set - following_elements_old_set

            for e in delta_elements:
                start_time = time.time()
                unfollow_username = e.find_elements_by_tag_name("div")[0].text[0:e.find_elements_by_tag_name("div")[0].text.find('\n')]
                following_button = e.find_elements_by_tag_name("div")[len(e.find_elements_by_tag_name("div")) - 1]

                if (unfollow_username in unfollow_list and unfollow_username not in unfollowed_list):
                    try:
                        unfollow_user(driver=driver, following_element=following_button)
                        unfollowed_list.append(unfollow_username)
                        print("Unfollowed %s" % unfollow_username)
                        time.sleep(1)
                    except StaleElementReferenceException as see:
                        error_unfollowed_list.append(unfollow_username)
                        print("Error unfollowing %s" % unfollow_username)
                        time.sleep(1)

            start_time = time.time()

            #print(len(following_user_new_set))

            # Break loop if no more scrolls available
            if (len(following_user_new_set) >= num_following):
                print("End break")
                break

        #print(len(following_user_new_set))

    return (unfollowed_list,error_unfollowed_list)

def unfollow_user(**kwargs):
    # Input arguments - instagram username + driver
    username = kwargs.get('username')
    driver = kwargs.get('driver')

    wait = WebDriverWait(driver, 5)

    # Go to webpage
    base_url = 'https://www.instagram.com/'
    full_url = base_url + username
    driver.get(full_url)
    time.sleep(1)

    # Find follow button element for public profile
    unfollow_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "_5f5mN")))
    time.sleep(random.randint(1, 5))

    # If already followed, then unfollow and confirm
    if (unfollow_button.text != 'Follow'):
        #Click unfollow button and get confrm button
        unfollow_button.click()
        unfollow_confirm_button = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'aOOlW')))
        time.sleep(random.randint(1, 3))

        if(unfollow_confirm_button.text == 'Unfollow'):
            #Confirm click
            unfollow_confirm_button.click()
            not_followed = False
    else:
        not_followed = True

    #Check if blocked
    blocked,blocked_text = check_blocked(driver=driver)

    return (not_followed,blocked,blocked_text)