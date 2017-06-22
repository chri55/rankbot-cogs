import discord
from discord.ext import commands
from .utils.dataIO import dataIO
from .utils.chat_formatting import escape_mass_mentions
from .utils import checks
from bs4 import BeautifulSoup
import requests
import aiohttp
import os

class Customrole(object):
    """Allows an admin or bot owner ;) to enable color changing roles!"""
    ## Uses a json to track servers that this is enabled and
    ## allows ONE role per server.
    def __init__(self, bot):
        self.bot = bot
        self.servers = dataIO.load_json("data/customrole/servers.json")

    @commands.command(pass_context=True)
    @checks.admin_or_permissions()
    async def crtoggle(self, ctx):
        TIMEOUT = 10
        server = ctx.message.server
        if not server.id in self.servers:
            await self.bot.say("If you wish to enable this, type `agree`.")
            response = await self.bot.wait_for_message(timeout=TIMEOUT, author=ctx.message.author, content="agree")
            if response is not None and response.content == "agree":
                self.servers.append(server.id)
                self.servers[server.id] = ""
                await self.bot.say("CustomRole has been enabled.")
            else:
                await self.bot.say("CustomRole has not been enabled.")
        else:
            await self.bot.say("Want to disable the CustomRole? y/n")
            response = await self.bot.wait_for_message(timeout=TIMEOUT, author=ctx.message.author)
            if response is not None and (response.content.lower() == "y" or response.content.lower() == "yes"):
                self.servers.remove(server.id)
                await self.bot.say("All settings have been disabled here.")
            else:
                await self.bot.say("Exiting CustomRole settings... No changes made.")
        dataIO.save_json("data/customrole/servers.json", self.servers)
        pass


    @commands.command(pass_context=True)
    async def customrole(self, ctx, rolename):
        """Allows for a color changing role if the role is in the server."""
        server = ctx.message.server
        roles = server.roles
        if rolename is None:
            await self.bot.say(":fire: Add the ***exact*** name of the role to be customized.")
            pass
        if rolename in roles:
            self.servers[server.id] = rolename
            await self.bot.say(":white_check_mark: ***{}*** has been made the custom role of the server.".format(rolename))
        else:
            await self.bot.say(":fire: Enter the ***exact*** name of the role to be customized!")
        dataIO.save_json("data/customrole/servers.json", self.servers)
        pass

    async def color_changer(self):
        CHANGE_TIME = 5

        while self == self.get_cog("Customrole"):
            for id in self.servers:
                role = self.servers[id]
                if not self.bot.get_server(id).unavailable:
                    for rolename in self.bot.get_server(id):
                        if rolename.name == role:
                            await self.bot.edit_role(self.bot.get_server(id), rolename, colour=rolename.colour.value + 10)
            await asyncio.sleep(CHANGE_TIME)

def check_folders():
    if not os.path.exists("data/customrole"):
        print("Creating data/customrole folder...")
        os.makedirs("data/customrole")


def check_files():
    f = "data/customrole/servers.json"
    if not dataIO.is_valid_json(f):
        print("Creating empty servers.json...")
        dataIO.save_json(f, [])

def setup(bot):
    check_folders()
    check_files()
    n = Customrole(bot)
    loop = asyncio.get_event_loop()
    loop.create_task(n.color_changer())
    bot.add_cog(n)
