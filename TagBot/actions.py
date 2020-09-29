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
    chrome_options.add_argument("--disable-plugins-discovery");
    chrome_options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=chrome_options,executable_path='../chromedriver')
    #driver = webdriver.Chrome(options=chrome_options)
    driver.delete_all_cookies()
    driver.set_window_size(800, 800)
    driver.set_window_position(0, 0)

    #Use Chrome Driver & login in to instagram
    driver.implicitly_wait(1)
    driver.get('https://www.instagram.com/')
    user_input = driver.find_elements_by_css_selector("label input")

    #Login with supplied details
    user_input[0].send_keys(username)
    user_input[1].send_keys(password)

    login_button = driver.find_element_by_css_selector(".DhRcB")
    login_button.click()
    time.sleep(3)

    #Check and remove popup if there
    popup = check_popup(driver=driver)
    if(popup):
        print("Popup Removed")

    time.sleep(3)

    #Remove notifications popup
    notification_buttons = driver.find_elements_by_tag_name("button")
    notification_button_off = notification_buttons[len(notification_buttons) - 1]
    notification_button_off.click()

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

def follow_user(**kwargs):
    # Input arguments - instagram username + driver
    username = kwargs.get('username')
    driver = kwargs.get('driver')

    wait = WebDriverWait(driver, 5)
    
    #Verified Accounts have different url
    username = username.replace('Verified','')
    
    # Go to webpage
    base_url = 'https://www.instagram.com/'
    full_url = base_url + username
    driver.get(full_url)
    time.sleep(1)

    try:
        # Find follow button element for public profile
        follow_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "_5f5mN")))
        time.sleep(random.randint(5, 10))
        private_account = False

    except Exception as e:
        # Find follow button element for private profile
        follow_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".y3zKF")))
        time.sleep(random.randint(5, 10))
        private_account = True

    # If not already followed, then follow
    if (follow_button.text == 'Follow'):
        follow_button.click()
        already_followed = False
    else:
        already_followed = True

    #Check if blocked
    blocked,blocked_text = check_blocked(driver=driver)

    return (already_followed,private_account,blocked,blocked_text)


def dm_user(**kwargs):
    # Input arguments - instagram username + driver
    username = kwargs.get('username')
    message = kwargs.get('message')
    driver = kwargs.get('driver')

    wait = WebDriverWait(driver, 5)

    # Go to webpage
    base_url = 'https://www.instagram.com/'
    full_url = base_url + username
    driver.get(full_url)
    time.sleep(1)

    # Find follow button element
    follow_button = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "_5f5mN")))

    # If not already followed, then follow
    if (follow_button.text == 'Follow'):
        follow_button.click()

    # Find message button element and click
    message_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "._8A5w5")))
    message_button.click()
    time.sleep(1)

    # Send text
    text_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "textarea")))
    text_box.send_keys(message)
    time.sleep(1)

    send_button_list = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "sqdOP")))
    send_button = send_button_list[2]
    send_button.click()

    return ()


def like_post(**kwargs):
    # Input arguments - instagram username + driver
    postlink = kwargs.get('postlink')
    driver = kwargs.get('driver')

    wait = WebDriverWait(driver, 5)

    # Go to post
    base_url = 'https://www.instagram.com/'
    full_url = base_url + postlink
    driver.get(full_url)
    time.sleep(1)

    # Get like button
    like_button = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "button svg")))[1]
    time.sleep(random.randint(1, 3))

    # Try button since videos don't have number of likes
    try:
        # Original number of likes
        likes_tag_orig = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "Nm9Fw")))
        likes_num_orig = int(reduce(lambda x, y: x + y, re.findall(r'\d+', likes_tag_orig.text)))

        # Click Like button
        like_button.click()
        time.sleep(random.random() * 3)

        # Number of likes after clicking
        likes_tag_new = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "Nm9Fw")))
        likes_num_new = int(reduce(lambda x, y: x + y, re.findall(r'\d+', likes_tag_new.text)))
        time.sleep(random.random() * 3)

        # If already liked, will be unliked & number of likes will go down - in that case click like button again
        if (likes_num_new < likes_num_orig):
            like_button = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "button svg")))[1]
            time.sleep(random.random() * 3)

            # Click Like button
            like_button.click()
            already_liked= True
        else:
            already_liked= False

    except Exception as e:

        # Click Like button
        like_button.click()
        already_liked = False
        time.sleep(random.random() * 3)

    # Go back to user page
    driver.get(full_url)
    time.sleep(random.random() * 3)

    # Check if blocked
    blocked,blocked_text = check_blocked(driver=driver)

    return (already_liked,blocked,blocked_text)


def get_user_from_post(**kwargs):
    # Input arguments - instagram username + driver
    driver = kwargs.get('driver')
    postlink = kwargs.get('postlink')

    wait = WebDriverWait(driver, 5)

    # Go to post
    base_url = 'https://www.instagram.com/'
    full_url = base_url + postlink
    driver.get(full_url)
    time.sleep(1)

    username = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".e1e1d")))
    username_text = username.text

    return (username_text)
