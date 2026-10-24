"""
Shizu Security - Zero-Trust AutoMod Event Listener
Monitors chat messages in real time with short-circuit evaluation,
granular scope bypasses, calibrated fixed thresholds, and smart whitelists.
"""

import discord
from discord.ext import commands
import re
import datetime
from collections import deque
import logging
from typing import Dict, Deque, Set, Tuple, Optional

from config import config

logger = logging.getLogger("ShizuSecurity.AutoMod")

INVITE_REGEX = re.compile(
    r"(https?://)?(www\.)?(discord\.(gg|io|me|li)|discordapp\.com/invite|discord\.com/invite)/[a-zA-Z0-9-]+",
    re.IGNORECASE
)
LINK_REGEX = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
SAFE_LINK_REGEX = re.compile(
    r"(https?://)?(www\.)?(tenor\.com|giphy\.com|cdn\.discordapp\.com|media\.discordapp\.net|open\.spotify\.com/track)",
    re.IGNORECASE
)
CUSTOM_EMOJI_REGEX = re.compile(r"<a?:[a-zA-Z0-9_]+:[0-9]+>")
UNICODE_EMOJI_REGEX = re.compile(r"[\U00010000-\U0010ffff]", flags=re.UNICODE)

class AutoModListener(commands.Cog):
    """Event listener for detecting spam, links, invites, bad words, caps, mass mentions, and emoji floods."""
    def __init__(self, bot):
        self.bot = bot
        # Track message rate: guild_id -> user_id -> deque of timestamps
        self.user_message_times: Dict[int, Dict[int, Deque[datetime.datetime]]] = {}
        # Track recent message content to detect rapid duplicates
        self.user_last_messages: Dict[int, Dict[int, list]] = {}
        # In-memory deduplication of handled message IDs
        self.handled_messages: Set[int] = set()

    async def is_author_globally_exempt(self, message: discord.Message) -> bool:
        """Determines if author/channel holds universal exemption from AutoMod."""
        if not message.guild or message.author.bot:
            return True

        guild = message.guild
        author = message.author

        # Executive exemptions
        if author.id == self.bot.user.id or author.id == guild.owner_id:
            return True

        if author.id in config.OWNER_IDS:
            return True

        if await self.bot.db.is_extra_owner(guild.id, author.id):
            return True

        # Ignored Channel check
        if await self.bot.db.is_automod_ignored(guild.id, message.channel.id, "channel"):
            return True

        # Ignored User check
        if await self.bot.db.is_automod_ignored(guild.id, author.id, "user"):
            return True

        # Ignored Role check
        if isinstance(author, discord.Member):
            for r in author.roles:
                if await self.bot.db.is_automod_ignored(guild.id, r.id, "role"):
                    return True

        # Full AutoMod Bypass scope
        if await self.bot.db.has_scope(guild.id, author, "automod.bypass.all"):
            return True

        return False

    async def has_rule_bypass(self, guild_id: int, author: discord.Member, rule_name: str) -> bool:
        """Checks if member holds specific granular bypass for a rule."""
        return await self.bot.db.has_scope(guild_id, author, f"automod.bypass.{rule_name}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        await self.process_automod(message)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.content != after.content:
            await self.process_automod(after)

    async def process_automod(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        if message.id in self.handled_messages:
            return

        cfg = await self.bot.db.get_guild_config(message.guild.id)
        if not cfg.get("automod_enabled"):
            return

        if await self.is_author_globally_exempt(message):
            return

        guild = message.guild
        author = message.author
        content = message.content or ""
        rules_list = await self.bot.db.get_all_automod_rules(guild.id)
        rules = {r["rule_name"]: r for r in rules_list}

        # 1. Anti-Invite Filter
        rule = rules.get("invite", {})
        if rule.get("enabled", True) and not await self.has_rule_bypass(guild.id, author, "invite"):
            invites = INVITE_REGEX.findall(content)
            if invites:
                is_foreign = True
                # Vanity URL check
                if guild.vanity_url_code and guild.vanity_url_code.lower() in content.lower():
                    is_foreign = False

                # Active server invites check
                if is_foreign and guild.me.guild_permissions.manage_guild:
                    try:
                        active_invites = await guild.invites()
                        for inv in active_invites:
                            if inv.code in content:
                                is_foreign = False
                                break
                    except Exception:
                        pass

                if is_foreign:
                    await self.execute_punishment(message, "invite", rule, "Posted foreign Discord invite link")
                    return

        # 2. Anti-Link Filter
        rule = rules.get("link", {})
        if rule.get("enabled", True) and not await self.has_rule_bypass(guild.id, author, "link"):
            links = LINK_REGEX.findall(content)
            if links:
                unauthorized_links = [l for l in links if not SAFE_LINK_REGEX.search(l)]
                if unauthorized_links:
                    await self.execute_punishment(message, "link", rule, f"Posted unauthorized link: `{unauthorized_links[0][:50]}`")
                    return

        # 3. Bad Words Filter (Exact Word-Boundary Regex)
        rule = rules.get("badwords", {})
        if rule.get("enabled", True) and not await self.has_rule_bypass(guild.id, author, "badwords"):
            badwords = await self.bot.db.get_badwords(guild.id)
            if badwords:
                for bw in badwords:
                    pattern = rf"\b{re.escape(bw)}\b"
                    if re.search(pattern, content, re.IGNORECASE):
                        await self.execute_punishment(message, "badwords", rule, f"Triggered blacklisted term: `{bw}`")
                        return

        # 4. Anti-Caps Filter (70% on strings > 8 chars)
        rule = rules.get("caps", {})
        if rule.get("enabled", True) and not await self.has_rule_bypass(guild.id, author, "caps"):
            cleaned = "".join([c for c in content if c.isalpha()])
            if len(cleaned) > 8:
                caps_ratio = sum(1 for c in cleaned if c.isupper()) / len(cleaned)
                if caps_ratio >= 0.70:
                    await self.execute_punishment(message, "caps", rule, f"Excessive uppercase shouting ({int(caps_ratio*100)}% caps)")
                    return

        # 5. Mass-Mention Filter (5 pings)
        rule = rules.get("mention", {})
        if rule.get("enabled", True) and not await self.has_rule_bypass(guild.id, author, "mention"):
            total_mentions = len(message.mentions) + len(message.role_mentions)
            if message.mention_everyone:
                total_mentions += 1
            if total_mentions >= 5:
                await self.execute_punishment(message, "mention", rule, f"Mass mention ping spam ({total_mentions} mentions)")
                return

        # 6. Emoji-Spam Filter (6 emojis)
        rule = rules.get("emoji", {})
        if rule.get("enabled", True) and not await self.has_rule_bypass(guild.id, author, "emoji"):
            custom_emojis = CUSTOM_EMOJI_REGEX.findall(content)
            unicode_emojis = UNICODE_EMOJI_REGEX.findall(content)
            total_emojis = len(custom_emojis) + len(unicode_emojis)
            if total_emojis >= 6:
                await self.execute_punishment(message, "emoji", rule, f"Emoji flood ({total_emojis} emojis)")
                return

        # 7. Anti-Spam / Flood Filter (5 msgs in 5s or 3 rapid duplicate messages)
        rule = rules.get("spam", {})
        if rule.get("enabled", True) and not await self.has_rule_bypass(guild.id, author, "spam"):
            now = datetime.datetime.utcnow()
            guild_times = self.user_message_times.setdefault(guild.id, {})
            user_queue = guild_times.setdefault(author.id, deque())
            user_queue.append(now)

            # Purge messages older than 5s
            cutoff = now - datetime.timedelta(seconds=5)
            while user_queue and user_queue[0] < cutoff:
                user_queue.popleft()

            if len(user_queue) >= 5:
                await self.execute_punishment(message, "spam", rule, f"Message flood detected ({len(user_queue)} messages in 5s)")
                return

            # Check rapid duplicate content
            guild_last = self.user_last_messages.setdefault(guild.id, {})
            last_msgs = guild_last.setdefault(author.id, [])
            last_msgs.append((content, now))
            if len(last_msgs) > 3:
                last_msgs.pop(0)

            if len(last_msgs) == 3 and len(content) > 3:
                if last_msgs[0][0] == last_msgs[1][0] == last_msgs[2][0]:
                    await self.execute_punishment(message, "spam", rule, "Repeated duplicate message spam")
                    return

    async def execute_punishment(
        self,
        message: discord.Message,
        rule_name: str,
        rule: dict,
        reason: str
    ):
        """Applies configured AutoMod penalty, logs audit case, and alerts."""
        self.handled_messages.add(message.id)
        if len(self.handled_messages) > 3000:
            self.handled_messages.clear()

        guild = message.guild
        author = message.author
        channel = message.channel
        punishment = (rule.get("punishment") or "delete").lower()
        timeout_seconds = rule.get("timeout_duration", 300)

        # 1. Attempt message deletion
        try:
            if guild.me.guild_permissions.manage_messages:
                await message.delete()
        except Exception:
            pass

        # 2. Check role hierarchy before punishing member
        if isinstance(author, discord.Member) and author.top_role >= guild.me.top_role:
            action_result = f"Message Deleted (Hierarchy block: cannot sanction {author.name})"
            await self.log_automod(guild, author, channel, rule_name, action_result, reason, message.content)
            return

        action_result = "Message Deleted"
        case_id = None
        try:
            if punishment == "warn":
                warn_id = await self.bot.db.add_warning(guild.id, author.id, self.bot.user.id, f"AutoMod [{rule_name}]: {reason}")
                case_id = await self.bot.db.create_case(
                    guild.id, "WARN", author.id, str(author), self.bot.user.id, self.bot.user.name, f"AutoMod [{rule_name}]: {reason}"
                )
                action_result = f"Warned (Warning #{warn_id} • Case #{case_id})"
            elif punishment == "timeout" and isinstance(author, discord.Member):
                if guild.me.guild_permissions.moderate_members:
                    duration = datetime.timedelta(seconds=timeout_seconds)
                    await author.timeout(duration, reason=f"Shizu AutoMod: {reason}")
                    case_id = await self.bot.db.create_case(
                        guild.id, "TIMEOUT", author.id, str(author), self.bot.user.id, self.bot.user.name, f"AutoMod [{rule_name}]: {reason} ({timeout_seconds // 60}m)"
                    )
                    action_result = f"Timed out for {timeout_seconds // 60}m (Case #{case_id})"
                else:
                    action_result = "Failed Timeout (Missing Moderate Members permission)"
            elif punishment == "kick" and isinstance(author, discord.Member):
                if guild.me.guild_permissions.kick_members:
                    await author.kick(reason=f"Shizu AutoMod: {reason}")
                    case_id = await self.bot.db.create_case(
                        guild.id, "KICK", author.id, str(author), self.bot.user.id, self.bot.user.name, f"AutoMod [{rule_name}]: {reason}"
                    )
                    action_result = f"Kicked (Case #{case_id})"
                else:
                    action_result = "Failed Kick (Missing Kick Members permission)"
            elif punishment == "ban":
                if guild.me.guild_permissions.ban_members:
                    await guild.ban(author, reason=f"Shizu AutoMod: {reason}")
                    case_id = await self.bot.db.create_case(
                        guild.id, "BAN", author.id, str(author), self.bot.user.id, self.bot.user.name, f"AutoMod [{rule_name}]: {reason}"
                    )
                    action_result = f"Banned (Case #{case_id})"
                else:
                    action_result = "Failed Ban (Missing Ban Members permission)"
        except Exception as e:
            action_result = f"Action Error ({e})"
            logger.warning(f"AutoMod punishment error on {author.id}: {e}")

        # Send clean transient notice in channel
        try:
            if channel.permissions_for(guild.me).send_messages:
                embed = discord.Embed(
                    description=f"{config.ANIM_WARN} {author.mention} violated AutoMod (**{rule_name.capitalize()}**): **{action_result}**.",
                    color=config.COLOR_DARK
                )
                await channel.send(embed=embed, delete_after=6)
        except Exception:
            pass

        # Log incident to AutoMod log channel
        await self.log_automod(guild, author, channel, rule_name, action_result, reason, message.content)

    async def log_automod(
        self,
        guild: discord.Guild,
        author: discord.abc.User,
        channel: discord.abc.GuildChannel,
        rule_name: str,
        action_result: str,
        reason: str,
        offending_content: str
    ):
        """Sends rich dark-themed audit log embed with animated emojis."""
        cfg = await self.bot.db.get_guild_config(guild.id)
        log_cid = cfg.get("log_automod")
        if not log_cid:
            return

        log_channel = guild.get_channel(log_cid)
        if not log_channel:
            return

        embed = discord.Embed(
            title=f"{config.ANIM_ALERT} AutoMod Violation Intercepted",
            description=f"Rule: **{rule_name.capitalize()}** | Action: **{action_result}**",
            color=config.COLOR_DARK
        )
        embed.add_field(name="User", value=f"{author.mention} (`{author.id}`)", inline=True)
        embed.add_field(name="Channel", value=channel.mention, inline=True)
        embed.add_field(name="Details", value=reason, inline=False)

        clean_content = offending_content[:400] if offending_content else "*No text content*"
        embed.add_field(name="Offending Content", value=f"```{clean_content}```", inline=False)
        embed.set_footer(text=f"Shizu Security v{config.VERSION}", icon_url=self.bot.user.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()

        try:
            await log_channel.send(embed=embed)
        except Exception:
            pass

async def setup(bot):
    await bot.add_cog(AutoModListener(bot))
