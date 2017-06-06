# AFILinkerBot
Reddit bot that searches /r/AirForce looking for AFI/Forms/Publication mentions and posts links to them

Usage:

'pip install -r requirements.txt'

Fill in the appropriate credentials in the LinkerBotCreds.txt file

Change the subreddit variable from 'AFILinkerBot' to the subreddit of your choice

Remove the 'True' from 'permlink = "http://www.reddit.com" + rAirForceComments.permalink(True) + "/"' on approx line 64 to get true permalink output, otherwise the script will print an estimated permalink, which won't actually work.

Run script
