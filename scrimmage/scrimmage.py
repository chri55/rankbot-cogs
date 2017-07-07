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
        self.schedule = dataIO.load_json("data/scrimmage/schedule.json")

    @commands.command(pass_context=True, no_pm=True)
    async def checkin(self, ctx):
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
                await self.bot.create_role(server, name="Playing", mentionable=True)
            except Forbidden:
                await self.bot.say("I need 'Manage Server' permissions to automatically create roles.")
                return
        for r in server.roles:
            if r.name == "Playing":
                role = r
        if role not in author.roles:
            await self.bot.add_roles(author, role)
            await self.bot.say("You are now set to ***play today, {}***".format(author.name))
        else:
            await self.bot.remove_roles(author, role)
            await self.bot.say("You are ***no longer set to play, {}***".format(author.name))
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
                        await self.bot.create_role(server, name="Playing", mentionable=True)
                        await self.bot.say("All have been removed from the Playing role")
                        return
                    except Forbidden:
                        await self.bot.say("I need 'Manage Server' permissions to do this.")
                        return
        pass

    @commands.command(pass_context=True, no_pm=True)
    async def scrimmage(self, ctx, teamcap1 : discord.Member, teamcap2 : discord.Member, time, timezone):
        """Allows for team captains to set a time for a scheduled scrimmage and be reminded"""
        author = ctx.message.author
        server = ctx.message.server
        tc1ID = teamcap1.id
        tc2ID = teamcap2.id

        timeHR = time.split(":")[0]
        timeMIN = time.split(":")[1]

        if tc1ID != author.id:
            await self.bot.say("Have the team captain mention themself first: `{}scrimmage @author/TeamCaptain @otherTeamCaptain time timezone`".format(ctx.prefix))
            pass

        ## TODO GET LIST OF TIMEZONES AND CONVERT. WILL USE EST
        ## FOR TESTING FOR NOW

        if server.id not in self.servers:
            await self.bot.say("Settings for the Scrimmage module haven't been enabled in this server yet.")
            pass

        to_save = "Team {} vs. Team {} - {} {}".format(teamcap1, teamcap2, time, timezone)
        self.schedule["{}|{}".format(tc1ID, tc2ID)] = {}
        self.schedule["{}|{}".format(tc1ID, tc2ID)]["cap1"] = teamcap1.name
        self.schedule["{}|{}".format(tc1ID, tc2ID)]["cap2"] = teamcap2.name
        self.schedule["{}|{}".format(tc1ID, tc2ID)]["time"] = time
        self.schedule["{}|{}".format(tc1ID, tc2ID)]["zone"] = timezone
        dataIO.save_json("data/scrimmage/schedule.json", self.schedule)

        await self.bot.say("The scrimmage has been saved as ```{}```".format(to_save))


        pass

    @commands.command(pass_context=True, no_pm=True)
    async def loadscrims(self, ctx):
        """Loads all scrims that the player has assigned"""
        author = ctx.message.author
        server = ctx.message.server

        output = "```Ruby\nScrims for {}:\n".format(author.name)
        for scrim in self.schedule:
            if author.id in scrim:
                output += "{} vs. {} - {} {}\n".format(scrim["cap1"], scrim["cap2"], scrim["time"], scrim["timezone"])
        output += "```"
        await self.bot.say(output)
        pass

    @commands.command(pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_server=True)
    async def scrimset(self, ctx):
        """Turn scrim settings on or off for this server."""
        server = ctx.message.server
        if server.id in self.servers:
            self.servers.remove(server.id)
            await self.bot.say("Scrimmage options have been turned ***`off`*** in this server.")
        else:
            self.servers.append(server.id)
            await self.bot.say("Scrimmage options have been turned ***`on`*** in this server.")
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
    f = "data/scrimmage/schedule.json"
    if not dataIO.is_valid_json(f):
        dataIO.save_json(f, {})

def setup(bot):
    check_folders()
    check_files()
    bot.add_cog(Scrimmage(bot))
