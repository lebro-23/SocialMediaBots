from itertools import chain
from functools import reduce
import pandas as pd
import numpy as np
import time
import re
import random
import numpy as np
import asyncio
import re
from datetime import datetime
from pyppeteer import launch
from pyppeteer_stealth import stealth

async def login(**kwargs):
    
    # Input arguments - instagram username + password
    username = kwargs.get('username')
    password = kwargs.get('password')
    
    #Use Chrome Driver & login in to instagram
    browser = await launch(headless=False)
    page = await browser.newPage()
    await stealth(page)
    await page.goto('https://www.instagram.com/')
    time.sleep(1)
    
    user_input = await page.querySelectorAll('label input')

    #Login with supplied details
    await user_input[0].type(username)
    await user_input[1].type(password)

    await page.click('.DhRcB')
    await page.waitForNavigation()
    time.sleep(3)

    return browser, page

async def follow_user(**kwargs):
    # Input arguments - instagram username + driver
    username = kwargs.get('username')
    browser = kwargs.get('browser')
    page = kwargs.get('page')

    #Verified Accounts have different url
    username = username.replace('Verified','')

    # Go to webpage
    base_url = 'https://www.instagram.com/'
    full_url = base_url + username
    await page.goto(full_url)
    time.sleep(1)

    # Find follow button element for private profile
    follow_button = await page.xpath("//button[contains(., 'Follow')]")
    time.sleep(random.randint(5, 10))

    # If not already followed, then follow
    follow_button_text = await page.evaluate("""element => element.textContent""", follow_button)

    if (follow_button_text == 'Follow'):
        await follow_button.click()
        already_followed = False
    else:
        already_followed = True

    #Check if blocked
    #blocked,blocked_text = check_blocked(driver=driver)

    return already_followed

async def follow_image_user(**kwargs):

    browser = kwargs.get('browser')
    page = kwargs.get('page')
    image_url = kwargs.get('image_url')
    blocked = kwargs.get('blocked')

    base_url = 'https://www.instagram.com/p/'
    full_url = base_url + image_url

    page = await browser.newPage()
    await stealth(page)
    await page.goto(full_url)
    time.sleep(1)

    # Find follow button element for private profile
    follow_element = await page.querySelector('.y3zKF')
    user_element = await page.querySelector('.ZIAjV')

    # If not already followed, then follow
    follow_text = await page.evaluate("""element => element.textContent""", follow_element)
    username = await page.evaluate("""element => element.textContent""", user_element)

    if (follow_text == 'Follow'):
        await follow_element.click()
        time.sleep(2)
        # Find follow button element for private profile
        follow_element = await page.querySelector('.y3zKF')
        follow_text = await page.evaluate("""element => element.textContent""", follow_element)

        if (follow_text == 'Follow'):
            if(blocked):
                return username, 'Blocked'
            blocked = True
            print("Can't follow user." "Waiting 60secs for Instagram")
            time.sleep(60)
            await page.close()
            already_followed = await follow_image_user(browser=browser,page=page,image_url=image_url,blocked=blocked)
        else:
            already_followed = False
            print("Successfully followed user: %s"%username)
    else:
        already_followed = True

    time.sleep(random.randint(1, 3))

    await page.close()
    #Check if blocked
    #blocked,blocked_text = check_blocked(driver=driver)

    return username,already_followed

async def get_usernames(browser, page, videos_set):

    urls_list = []

    for v in videos_set:
        browser, page, url = await get_username(browser, page, v)
        urls_list = urls_list + url

    # Replace
    if len(urls_list) == 0 and html.find('<meta name="keywords" content="TikTok security verification" />') != -1:
        print("Security captcha! Waiting 10 seconds")
        time.sleep(10)
        page = await browser.newPage()
        await stealth(page)

    return browser, page, urls_list

async def get_username(browser, page, element):

    html = await page.evaluate("""element => element.innerHTML""", element)
    url = re.findall(r'href=\".*?\"', html)
    url = [u[len('href="/p/'):-1] for u in url]

    return browser, page, url

async def run_tag(**kwargs):

    tag = kwargs.get('tag')
    browser = kwargs.get('browser')
    page = kwargs.get('page')

    time_start = datetime.now()

    await page.goto('https://www.instagram.com/explore/tags/%s' % tag)
    time.sleep(1)

    videos_list_old = await page.querySelectorAll('.video-card-mask')
    videos_list_old_set = set(videos_list_old)
    urls_list = []
    user_list = []
    error_url_list = []
    check_count = 0
    scrolls = 0
    blocked = False
    already_followed = True

    await page.evaluate("""{window.scrollBy(0, document.body.scrollHeight);}""")
    time.sleep(1)
    videos_list_new = await page.xpath('//*[contains(concat( " ", @class, " " ), concat( " ", "v1Nh3 kIKUG  _bz0w", " " ))]')
    videos_list_new_set = set(videos_list_new) | videos_list_old_set

    while len(videos_list_old_set) <= len(videos_list_new_set):
        # Get video elements
        videos_list_old = await page.xpath('//*[contains(concat( " ", @class, " " ), concat( " ", "v1Nh3 kIKUG  _bz0w", " " ))]')
        videos_list_old_set = videos_list_new_set | set(videos_list_old)

        browser,page,urls = await get_usernames(browser, page, videos_list_old_set)
        new_urls = set(urls) - set(urls_list)
        urls_list = urls_list + list(new_urls)

        for u in new_urls:
            try:
                user, already_followed = await follow_image_user(browser=browser,image_url=u,blocked=blocked)
            except Exception as e:
                print("Error getting url: %s"%u)
                error_url_list.append(u)

            if not already_followed:
                user_list.append(user)

            if len(user_list) % 10 == 0:
                urls_df = pd.DataFrame(urls_list)
                users_df = pd.DataFrame(user_list)
                error_url_df = pd.DataFrame(error_url_list)
                urls_df.to_csv("%s_urls_df.csv" % tag)
                users_df.to_csv("%s_users_df.csv" % tag)
                error_url_df.to_csv("%s_error_url_df.csv" % tag)
                time_elapsed = (datetime.now() - time_start).seconds / 60
                print("Finished %s records in %f minutes" % (users_df.shape[0], time_elapsed))

        urls_df = pd.DataFrame(urls_list)
        users_df = pd.DataFrame(user_list)
        error_url_df = pd.DataFrame(error_url_list)
        urls_df.to_csv("%s_urls_df.csv" % tag)
        users_df.to_csv("%s_users_df.csv" % tag)
        error_url_df.to_csv("%s_error_url_df.csv" % tag)
        time_elapsed = (datetime.now() - time_start).seconds / 60
        print("Finished %s records in %f minutes" % (users_df.shape[0], time_elapsed))

        if len(new_urls) == 0:
            if check_count > 5:
                break
            check_count = check_count + 1
            time.sleep(3)
        else:
            check_count = 0
        scrolls = scrolls + 1

        await page.evaluate("""{window.scrollBy(0, document.body.scrollHeight);}""")
        time.sleep(1)
        videos_list_new = await page.querySelectorAll('._9AhH0')
        videos_list_new_set = set(videos_list_new) | videos_list_old_set

    return user_list,urls_list

browser,page = asyncio.get_event_loop().run_until_complete(login(username='ensu.app',password='3ng13Cun1MuFF1n5'))
#already_followed,private_account = asyncio.get_event_loop().run_until_complete(follow_user(username='petesmith',browser=browser,page=page))
user_list,urls_list = asyncio.get_event_loop().run_until_complete(run_tag(tag='mentalhealth',browser=browser,page=page))

    # #Remove notifications popup
    # notification_buttons = driver.find_elements_by_tag_name("button")
    # notification_button_off = notification_buttons[len(notification_buttons) - 1]
    # notification_button_off.click()

# def check_blocked(**kwargs):
#     #Input argument - driver
#     driver = kwargs.get('driver')
#
#     wait = WebDriverWait(driver, 3)
#     #Check if blocked
#     try:
#         blocked_notification = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "_08v79")))
#         blocked_text = blocked_notification.find_element_by_tag_name("h3").text
#         blocked = True
#     except Exception as e:
#         blocked = False
#         blocked_text = 'Not Blocked :)'
#
#     return(blocked,blocked_text)
#
#
# def check_popup(**kwargs):
#     # Input argument - driver
#     driver = kwargs.get('driver')
#
#     wait = WebDriverWait(driver, 3)
#
#     # Check if popup, click ok to continue if so
#     try:
#         browser_notification = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "cmbtv")))
#         browser_notification_button = browser_notification.find_element_by_class_name("sqdOP")
#         popup = True
#
#         if (browser_notification_button.text == 'Not Now'):
#             browser_notification_button.click()
#     except Exception as e:
#         popup = False
#
#     return (popup)
#

#
# def dm_user(**kwargs):
#     # Input arguments - instagram username + driver
#     username = kwargs.get('username')
#     message = kwargs.get('message')
#     driver = kwargs.get('driver')
#
#     wait = WebDriverWait(driver, 5)
#
#     # Go to webpage
#     base_url = 'https://www.instagram.com/'
#     full_url = base_url + username
#     driver.get(full_url)
#     time.sleep(1)
#
#     # Find follow button element
#     follow_button = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "_5f5mN")))
#
#     # If not already followed, then follow
#     if (follow_button.text == 'Follow'):
#         follow_button.click()
#
#     # Find message button element and click
#     message_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "._8A5w5")))
#     message_button.click()
#     time.sleep(1)
#
# # Send text
# text_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "textarea")))
#     text_box.send_keys(message)
#     time.sleep(1)
#
#     send_button_list = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "sqdOP")))
#     send_button = send_button_list[2]
#     send_button.click()
#
#     return ()
#
#
# def like_post(**kwargs):
#     # Input arguments - instagram username + driver
#     postlink = kwargs.get('postlink')
#     driver = kwargs.get('driver')
#
#     wait = WebDriverWait(driver, 5)
#
#     # Go to post
#     base_url = 'https://www.instagram.com/'
#     full_url = base_url + postlink
#     driver.get(full_url)
#     time.sleep(1)
#
#     # Get like button
#     like_button = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "button svg")))[1]
#     time.sleep(random.randint(1, 3))
#
#     # Try button since videos don't have number of likes
#     try:
#         # Original number of likes
#         likes_tag_orig = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "Nm9Fw")))
#         likes_num_orig = int(reduce(lambda x, y: x + y, re.findall(r'\d+', likes_tag_orig.text)))
#
#         # Click Like button
#         like_button.click()
#         time.sleep(random.random() * 3)
#
#         # Number of likes after clicking
#         likes_tag_new = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "Nm9Fw")))
#         likes_num_new = int(reduce(lambda x, y: x + y, re.findall(r'\d+', likes_tag_new.text)))
#         time.sleep(random.random() * 3)
#
#         # If already liked, will be unliked & number of likes will go down - in that case click like button again
#         if (likes_num_new < likes_num_orig):
#             like_button = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "button svg")))[1]
#             time.sleep(random.random() * 3)
#
#             # Click Like button
#             like_button.click()
#             already_liked= True
#         else:
#             already_liked= False
#
# except Exception as e:
#
#     # Click Like button
#     like_button.click()
#     already_liked = False
#         time.sleep(random.random() * 3)
#
#     # Go back to user page
#     driver.get(full_url)
#     time.sleep(random.random() * 3)
#
# # Check if blocked
# blocked,blocked_text = check_blocked(driver=driver)
#
# return (already_liked,blocked,blocked_text)
#
#
# def get_user_from_post(**kwargs):
#     # Input arguments - instagram username + driver
#     driver = kwargs.get('driver')
#     postlink = kwargs.get('postlink')
#
#     wait = WebDriverWait(driver, 5)
#
#     # Go to post
#     base_url = 'https://www.instagram.com/'
#     full_url = base_url + postlink
#     driver.get(full_url)
#     time.sleep(1)
#
#     username = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".e1e1d")))
#     username_text = username.text
#
#     return (username_text)
#
