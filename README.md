# AFILinkerBot
Reddit bot that searches /r/AirForce looking for AFI/Forms/Publication mentions and posts links to them

[![Docker Image CI](https://github.com/HadManySons/AFILinkerBot/actions/workflows/docker-image.yml/badge.svg?branch=master)](https://github.com/HadManySons/AFILinkerBot/actions/workflows/docker-image.yml)

# Run
## To run the latest image from docker, execute:

`cd AFILinkerBot`

`docker build -t afilinkerbot .`

`docker run -d --name afexcuses -v AFexcuses:/app --restart unless-stopped --env-file ./AFE_ENVS.list afilinkerbot`

`--restart unless-stopped` is optional, only needed if you want the bot to survive errors.

`--env-file ./AFE_ENVS.list` needs to be populated with the bot creds, the excuse file name and the subreddits 
