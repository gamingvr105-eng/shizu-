"""
Shizu Security - Zero-Trust System Diagnostics & Configuration
Provides server security status, latency diagnostics, stats, and log channel configuration.
"""

import discord
from discord.ext import commands
import sys
import psutil
import time
import datetime
from typing import Optional, Literal

from config import config
from core.checks import is_guild_owner_or_extra

start_time = time.time()

class SystemCommands(commands.Cog, name="System"):
    """Core utilities, server security dashboard, diagnostics, and prefix configuration."""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="security", aliases=["secstatus", "sec"])
    @commands.guild_only()
    async def security_status(self, ctx):
        """Displays the comprehensive Zero-Trust security dashboard for this server."""
        cfg = await self.bot.db.get_guild_config(ctx.guild.id)
        whitelisted = await self.bot.db.get_all_whitelist_entities(ctx.guild.id)
        extra_owners = await self.bot.db.get_extra_owners(ctx.guild.id)
        raw_am_rules = await self.bot.db.get_all_automod_rules(ctx.guild.id)
        am_rules = {r["rule_name"]: r for r in raw_am_rules}
        bad_words = await self.bot.db.get_badwords(ctx.guild.id)

        an_active = cfg.get("antinuke_enabled")
        ab_active = cfg.get("antibot_enabled")
        am_active = cfg.get("automod_enabled")
        is_locked = cfg.get("emergency_locked")

        sec_log = ctx.guild.get_channel(cfg.get("log_antinuke")) if cfg.get("log_antinuke") else None
        mod_log = ctx.guild.get_channel(cfg.get("log_moderation")) if cfg.get("log_moderation") else None

        bot_perms = ctx.guild.me.guild_permissions
        healthy = (
            bot_perms.administrator or 
            (bot_perms.manage_roles and bot_perms.manage_channels and bot_perms.ban_members and bot_perms.view_audit_log)
        )
        health_str = f"{config.ANIM_SUCCESS} Optimal (Admin)" if bot_perms.administrator else (f"{config.ANIM_WARN} Partial" if healthy else f"{config.ANIM_WARN} Critical")

        embed = discord.Embed(
            title=f"{config.ANIM_SHIELD} {ctx.guild.name} — Security Health & Dashboard",
            color=config.COLOR_DARK
        )
        embed.add_field(
            name="🛡️ Anti-Nuke & Anti-Bot",
            value=(
                f"• Anti-Nuke: {config.ANIM_SUCCESS + ' **Armed**' if an_active else config.ANIM_WARN + ' **Disabled**'}\n"
                f"• Anti-Bot: {config.ANIM_SUCCESS + ' **Armed**' if ab_active else config.ANIM_WARN + ' **Disabled**'}\n"
                f"• Punishment: `{(cfg.get('antinuke_punishment') or 'ban').upper()}`\n"
                f"• Burst Limit: `{config.MAX_BURST_ACTIONS} actions / {config.BURST_WINDOW}s`\n"
                f"• Whitelisted Entities: `{len(whitelisted)}`\n"
                f"• Extra Owners: `{len(extra_owners)}`"
            ),
            inline=True
        )
        embed.add_field(
            name="⚡ AutoMod Engine",
            value=(
                f"• Status: {config.ANIM_SUCCESS + ' **Armed**' if am_active else config.ANIM_WARN + ' **Disabled**'}\n"
                f"• Active Rules: `{sum(1 for r in am_rules.values() if r.get('enabled'))} / {len(am_rules)}`\n"
                f"• Bad Words: `{len(bad_words)}` blacklisted\n"
                f"• Server Lockdown: {'🔒 Active' if is_locked else '🔓 Normal'}"
            ),
            inline=True
        )
        embed.add_field(
            name="📋 Dedicated Audit Channels",
            value=(
                f"• **Shizu Security Logs:** {sec_log.mention if sec_log else '*Unlinked (`?setlog security #channel`)*'}\n"
                f"• **Shizu Mod Logs:** {mod_log.mention if mod_log else '*Unlinked (`?setlog mod #channel`)*'}"
            ),
            inline=False
        )
        embed.add_field(
            name="⚙️ Diagnostics & Role Position",
            value=(
                f"• Bot Perms: {health_str}\n"
                f"• Bot Top Role: {ctx.guild.me.top_role.mention} (Pos: `{ctx.guild.me.top_role.position}`)\n"
                f"• TopCheck: {'🟢 Enabled' if cfg.get('topcheck_enabled', True) else '🔴 Disabled'}"
            ),
            inline=False
        )

        embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else self.bot.user.display_avatar.url)
        embed.set_footer(text=f"Shizu Security v{config.VERSION} • Developers: {config.DEVELOPER_STRING}", icon_url=self.bot.user.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="setlog", usage="setlog <security|mod> <#channel>")
    @commands.guild_only()
    @is_guild_owner_or_extra()
    async def setlog(self, ctx, log_type: str, channel: discord.TextChannel):
        """Binds a dedicated log channel: `security` (for Anti-Nuke/Anti-Bot) or `mod` (for Staff Mod)."""
        clean_type = log_type.lower()
        if clean_type in ("security", "antinuke", "sec", "safety", "automod"):
            db_key = "log_antinuke"
            label = "SHIZU SECURITY LOGS"
        elif clean_type in ("mod", "moderation", "staff"):
            db_key = "log_moderation"
            label = "SHIZU MOD LOGS"
        else:
            await ctx.reply_error(f"Invalid log type! Please use `{ctx.prefix}setlog security #channel` or `{ctx.prefix}setlog mod #channel`.")
            return

        await self.bot.db.update_guild_config(ctx.guild.id, **{db_key: channel.id})

        # Send confirmation into the target log channel with top-right thumbnail
        try:
            embed = discord.Embed(
                title=f"{config.ANIM_SUCCESS} Dedicated Log Channel Activated",
                description=f"This channel has been bound as the dedicated **{label}** for **{ctx.guild.name}**.",
                color=config.COLOR_DARK
            )
            embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else ctx.author.display_avatar.url)
            embed.set_footer(text=f"Shizu Security v{config.VERSION}")
            embed.timestamp = discord.utils.utcnow()
            await channel.send(embed=embed)
        except Exception:
            pass

        await ctx.reply_success(f"Dedicated **{label}** set to: {channel.mention}")

    @commands.command(name="ping", aliases=["latency"])
    async def ping(self, ctx):
        """Measures Discord gateway latency and API roundtrip."""
        start = time.perf_counter()
        msg = await ctx.reply_loading("Pinging gateway...")
        end = time.perf_counter()

        api_latency = round(self.bot.latency * 1000)
        roundtrip = round((end - start) * 1000)

        embed = discord.Embed(
            title=f"{config.ANIM_SHIELD} Shizu Latency Diagnostics",
            description=(
                f"• **Gateway Latency:** `{api_latency}ms`\n"
                f"• **Roundtrip Response:** `{roundtrip}ms`\n"
                f"• **Shards:** `{self.bot.shard_count or 1}`"
            ),
            color=config.COLOR_DARK
        )
        await msg.edit(content=None, embed=embed)

    @commands.command(name="stats", aliases=["botinfo", "about", "info"])
    async def stats(self, ctx):
        """Displays system specifications, uptime, memory, and developer credits."""
        uptime_seconds = int(time.time() - start_time)
        uptime = str(datetime.timedelta(seconds=uptime_seconds))

        total_guilds = len(self.bot.guilds)
        total_members = sum(g.member_count or 0 for g in self.bot.guilds)
        total_channels = sum(len(g.channels) for g in self.bot.guilds)

        mem = psutil.virtual_memory()
        cpu = psutil.cpu_percent()

        embed = discord.Embed(
            title=f"{config.ANIM_SHIELD} Shizu Security — System Specifications",
            description=(
                f"High-performance standalone Discord defense system engineered for "
                f"Zero-Trust Anti-Nuke, AutoMod, and strict Moderation enforcement."
            ),
            color=config.COLOR_DARK
        )
        embed.add_field(name="Developers", value=f"**{config.DEVELOPER_STRING}**", inline=True)
        embed.add_field(name="Version", value=f"`v{config.VERSION}` (Zero-Trust)", inline=True)
        embed.add_field(name="Uptime", value=f"`{uptime}`", inline=True)
        embed.add_field(name="Guilds Protected", value=f"`{total_guilds}`", inline=True)
        embed.add_field(name="Users Guarded", value=f"`{total_members:,}`", inline=True)
        embed.add_field(name="Channels Watched", value=f"`{total_channels:,}`", inline=True)
        embed.add_field(name="Memory Usage", value=f"`{mem.percent}%` ({round(mem.used / 1024 / 1024)} MB)", inline=True)
        embed.add_field(name="CPU Load", value=f"`{cpu}%`", inline=True)
        embed.add_field(name="Library", value=f"`discord.py v{discord.__version__}`", inline=True)

        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="setprefix", aliases=["prefix"], usage="setprefix <new_prefix>")
    @commands.guild_only()
    @is_guild_owner_or_extra()
    async def setprefix(self, ctx, new_prefix: str):
        """Configures a custom command prefix for this server."""
        if len(new_prefix) > 5:
            return await ctx.reply_error("Prefix cannot exceed 5 characters.")

        await self.bot.db.set_prefix(ctx.guild.id, new_prefix)
        await ctx.reply_success(f"Server command prefix updated to: `{new_prefix}`")

    @commands.command(name="topcheck", usage="topcheck <enable|disable>")
    @commands.guild_only()
    @is_guild_owner_or_extra()
    async def topcheck_cmd(self, ctx, state: Literal["enable", "disable"]):
        """Toggles the top-role hierarchy requirement for moderators."""
        enabled = (state == "enable")
        await self.bot.db.update_guild_config(ctx.guild.id, topcheck_enabled=enabled)
        state_str = "Enabled" if enabled else "Disabled"
        await ctx.reply_success(
            f"TopCheck role hierarchy verification is now **{state_str}**.\n"
            + ("Moderators must possess a role strictly above the bot's highest role." if enabled else "Role check bypassed.")
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Responds with server prefix and help info when the bot is mentioned."""
        if message.author.bot or not message.guild:
            return

        bot_user = self.bot.user
        if bot_user in message.mentions and not message.mention_everyone:
            clean_content = message.content.strip()
            mention_strings = [f"<@{bot_user.id}>", f"<@!{bot_user.id}>"]
            if clean_content in mention_strings:
                prefix = await self.bot.db.get_prefix(message.guild.id)
                cfg = await self.bot.db.get_guild_config(message.guild.id)
                an_status = "🟢 Active" if cfg.get("antinuke_enabled") else "🔴 Disabled"
                ab_status = "🟢 Active" if cfg.get("antibot_enabled") else "🔴 Disabled"

                embed = discord.Embed(
                    title=f"{config.ANIM_SHIELD} Hey {message.author.name}, I am Shizu Security!",
                    description=(
                        f"My command prefix for **{message.guild.name}** is: `{prefix}`\n"
                        f"Type `{prefix}help` to view all security and moderation commands.\n\n"
                        f"• **Anti-Nuke Status:** {an_status}\n"
                        f"• **Anti-Bot Status:** {ab_status}\n"
                        f"• **Developers:** {config.DEVELOPER_STRING}"
                    ),
                    color=config.COLOR_DARK
                )
                embed.set_thumbnail(url=bot_user.display_avatar.url)
                embed.set_footer(text=f"Shizu Security v{config.VERSION} • 24/7 Automated Protection")
                embed.timestamp = discord.utils.utcnow()

                view = discord.ui.View()
                invite_url = f"https://discord.com/oauth2/authorize?client_id={bot_user.id}&permissions=8&scope=bot%20applications.commands"
                view.add_item(discord.ui.Button(label="Invite Shizu", url=invite_url, style=discord.ButtonStyle.link))
                view.add_item(discord.ui.Button(label="Support Server", url="https://discord.gg/shizu", style=discord.ButtonStyle.link))

                try:
                    await message.reply(embed=embed, view=view, mention_author=False)
                except Exception:
                    pass

async def setup(bot):
    await bot.add_cog(SystemCommands(bot))
