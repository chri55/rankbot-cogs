import discord
from discord.ext import commands
from bs4 import BeautifulSoup
import requests
import aiohttp
import time
from .utils.dataIO import dataIO
from .utils.chat_formatting import escape_mass_mentions
from .utils import checks
import asyncio
import os


class Overstalk:
    """Grabs a couple of posts from overstalk.io.
    Only Blizzard Forum posts for now."""

    def __init__(self, bot):
        self.bot = bot
        self.most_recent = dataIO.load_json("data/overstalk/recent.json")
        
    @commands.command(pass_context=True)
    @checks.admin_or_permissions()
    async def stalkset(self, ctx):
        ############################################################
        ## TODO: MAKE THIS GRAB ALL CHANNELS AND HAVE THEM SELECT ##
        ############################################################
        """Settings to add overstalk.io notifications to a channel"""
        chans = [chan for chan in ctx.message.server.channels]
        help_str = "***Choose a channel on the server to send these alerts to by specicfying the number:\n***"
        num = 1
        for chan in chans:
            help_str += str(num) + ": " + chan.name + "\n"
            num += 1
        await self.bot.say(help_str)
        resp = await self.bot.wait_for_message(timeout = 15, author = ctx.message.author)
        if int(resp.content) <= num and int(resp.content) >= 1:
            #try:
            if chans[int(resp.content)-1].id not in self.most_recent["CHANNELS"]:
                self.most_recent["CHANNELS"].append(chans[int(resp.content)-1].id)
                await self.bot.say("This channel will now get Overstalk.io alerts.")
            else:
                await self.bot.say("The channel already gets alerts.")
            #except:
            #    await self.bot.say("The list has not been populated properly. Contact the bot owner for help.")
        dataIO.save_json("data/overstalk/recent.json", self.most_recent)
        pass
        
        
    async def site_checker(self):
        CHECK_DELAY = 60 

        url = "http://www.overstalk.io/?sources=BLIZZARD_FORUM"
        while self == self.bot.get_cog("Overstalk"):
            async with aiohttp.get(url) as response:
                soup_obj = BeautifulSoup(await response.text(), "html.parser")
            titlecode = soup_obj.find_all(class_="os-post-header col-md-8")[0]
            title = soup_obj.find_all(class_="os-post-header col-md-8")[0].get_text()
            link = soup_obj.find(class_="os-post-header col-md-8").a.get('href')
            stamps = soup_obj.find_all(class_="os-post-meta col-md-4 text-right")[0].get_text()
            await asyncio.sleep(0.5)
            if title == self.most_recent["TITLE"] and link == self.most_recent["LINK"]:
                # I think it's safe to assume the same 
                # post content AND title would not happen
                # twice in a row
                print("No new posts. Sleeping...")
            else:
                dataIO.save_json("data/overstalk/recent.json", self.most_recent)
                await asyncio.sleep(0.5)
                for channel in self.most_recent["CHANNELS"]:
                    channel_obj = self.bot.get_channel(channel)
                    if channel_obj is None:
                        continue
                    can_speak = channel_obj.permissions_for(channel_obj.server.me).send_messages
                    if channel_obj and can_speak:
                        try:
                            post = discord.Embed()
                            post.add_field(name="New Post From overstalk.io:", value=title)
                            post.add_field(name="Link:", value=title)
                            post.set_footer(text=stamps)
                            await self.bot.send_message(channel_obj, embed=post)
                        except:
                            await self.bot.say("I need to be able to post embeds in this channel.")
                self.most_recent["TITLE"] = title
                self.most_recent["LINK"] = link
                self.most_recent["STAMPS"] = stamps
                dataIO.save_json("data/overstalk/recent.json", self.most_recent)
                print("Got new post.  Sleeping...")
            await asyncio.sleep(CHECK_DELAY)

    @commands.command(pass_context=True)
    async def recent(self):
        url = "http://www.overstalk.io/?sources=BLIZZARD_FORUM"
        async with aiohttp.get(url) as response:
            soup_obj = BeautifulSoup(await response.text(), "html.parser")
            titlecode = soup_obj.find_all(class_="os-post-header col-md-8")[0]
            title = soup_obj.find_all(class_="os-post-header col-md-8")[0].get_text()
            link = soup_obj.find(class_="os-post-header col-md-8").a
            link = link.get('href')
            stamps = soup_obj.find_all(class_="os-post-meta col-md-4 text-right")[0].get_text()
            await asyncio.sleep(0.5)
            if title == self.most_recent["TITLE"] and link == self.most_recent["LINK"]:
                # I think it's safe to assume the same 
                # post content AND title would not happen
                # twice in a row
                print("No new posts. Sleeping...")
            else:
                dataIO.save_json("data/overstalk/recent.json", self.most_recent)
                await asyncio.sleep(0.5)
                for channel in self.most_recent["CHANNELS"]:
                    channel_obj = self.bot.get_channel(channel)
                    if channel_obj is None:
                        continue
                    can_speak = channel_obj.permissions_for(channel_obj.server.me).send_messages
                    if channel_obj and can_speak:
                        try:
                            post = discord.Embed()
                            post.add_field(name="New Post From overstalk.io: {}".format(title), value=link)
                            post.set_footer(text=stamps)
                            await self.bot.send_message(channel_obj, embed=post)
                        except:
                            await self.bot.say("I need to be able to post embeds in this channel.")
                self.most_recent["TITLE"] = title
                self.most_recent["LINK"] = link
                self.most_recent["STAMPS"] = stamps
                dataIO.save_json("data/overstalk/recent.json", self.most_recent)
                print("Got new post.  Sleeping...")
            
            
def check_folders():
    if not os.path.exists("data/overstalk"):
        print("Creating data/overstalk folder...")
        os.makedirs("data/overstalk")


def check_files():
    f = "data/overstalk/recent.json"
    if not dataIO.is_valid_json(f):
        print("Creating empty recent.json...")
        dataIO.save_json(f, {"TITLE": "", "LINK" : "", "STAMPS" : "", "CHANNELS" : ["0000000000"]}) #Dummy channel
     

def setup(bot):
    check_folders()
    check_files()
    n = Overstalk(bot)
    loop = asyncio.get_event_loop()
    loop.create_task(n.site_checker())
    bot.add_cog(n)
    
    
