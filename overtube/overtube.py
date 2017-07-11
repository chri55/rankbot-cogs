import os
import urllib
import discord
import asyncio
from discord.ext import commands
from .utils.dataIO import dataIO
from .utils.chat_formatting import escape_mass_mentions
from .utils import checks
import requests
import aiohttp
from apiclient.discovery import build
#from optparse import OptionParser

class Overtube:
    """Server commands for posting updates from
    the PlayOverwatch Youtube account"""

    def __init__(self, bot):
        self.bot = bot
        self.servers = dataIO.load_json("data/overtube/servers.json")
        ##TODO replace key
        self.DEVELOPER_KEY = "AIzaSyB8TEnPxmiOgF5NDnBiFauoOvTXmdUFAV8"
        self.YOUTUBE_API_SERVICE_NAME = "youtube"
        self.YOUTUBE_API_VERSION = "v3"
        self.uploads = 0

    @commands.command(pass_context=True)
    @checks.admin_or_permissions()
    async def tubeset(self, ctx):
        """Allows an admin to set where the updates post to."""
        server = ctx.message.server
        author = ctx.message.author

        chans = [chan for chan in server.channels]
        help_str = "***Choose the channel to post updates to by selecting the number:***\n"
        num = 1
        for chan in chans:
            help_str += "{}: {}\n".format(str(num), chan.name)
            num += 1
        await self.bot.say(help_str)
        resp = await self.bot.wait_for_message(timeout = 15, author = ctx.message.author)
        self.servers[server.id] = {}
        if chans[int(resp.content)-1].id not in self.servers[server.id]["CHANNELS"]:
            self.servers[server.id]["CHANNELS"].append(chans[int(resp.content)-1].id)
            await self.bot.say("***{}*** will now get PlayOverwatch alerts.".format(chans[int(resp.content)-1].name))
        else:
            self.servers[server.id]["CHANNELS"].remove(chans[int(resp.content)-1].id)
            await self.bot.say("Alerts have been removed from ***" + chans[int(resp.content)-1].name + "***")
        dataIO.save_json("data/overtube/servers.json")
        pass

    async def playlist_checker(self):
        """Checks the PlayOverwatch youtube channel for new vids."""
        CHECK_DELAY = 60 ##TODO Change to news 10 minutes once this works

        while self == self.bot.get_cog("Overtube"):
            youtube = build(self.YOUTUBE_API_SERVICE_NAME,
                            self.YOUTUBE_API_VERSION,
                            developerKey=self.DEVELOPER_KEY)

            ytchannel = youtube.channels().list(part='snippet,contentDetails', id="UClOf1XXinvZsy4wKPAkro2A").execute()
            uploadPL = ytchannel['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            results = youtube.playlistItems().list(
                part='snippet,contentDetails',
                id=uploadPL
            ).execute()
            url = "https://youtube.com/watch?v="
            print(results['pageInfo'])
            if results['pageInfo']['totalResults'] != self.uploads:
                for vid in results['items']:
                    if vid['snippet']['position'] == 0:
                        vid_title = vid['snippet']['title']
                        vid_description = vid['snippet']['description']
                        vid_id = url + vid['snippet']['resourceId']['videoId']
                        break

                print("New video from PlayOverwatch")
                print(vid_title)
                print(vid_description)
                print(vid_id)

            await asyncio.sleep(CHECK_DELAY)

def check_folders():
    if not os.path.exists("data/overtube"):
        print("Creating data/overtube folder")
        os.makedirs("data/overtube")

def check_files():
    f = "data/overtube/servers.json"
    if not dataIO.is_valid_json(f):
        print("OVERTUBE: Creating empty servers.json...")
        dataIO.save_json(f, {})

def setup(bot):
    check_folders()
    check_files()
    n = Overtube(bot)
    loop = asyncio.get_event_loop()
    loop.create_task(n.playlist_checker())
    bot.add_cog(n)
