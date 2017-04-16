import discord
from discord.ext import commands
from bs4 import BeautifulSoup
import requests
import aiohttp

class Rank:
    """Server commands for users to assign themselves skill rank roles, region, and game role.
       Also finds and displays OverBuff and OverwatchTracker profiles."""

    skillRankRoles = ['Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond', 'Master', 'Grandmaster']
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True, no_pm=True)
    async def sr(self, ctx, sr):
        """Assigns SR based on the integer [sr] given. (1-5000). 0 no longer removes rank (edited 4/11/17)"""
        skillRankRoles = ['Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond', 'Master', 'Grandmaster']

        server = ctx.message.server
        serverroles = ctx.message.server.roles
        authorroles = ctx.message.author.roles
        messagechannel = ctx.message.channel
        serverrolenames = list([lambda x : x.name in serverroles])
        
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
        serverrolenames = list([lambda x : x.name in serverRoles])
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
        author = message.author
        serverroles = server.roles
        authorroles = author.roles
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
        embed.add_field(name='Invite me here:', value='https://discordapp.com/oauth2/authorize?client_id=268542937573359617&scope=bot&permissions=536063039')
        embed.add_field(name='My Support Server:', value='https://discord.gg/5JbuhSy')
        await self.bot.say(embed=embed)
        pass
    
    def author_role(role):
        if role.name.capitalize() in skillRankRoles:
            return role

def setup(bot):
    bot.add_cog(Rank(bot))
