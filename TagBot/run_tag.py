import sys
import pandas as pd
from actions import *
from tag_actions import *
from storage_functions import *

username = sys.argv[1]
password = sys.argv[2]
tag = sys.argv[3]
action = sys.argv[4]
max_likes = sys.argv[5]
max_follows = sys.argv[6]

#Login with details
driver = login(username=username,password=password)
print("Logged in successfully for account: %s"%username)
time.sleep(10)

#Login again with details
driver2 = login(username=username,password=password)
print("Logged in successfully for account: %s"%username)
time.sleep(10)

tag_action(driver=driver,driver2=driver2,tag=tag,action=action,max_likes=max_likes,max_follows=max_follows)