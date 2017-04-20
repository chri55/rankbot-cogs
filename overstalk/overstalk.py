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
    async def recent(self, ctx):
        """Grabs the most recent saved post from overstalk.io"""
        channel_obj = ctx.message.channel
        title = self.most_recent["TITLE"]
        content = self.most_recent["CONTENT"]
        stamps = self.most_recent["TIME"]
        forum_link = self.most_recent["LINK"]
        try:
            post = discord.Embed()
            post.add_field(name="New Post From overstalk.io:", value=title)
            await self.bot.send_message(channel_obj, embed=post)
        except:    
            await self.bot.say("New post from overstalk.io: {}".format(title))
        pass
        
    @commands.command(pass_context=True)
    async def stalkset(self, ctx):
        """Settings to add overstalk.io notifications to a channel"""
        channel = ctx.message.channel
        if channel.id in self.most_recent["CHANNELS"]:
                self.most_recent["CHANNELS"].remove(channel.id)
                await self.bot.say("Alert has been removed "
                                   "from this channel.")
        else:
            self.most_recent["CHANNELS"].append(channel.id)
            await self.bot.say("Alert activated. I will notify this " +
                               "channel everytime there is a new post.")
        dataIO.save_json("data/overstalk/recent.json", self.most_recent)
        
    @commands.command(pass_context=True, hidden=True)
    @checks.is_owner()
    async def stalkupdate(self, ctx):
        await self.site_checker()
        dataIO.save_json("data/overstalk/recent.json", self.most_recent)
        await self.bot.say("Recent post from overstalk.io has been updated")
        
    async def site_checker(self):
        CHECK_DELAY = 60 

        url = "http://www.overstalk.io/?sources=BLIZZARD_FORUM"
        while self == self.bot.get_cog("Overstalk"):
            async with aiohttp.get(url) as response:
                soup_obj = BeautifulSoup(await response.text(), "html.parser")
            titlecode = soup_obj.find_all(class_="os-post-header col-md-8")[0]
            title = titlecode.get_text()
            content = soup_obj.find_all(class_="os-post-content card-block")[0].get_text()
            stamps = soup_obj.find_all(class_="os-post-meta col-md-4 text-right")[0].get_text()
            forum_link = titlecode.find_all("a")[0].get_text()
            await asyncio.sleep(0.5)
            if title == self.most_recent["TITLE"] and content == self.most_recent["CONTENT"]:
                # I think it's safe to assume the same 
                # post content AND title would not happen
                # twice in a row
                print("No new posts. Sleeping...")
            else:
                self.most_recent["TITLE"] = title
                self.most_recent["CONTENT"] = content
                self.most_recent["TIME"] = stamps
                self.most_recent["LINK"] = forum_link
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
                            await self.bot.send_message(channel_obj, embed=post)
                        except:    
                            await self.bot.say("New post from overstalk.io: {}".format(title))
                        #if len(title) + len(content) + len(stamps) > 2000:
                        #    post = discord.Embed()
                        #    post.add_field(name="New Post From overstalk.io:", value=forum_link)
                        #    post.set_footer(text="The post was too long to send on Discord.")
                        #else:    
                        #    post = embed_format(title, content, stamps)
                        #    await self.bot.send_message(channel_obj, embed=post)
                dataIO.save_json("data/overstalk/recent.json", self.most_recent)
                print("Got new post.  Sleeping...")
            await asyncio.sleep(CHECK_DELAY)
            
def embed_format(title, content, stamps):
    post = discord.Embed()
    post.add_field(name=title, value=content)
    post.set_footer(text=stamps)
    return post

def post_format(title, content, stamps):
    post = ""
    post += "__***{}***__\n\n".format(title)
    post += "{}\n\n".format(content)
    post += "{}\n(This post did not send in Embed format because the content was too long. Sorry!)".format(stamps)
    return post
            
def check_folders():
    if not os.path.exists("data/overstalk"):
        print("Creating data/overstalk folder...")
        os.makedirs("data/overstalk")


def check_files():
    f = "data/overstalk/recent.json"
    if not dataIO.is_valid_json(f):
        print("Creating empty recent.json...")
        dataIO.save_json(f, [])
        

def setup(bot):
    check_folders()
    check_files()
    n = Overstalk(bot)
    loop = asyncio.get_event_loop()
    loop.create_task(n.site_checker())
    bot.add_cog(Overstalk(bot))
    
    