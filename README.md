# AFILinkerBot
Reddit bot that searches /r/AirForce looking for AFI/Forms/Publication mentions and posts links to them

Usage:

1. 'pip install -r requirements.txt'

2. Fill in the appropriate credentials in the LinkerBotCreds.txt file

3. Change the subreddit variable from 'AFILinkerBot' to the subreddit of your choice

4. Remove the 'True' from 'permlink = "http://www.reddit.com" + rAirForceComments.permalink(True) + "/"' on approx line 86 to get true permalink output, otherwise the script will print an estimated permalink, which won't actually work.

5. Run script
