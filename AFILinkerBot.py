from bs4 import BeautifulSoup
import requests
import praw
import sqlite3
from pathlib import Path
import re
import random
import logging
import time
import os
import sys
import json
from BotCreds import credsUserAgent, credsClientID, credsClientSecret, credsPassword, credsUserName
# Initialize a logging object and have some examples below from the Python
# Doc page
logging.basicConfig(filename='AFILinkerBot.log', level=logging.INFO)

#Get the PID of this process
pid = str(os.getpid())
pidfile = "AFILinkerBot.pid"

#Exit if a version of the script is already running
if os.path.isfile(pidfile):
    print(pidfile + " already running, exiting")
    sys.exit()

#Create the lock file for the script
open(pidfile, 'w').write(pid)

logging.info(time.strftime("%Y/%m/%d %H:%M:%S ") + "Starting script")

#Try to login or sleep/wait until logged in, or exit if user/pass wrong
NotLoggedIn = True
while NotLoggedIn:
    try:
        reddit = praw.Reddit(
            user_agent=credsUserAgent.strip(),
            client_id=credsClientID.strip(),
            client_secret=credsClientSecret.strip(),
            username=credsUserName.strip(),
            password=credsPassword.strip())
        print("Logged in")
        NotLoggedIn = False
    except praw.errors.InvalidUserPass:
        print("Wrong username or password")
        logging.error(time.strftime("%Y/%m/%d %H:%M:%S ") + "Wrong username or password")
        exit(1)
    except Exception as err:
        print(err)
        time.sleep(5)


# regex expression used to search for an AFI mention
AFIsearchRegEx = "((afi|afpd|afman|afva|afh|afji|afjman|afpam|afgm|afpci|aetci|" \
                 "usafai|afttp)[0-9]{1,2}-[0-9]{1,4}([0-9]{1})?([a-z]{1,2}-)?" \
                 "([0-9]{1,3})?(vol|v)?\d?)|((af|form|afform|sf|afto|afcomsec|afg|" \
                 "apda|aftd|imt|afimt|aetc)[0-9]{1,4}([a-z]{1,2})?)"

# Reply templates to go in the middle of comments
NormalReplyTemplate = '^^It ^^looks ^^like ^^you ^^mentioned ^^an ^^AFI, ^^form ^^or ^^other ^^publication ^^without ' \
                      '^^linking ^^to ^^it, ^^so ^^I ^^have ^^posted ^^a ^^link ^^to ^^it. ^^Additionally, ^^there ' \
                      '^^may ^^be ^^other ^^MAJCOM, ^^NAF ^^or ^^Wing ^^sups ^^to ^^the ^^linked ^^AFI, ^^so ^^I ' \
                      '^^will ^^also ^^post ^^a ^^link ^^to ^^the ^^search ^^URL ^^used ^^below ^^so ^^that ^^you ' \
                      '^^can ^^look ^^for ^^additional ^^supplements ^^or ^^guidance ^^memos ^^that ^^may ' \
                      '^^apply. ^^Please ^^let ^^me ^^know ^^if ^^this ^^is ^^incorrect ^^or ^^if ^^you ^^have ^^a '\
                      '^^suggestion ^^to ^^make ^^me ^^better ^^by ^^posting ^^in ^^my ^^subreddit ^^(/r/AFILinkerBot)'\
                      ' ^^| ^^[GitHub](https://github.com/HadManySons/AFILinkerBot).\n\n' \
                      'I am a bot, this was an automatic reply.\n\n'
SmarmyReplyTemplate = 'This is where I would normally post a link to an AFI or something but I see you tried to ' \
                      'reference an AFTTP. So instead I will leave you a gem from /r/AirForce, chosen at random ' \
                      'from a list:\n\n**'

# vars
globalCount = 0
dbFile = Path("CommentRecord.db")

# check to see if database file exists
if dbFile.is_file():
    # connection to database file
    conn = sqlite3.connect("CommentRecord.db")
    # database cursor object
    dbCommentRecord = conn.cursor()
else:  # if it doesn't, create it
    conn = sqlite3.connect("CommentRecord.db")
    dbCommentRecord = conn.cursor()
    dbCommentRecord.execute('''CREATE TABLE comments(comment text)''')

# subreddit instance of /r/AirForce. 'AFILinkerBot' must be changed to 'airforce' for a production version of the
# script. AFILB subreddit used for testing.
#subreddit = 'airforce+airnationalguard+afrotc'
subreddit = 'AFILinkerBot'
rAirForce = reddit.subreddit(subreddit)

logging.info(time.strftime("%Y/%m/%d %H:%M:%S ") +
             "Starting processing loop for subreddit: " + subreddit)

#System to keep track of how many 404 errors we get from ePubs, for data research purposes
#All the .close() statements
ePubs404Error = 0
with open("404errors.txt", "a") as f:
    f.write(f'START: {time.strftime("%Y/%m/%d %H:%M:%S ")}\n')

while True:
    try:
        # stream all comments from /r/AirForce
        for rAirForceComments in rAirForce.stream.comments():
            globalCount += 1
            print("\nComments processed since start of script: " + str(globalCount))
            print("Processing comment: " + rAirForceComments.id)

            # prints a link to the comment.
            permlink = "http://www.reddit.com" + \
                rAirForceComments.permalink
            print(permlink)
            logging.info(time.strftime("%Y/%m/%d %H:%M:%S ") +
                         "Processing comment: " + permlink)

            # Pulls all comments previously commented on
            dbCommentRecord.execute(
                "SELECT * FROM comments WHERE comment=?", (rAirForceComments.id,))

            id_exists = dbCommentRecord.fetchone()

            # Make sure we don't reply to the same comment twice or to the bot
            # itself
            if id_exists:
                print("Already processed comment: " +
                      str(rAirForceComments.id) + ", skipping")
                continue
            elif rAirForceComments.author == "AFILinkerBot":
                print("Author was the bot, skipping...")
                continue
            else:
                # make the comment all lowercase and remove all spaces, change
                # vol to v, and other cleanup
                formattedComment = rAirForceComments.body
                formattedComment = formattedComment.lower()
                formattedComment = formattedComment.replace(' ', '')
                if "form" in formattedComment:
                    if "afform" in formattedComment or "aftoform" in formattedComment:
                        formattedComment = formattedComment.replace('form', '')
                    else:
                        formattedComment = formattedComment.replace('form', 'af')
                formattedComment = formattedComment.replace('vol', 'v')
                print("Formatted Comment: " + formattedComment)

                # search the comments for a match
                inputToTest = re.compile(AFIsearchRegEx, re.IGNORECASE)
                MatchedComments = inputToTest.finditer(formattedComment)

                # Keep a list of matched comments so we only post one link per
                # AFI
                ListOfMatchedComments = []

                # Variables to hold all the matched AFI links and their
                # respective search links
                TotalAFILinks = ""
                TotalSearchLinks = ""

                # Iterate through all the matched comments
                for individualMention in MatchedComments:
                    # Skip to the next match if an AFI referenced has already been processed. Prevents post multiple
                    # links to the same pub
                    if individualMention.group() in ListOfMatchedComments:
                        continue
                    else:
                        # A little extra something
                        if "afttp" in individualMention.group():
                            dalist = []
                            with open('smarmycomments.txt', 'r') as f:
                                dalist = f.read().splitlines()
                            print("Dropping a smarmy comment on the mention of: " + individualMention.group() +
                                  " by " + str(rAirForceComments.author) + ". Comment ID: " + rAirForceComments.id)
                            logging.info(time.strftime("%Y/%m/%d %H:%M:%S ") +
                                         "Dropping a smarmy comment on the mention of: " + individualMention.group()
                                         + " by " + str(rAirForceComments.author) + ". Comment ID: " +
                                         rAirForceComments.id + "\n")
                            smarmyReply = SmarmyReplyTemplate + (dalist[random.randint(0, len(dalist) - 1)])
                            smarmyReply += '\n\nI am a bot, this was an automatic reply.'
                            rAirForceComments.reply(smarmyReply)
                            dbCommentRecord.execute(
                                'INSERT INTO comments VALUES (?);', (rAirForceComments.id,))
                            conn.commit()
                            continue

                        # searchLink is what is at the bottom of a comment to
                        # let people search for their own crap
                        searchLink = '[' + str(
                            individualMention.group()).upper() + ' search link](http://www.e-publishing.af.mil' \
                                                                 '/DesktopModules/MVC/EPUBS/EPUB/GetPubsSearchView' \
                                                                 '?keyword=%s&obsolete=false)' \
                                                                 % individualMention.group()

                        #polls the epubs website for a search
                        reqParams = {'keyword' : individualMention.group(), 'obsolete':'false'}
                        epubsReturn = requests.get('http://www.e-publishing.af.mil/DesktopModules/MVC/EPUBS/EPUB/GetPubsSearchView/', params=reqParams)

                        if epubsReturn.status_code == requests.codes.ok:
                            break
                        else:
                            with open("404errors.txt","a") as f:
                                f.write(f'{time.strftime("%Y/%m/%d %H:%M:%S ")} Comment: {permlink}\n')
                            print("404 Error received, retrying in 10 seconds")
                            for i in range(5):
                                time.sleep(10)
                                ePubs404Error += 1
                                with open("404errors.txt", "a") as f:
                                    f.write(f'Try #{i+1} for {epubsReturn.url}, total failure this lifecycle: {ePubs404Error}\n')
                                print(f'Got a {str(epubsReturn.status_code)}, this is try number {i+1} to get a return')
                                epubsReturn = requests.get(
                                    'http://www.e-publishing.af.mil/DesktopModules/MVC/EPUBS/EPUB/GetPubsSearchView/',
                                    params=reqParams)
                                if epubsReturn.status_code == requests.codes.ok:
                                    with open("404errors.txt", "a") as f:
                                        f.write('Finally worked\n')
                                    print("Finally worked, breaking")
                                    break
                            with open("404errors.txt", "a") as f:
                                f.write('Never worked\n')


                        epubsSearch = BeautifulSoup(
                            epubsReturn.text, 'html.parser')

                        # regex to match exactly the afi typed from the ePubs
                        # crawl
                        individualMentionRegex = "(?<=/)(" + \
                            individualMention.group() + ")(?=\.pdf)"
                        # scrub the epubs search return and look for an exact
                        # match between a / and .pdf

                        listOfLinks = []
                        listOfMatchedLinks = []

                        #find all <a href> tags and append the hyperlink to a list
                        for aTags in epubsSearch.find_all('a'):
                            listOfLinks.append(aTags.get('href'))

                        regObject = re.compile(individualMentionRegex)

                        #iterate through the list of link to find exact matches
                        for i in range(0,len(listOfLinks)):
                            listItem = regObject.findall(str(listOfLinks[i]))
                            if listItem:
                                listOfMatchedLinks.append(listOfLinks[i])

                        # Parse through results and start building the
                        # TotalAFILinks and TotalSearchLinks variables
                        for link in listOfMatchedLinks:
                            if "CDATA" in link:
                                print("Garbage return, skipping link")
                                logging.error(time.strftime("%Y/%m/%d %H:%M:%S ")
                                              + "Garbage ePubs return")
                                continue
                            if link in formattedComment:
                                print(str(individualMention.group()).upper() + " link already posted by OP, skipping")
                            else:
                                # Add the matched comment into the master list
                                ListOfMatchedComments.append(individualMention.group())
                                print("Link: " + link)
                                TotalAFILinks += link + "\n\n"
                                TotalSearchLinks += searchLink + "\n\n"

                # if the TotalAFILinks variable isn't empty (no matches),
                # prepare the reply comment
                if TotalAFILinks != "":
                    replyComment = TotalAFILinks
                    replyComment += "___________________________________________________________\n\n"
                    replyComment += NormalReplyTemplate
                    replyComment += "___________________________________________________________\n\n"
                    replyComment += "\n\n" + TotalSearchLinks
                    # create db record of comment so we don't comment on it
                    # again
                    dbCommentRecord.execute(
                        'INSERT INTO comments VALUES (?);', (rAirForceComments.id,))

                    # Comments on post
                    print("Commenting on mention of: " + str(ListOfMatchedComments) + " by " + str(
                        rAirForceComments.author) + ". Comment ID: " + rAirForceComments.id)
                    logging.info(time.strftime("%Y/%m/%d %H:%M:%S ") + "Commenting on mention of: " + str(
                        ListOfMatchedComments) + " by " + str(
                        rAirForceComments.author) + ". Comment ID: " + rAirForceComments.id + "\n")
                    # Comments on post
                    rAirForceComments.reply(replyComment)
                    # save changes to db
                    conn.commit()

    # what to do if Ctrl-C is pressed while script is running
    except KeyboardInterrupt:
        print("Keyboard Interrupt experienced, cleaning up and exiting")
        conn.commit()
        conn.close()
        print("Exiting due to keyboard interrupt")
        logging.info(time.strftime("%Y/%m/%d %H:%M:%S ")
                    + "Exiting due to keyboard interrupt")
        exit(0)
    
    except Exception as err:
        print("Exception: " + str(err.with_traceback()))
        logging.error(time.strftime("%Y/%m/%d %H:%M:%S ") 
                                + "Unhandled exception: " + + str(err.with_traceback()))

    finally:
        os.unlink(pidfile)
