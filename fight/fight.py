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

## PLAYERS HAVE THE FOLLWING ATTRIBUTES!!!
## GOLD, LEVEL, HP, IN_BATTLE(BOOL)

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
            else:
                self.players[server.id][author.id]["IN_BATTLE"] = True
                dataIO.save_json("data/fight/players.json", self.players)
                enemy = Enemy(author, server, self.players)
                hp = self.players[server.id][author.id]["HP"]
                gold = self.players[server.id][author.id]["GOLD"]
                while enemy.hp > 0 and hp > 0:
                    await self.bot.say("Type `fight`, `steal`, or `run`.\n"
                                       "`fight` will make you attack the enemy.\n"
                                       "`steal` attempts to take some gold and run away.\n"
                                       "`run` attempts to leave the battle")
                    response = await self.bot.wait_for_message(timeout=TIMEOUT, author=author)
                    if response is None:
                        await self.bot.say("Too long. The enemy ran away.")
                        enemy.hp = 0
                    if response.content.lower() == "fight":
                        ## Can tweak numbers later...
                        atk = random.randint(1,4) * self.players[server.id][author.id]["LEVEL"]
                        enemy.hp -= atk
                        await self.bot.say("Attacked for {0}! Enemy has {1} HP left.".format(atk, enemy.hp)) 
                        enemyatk = enemy.attack()
                        hp -= enemyatk
                        await self.bot.say("Enemy attacked for {0}! You have {1} HP left.".format(enemyatk, hp))
                        if enemy.hp <= 0:
                            gold += enemy.giveall()
                    if response.content.lower() == "steal":
                        chance = random.randint(1, 21)
                        if chance <= 5: # Able to run away. 
                            goldgain = enemy.givegold()
                            gold += goldgain
                            await self.bot.say("Stole successfully! +{} gold. Enemy is gone.".format(goldgain))
                            enemy.hp = 0
                        else:
                            atk = random.randint(1,6)
                            enemy.hp -= atk
                            await self.bot.say("Attacked for {0}! Enemy has {1} HP left.".format(atk, enemy.hp)) 
                            enemyatk = enemy.attack()
                            hp -= enemyatk
                            await self.bot.say("Enemy attacked for {0}! You have {1} HP left.".format(enemyatk, hp))
                    if response.content.lower() == "run":
                        chance = random.randint(1, 21)
                        if chance <= 10:
                            await self.bot.say("You were able to run away!")
                            enemy.hp = 0
                        else:
                            enemyatk = enemy.attack()
                            hp -= enemyatk
                            await self.bot.say("Unable to run! Enemy attacked for {0}! You have {1} HP left.".format(enemyatk, hp))

                self.players[server.id][author.id]["IN_BATTLE"] = False
                self.players[server.id][author.id]["GOLD"] += gold
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
                self.players[server.id][author.id]["HP"] = 30
                self.players[server.id][author.id]["GOLD"] = 100
                self.players[server.id][author.id]["LEVEL"] = 1
                self.players[server.id][author.id]["IN_BATTLE"] = True
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
                name = author.name
                gold = self.players[server.id][author.id]["GOLD"]
                hp = self.players[server.id][author.id]["HP"]
                level = self.players[server.id][author.id]["LEVEL"]
                await self.bot.say("```\nPlayer: {0}\n\nTotal Gold: {1}\n\nCurrent HP: {2}\n\nLevel: {3}```".format(name, gold, hp, level))
            else:
                await self.bot.say("You haven't registered a character here!")
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
            reponse = await self.bot.wait_for_message(timeout=15, author=author, content="yes")
            if response.content.lower() == "yes":
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