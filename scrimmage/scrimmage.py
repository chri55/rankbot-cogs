import discord
from discord.ext import commands
from .utils.dataIO import dataIO
from .utils.chat_formatting import escape_mass_mentions
from .utils import checks
import os

class Scrimmage:
    """Adds and removes players from the 'Playing' role"""
    def __init__(self, bot):
        self.bot = bot
        self.servers = dataIO.load_json("data/scrimmage/servers.json")
        
    @commands.command(pass_context=True, no_pm=True)
    async def playing(self, ctx):
        """Allows users to add and remove their 'Playing' role.
        Toggles on and off."""
        author = ctx.message.author
        server = ctx.message.server
        if server.id not in self.servers:
            await self.bot.say("Setting the Playing role is not available in this server yet.")
            return
        
        serverrolenames = [x.name for x in ctx.message.server.roles]
        if "Playing" not in serverrolenames:
            try:
                await self.bot.say("Creating the Playing role...")
                await self.bot.create_role(server, name="Playing")
            except Forbidden:
                await self.bot.say("I need 'Manage Server' permissions to automatically create roles.")
                return
        
        for r in author.roles:
            if r.name == "Playing":
                await self.bot.remove_roles(author, r)
                await self.bot.say("You are no longer playing today, **{}**.".format(author.name))
                pass
            else:
                await self.bot.add_roles(author, r)
                await self.bot.say("You are now set to play today, **{}**.".format(author.name))
                pass
    
    @commands.command(pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_roles=True)
    async def removeall(self, ctx):
        """Allows those with the 'Manage Roles' permission to remove everyone from the 'Playing' role."""
        server = ctx.message.server
        if server.id not in self.servers:
            await self.bot.say("Setting the Playing role is not available in this server yet.")
            return
        serverrolenames = [x.name for x in server.roles]
        if "Playing" not in serverrolenames:
            await self.bot.say("I can't remove people from a non-existent role!")
        else:
            for role in server.roles:
                if role.name == "Playing":
                    try:
                        await self.bot.delete_role(server, role)
                        await self.bot.create_role(server, name="Playing")
                        await self.bot.say("All have been removed from the Playing role")
                        return
                    except Forbidden:
                        await self.bot.say("I need 'Manage Server' permissions to do this.")
                        return
        pass
        
    @commands.command(pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_server=True)
    async def scrimset(self, ctx):
        """Turn scrim settings on or off for this server."""
        server = ctx.message.server
        if server.id in self.servers:
            self.servers.remove(server.id)
            await self.bot.say("Scrimmage options have been turned off in this server.")
        else:
            self.servers.append(server.id)
            await self.bot.say("Scrimmage options have been turned on in this server.")
        dataIO.save_json("data/scrimmage/servers.json", self.servers)
        pass
    
def check_folders():
    if not os.path.exists("data/scrimmage"):
        print("Making data/scrimmage...")
        os.makedirs("data/scrimmage")

def check_files():
    f = "data/scrimmage/servers.json"
    if not dataIO.is_valid_json(f):
        dataIO.save_json(f, [])

def setup(bot):
    check_folders()
    check_files()
    bot.add_cog(Scrimmage(bot))