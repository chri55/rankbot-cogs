import discord
from discord.ext import commands
from .utils.dataIO import dataIO
from .utils.chat_formatting import escape_mass_mentions
from .utils import checks
from __main__ import send_cmd_help
from collections import defaultdict
import os
import re
import aiohttp
import asyncio
import logging
import random
import operator

## PLAYERS HAVE THE FOLLWING ATTRIBUTES!!!
## GOLD, LEVEL, HP, IN_BATTLE(BOOL), NAME

class Enemy:
    """A representation of an enemy for a user to fight."""
    
    def __init__(self, author: discord.Member, server: discord.Server, players):
        self.hp = players[server.id][author.id]["HP"]
        self.gold = random.randint(1, 15) * players[server.id][author.id]["LEVEL"]
        
    def attack(self):
        return random.randint(1,4)
    
    def givegold(self):
        return random.randint(1, self.gold + 1)
    
    def giveall(self):
        return self.gold

class Fight:
    """Fight your friends (or enemies) for money!"""
    
    def is_enabled(server: discord.Server):
        return server.id in self.players
    
    def __init__(self, bot):
        self.bot = bot
        self.settings = dataIO.load_json("data/fight/settings.json")
        self.players = dataIO.load_json("data/fight/players.json")
        
        
    @commands.group(pass_context=True, name="fight")
    async def _fight(self, ctx):
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)
    
    @_fight.command(pass_context=True, name="enemy")
    async def _enemy(self, ctx):
        TIMEOUT = 60
        author = ctx.message.author
        server = ctx.message.server
        if server.id in self.players:
            if author.id not in self.players[server.id]:
                await self.bot.say("You need to register to fight!")
                return
            elif self.players[server.id][author.id]["IN_BATTLE"]:
                await self.bot.say("You are already in a battle!")
                return
            else:
                self.players[server.id][author.id]["IN_BATTLE"] = True
                dataIO.save_json("data/fight/players.json", self.players)
                enemy = Enemy(author, server, self.players)
                hp = self.players[server.id][author.id]["HP"]
                gold = self.players[server.id][author.id]["GOLD"]
                help_str = ("Type `fight`, `steal`, or `run`.\n"
                                       "`fight` will make you attack the enemy.\n"
                                       "`steal` attempts to take some gold and run away.\n"
                                       "`run` attempts to leave the battle")
                await self.bot.say(help_str)
                while enemy.hp > 0 and hp > 0:
                    s = ""
                    response = await self.bot.wait_for_message(timeout=TIMEOUT, author=author)
                    if response is None:
                        await self.bot.say("Too long. {}'s enemy ran away.".format(author.name))
                        enemy.hp = 0
                        # Before this 'break' it would catch AttributeErrors
                        # on the next statement, never finish and leave people in battle forever. RIP
                        break
                    if response.content.lower() == "fight":
                        ## Can tweak numbers later...
                        atk = random.randint(1,6) # * self.players[server.id][author.id]["LEVEL"] (possible idea)
                        enemy.hp -= atk 
                        s += "Attacked for {0}! Enemy has {1} HP left.\n\n".format(atk, enemy.hp)
                        enemyatk = enemy.attack()
                        hp -= enemyatk
                        s += "Enemy attacked for {0}! {2} has {1} HP left.\n\n".format(enemyatk, hp, author.mention)
                        if enemy.hp <= 0:
                            allgold = enemy.giveall()
                            gold += allgold
                            s += "Enemy defeated! +{} gold.\n".format(allgold)
                            hp = 1
                        elif hp <= 0:
                            s += "You were slain! No gold gained.\n"
                        else:
                            s += help_str
                        await self.bot.say(s)
                        
                    if response.content.lower() == "steal":
                        chance = random.randint(1, 21)
                        if chance <= 5: # Able to run away. 
                            goldgain = enemy.givegold()
                            gold += goldgain
                            s += "Stole successfully! +{} gold. Enemy is gone.".format(goldgain)
                            enemy.hp = 0
                        else:
                            atk = random.randint(1,4)
                            enemy.hp -= atk
                            s += "Steal failed! Attacked for {0}! Enemy has {1} HP left.\n\n".format(atk, enemy.hp)
                            enemyatk = enemy.attack()
                            hp -= enemyatk
                            s += "Enemy attacked for {0}! {2} has {1} HP left.\n\n".format(enemyatk, hp, author.mention)
                            if hp <= 0:
                                s += "You were slain! No gold gained."
                            elif enemy.hp <= 0:
                                goldgain = enemy.givegold()
                                gold += goldgain
                                s += "Enemy defeated! +{} gold.\n".format(goldgain)
                                s += help_str
                            else: 
                                s += help_str
                        await self.bot.say(s)
                    if response.content.lower() == "run":
                        chance = random.randint(1, 21)
                        if chance <= 10:
                            s += "You were able to run away!"
                            enemy.hp = 0
                        else:
                            enemyatk = enemy.attack()
                            hp -= enemyatk
                            s += "Unable to run! Enemy attacked for {0}! {2} has {1} HP left.\n\n".format(enemyatk, hp, author.mention)
                            if hp <= 0:
                                s += "You were slain! No gold gained."
                            else: 
                                s += help_str
                        await self.bot.say(s)

                self.players[server.id][author.id]["IN_BATTLE"] = False
                self.players[server.id][author.id]["GOLD"] = gold
                dataIO.save_json("data/fight/players.json", self.players)
        else:
            await self.bot.say("This hasnt been enabled for the server.")
                
            
    @_fight.command(pass_context=True)
    async def register(self, ctx):
        """Register your character in the fight!"""
        author = ctx.message.author
        server = ctx.message.server
        if server.id in self.players:
            if author.id not in self.players[server.id]:
                self.players[server.id][author.id] = {}
                self.players[server.id][author.id]["NAME"] = author.name
                self.players[server.id][author.id]["HP"] = 30
                self.players[server.id][author.id]["GOLD"] = 100
                self.players[server.id][author.id]["LEVEL"] = 1
                self.players[server.id][author.id]["IN_BATTLE"] = False
                await self.bot.say("Your character has been created.")
                dataIO.save_json("data/fight/players.json", self.players)
            else:
                await self.bot.say("You already have a character!")
        else:
            await self.bot.say("This hasnt been enabled for the server.")
                
        
    @commands.command(pass_context=True)
    async def fightstats(self, ctx):
        author = ctx.message.author
        server = ctx.message.server
        if server.id in self.players:
            if author.id in self.players[server.id]:
                name = self.players[server.id][author.id]["NAME"]
                gold = self.players[server.id][author.id]["GOLD"]
                hp = self.players[server.id][author.id]["HP"]
                level = self.players[server.id][author.id]["LEVEL"]
                await self.bot.say("```\nPlayer: {0}\n\nTotal Gold: {1}\n\nCurrent HP: {2}\n\nLevel (coming soon!): {3}```".format(name, gold, hp, level))
            else:
                await self.bot.say("You haven't registered a character here!")
        else:
            await self.bot.say("This hasnt been enabled for the server.")
            
    @commands.command(pass_context=True)
    async def stash(self, ctx):
        """Shows who in the server has the highest amount of gold!"""
        author = ctx.message.author
        server = ctx.message.server
        if server.id in self.players:
            users = []
            for user in self.players[server.id]:
                users.append((self.players[server.id][user]["NAME"], self.players[server.id][user]["GOLD"]))
            sorted_list = sorted(users, key=operator.itemgetter(1), reverse=True)
            s = "```ruby\n"
            if len(sorted_list) < 10:
                i = 1
                for user in sorted_list:
                    s += u"{}. ➤ {} : {}\n\n".format(i, user[0], user[1])
                    i += 1
            else:
                for i in range(10):
                    s += u"{}. ➤ {} : {}\n\n".format(i + 1, sorted_list[i][0], sorted_list[i][1])
            s += "```"
            await self.bot.say(s)
        else:
            await self.bot.say("This hasnt been enabled for the server.")
        
                
    @commands.command(pass_context=True)
    @checks.mod_or_permissions(manage_server=True)
    async def fightset(self, ctx):
        server = ctx.message.server
        author = ctx.message.author
        if server.id not in self.players:
            self.players[server.id] = {}
            await self.bot.say("Fight module has been enabled! Have fun!")
        else:
            await self.bot.say("WARNING: Want to disable the fight module in the server? All data will be deleted!\n\nType `yes` to continue.")
            response = await self.bot.wait_for_message(timeout=15, author=author, content="yes")
            if response is not None and response.content.lower() == "yes":
                del self.players[server.id]
                await self.bot.say("It has been done. Bye bye fighters!")
            else:
                await self.bot.say("I won't disable this for now.")
        dataIO.save_json("data/fight/players.json", self.players)
                        
        
def check_folders():
    if not os.path.exists("data/fight"):
        print("Creating data/fight...")
        os.makedirs("data/fight")
    return
        
def check_files():
    f = "data/fight/settings.json"
    if not dataIO.is_valid_json(f):
        print("Creating {}...".format(f))
        dataIO.save_json(f, {})
    f = "data/fight/players.json"
    if not dataIO.is_valid_json(f):
        print("Creating {}...".format(f))
        dataIO.save_json(f, {})
    return

def setup(bot):
    check_folders()
    check_files()
    bot.add_cog(Fight(bot))