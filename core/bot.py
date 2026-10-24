import discord
from discord.ext import commands
import os
import sys
import logging
from typing import List, Optional

import config
from .database import Database
from .context import Context

logger = logging.getLogger("ShizuSecurity")

COGS: List[str] = [
    "cogs.antinuke.events",
    "cogs.antinuke.commands",
    "cogs.automod.listener",
    "cogs.automod.commands",
    "cogs.moderation.commands",
    "cogs.moderation.cases",
    "cogs.general.help",
    "cogs.general.system"
]

class ShizuSecurity(commands.AutoShardedBot):
    def __init__(self):
        intents = discord.Intents.all()
        intents.presences = True
        intents.members = True
        intents.message_content = True

        super().__init__(
            command_prefix=self.determine_prefix,
            case_insensitive=True,
            intents=intents,
            owner_ids=set(config.OWNER_IDS),
            strip_after_prefix=True,
            help_command=None,
            allowed_mentions=discord.AllowedMentions(everyone=False, replied_user=False, roles=False)
        )
        self.db = Database(config.DATABASE_PATH)
        self.color = config.COLOR_DEFAULT

    async def determine_prefix(self, bot, message: discord.Message) -> List[str]:
        if not message.guild:
            return commands.when_mentioned_or(config.DEFAULT_PREFIX)(bot, message)
        prefix = await self.db.get_prefix(message.guild.id)
        return commands.when_mentioned_or(prefix)(bot, message)

    async def get_context(self, message: discord.Message, *, cls=Context) -> Context:
        return await super().get_context(message, cls=cls)

    async def setup_hook(self):
        """Initializes database and loads all security and moderation modules."""
        logger.info("Initializing Shizu Security database...")
        await self.db.connect()

        logger.info("Loading extensions...")
        for cog in COGS:
            try:
                await self.load_extension(cog)
                logger.info(f"Loaded extension: {cog}")
            except Exception as e:
                logger.error(f"Failed to load extension {cog}: {e}", exc_info=True)

    async def on_ready(self):
        total_guilds = len(self.guilds)
        total_users = sum(g.member_count or 0 for g in self.guilds)
        
        banner = f"""
=========================================================
  SHIZU SECURITY -- HIGH PERFORMANCE DISCORD DEFENSE
  Version: {config.VERSION}
  Developers: {config.DEVELOPER_STRING}
  Logged in as: {self.user} (ID: {self.user.id})
  Guilds: {total_guilds} | Users Protected: {total_users}
=========================================================
"""
        print(banner)
        logger.info(f"Shizu Security online as {self.user}")

        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"security across {total_guilds} guilds | {config.DEFAULT_PREFIX}help"
        )
        await self.change_presence(status=discord.Status.dnd, activity=activity)

    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.content != after.content and not after.author.bot:
            ctx = await self.get_context(after, cls=Context)
            if ctx.command:
                await self.invoke(ctx)

    async def close(self):
        logger.info("Shutting down Shizu Security...")
        await self.db.close()
        await super().close()
