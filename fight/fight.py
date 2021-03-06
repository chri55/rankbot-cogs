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
    ## This is kinda eh
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
    # Fight is a command group including subcommands:
    # enemy
    # register
    # user
    # Proper usage of these commands is in the format [p]fight subcmd
    # [p] is the bot prefix
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @_fight.command(pass_context=True, name="enemy")
    async def _enemy(self, ctx):
    """Fight an enemy for gold."""
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
                # Making another class for the enemy was probably extra
                # but I made class methods for it which I would
                # have done in Unity anyways.
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
                        await self.bot.say("Too long. {}'s enemy ran away.".format(author.mention))
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
        pass

    @_fight.command(pass_context=True, name="user")
    async def _user(self, ctx, opponent: discord.Member, wager):
        """Attempt to fight another user."""
        author = ctx.message.author
        server = ctx.message.server
        wager = int(wager)
        if server.id in self.players:
            if author.id in self.players[server.id]:
                if opponent.id in self.players[server.id]:
                    if wager < self.players[server.id][author.id]["GOLD"] and wager < self.players[server.id][opponent.id]["GOLD"]:
                        await self.bot.say("{0}, {1} would like to battle you for {2} gold! Type `agree` to start.".format(opponent.mention, author.name, wager))
                        response = await self.bot.wait_for_message(timeout=60, author=opponent, content="agree")
                        if response is not None and response.content.lower() == "agree":
                            ## BEGIN PLAYER LOOPING HERE!!!!
                            coinflip = random.randint(0, 1)
                            if coinflip == 1:
                                sp = author.name
                                turn = True
                            else:
                                sp = opponent.name
                                turn = False
                            await self.bot.say("A coin has been flipped! {} will start the battle!".format(sp))
                            self.players[server.id][author.id]["IN_BATTLE"] = True
                            self.players[server.id][opponent.id]["IN_BATTLE"] = True
                            dataIO.save_json("data/fight/players.json", self.players)
                            auth_hp = self.players[server.id][author.id]["HP"]
                            oppo_hp = self.players[server.id][opponent.id]["HP"]
                            help_str = ("Type `fight` or `run`.\n"
                                                   "`fight` will make you attack the enemy.\n"
                                                   "`run` forfeits the battle.")
                            while auth_hp > 0 and oppo_hp > 0:
                                if turn: # AUTHOR TURN
                                    await self.bot.say("{}'s' turn:\n\n{}".format(author.mention, help_str))
                                    response = await self.bot.wait_for_message(timeout=60, author=author)
                                    if response is None:
                                        self.players[server.id][author.id]["GOLD"] -= wager
                                        self.players[server.id][opponent.id]["GOLD"] += wager
                                        await self.bot.say("Battle forfeited by {0}. {1} gains {2} gold.".format(author.name, opponent.mention, wager))
                                        break
                                    elif response.content.lower() == "fight":
                                        atk = random.randint(2,6)
                                        miss_chance = random.randint(1,50)
                                        if miss_chance % 10 == 0:
                                            await self.bot.say("{}'s attack missed!".format(author.name))
                                            turn = not turn
                                        else:
                                            oppo_hp -= atk
                                            await self.bot.say("{0} hit the opponent for {1}.\n\n{2}: {3}/{4} HP".format(author.name, atk, opponent.name, oppo_hp, self.players[server.id][opponent.id]["HP"]))
                                            turn = not turn
                                        if auth_hp <= 0:
                                            self.players[server.id][opponent.id]["GOLD"] += wager
                                            self.players[server.id][author.id]["GOLD"] -= wager
                                            await self.bot.say("{} wins! +{} gold.".format(opponent.name, wager))
                                        elif oppo_hp <= 0:
                                            self.players[server.id][opponent.id]["GOLD"] -= wager
                                            self.players[server.id][author.id]["GOLD"] += wager
                                            await self.bot.say("{} wins! +{} gold.".format(author.name, wager))
                                    elif response.content.lower() == "run":
                                        auth_hp = 0
                                        self.players[server.id][opponent.id]["GOLD"] += wager
                                        self.players[server.id][author.id]["GOLD"] -= wager
                                        await self.bot.say("{} has run away! {} is the winner. +{} gold.".format(author.name, opponent.mention,wager))
                                else: #OPPONENT TURN
                                    await self.bot.say("{}'s' turn:\n\n{}".format(opponent.mention, help_str))
                                    response = await self.bot.wait_for_message(timeout=60, author=opponent)
                                    if response is None:
                                        self.players[server.id][opponent.id]["GOLD"] -= wager
                                        self.players[server.id][author.id]["GOLD"] += wager
                                        await self.bot.say("Battle forfeited by {0}. {1} gains {2} gold.".format(opponent.name, author.mention, wager))
                                        break
                                    elif response.content.lower() == "fight":
                                        atk = random.randint(2,6)
                                        miss_chance = random.randint(1,50)
                                        if miss_chance % 10 == 0:
                                            await self.bot.say("{}'s attack missed!".format(opponent.name))
                                            turn = not turn
                                        else:
                                            auth_hp -= atk
                                            await self.bot.say("{0} hit the opponent for {1}.\n\n{2}: {3}/{4} HP".format(opponent.name, atk, author.name, auth_hp, self.players[server.id][author.id]["HP"]))
                                            turn = not turn
                                        if auth_hp <= 0:
                                            self.players[server.id][opponent.id]["GOLD"] += wager
                                            self.players[server.id][author.id]["GOLD"] -= wager
                                            await self.bot.say("{} wins! +{} gold.".format(opponent.name, wager))
                                        elif oppo_hp <= 0:
                                            self.players[server.id][opponent.id]["GOLD"] -= wager
                                            self.players[server.id][author.id]["GOLD"] += wager
                                            await self.bot.say("{} wins! +{} gold.".format(author.name, wager))
                                    elif response.content.lower() == "run":
                                        oppo_hp = 0
                                        self.players[server.id][author.id]["GOLD"] += wager
                                        self.players[server.id][opponent.id]["GOLD"] -= wager
                                        await self.bot.say("{} has run away! {} is the winner. +{} gold.".format(opponent.name, author.mention,wager))
                            self.players[server.id][author.id]["IN_BATTLE"] = False
                            self.players[server.id][opponent.id]["IN_BATTLE"] = False
                            dataIO.save_json("data/fight/players.json", self.players)
                            return
                        else:
                            await self.bot.say("Yeah, sorry {} but they didn't answer. I wouldn't either.".format(author.name))
                    else:
                        await self.bot.say("Both players must have enough gold!")
                else:
                    await self.bot.say("That person needs to register to fight!")
            else:
                await self.bot.say("You need to register to fight!")
        else:
            await self.bot.say("This hasn't been enabled for the server.")
        pass


    @_fight.command(pass_context=True)
    async def register(self, ctx):
        """Register your character in the fight! Use this if you need to register."""
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
        pass


    @commands.command(pass_context=True)
    async def fightstats(self, ctx):
        """See your current HP, Gold, and Level."""
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
        pass

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
        pass


    @commands.command(pass_context=True)
    @checks.mod_or_permissions(manage_server=True)
    async def fightset(self, ctx):
        """Admins: Use this to enable fights in the server."""
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
        pass

    @commands.command(pass_context=True, name="reset", hidden=True)
    @checks.is_owner()
    async def _reset(self, ctx):
        server = ctx.message.server
        for p in self.players[server.id]:
            self.players[server.id][p]["IN_BATTLE"] = False
        await self.bot.say("Battles have been reset.")
        dataIO.save_json("data/fight/players.json", self.players)
        pass

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
