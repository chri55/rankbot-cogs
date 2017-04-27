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

class Fight:
    """Fight your friends (or enemies) for money!"""