import discord
from discord.ext import commands
from .utils.dataIO import dataIO
from .utils.chat_formatting import escape_mass_mentions
from .utils import checks
from bs4 import BeautifulSoup
import requests
import aiohttp
import os

class Rank:
    """Server commands for users to assign themselves skill rank roles, region, and game role.
       Also finds and displays OverBuff and OverwatchTracker profiles."""

    skillRankRoles = ['Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond', 'Master', 'Grandmaster']
    def __init__(self, bot):
        self.bot = bot
        self.servers = dataIO.load_json("data/rank/servers.json")

    @commands.command(pass_context=True, no_pm=True)
    async def sr(self, ctx, sr):
        """Assigns SR based on the integer <sr> given. (1-5000). 0 no longer removes rank (edited 4/11/17)"""
        skillRankRoles = ['Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond', 'Master', 'Grandmaster']

        server = ctx.message.server
        if server.id not in self.servers:
            await self.bot.say("This function is not enabled. Please use `rankset` as an admin to enable it.")
            return
        serverroles = ctx.message.server.roles
        authorroles = ctx.message.author.roles
        messagechannel = ctx.message.channel
        serverrolenames = [x.name for x in serverroles]
        for r in skillRankRoles:
            if r not in serverrolenames:
                try:
                    await self.bot.say("{} role not detected, creating it in the server...".format(r))
                    await self.bot.create_role(server, name=r)
                except Forbidden:
                    await self.bot.say("I need to have the 'Manage Roles' permission to automatically add the right roles!")
                    return
        
        
        try:
            sr = int(sr)
        except ValueError:
            await self.bot.send_message(messagechannel, ':fire: ' + ctx.message.author.name + ', Please enter a number in the range 1-5000!')
            return

        roleIndex = -1
        
        if sr >= 1 and sr <= 1499:
            roleIndex = 0
        elif sr >= 1500 and sr <= 1999:
            roleIndex = 1
        elif sr >= 2000 and sr <= 2499:
            roleIndex = 2
        elif sr >= 2500 and sr <= 2999:
            roleIndex = 3
        elif sr >= 3000 and sr <= 3499:
            roleIndex = 4
        elif sr >= 3500 and sr <= 3999:
            roleIndex = 5
        elif sr >= 4000 and sr <= 5000:
            roleIndex = 6
        elif sr > 5000 or sr < 1:
            await self.bot.send_message(messagechannel, ':fire: Please enter a number in the range 1-5000!')
            return

        for aRole in authorroles:
            if aRole.name in skillRankRoles:
                authorroles.remove(aRole)

        for sRole in serverroles:
            if sRole.name in skillRankRoles[roleIndex]:
                authorroles.append(sRole)

        await self.bot.replace_roles(ctx.message.author, *authorroles)

        msgString = ':white_check_mark: ' + ctx.message.author.name + ", your rank has been updated to: " + skillRankRoles[roleIndex]
        await self.bot.send_message(messagechannel, msgString)
        pass 
    
    @commands.command(pass_context=True, no_pm=True)
    async def reg(self, ctx, region):
        """Sets your role to the [region] specified. (NA, EU, SEA)"""
        regions = ['NA', 'EU', 'SEA']
        serverRoles = ctx.message.server.roles
        authorRoles = ctx.message.author.roles
        author = ctx.message.author
        server = ctx.message.server
        if server.id not in self.servers:
            await self.bot.say("This function is not enabled. Please use `rankset` as an admin to enable it.")
            return
        serverrolenames = [x.name for x in serverRoles]
        for r in regions:
            if r not in serverrolenames:
                try:
                    await self.bot.say("{} role not detected, creating it in the server...".format(r))
                    await self.bot.create_role(server, name=r)
                except Forbidden:
                    await self.bot.say("I need to have the 'Manage Roles' permission to automatically add the right roles!")
                    return
        roleindex = -1
        earth_emoji = ''

        if region.lower() == 'na':
            earth_emoji = ':earth_americas:'
            roleindex = 0
        elif region.lower() == 'eu':
            earth_emoji = ':earth_africa:'
            roleindex = 1
        elif region.lower() == 'sea':
            earth_emoji = ':earth_asia:'
            roleindex = 2
        else:
            await self.bot.say(':fire: ' + author.name + ', please set a valid region. (NA, EU, or SEA)')
            return

        for sRole in serverRoles:
            if sRole.name in regions[roleindex]:
                authorRoles.append(sRole)


        await self.bot.replace_roles(author, *authorRoles)

        await self.bot.say(':white_check_mark: ' + author.name + ', your region is now: ' + region.upper() + ' ' + earth_emoji)
        pass
    @commands.command(pass_context=True, no_pm=True)
    async def gr(self, ctx, gamerole):
        """Sets your priority [gamerole] (DPS, Flex, Tank, Support)"""
        gameroles = ['DPS', 'Flex', 'Tank', 'Support']
        message = ctx.message
        server = message.server
        if server.id not in self.servers:
            await self.bot.say("This function is not enabled. Please use `rankset` as an admin to enable it.")
            return
        author = message.author
        serverroles = server.roles
        authorroles = author.roles
        serverrolenames = [x.name for x in serverroles]
        for r in gameroles:
            if r not in serverrolenames:
                try:
                    await self.bot.say("{} role not detected, creating it in the server...".format(r))
                    await self.bot.create_role(server, name=r)
                except Forbidden:
                    await self.bot.say("I need to have the 'Manage Roles' permission to automatically add the right roles!")
        roleindex = -1

        if gamerole.lower() == 'dps':
            roleindex = 0
        elif gamerole.lower() == 'flex':
            roleindex = 1
        elif gamerole.lower() == 'tank':
            roleindex = 2
        elif gamerole.lower() == 'support':
            roleindex == 3
        else:
            await self.bot.send_message(message.channel, ':fire: ' + author.name + ', please set a valid game role. (DPS, Flex, Tank, Support)')
            return 

        for aRole in authorroles:
            if aRole.name in gameroles:
                authorroles.remove(aRole)

        for sRole in serverroles:
            if sRole.name in gameroles[roleindex]:
                authorroles.append(sRole)

        await self.bot.replace_roles(author, *authorroles)
        await self.bot.send_message(message.channel, ':white_check_mark: ' + author.name + ', your game role is now: ' + gamerole.upper())
        pass

    @commands.command(pass_context=True)
    async def platform(self, ctx, plat):
        """Use to apply a PS4, XBONE, or PC role to yourself. Can apply more than 1.(ps4, xbox, or pc)"""
        plat = plat.lower()
        platforms = ['PS4', 'XBOX', 'PC']
        message = ctx.message
        server = message.server
        if server.id not in self.servers:
            await self.bot.say("This function is not enabled. Please use `rankset` as an admin to enable it.")
            return
        author = message.author
        serverroles = server.roles
        authorroles = author.roles
        serverrolenames = [x.name for x in serverroles]
        for r in platforms:
            if r not in serverrolenames:
                try:
                    await self.bot.say("{} role not detected, creating it in the server...".format(r))
                    await self.bot.create_role(server, name=r)
                except Forbidden:
                    await self.bot.say("I need to have the 'Manage Roles' permission to automatically add the right roles!")
                    pass
        if plat == "pc":
            await self.bot.add_roles(author, "PC")
        elif plat == "xbox":
            await self.bot.add_roles(author, "XBOX")
        elif plat == "ps4":
            await self.bot.add_roles(author, "PS4")
        else:
            await self.bot.say(":fire: Please enter `pc` `ps4` or `xbox`!") 
        pass
    
    @commands.command(pass_context=True)
    async def ob(self, ctx, battletag):
        """Brings up stats from Overbuff with the given [BattleTag#0000]"""
        battleTag = battletag.replace("#", "-")
        link = "https://www.overbuff.com/players/pc/" + battleTag.rstrip()

        msgString = ':white_check_mark: Here is the OverBuff profile you searched for. \n' + link

        await self.bot.send_message(ctx.message.channel, msgString)
        pass
    
    @commands.command(pass_context=True)
    async def stats(self, ctx, battletag, comp="normal"):
        """Looks up a couple of stats from Overbuff.com  Add 'comp' as an argument to see a user's competitive stats. Percentage is NOT winrate, it is hero rank overall."""
        battletagurl = battletag.replace('#', '-')
        url = 'https://www.overbuff.com/players/pc/' + battletagurl
        if comp == "comp":
            url += "?mode=competitive"
        async with aiohttp.get(url) as response:
            soupobject = BeautifulSoup(await response.text(), "html.parser")
        stats = discord.Embed()
        h1 = soupobject.find_all('h1')
        for tag in h1:
            stats.add_field(name='Tag:', value=tag.get_text(), inline=True)
        sr = soupobject.find_all('span', class_='color-stat-rating')
        try:
            stats.add_field(name='Skill Rank:', value=sr[0].get_text(), inline=True)
        except IndexError:
            stats.add_field(name="Skill Rank:", value="User has no SR", inline=True)
        heroes = soupobject.find_all('a', class_='color-white')
        heroranks = soupobject.find_all('span', rel='tooltip')
        mostplayed = soupobject.find_all('div', class_='player-hero')
        i = 0
        topthree = ''
        for i in range (0, 3):
            try:
                topthree += '- {0:<11} Rank: {1:>5}'.format(heroes[i].get_text(), heroranks[i+1].get_text()) + '\n'
            except IndexError:
                topthree += 'No more heroes played.'
                break
        stats.add_field(name='Top Heroes Played:', value=topthree, inline = True)
        wins = soupobject.find_all('span', class_='color-stat-win')
        losses = soupobject.find_all('span', class_='color-stat-loss')
        total = int(int(wins[0].get_text()) + int(losses[0].get_text()))
        stats.add_field(name='Wins:', value=wins[0].get_text(), inline=True)
        stats.add_field(name='Losses:', value=losses[0].get_text() , inline=True)
        stats.add_field(name='Total Games: ', value=str(total), inline = True)
        await self.bot.say(embed=stats)
        pass
    
    @commands.command()
    async def invite(self):
        """Provides links to add RankBot to your own server."""
        embed = discord.Embed()
        embed.add_field(name='Invite me here:', value='https://discordapp.com/oauth2/authorize?client_id=268542937573359617&scope=bot&permissions=335019127')
        embed.add_field(name='My Support Server:', value='https://discord.gg/5JbuhSy')
        await self.bot.say(embed=embed)
        pass
    
    @commands.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions()
    async def rankset(self, ctx):
        """Turns on and off the rank, role, and region commands in the server"""
        TIMEOUT=10
        server = ctx.message.server
        if server.id in self.servers:
            self.servers.remove(server.id)
            await self.bot.say("Rank commands are turned off in the server. Don't forget to delete the roles unless"
                               " you plan on turning this on again.")
        else:
            await self.bot.say("Do you want to enable Rank commands in the server?"
                               " This will automatically create all the necessary roles when using each command"
                               " for the first time only. If this is ok type 'yes'")
            response = await self.bot.wait_for_message(timeout=TIMEOUT, author=ctx.message.author, content="yes")
            if response is not None and response.content=="yes":
                self.servers.append(server.id)
                await self.bot.say("Rank commands have been enabled.")
            else:
                await self.bot.say("This will not be enabled for now.")
        dataIO.save_json("data/rank/servers.json", self.servers)
        pass
        
    
    def author_role(role):
        if role.name.capitalize() in skillRankRoles:
            return role
        
def check_folders():
    if not os.path.exists("data/rank"):
        print("Creating rank folder...")
        os.makedirs("data/rank")

def check_files():
    f = "data/rank/servers.json"
    if not dataIO.is_valid_json(f):
        dataIO.save_json(f, [])

def setup(bot):
    check_folders()
    check_files()
    bot.add_cog(Rank(bot))
