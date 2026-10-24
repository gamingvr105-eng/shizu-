import discord
from discord.ext import commands
from typing import Optional, Union, Literal
import datetime
import re
import asyncio
import logging

import config
from core.checks import check_hierarchy, top_role_check

logger = logging.getLogger("ShizuSecurity.Moderation")

TIME_REGEX = re.compile(r"^(\d+)([smhdw])$")
TIME_MULTIPLIERS = {
    "s": 1,
    "m": 60,
    "h": 3600,
    "d": 86400,
    "w": 604800
}

def parse_time(time_str: str) -> Optional[datetime.timedelta]:
    """Parses time strings like 30s, 10m, 2h, 7d into timedelta."""
    match = TIME_REGEX.match(time_str.lower())
    if not match:
        return None
    val, unit = match.groups()
    seconds = int(val) * TIME_MULTIPLIERS[unit]
    return datetime.timedelta(seconds=seconds)

class ModerationCommands(commands.Cog, name="Moderation"):
    """Comprehensive moderation suite with hierarchy enforcement, case IDs, animated emoji replies, and safety checks."""
    def __init__(self, bot):
        self.bot = bot
        # Channel snipe storage: channel_id -> message object dict
        self.sniped_messages = {}

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return
        self.sniped_messages[message.channel.id] = {
            "content": message.content,
            "author": message.author,
            "created_at": message.created_at,
            "attachments": [a.url for a in message.attachments]
        }

    async def log_mod_action(
        self,
        guild: discord.Guild,
        case_id: int,
        action: str,
        target: discord.abc.User,
        moderator: discord.abc.User,
        reason: str
    ):
        """Sends case embed to the configured moderation log channel."""
        cfg = await self.bot.db.get_guild_config(guild.id)
        log_ch_id = cfg.get("log_moderation")
        if not log_ch_id:
            return

        channel = guild.get_channel(log_ch_id)
        if not channel or not channel.permissions_for(guild.me).send_messages:
            return

        embed = discord.Embed(
            title=f"{config.ANIM_SHIELD} Moderation Case #{case_id} — {action.upper()}",
            color=config.COLOR_DARK
        )
        embed.add_field(name="Target User", value=f"{target.mention} (`{target.id}`)", inline=True)
        embed.add_field(name="Moderator", value=f"{moderator.mention} (`{moderator.id}`)", inline=True)
        embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
        embed.set_thumbnail(url=target.display_avatar.url if hasattr(target, "display_avatar") else guild.me.display_avatar.url)
        embed.set_footer(text=f"Shizu Security v{config.VERSION}", icon_url=self.bot.user.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()

        try:
            await channel.send(embed=embed)
        except Exception:
            pass

    # --- Ban Command ---
    @commands.command(name="ban", usage="ban <member|id> [reason]")
    @commands.guild_only()
    @top_role_check()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx, user: Union[discord.Member, discord.User], *, reason: Optional[str] = "No reason provided"):
        """Bans a member or user ID from the server."""
        if isinstance(user, discord.Member):
            allowed, err = check_hierarchy(ctx, user)
            if not allowed:
                return await ctx.reply_error(err)

        # Notify user via DM if possible
        dm_sent = False
        try:
            await user.send(
                f"{config.ANIM_WARN} You have been **banned** from **{ctx.guild.name}** by {ctx.author}.\n"
                f"**Reason:** {reason}"
            )
            dm_sent = True
        except Exception:
            pass

        try:
            await ctx.guild.ban(user, reason=f"Moderator: {ctx.author} | Reason: {reason}")
        except discord.Forbidden:
            return await ctx.reply_error("Failed to ban: Missing Discord API permissions or role hierarchy conflict.")
        except discord.HTTPException as e:
            return await ctx.reply_error(f"Failed to ban due to a Discord API error: {e}")

        case_id = await self.bot.db.create_case(
            ctx.guild.id, "BAN", user.id, str(user), ctx.author.id, str(ctx.author), reason
        )
        await self.log_mod_action(ctx.guild, case_id, "Ban", user, ctx.author, reason)

        await ctx.reply_success(
            f"Successfully banned **{user}** (`{user.id}`).\n"
            f"• **Case ID:** `#{case_id}`\n"
            f"• **DM Notification:** {'Delivered' if dm_sent else 'Failed/Disabled'}\n"
            f"• **Reason:** {reason}"
        )

    # --- Unban Command ---
    @commands.command(name="unban", usage="unban <user_id> [reason]")
    @commands.guild_only()
    @top_role_check()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int, *, reason: Optional[str] = "No reason provided"):
        """Unbans a user from the server using their user ID."""
        try:
            ban_entry = await ctx.guild.fetch_ban(discord.Object(id=user_id))
        except discord.NotFound:
            return await ctx.reply_error(f"No active ban found for user ID `{user_id}` on this server.")
        except discord.Forbidden:
            return await ctx.reply_error("I lack permission to view server bans.")

        banned_user = ban_entry.user
        try:
            await ctx.guild.unban(banned_user, reason=f"Moderator: {ctx.author} | Reason: {reason}")
        except discord.Forbidden:
            return await ctx.reply_error("Failed to unban: Missing ban permissions.")
        except discord.HTTPException as e:
            return await ctx.reply_error(f"Discord API error unbanning user: {e}")

        case_id = await self.bot.db.create_case(
            ctx.guild.id, "UNBAN", banned_user.id, str(banned_user), ctx.author.id, str(ctx.author), reason
        )
        await self.log_mod_action(ctx.guild, case_id, "Unban", banned_user, ctx.author, reason)

        await ctx.reply_success(
            f"Successfully unbanned **{banned_user}** (`{banned_user.id}`).\n"
            f"• **Case ID:** `#{case_id}`\n"
            f"• **Reason:** {reason}"
        )

    # --- Kick Command ---
    @commands.command(name="kick", usage="kick <member> [reason]")
    @commands.guild_only()
    @top_role_check()
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: Optional[str] = "No reason provided"):
        """Kicks a member from the server."""
        allowed, err = check_hierarchy(ctx, member)
        if not allowed:
            return await ctx.reply_error(err)

        dm_sent = False
        try:
            await member.send(
                f"{config.ANIM_WARN} You have been **kicked** from **{ctx.guild.name}** by {ctx.author}.\n"
                f"**Reason:** {reason}"
            )
            dm_sent = True
        except Exception:
            pass

        try:
            await member.kick(reason=f"Moderator: {ctx.author} | Reason: {reason}")
        except discord.Forbidden:
            return await ctx.reply_error("Failed to kick: Missing permission or role hierarchy error.")
        except discord.HTTPException as e:
            return await ctx.reply_error(f"Failed to kick member due to API error: {e}")

        case_id = await self.bot.db.create_case(
            ctx.guild.id, "KICK", member.id, str(member), ctx.author.id, str(ctx.author), reason
        )
        await self.log_mod_action(ctx.guild, case_id, "Kick", member, ctx.author, reason)

        await ctx.reply_success(
            f"Successfully kicked **{member}** (`{member.id}`).\n"
            f"• **Case ID:** `#{case_id}`\n"
            f"• **DM Notification:** {'Delivered' if dm_sent else 'Failed/Disabled'}\n"
            f"• **Reason:** {reason}"
        )

    # --- Timeout / Mute Command ---
    @commands.command(name="timeout", aliases=["mute"], usage="timeout <member> <duration> [reason]")
    @commands.guild_only()
    @top_role_check()
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def timeout(self, ctx, member: discord.Member, duration_str: str, *, reason: Optional[str] = "No reason provided"):
        """Times out (mutes) a member for a specified duration (e.g. 10m, 1h, 1d)."""
        allowed, err = check_hierarchy(ctx, member)
        if not allowed:
            return await ctx.reply_error(err)

        delta = parse_time(duration_str)
        if not delta:
            return await ctx.reply_error(
                "Invalid duration format. Use numbers followed by `s`, `m`, `h`, `d`, or `w` (e.g. `10m`, `2h`, `1d`)."
            )

        if delta.total_seconds() > 2419200:
            return await ctx.reply_error("Timeouts cannot exceed 28 days.")

        try:
            await member.timeout(delta, reason=f"Moderator: {ctx.author} | Reason: {reason}")
        except discord.Forbidden:
            return await ctx.reply_error("Failed to timeout member: Missing permissions or role hierarchy block.")
        except discord.HTTPException as e:
            return await ctx.reply_error(f"Discord API error applying timeout: {e}")

        case_id = await self.bot.db.create_case(
            ctx.guild.id, "TIMEOUT", member.id, str(member), ctx.author.id, str(ctx.author), f"{duration_str} - {reason}"
        )
        await self.log_mod_action(ctx.guild, case_id, f"Timeout ({duration_str})", member, ctx.author, reason)

        await ctx.reply_success(
            f"Successfully timed out **{member}** for **{duration_str}**.\n"
            f"• **Case ID:** `#{case_id}`\n"
            f"• **Reason:** {reason}"
        )

    # --- Untimeout / Unmute Command ---
    @commands.command(name="untimeout", aliases=["unmute"], usage="untimeout <member> [reason]")
    @commands.guild_only()
    @top_role_check()
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def untimeout(self, ctx, member: discord.Member, *, reason: Optional[str] = "No reason provided"):
        """Removes an active timeout from a member."""
        allowed, err = check_hierarchy(ctx, member)
        if not allowed:
            return await ctx.reply_error(err)

        if not member.is_timed_out():
            return await ctx.reply_warning(f"{member.mention} does not have an active timeout.")

        try:
            await member.timeout(None, reason=f"Moderator: {ctx.author} | Reason: {reason}")
        except discord.Forbidden:
            return await ctx.reply_error("Failed to remove timeout: Permission or role hierarchy block.")
        except discord.HTTPException as e:
            return await ctx.reply_error(f"Discord API error removing timeout: {e}")

        case_id = await self.bot.db.create_case(
            ctx.guild.id, "UNTIMEOUT", member.id, str(member), ctx.author.id, str(ctx.author), reason
        )
        await self.log_mod_action(ctx.guild, case_id, "Untimeout", member, ctx.author, reason)

        await ctx.reply_success(
            f"Successfully removed timeout from **{member}**.\n"
            f"• **Case ID:** `#{case_id}`\n"
            f"• **Reason:** {reason}"
        )

    # --- Warn Command ---
    @commands.command(name="warn", usage="warn <member> [reason]")
    @commands.guild_only()
    @top_role_check()
    @commands.has_permissions(moderate_members=True)
    async def warn(self, ctx, member: discord.Member, *, reason: Optional[str] = "No reason provided"):
        """Issues a formal warning to a server member."""
        allowed, err = check_hierarchy(ctx, member)
        if not allowed:
            return await ctx.reply_error(err)

        warn_id = await self.bot.db.add_warning(ctx.guild.id, member.id, ctx.author.id, reason)
        case_id = await self.bot.db.create_case(
            ctx.guild.id, "WARN", member.id, str(member), ctx.author.id, str(ctx.author), reason
        )

        dm_sent = False
        try:
            await member.send(
                f"{config.ANIM_WARN} You have received a formal warning in **{ctx.guild.name}**.\n"
                f"**Reason:** {reason}"
            )
            dm_sent = True
        except Exception:
            pass

        await self.log_mod_action(ctx.guild, case_id, "Warning", member, ctx.author, reason)

        total_warns = len(await self.bot.db.get_warnings(ctx.guild.id, member.id))
        await ctx.reply_success(
            f"Successfully warned **{member}** (`{member.id}`).\n"
            f"• **Warning ID:** `#{warn_id}` | **Case ID:** `#{case_id}`\n"
            f"• **Total Warnings:** `{total_warns}`\n"
            f"• **DM Status:** {'Delivered' if dm_sent else 'Failed/Disabled'}\n"
            f"• **Reason:** {reason}"
        )

    # --- Purge / Clear Command ---
    @commands.command(name="purge", aliases=["clear"], usage="purge <amount> [@user]")
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True, read_message_history=True)
    async def purge(self, ctx, amount: int, member: Optional[discord.Member] = None):
        """Purges messages from the current channel (up to 500), optionally filtered by member."""
        if amount < 1 or amount > 500:
            return await ctx.reply_error("Purge amount must be between 1 and 500 messages.")

        try:
            await ctx.message.delete()
        except Exception:
            pass

        def check(m):
            if member:
                return m.author.id == member.id
            return True

        # Discord enforces a strict 14-day limit on bulk deletions
        fourteen_days_ago = discord.utils.utcnow() - datetime.timedelta(days=14)

        try:
            deleted = await ctx.channel.purge(limit=amount, check=check, after=fourteen_days_ago)
        except discord.Forbidden:
            return await ctx.reply_error("I do not have permission to delete messages in this channel.")
        except discord.HTTPException as e:
            return await ctx.reply_error(f"Purge failed due to Discord API error: {e}")

        filter_str = f" from {member.mention}" if member else ""
        msg = await ctx.reply_success(f"Successfully deleted **{len(deleted)}** message(s){filter_str}.")
        await asyncio.sleep(4)
        try:
            await msg.delete()
        except Exception:
            pass

    # --- Slowmode Command ---
    @commands.command(name="slowmode", aliases=["slow"], usage="slowmode <seconds|0> [channel]")
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def slowmode(self, ctx, seconds: int, channel: Optional[discord.TextChannel] = None):
        """Configures channel slowmode (0 to 21600 seconds)."""
        target_ch = channel or ctx.channel
        if seconds < 0 or seconds > 21600:
            return await ctx.reply_error("Slowmode delay must be between 0 and 21600 seconds (6 hours).")

        try:
            await target_ch.edit(slowmode_delay=seconds, reason=f"Slowmode set by {ctx.author}")
        except discord.Forbidden:
            return await ctx.reply_error("Failed to edit channel slowmode: Missing permissions.")

        if seconds == 0:
            await ctx.reply_success(f"Disabled slowmode in {target_ch.mention}.")
        else:
            await ctx.reply_success(f"Set slowmode in {target_ch.mention} to **{seconds} seconds**.")

    # --- Lock & Unlock Channel ---
    @commands.command(name="lock", usage="lock [channel] [reason]")
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def lock(self, ctx, channel: Optional[discord.TextChannel] = None, *, reason: Optional[str] = "No reason provided"):
        """Locks a text channel to prevent @everyone from sending messages."""
        target_ch = channel or ctx.channel
        overwrite = target_ch.overwrites_for(ctx.guild.default_role)

        if overwrite.send_messages is False:
            return await ctx.reply_warning(f"{target_ch.mention} is already locked.")

        overwrite.send_messages = False
        overwrite.send_messages_in_threads = False
        try:
            await target_ch.set_permissions(ctx.guild.default_role, overwrite=overwrite, reason=f"Locked by {ctx.author}: {reason}")
        except discord.Forbidden:
            return await ctx.reply_error(f"Cannot lock {target_ch.mention}: Missing permissions.")

        await ctx.reply_success(f"{target_ch.mention} has been **locked** 🔒.\n**Reason:** {reason}")

    @commands.command(name="unlock", usage="unlock [channel]")
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def unlock(self, ctx, channel: Optional[discord.TextChannel] = None):
        """Unlocks a previously locked text channel."""
        target_ch = channel or ctx.channel
        overwrite = target_ch.overwrites_for(ctx.guild.default_role)

        if overwrite.send_messages is not False:
            return await ctx.reply_warning(f"{target_ch.mention} is not locked.")

        overwrite.send_messages = None
        overwrite.send_messages_in_threads = None
        try:
            await target_ch.set_permissions(ctx.guild.default_role, overwrite=overwrite, reason=f"Unlocked by {ctx.author}")
        except discord.Forbidden:
            return await ctx.reply_error(f"Cannot unlock {target_ch.mention}: Missing permissions.")

        await ctx.reply_success(f"{target_ch.mention} has been **unlocked** 🔓.")

    # --- Hide & Unhide Channel ---
    @commands.command(name="hide", usage="hide [channel]")
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def hide(self, ctx, channel: Optional[discord.TextChannel] = None):
        """Hides a text channel from @everyone."""
        target_ch = channel or ctx.channel
        overwrite = target_ch.overwrites_for(ctx.guild.default_role)
        overwrite.view_channel = False

        try:
            await target_ch.set_permissions(ctx.guild.default_role, overwrite=overwrite, reason=f"Hidden by {ctx.author}")
        except discord.Forbidden:
            return await ctx.reply_error(f"Cannot hide {target_ch.mention}: Missing permissions.")

        await ctx.reply_success(f"{target_ch.mention} is now **hidden** from regular members.")

    @commands.command(name="unhide", usage="unhide [channel]")
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def unhide(self, ctx, channel: Optional[discord.TextChannel] = None):
        """Unhides a hidden text channel for @everyone."""
        target_ch = channel or ctx.channel
        overwrite = target_ch.overwrites_for(ctx.guild.default_role)
        overwrite.view_channel = None

        try:
            await target_ch.set_permissions(ctx.guild.default_role, overwrite=overwrite, reason=f"Unhidden by {ctx.author}")
        except discord.Forbidden:
            return await ctx.reply_error(f"Cannot unhide {target_ch.mention}: Missing permissions.")

        await ctx.reply_success(f"{target_ch.mention} is now **visible**.")

    # --- Nickname Command ---
    @commands.command(name="setnick", aliases=["nick"], usage="setnick <member> [nickname]")
    @commands.guild_only()
    @top_role_check()
    @commands.has_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    async def setnick(self, ctx, member: discord.Member, *, nickname: Optional[str] = None):
        """Changes or resets a member's nickname."""
        allowed, err = check_hierarchy(ctx, member)
        if not allowed:
            return await ctx.reply_error(err)

        try:
            await member.edit(nick=nickname, reason=f"Nickname edited by {ctx.author}")
        except discord.Forbidden:
            return await ctx.reply_error("Failed to change nickname: Missing permissions or role hierarchy error.")

        if nickname:
            await ctx.reply_success(f"Changed nickname for {member.mention} to **{nickname}**.")
        else:
            await ctx.reply_success(f"Reset nickname for {member.mention}.")

    # --- Role Management ---
    @commands.group(name="role", invoke_without_command=True)
    @commands.guild_only()
    @top_role_check()
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def role_cmd(self, ctx):
        """Role management command menu."""
        prefix = ctx.prefix
        embed = discord.Embed(
            title=f"{config.ANIM_SHIELD} Role Management",
            description=(
                f"`{prefix}role add <member> <role>` — Assign a role to a member\n"
                f"`{prefix}role remove <member> <role>` — Strip a role from a member"
            ),
            color=config.COLOR_DARK
        )
        await ctx.reply(embed=embed, mention_author=False)

    @role_cmd.command(name="add")
    @commands.guild_only()
    @top_role_check()
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def role_add(self, ctx, member: discord.Member, *, role: discord.Role):
        """Assigns a role to a member."""
        if role >= ctx.guild.me.top_role:
            return await ctx.reply_error(f"I cannot assign {role.mention} because it is equal or higher than my highest role.")

        if ctx.author.id != ctx.guild.owner_id and ctx.author.id not in config.OWNER_IDS:
            if role >= ctx.author.top_role:
                return await ctx.reply_error(f"You cannot assign {role.mention} because it is equal or higher than your highest role.")

        if role in member.roles:
            return await ctx.reply_warning(f"{member.mention} already has the {role.mention} role.")

        try:
            await member.add_roles(role, reason=f"Assigned by {ctx.author}")
        except discord.Forbidden:
            return await ctx.reply_error("Failed to assign role: Permission or hierarchy error.")

        await ctx.reply_success(f"Assigned {role.mention} to {member.mention}.")

    @role_cmd.command(name="remove")
    @commands.guild_only()
    @top_role_check()
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def role_remove(self, ctx, member: discord.Member, *, role: discord.Role):
        """Removes a role from a member."""
        if role >= ctx.guild.me.top_role:
            return await ctx.reply_error(f"I cannot remove {role.mention} because it is equal or higher than my highest role.")

        if ctx.author.id != ctx.guild.owner_id and ctx.author.id not in config.OWNER_IDS:
            if role >= ctx.author.top_role:
                return await ctx.reply_error(f"You cannot remove {role.mention} because it is equal or higher than your highest role.")

        if role not in member.roles:
            return await ctx.reply_warning(f"{member.mention} does not possess the {role.mention} role.")

        try:
            await member.remove_roles(role, reason=f"Removed by {ctx.author}")
        except discord.Forbidden:
            return await ctx.reply_error("Failed to remove role: Permission or hierarchy error.")

        await ctx.reply_success(f"Removed {role.mention} from {member.mention}.")

    # --- Snipe Command ---
    @commands.command(name="snipe", usage="snipe [channel]")
    @commands.guild_only()
    async def snipe(self, ctx, channel: Optional[discord.TextChannel] = None):
        """Retrieves the most recently deleted message in this channel."""
        target_ch = channel or ctx.channel
        data = self.sniped_messages.get(target_ch.id)
        if not data:
            return await ctx.reply_warning(f"No recently deleted messages found in {target_ch.mention}.")

        embed = discord.Embed(
            description=data["content"] or "*[No text content / attachment only]*",
            color=config.COLOR_DARK
        )
        author = data["author"]
        embed.set_author(name=f"{author} ({author.id})", icon_url=author.display_avatar.url)
        if data["attachments"]:
            embed.add_field(name="Attachments", value="\n".join(data["attachments"]), inline=False)
        embed.set_footer(text=f"Deleted in #{target_ch.name}")
        embed.timestamp = data["created_at"]
        await ctx.reply(embed=embed, mention_author=False)

async def setup(bot):
    await bot.add_cog(ModerationCommands(bot))
