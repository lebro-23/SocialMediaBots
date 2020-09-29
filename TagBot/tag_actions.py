from actions import *
from storage_functions import *

def tag_action(**kwargs):
    driver = kwargs.get('driver')
    driver2 = kwargs.get('driver2')
    tag = kwargs.get('tag')
    action = kwargs.get('action')
    max_likes = kwargs.get('max_likes')
    max_follows = kwargs.get('max_follows')

    wait = WebDriverWait(driver, 5)
    
    #Set error flag
    is_error_like = False
    is_error_follow = False
    
    # Go to tag search page
    base_url = 'https://www.instagram.com/explore/tags/'
    full_url = base_url + tag
    driver.get(full_url)
    time.sleep(1)

    # List to store output
    liked_posts_list = []
    users_followed_list = []
    post_liked_outpath = tag + '/post_liked_list.csv'
    users_followed_outpath = tag + '/post_followed_list.csv'

    # Create sets of links
    links_set_new = set()
    links_set_old = set()
    full_link_list = []

    # Set pause time and scroll count
    CLICK_PAUSE_TIME = 60
    SCROLL_PAUSE_TIME = 1
    num_scrolls = 0
    post_count = 0
    follow_count = 0

    # Get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")

    # Loop through all posts on tag search page
    while True:

        links_set_old = links_set_old | links_set_new
        links = driver.find_elements_by_tag_name("a")
        links_set_new = set(links) - links_set_old
        links_list = list(links_set_new)
        links_text = [l.get_attribute("href") for l in links_list]
        links_posts = [l.replace('https://www.instagram.com/', '') for l in links_text if l.find('/p/') != -1]

        for l in links_posts:
            
            if (l not in full_link_list):
                
                #Initialise as none in case of no return in first iteration
                insta_username = None
                     
                #Try to do action
                try:
                    
                    if (action == 'Like Post'):
                        
                        post_count = post_count + 1
                        
                        # Like post
                        already_liked, blocked, blocked_text = like_post(driver=driver2, postlink=l)
                        
                        # If Blocked then break loop
                        if (blocked and blocked_text == 'Action Blocked'):
                            print("Blocked! :(")
                            break
                        else:
                            liked_posts_list.append(l)
                            print("Successfully liked post %s" %l)
                    
                    if (action == 'Follow User'):
                        
                        follow_count = follow_count + 1
                        
                        #Get username
                        insta_username = get_user_from_post(driver=driver2,postlink=l)
                        
                        # Follow user
                        already_followed,private_account,blocked,blocked_text = follow_user(driver=driver2, username=insta_username)
                        
                        # If Blocked then break loop
                        if (blocked and blocked_text == 'Action Blocked'):
                            print("Blocked! :(")
                            break
                        else:
                            users_followed_list.append(insta_username)
                            print("Successfully followed user %s" %insta_username)

                except Exception as e:
                    
                    #Set error flags to True and upload done actions to bucket and print
                    if (action == 'Like Post'):
                        is_error_like = True
                        print("Error liking post %s"%l)
                    
                    if (action == 'Follow User'):
                        is_error_follow = True
                        print("Error following user %s"%insta_username)


            # Upload to Google bucket every 10 iterations for tracking
            if (post_count % 10 == 0):
                upload_df_to_bucket(credentials_path='../InstagramBot-9cb1dfece602.json',
                                    bucket_path='insta-schools-bucket',
                                    filepath=post_liked_outpath, df=pd.Series(list(liked_posts_list)))

            # Upload to Google bucket every 10 iterations for tracking
            if (follow_count % 10 == 0):
                upload_df_to_bucket(credentials_path='../InstagramBot-9cb1dfece602.json',
                                    bucket_path='insta-schools-bucket',
                                    filepath=users_followed_outpath, df=pd.Series(list(users_followed_list)))

            # Break if reached maximum numer of liked posts
            if (len(liked_posts_list) >= int(max_likes) or len(users_followed_list) >= int(max_follows)):
                break

        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        num_scrolls = num_scrolls + 1

        # Wait to load page
        time.sleep(SCROLL_PAUSE_TIME + num_scrolls * 0.1)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

        # Break if reached maximum numer of liked posts
        if (len(liked_posts_list) >= int(max_likes)):
            upload_df_to_bucket(credentials_path='../InstagramBot-9cb1dfece602.json',
                                bucket_path='insta-schools-bucket',
                                filepath=post_liked_outpath, df=pd.Series(list(liked_posts_list)))
            break

        # Break if reached maximum numer of follows
        if (len(users_followed_list) >= int(max_follows)):
            upload_df_to_bucket(credentials_path='../InstagramBot-9cb1dfece602.json',
                                bucket_path='insta-schools-bucket',
                                filepath=post_liked_outpath, df=pd.Series(list(liked_posts_list)))
            break
