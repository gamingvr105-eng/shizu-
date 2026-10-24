"""
Shizu Security - Zero-Trust AutoMod Commands
Manages rule toggles, punishments, word blacklists, and exemptions.
Thresholds are fixed internally for rock-solid stability without configuration bloat.
"""

import discord
from discord.ext import commands
from typing import Literal, Optional, Union
from config import config
from core.checks import is_guild_owner_or_extra

VALID_RULES = ["spam", "invite", "link", "badwords", "caps", "mention", "emoji"]

class AutoModCommands(commands.Cog, name="AutoMod"):
    """Commands for managing Shizu AutoMod filters, punishments, bad words, and exemptions."""
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="automod", invoke_without_command=True)
    @commands.guild_only()
    @is_guild_owner_or_extra()
    async def automod(self, ctx):
        """View AutoMod control dashboard and command usage."""
        prefix = ctx.prefix
        cfg = await self.bot.db.get_guild_config(ctx.guild.id)
        status_str = f"{config.ANIM_SUCCESS} **Active**" if cfg.get("automod_enabled") else f"{config.ANIM_WARN} **Disabled**"

        embed = discord.Embed(
            title=f"{config.ANIM_SHIELD} Shizu AutoMod Control Center",
            description=f"Global Engine: {status_str}",
            color=config.COLOR_DARK
        )
        embed.add_field(
            name="General Management",
            value=(
                f"`{prefix}automod enable` — Arms AutoMod message scanning\n"
                f"`{prefix}automod disable` — Disarms AutoMod message scanning\n"
                f"`{prefix}automod status` — View active rule matrix and fixed thresholds\n"
                f"`{prefix}setlog automod <#channel>` — Set dedicated AutoMod log channel"
            ),
            inline=False
        )
        embed.add_field(
            name="Rule Configuration",
            value=(
                f"`{prefix}automod rule <rule> <enable|disable>` — Toggle individual filter\n"
                f"`{prefix}automod punish <rule> <delete|warn|timeout|kick|ban> [minutes]` — Configure penalty\n"
                f"*Valid Rules:* `spam`, `invite`, `link`, `badwords`, `caps`, `mention`, `emoji`"
            ),
            inline=False
        )
        embed.add_field(
            name="Exemptions & Word Blacklist",
            value=(
                f"`{prefix}automod ignore <channel|role|user> <target>` — Exclude from AutoMod\n"
                f"`{prefix}automod unignore <channel|role|user> <target>` — Remove exemption\n"
                f"`{prefix}automod ignored` — View all active exemptions\n"
                f"`{prefix}badwords add <word>` — Add term to word-boundary filter\n"
                f"`{prefix}badwords remove <word>` — Remove term from filter\n"
                f"`{prefix}badwords list` — View blacklisted terms"
            ),
            inline=False
        )
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()
        await ctx.reply(embed=embed, mention_author=False)

    @automod.command(name="enable")
    @commands.guild_only()
    @is_guild_owner_or_extra()
    async def automod_enable(self, ctx):
        """Globally arms the AutoMod engine."""
        await self.bot.db.update_guild_config(ctx.guild.id, automod_enabled=True)
        await ctx.reply_success(
            "**AutoMod is now ARMED!**\nAll enabled filters are actively inspecting incoming messages."
        )

    @automod.command(name="disable")
    @commands.guild_only()
    @is_guild_owner_or_extra()
    async def automod_disable(self, ctx):
        """Globally disarms the AutoMod engine."""
        await self.bot.db.update_guild_config(ctx.guild.id, automod_enabled=False)
        await ctx.reply_warning("AutoMod system has been **DISARMED**. Messages will not be filtered.")

    @automod.command(name="rule")
    @commands.guild_only()
    @is_guild_owner_or_extra()
    async def automod_rule(self, ctx, rule: str, state: Literal["enable", "disable"]):
        """Toggles an individual AutoMod rule on or off."""
        rule_name = rule.lower()
        if rule_name not in VALID_RULES:
            return await ctx.reply_error(f"Invalid rule name. Choose from: `{', '.join(VALID_RULES)}`.")

        enabled = (state == "enable")
        await self.bot.db.update_automod_rule(ctx.guild.id, rule_name, enabled=enabled)
        state_str = "Enabled" if enabled else "Disabled"
        await ctx.reply_success(f"Rule **{rule_name.capitalize()}** is now **{state_str}**.")

    @automod.command(name="punish")
    @commands.guild_only()
    @is_guild_owner_or_extra()
    async def automod_punish(
        self,
        ctx,
        rule: str,
        punishment: Literal["delete", "warn", "timeout", "kick", "ban"],
        timeout_minutes: Optional[int] = 5
    ):
        """Sets the punishment action for an AutoMod rule."""
        rule_name = rule.lower()
        if rule_name not in VALID_RULES:
            return await ctx.reply_error(f"Invalid rule name. Choose from: `{', '.join(VALID_RULES)}`.")

        timeout_seconds = (timeout_minutes or 5) * 60
        await self.bot.db.update_automod_rule(
            ctx.guild.id,
            rule_name,
            punishment=punishment.lower(),
            timeout_duration=timeout_seconds
        )
        await ctx.reply_success(
            f"Punishment for **{rule_name.capitalize()}** set to: **{punishment.upper()}**"
            + (f" ({timeout_minutes}m)" if punishment == "timeout" else "")
        )

    @automod.command(name="status")
    @commands.guild_only()
    @is_guild_owner_or_extra()
    async def automod_status(self, ctx):
        """Displays full rule matrix, configured punishments, and fixed calibrated thresholds."""
        cfg = await self.bot.db.get_guild_config(ctx.guild.id)
        raw_rules = await self.bot.db.get_all_automod_rules(ctx.guild.id)
        rules = {r["rule_name"]: r for r in raw_rules}
        log_ch = ctx.guild.get_channel(cfg.get("log_automod")) if cfg.get("log_automod") else None

        embed = discord.Embed(
            title=f"{config.ANIM_SHIELD} Shizu AutoMod Rules Matrix",
            color=config.COLOR_DARK
        )
        embed.description = (
            f"**System State:** {'🟢 ARMED' if cfg.get('automod_enabled') else '🔴 DISARMED'}\n"
            f"**Log Channel:** {log_ch.mention if log_ch else '*Not Configured*'}\n"
            f"*Thresholds are fixed internally for maximum stability without false positives.*"
        )

        fixed_thresholds = {
            "spam": "5 msgs / 5s",
            "invite": "Instant (Vanity URL exempt)",
            "link": "Instant (Media whitelisted)",
            "badwords": "Instant (Word boundary regex)",
            "caps": "70% uppercase (>8 chars)",
            "mention": "5 pings / msg",
            "emoji": "6 emojis / msg"
        }

        for r_name in VALID_RULES:
            r = rules.get(r_name, {})
            state = f"{config.ANIM_SUCCESS} ON" if r.get("enabled", True) else f"{config.ANIM_WARN} OFF"
            punish = (r.get("punishment") or "delete").upper()
            thresh = fixed_thresholds.get(r_name, "Standard")
            embed.add_field(
                name=f"{r_name.capitalize()}",
                value=f"State: {state}\nPunish: `{punish}`\nThreshold: `{thresh}`",
                inline=True
            )

        embed.set_footer(text=f"Shizu Security v{config.VERSION}", icon_url=ctx.author.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()
        await ctx.reply(embed=embed, mention_author=False)

    # --- AutoMod Ignore / Exemption Management ---
    @automod.command(name="ignore")
    @commands.guild_only()
    @is_guild_owner_or_extra()
    async def automod_ignore(self, ctx, target_type: Literal["channel", "role", "user"], target: Union[discord.TextChannel, discord.Role, discord.Member]):
        """Adds a channel, role, or user to the AutoMod exemption list."""
        added = await self.bot.db.add_automod_ignored(ctx.guild.id, target.id, target_type.lower())
        if not added:
            return await ctx.reply_warning(f"{target.mention} is already exempted from AutoMod.")

        await ctx.reply_success(f"{target.mention} (`{target.id}`) has been **exempted** from AutoMod.")

    @automod.command(name="unignore")
    @commands.guild_only()
    @is_guild_owner_or_extra()
    async def automod_unignore(self, ctx, target_type: Literal["channel", "role", "user"], target: Union[discord.TextChannel, discord.Role, discord.Member]):
        """Removes a channel, role, or user from the AutoMod exemption list."""
        removed = await self.bot.db.remove_automod_ignored(ctx.guild.id, target.id, target_type.lower())
        if not removed:
            return await ctx.reply_error(f"{target.mention} is not in the AutoMod exemption list.")

        await ctx.reply_success(f"{target.mention} (`{target.id}`) is no longer exempted from AutoMod.")

    @automod.command(name="ignored")
    @commands.guild_only()
    @is_guild_owner_or_extra()
    async def automod_ignored_list(self, ctx):
        """Displays all channels, roles, and users currently exempted from AutoMod."""
        ignored = await self.bot.db.get_all_automod_ignored(ctx.guild.id)
        if not ignored:
            return await ctx.reply_warning("There are currently no AutoMod exemptions configured on this server.")

        channels, roles, users = [], [], []
        for item in ignored:
            t_type = item["target_type"]
            t_id = item["target_id"]
            if t_type == "channel":
                ch = ctx.guild.get_channel(t_id)
                channels.append(ch.mention if ch else f"Deleted Channel (`{t_id}`)")
            elif t_type == "role":
                r = ctx.guild.get_role(t_id)
                roles.append(r.mention if r else f"Deleted Role (`{t_id}`)")
            elif t_type == "user":
                u = ctx.guild.get_member(t_id)
                users.append(u.mention if u else f"User ID `{t_id}`")

        embed = discord.Embed(
            title=f"{config.EMOJI_LIST} AutoMod Exemptions",
            color=config.COLOR_DARK
        )
        if channels:
            embed.add_field(name=f"Ignored Channels ({len(channels)})", value=", ".join(channels), inline=False)
        if roles:
            embed.add_field(name=f"Ignored Roles ({len(roles)})", value=", ".join(roles), inline=False)
        if users:
            embed.add_field(name=f"Ignored Users ({len(users)})", value=", ".join(users), inline=False)

        await ctx.reply(embed=embed, mention_author=False)

    # --- Bad Words Commands ---
    @commands.group(name="badwords", aliases=["badword", "bw"], invoke_without_command=True)
    @commands.guild_only()
    @is_guild_owner_or_extra()
    async def badwords_cmd(self, ctx):
        """Manage blacklisted bad words."""
        prefix = ctx.prefix
        embed = discord.Embed(
            title=f"{config.ANIM_SHIELD} Word Blacklist Management",
            description=(
                f"`{prefix}badwords add <word>` — Add term to filter (word-boundary matched)\n"
                f"`{prefix}badwords remove <word>` — Remove term from filter\n"
                f"`{prefix}badwords list` — View all blacklisted terms\n"
                f"`{prefix}badwords clear` — Clear all blacklisted terms"
            ),
            color=config.COLOR_DARK
        )
        await ctx.reply(embed=embed, mention_author=False)

    @badwords_cmd.command(name="add")
    @commands.guild_only()
    @is_guild_owner_or_extra()
    async def badwords_add(self, ctx, *, word: str):
        """Adds a term to the server blacklist."""
        clean_word = word.strip().lower()
        if len(clean_word) < 2:
            return await ctx.reply_error("Word must be at least 2 characters long.")

        added = await self.bot.db.add_badword(ctx.guild.id, clean_word)
        if not added:
            return await ctx.reply_warning(f"The term `{clean_word}` is already in the blacklist.")

        await ctx.reply_success(f"Added `{clean_word}` to the server blacklist (uses word-boundary regex).")

    @badwords_cmd.command(name="remove")
    @commands.guild_only()
    @is_guild_owner_or_extra()
    async def badwords_remove(self, ctx, *, word: str):
        """Removes a term from the blacklist."""
        clean_word = word.strip().lower()
        removed = await self.bot.db.remove_badword(ctx.guild.id, clean_word)
        if not removed:
            return await ctx.reply_error(f"The term `{clean_word}` was not found in the blacklist.")

        await ctx.reply_success(f"Removed `{clean_word}` from the blacklist.")

    @badwords_cmd.command(name="list")
    @commands.guild_only()
    @is_guild_owner_or_extra()
    async def badwords_list(self, ctx):
        """Displays all blacklisted words."""
        words = await self.bot.db.get_badwords(ctx.guild.id)
        if not words:
            return await ctx.reply_warning("There are currently no blacklisted words on this server.")

        embed = discord.Embed(
            title=f"{config.EMOJI_LIST} Blacklisted Words ({len(words)})",
            description=" • " + "\n • ".join(f"`{w}`" for w in words[:40]),
            color=config.COLOR_DARK
        )
        if len(words) > 40:
            embed.set_footer(text=f"Showing top 40 of {len(words)} blacklisted words.")
        await ctx.reply(embed=embed, mention_author=False)

    @badwords_cmd.command(name="clear")
    @commands.guild_only()
    @is_guild_owner_or_extra()
    async def badwords_clear(self, ctx):
        """Clears all blacklisted words."""
        await self.bot.db.clear_badwords(ctx.guild.id)
        await ctx.reply_success("All terms have been cleared from the server blacklist.")

async def setup(bot):
    await bot.add_cog(AutoModCommands(bot))
