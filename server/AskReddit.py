import string
import praw
import Listofbadwords
from praw.models import MoreComments


# def is_sfw(s):
#     for word in badwords:
#         if word in s.title or word in s.body:
#             return false
#
#     return true

reddit = praw.Reddit(client_id='10cXpuGVM-6W3A',
                     client_secret="eJk6Gg9KrwoI0X2hadV56P-f7lk",
                     user_agent='Yeeeeeeeet321')

values_dict = {}

askReddit = reddit.subreddit('AskReddit')
from datetime import datetime
for submission in askReddit.top("all",limit=200):
    i = 0
    printed = False
    # print(submission.tags)
    for s in submission.comments:
        if i == 10:
            break;
        if not isinstance(s,MoreComments):
            if len(s.body) < 20 and s.body != "[deleted]" and s.body != "[removed]" and not submission.over_18:
                i += 1
                if i == 1:
                    values_dict[submission.title] = []
                    # printed = True
                values_dict[submission.title].append(s.body)
                # print(s.body)

    # if printed == True:
    #     print("----------------")

import pickle
# dict = {'Python' : '.py', 'C++' : '.cpp', 'Java' : '.java'}
f = open("save_file.pkl","wb")
pickle.dump(values_dict,f)
f.close()
# print(reddit.read_only)  # Output: True
# print("time:", datetime.utcfromtimestamp(submission.created_utc).strftime('%Y-%m-%d, %H::%M'))
# print("author: ",submission.author.name)
# print("score: ", submission.score,)
# print("id:", submission.id)

#print("ups & ratio:", submission.ups,',', submission.upvote_ratio)

# if len(submission.comments) > 10:
