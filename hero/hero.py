import discord
from discord.ext import commands
from __main__ import send_cmd_help
import os
from .utils.dataIO import dataIO
from .utils.chat_formatting import escape_mass_mentions
from .utils import checks
from collections import defaultdict
import asyncio

class Hero:
    """Hero:
    
    Allows members to add their own hero roles so people can see what characters the play."""
    def __init__(self, bot):
        ###########################
        # Make settings include   #
        # a server_disabled value #
        ###########################
        self.bot = bot
        self.server_list = dataIO.load_json("data/hero/servers.json")
        settings = dataIO.load_json("data/hero/settings.json")
        self.hero_list = ["genji", "mccree", "pharah", "reaper", "soldier", "sombra",
                     "bastion", "hanzo", "junkrat", "mei", "torbjorn",
                     "d.va", "orisa", "reinhardt", "roadhog", "winston",
                     "ana", "lucio", "mercy", "symmetra", "zenyatta"]
        self.settings = defaultdict(dict, settings)
        
    @commands.group(name="hero", pass_context=True, no_pm=True)
    async def _hero(self, ctx):
        """Hero Role Operations
        Soldier: 76 has been shortened to Soldier for simplicity."""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)
            
    @_hero.command(pass_context=True, no_pm=True)
    async def add(self, ctx, hero1=None, hero2=None, hero3=None):
        """Allows you to add heroes to your role list. Max is three."""
        server = ctx.message.server
        if server.id not in self.settings["ENABLED"]:
            await self.bot.say("Please enable hero switching with **set**!")
            return
        if hero1 is None:
            await self.bot.say("Please specify at least one hero!")
            return
        author = ctx.message.author
        server_roles = ctx.message.server.roles
        author_roles = ctx.message.author.roles
        chan_obj = ctx.message.channel
        
        #############################
        # TODO: CHECK FOR ALL ROLES #
        #############################
        
        # Check that they do not have heroes added:
        for role in author_roles:
            if role.name.lower() in self.hero_list:
                await self.bot.say("Please use **removeall** to reset your heroes before adding new ones!")
                return
        
        ## ADD TESTS TO SEE IF THEY ARE ACTUAL ROLES
        hero1 = hero1.lower()
        hero_assign = [hero1]
        if hero2 is not None:
            hero2 = hero2.lower()
            hero_assign.append(hero2)
            
        if hero3 is not None:
            hero3 = hero3.lower()
            hero_assign.append(hero3)
            
        for role in server_roles:
            if role.name.lower() in hero_assign:
                print("Adding role {} to {}...".format(role.name, author.name))
                self.server_list[server.id][role.name.lower()].append(author.name)
                await self.bot.add_roles(author, role)
                await asyncio.sleep(0.5)
                
                
        await self.bot.say("Those heroes have been added to your active roles.")
        dataIO.save_json("data/hero/servers.json", self.server_list)
        pass
                
    @_hero.command(pass_context=True, no_pm=True)
    async def removeall(self, ctx):
        """Allows you to remove your assigned heroes."""
        server = ctx.message.server
        if server.id not in self.settings["ENABLED"]:
            await self.bot.say("Please enable hero switching with **heroset**!")
            return
        author = ctx.message.author
        author_roles = ctx.message.author.roles
        
        to_remove = []
        for role in author_roles:
            if role.name.lower() in self.hero_list:
                self.server_list[server.id][role.name.lower()].remove(author.name)
                to_remove.append(role)
                
        await self.bot.remove_roles(author, *to_remove)
        await self.bot.say("Your hero roles have been removed.")
        dataIO.save_json("data/hero/servers.json", self.server_list)
        pass
    
    @_hero.command(name="list", pass_context=True, no_pm=True)
    async def _list(self, ctx, hero):
        """Shows all people in your server with the hero role"""
        server = ctx.message.server
        if server.id not in self.settings["ENABLED"]:
            await self.bot.say("Please enable hero switching with **heroset**!")
            return
        person_list = "```The people in this server with the role {} include:\n".format(hero.capitalize())
        if len(self.server_list[server.id][hero.lower()]) > 0:    
            for person in self.server_list[server.id][hero.lower()]:
                person_list += "- " + person + "\n"
        else:
            person_list += "\nNone!"
        person_list += "```"
        await self.bot.say(person_list)
        pass
        
    @_hero.command(name="set", pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_server=True)
    async def _set(self, ctx):
        """Turns hero switching on or off for the server.
        User needs 'Manage Server' permission."""
        server = ctx.message.server
        
        if server.id not in self.settings["ENABLED"]:
            self.settings["ENABLED"].append(server.id)
            self.server_list.update({server.id : {}})
            for hero in self.hero_list:
                self.server_list[server.id].update({hero : []})
            await self.bot.say("Hero switching has been enabled on this server. Please make sure you have added all hero roles to the server.")
        else:
            await self.bot.say("Are you sure you want to disable"
                               " hero switching? All data will be deleted for this server and could cause issues if"
                               " you re-enable it in the future! Type 'I agree' to continue.")
            response = await self.bot.wait_for_message(timeout=15, author=ctx.message.author, content="I agree")
            if response is not None and response.content == "I agree":
                self.settings["ENABLED"].remove(server.id)
                del self.server_list[server.id]
                await self.bot.say("Hero switching has been disabled in this server. You will have to reset hero roles for all members if you want it to re-enable properly.")
            else:
                await self.bot.say("15 seconds has passed. I assume you don't really want to disable this.")
        dataIO.save_json("data/hero/settings.json", self.settings)
        dataIO.save_json("data/hero/servers.json", self.server_list)
        pass
        
def check_folders():
    if not os.path.exists("data/hero"):
        print("Creating hero folder...")
        os.makedirs("data/hero")
        
def check_files():
    f = "data/hero/servers.json"
    if not dataIO.is_valid_json(f):
        print("Creating empty servers.json...")
        dataIO.save_json(f, {})
        
    f = "data/hero/settings.json"
    if not dataIO.is_valid_json(f):
        print("Creating empty settings.json...")
        dataIO.save_json(f, {"ENABLED" : []})
    
def setup(bot):
    check_folders()
    check_files()
    bot.add_cog(Hero(bot))