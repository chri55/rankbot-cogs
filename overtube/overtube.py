import os
import urllib
import discord
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

    ##TODO replace key with method
    DEVELOPER_KEY = "AIzaSyAiGsZkKXMAm0nYbq4OoU8BWy13EVjRbdw"
    YOUTUBE_API_SERVICE_NAME = "youtube"
    YOUTUBE_API_VERSION = "v3"

    def __init__(self, bot):
        self.bot = bot
        self.servers = dataIO.load_json("data/overtube/servers.json")
        with open("data/overtube/uploads.txt") as f:
            try:
                self.uploads = int(f.readlines()[0])
            except:
                self.uploads = 0

    @commands.command(pass_context=True)
    @checks.admin_or_permissions()
    async def tubeset(self, ctx):
        """Allows an admin to set where the updates post to."""
        server = ctx.message.server
        author = ctx.message.author

        chans = [chan.type.text for chan in server.channels]
        help_str = "***Choose the channel to post updates to by selecting the number:***\n"
        num = 1
        for chan in chans:
            help_str += "{}: {}\n".format(str(num), chan.name)
            num += 1
        await self.bot.say(help_str)
        resp = await self.bot.wait_for_message(timeout = 15, author = ctx.message.author)
        if self.servers[server.id] == None:
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
        CHECK_DELAY = 60 ##TODO Change to 10 minutes once this works

        while self == self.bot.get_cog("Overtube"):
            youtube = build(YOUTUBE_API_SERVICE_NAME,
                            YOUTUBE_API_VERSION,
                            developerKey=DEVELOPER_KEY)

            ytchannel = youtube.channels().list(id="UClOf1XXinvZsy4wKPAkro2A").execute()
            uploadPL = ytchannel.contentDetails.relatedPlaylists.uploads
            if uploadPL.pageInfo.totalResults != self.uploads:
                print("New video from PlayOverwatch")

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
    f = "data/overtube/uploads.txt"
    if not os.path.exists(f):
        print("OVERTUBE: Creating empty uploads.txt...")
        os.mknod("data/overtube/uploads.txt")

def setup(bot):
    check_folders()
    check_files()
    n = Overtube(bot)
    loop = asyncio.get_event_loop()
    loop.create_task(n.playlist_checker())
    bot.add_cog(n)
