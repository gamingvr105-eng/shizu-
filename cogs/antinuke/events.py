"""
Shizu Security - Anti-Nuke & Anti-Bot Event Listeners
Engineered with Direct-Ban for Unwhitelisted Users, Token Burst Defense for Whitelist,
Server Owner Emergency DMs for Every Trigger, Discord Bot Hierarchy Defense,
and Instant Self-Healing Reversions.
"""

import discord
from discord.ext import commands
import datetime
import asyncio
import logging
import json
from typing import Optional, Any, Set, Tuple, List, Dict, Callable

from config import config
from core.scopes import ALL_OPERATIONAL_SCOPES
from core.enforcement import (
    burst_tracker,
    generate_incident_id,
    execute_breach_countermeasures,
    log_security_event,
    log_security_breach,
    dispatch_owner_security_dm,
    revert_channel_delete,
    revert_role_delete
)

logger = logging.getLogger("ShizuSecurity.AntiNuke")

DANGEROUS_PERMS = {
    "administrator",
    "manage_guild",
    "manage_roles",
    "manage_channels",
    "ban_members",
    "kick_members",
    "manage_webhooks"
}

class AntiNukeEvents(commands.Cog):
    """Event listeners for Anti-Nuke defense, Anti-Bot enforcement, instant rogue deletion, and auto-recreation."""
    def __init__(self, bot):
        self.bot = bot
        self.processed_entries: Set[Tuple[int, int]] = set()

    @commands.Cog.listener()
    async def on_ready(self):
        """Auto-snapshot all guild structures on startup for instant recovery."""
        for guild in self.bot.guilds:
            try:
                await self.snapshot_guild(guild)
            except Exception as e:
                logger.debug(f"Startup snapshot error for guild {guild.id}: {e}")

    async def snapshot_guild(self, guild: discord.Guild):
        """Captures full snapshot of channels, roles, emojis, and settings."""
        # Channels snapshot
        for ch in guild.channels:
            try:
                ch_type = "category" if isinstance(ch, discord.CategoryChannel) else ("voice" if isinstance(ch, discord.VoiceChannel) else "text")
                overwrites_data = {}
                for target, ow in ch.overwrites.items():
                    allow, deny = ow.pair()
                    overwrites_data[str(target.id)] = {"allow": allow.value, "deny": deny.value}

                await self.bot.db.save_channel_snapshot(
                    guild_id=guild.id,
                    channel_id=ch.id,
                    name=ch.name,
                    channel_type=ch_type,
                    category_name=ch.category.name if ch.category else None,
                    category_id=ch.category_id,
                    position=ch.position,
                    topic=getattr(ch, "topic", None),
                    nsfw=getattr(ch, "nsfw", False),
                    slowmode_delay=getattr(ch, "slowmode_delay", 0),
                    overwrites_json=json.dumps(overwrites_data)
                )
            except Exception:
                pass

        # Roles snapshot
        for r in guild.roles:
            if r.is_default():
                continue
            try:
                await self.bot.db.save_role_snapshot(
                    guild_id=guild.id,
                    role_id=r.id,
                    name=r.name,
                    permissions=r.permissions.value,
                    color=r.color.value,
                    hoist=r.hoist,
                    mentionable=r.mentionable,
                    position=r.position
                )
            except Exception:
                pass

        # Guild settings snapshot
        try:
            await self.bot.db.save_guild_snapshot(
                guild_id=guild.id,
                name=guild.name,
                description=guild.description,
                afk_timeout=guild.afk_timeout,
                afk_channel_id=guild.afk_channel.id if guild.afk_channel else None,
                system_channel_id=guild.system_channel.id if guild.system_channel else None,
                rules_channel_id=guild.rules_channel.id if guild.rules_channel else None,
                verification_level=str(guild.verification_level),
                default_notifications=str(guild.default_notifications),
                vanity_code=guild.vanity_url_code
            )
        except Exception:
            pass

    async def get_audit_entry(
        self,
        guild: discord.Guild,
        action: discord.AuditLogAction,
        target_id: Optional[int] = None,
        max_age: float = config.AUDIT_TOLERANCE_SECONDS
    ) -> Optional[discord.AuditLogEntry]:
        """Queries the Discord audit log with cache deduplication."""
        if not guild.me.guild_permissions.view_audit_log:
            return None

        try:
            async for entry in guild.audit_logs(action=action, limit=6):
                age = (discord.utils.utcnow() - entry.created_at).total_seconds()
                if age > max_age:
                    continue

                if target_id is not None and entry.target and entry.target.id != target_id:
                    continue

                cache_key = (guild.id, entry.id)
                if cache_key in self.processed_entries:
                    continue

                self.processed_entries.add(cache_key)
                if len(self.processed_entries) > 3000:
                    self.processed_entries.clear()

                return entry
        except Exception as e:
            logger.warning(f"Audit log query failed for {guild.id}: {e}")
            return None

        return None

    # --- Core Anti-Nuke Event Evaluator ---
    async def evaluate_event(
        self,
        guild: discord.Guild,
        action: discord.AuditLogAction,
        target_id: Optional[int],
        required_scope: str,
        breach_vector: str,
        revert_func: Optional[Callable[[str], Any]],
        details_builder: Callable[[Any], str]
    ):
        """
        Main Anti-Nuke Security Pipeline:
        1. Checks if Anti-Nuke is active.
        2. Queries Audit Log to correlate actor.
        3. If Actor is Unwhitelisted -> BANS directly + 100% Revert + Owner DM alert.
        4. If Actor is Whitelisted -> Checks burst window (>= 3 in 10s):
           - Burst Tripped -> BANS directly (compromised token defense) + 100% Revert.
           - Isolated Action -> WARNS actor + 100% Revert to protect guild.
        5. For EVERY trigger: Owner DM warning dispatched + logged to Shizu security logs.
        6. Hierarchy safety: If actor has higher hierarchy than the bot, action is STILL 100%
           reverted, and an Emergency Hierarchy Escalation alert is sent to Owner DM.
        """
        cfg = await self.bot.db.get_guild_config(guild.id)
        if not cfg.get("antinuke_enabled"):
            return

        entry = await self.get_audit_entry(guild, action, target_id)
        incident_id = generate_incident_id()

        # AUDIT UNCERTAINTY RULE:
        # If audit log cannot correlate actor with certainty within tolerance,
        # revert damage immediately and alert owners, but NEVER BAN an innocent member.
        if not entry or not entry.user:
            logger.warning(f"Uncertain audit actor for {breach_vector} in {guild.id}. Reverting safely.")
            if revert_func:
                try:
                    await revert_func(incident_id)
                except Exception as e:
                    logger.error(f"Reversion under uncertainty failed: {e}")

            await self.bot.db.log_security_audit(
                guild.id, 0, breach_vector, required_scope, target_id, "REVERTED_UNCERTAIN", incident_id,
                f"Audit actor uncertain within {config.AUDIT_TOLERANCE_SECONDS}s. Reverted damage without ban."
            )
            await log_security_event(
                self.bot, guild, "Uncertain (Audit Lag)", breach_vector,
                "REVERTED_UNCERTAIN (No Ban)", "Actor could not be determined. Action reverted safely.",
                incident_id=incident_id, is_warn=True
            )
            await dispatch_owner_security_dm(
                self.bot, guild, "Uncertain (Audit Lag)", breach_vector,
                "Action Reverted (Actor Uncertain)", "Audit log was delayed. Action was reverted safely.",
                incident_id=incident_id
            )
            return

        actor = entry.user

        # Bot self-actions bypass (internal auto-recreations and sweeps)
        if actor.id == self.bot.user.id:
            return

        # Global Developer check: bypass with diagnostic log
        if actor.id in config.OWNER_IDS:
            await self.bot.db.log_security_audit(
                guild.id, actor.id, breach_vector, required_scope, target_id, "ALLOWED", incident_id,
                "Global Developer Diagnostic Override"
            )
            return

        # Resolve member object
        member = guild.get_member(actor.id) or actor

        # Check Whitelist Scope
        has_authorized_scope = await self.bot.db.has_scope(guild.id, member, required_scope, target_id)

        # SCENARIO A: UNWHITELISTED USER TRIGGER -> BAN DIRECTLY + REVERT
        if not has_authorized_scope:
            details = details_builder(actor) + f" (Unwhitelisted User Trigger)"
            if revert_func:
                try:
                    await revert_func(incident_id)
                except Exception as e:
                    logger.error(f"Revert failed during unwhitelisted trigger: {e}")

            await execute_breach_countermeasures(
                self.bot, guild, actor, breach_vector, details, incident_id
            )
            return

        # SCENARIO B: WHITELISTED USER TRIGGER -> CHECK BURST LIMIT (3 in 10s)
        is_burst = burst_tracker.record_and_check(guild.id, actor.id)
        if is_burst:
            # MASS BURST EXCEEDED: Compromised account / hijacked token defense -> BAN DIRECTLY + REVERT
            details = (
                details_builder(actor) + 
                f" (Mass burst tripped: exceeded {config.MAX_BURST_ACTIONS} actions in {config.BURST_WINDOW}s)"
            )
            if revert_func:
                try:
                    await revert_func(incident_id)
                except Exception as e:
                    logger.error(f"Revert failed during burst breach: {e}")

            await execute_breach_countermeasures(
                self.bot, guild, actor, f"Mass Burst [{breach_vector}]", details, incident_id
            )
            return

        # SCENARIO C: WHITELISTED USER ISOLATED ACTION -> WARN + REVERT SENSITIVE DESTRUCTIVE ACTION
        destructive_scopes = {
            "antinuke.channel.delete",
            "antinuke.channel.create",
            "antinuke.role.delete",
            "antinuke.role.create",
            "antinuke.member.ban",
            "antinuke.member.kick",
            "antinuke.webhook.manage"
        }
        if required_scope in destructive_scopes:
            details = details_builder(actor) + " (Whitelisted Single Action - Reverted & Warned)"
            if revert_func:
                try:
                    await revert_func(incident_id)
                except Exception as e:
                    logger.error(f"Revert failed during whitelisted action: {e}")

            # 1. Log Whitelist Warning to security logs
            await log_security_event(
                self.bot, guild, actor, f"Whitelist Warning [{breach_vector}]",
                "⚠️ WARNED (Action Reverted)", details,
                incident_id=incident_id, is_warn=True
            )
            # 2. Dispatch warning DM to Server Owner
            await dispatch_owner_security_dm(
                self.bot, guild, actor, f"Whitelist Warning [{breach_vector}]",
                "Warned + Action Reverted", details,
                incident_id=incident_id
            )
            # 3. Log to DB
            await self.bot.db.log_security_audit(
                guild.id, actor.id, breach_vector, required_scope, target_id, "WARNED_REVERTED", incident_id,
                details
            )
            return

        # Action is authorized and benign
        await self.bot.db.log_security_audit(
            guild.id, actor.id, breach_vector, required_scope, target_id, "ALLOWED", incident_id,
            details_builder(actor)
        )

    # --- 1. CHANNEL CREATION DEFENSE ---
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        guild = channel.guild

        async def revert(inc_id: str):
            try:
                if guild.me.guild_permissions.manage_channels:
                    await channel.delete(reason=f"Shizu Anti-Nuke: Purged unauthorized rogue channel [{inc_id}]")
            except Exception:
                pass

        await self.evaluate_event(
            guild=guild,
            action=discord.AuditLogAction.channel_create,
            target_id=channel.id,
            required_scope="antinuke.channel.create",
            breach_vector="Channel Create",
            revert_func=revert,
            details_builder=lambda actor: f"Created rogue channel #{channel.name} (`ID: {channel.id}`)"
        )

    # --- 2. CHANNEL DELETION DEFENSE & AUTO-RECREATION ---
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        guild = channel.guild

        async def revert(inc_id: str):
            if guild.me.guild_permissions.manage_channels:
                await revert_channel_delete(self.bot, guild, channel.id, inc_id)

        await self.evaluate_event(
            guild=guild,
            action=discord.AuditLogAction.channel_delete,
            target_id=channel.id,
            required_scope="antinuke.channel.delete",
            breach_vector="Channel Delete",
            revert_func=revert,
            details_builder=lambda actor: f"Deleted server channel #{channel.name} (`ID: {channel.id}`)"
        )

    # --- 3. CHANNEL UPDATE DEFENSE ---
    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        guild = after.guild

        async def revert(inc_id: str):
            snap = await self.bot.db.get_channel_snapshot(guild.id, before.id)
            if snap and guild.me.guild_permissions.manage_channels:
                try:
                    await after.edit(name=snap["name"], topic=snap.get("topic"), reason=f"Shizu Anti-Nuke: Restored channel [{inc_id}]")
                except Exception:
                    pass

        await self.evaluate_event(
            guild=guild,
            action=discord.AuditLogAction.channel_update,
            target_id=after.id,
            required_scope="antinuke.channel.edit",
            breach_vector="Channel Edit",
            revert_func=revert,
            details_builder=lambda actor: f"Modified channel settings/permissions on #{after.name}"
        )

    # --- 4. ROLE CREATION DEFENSE ---
    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        guild = role.guild

        async def revert(inc_id: str):
            try:
                if guild.me.guild_permissions.manage_roles and role < guild.me.top_role:
                    await role.delete(reason=f"Shizu Anti-Nuke: Purged rogue role [{inc_id}]")
            except Exception:
                pass

        await self.evaluate_event(
            guild=guild,
            action=discord.AuditLogAction.role_create,
            target_id=role.id,
            required_scope="antinuke.role.create",
            breach_vector="Role Create",
            revert_func=revert,
            details_builder=lambda actor: f"Created rogue role @{role.name} (`ID: {role.id}`)"
        )

    # --- 5. ROLE DELETION DEFENSE & AUTO-RECREATION ---
    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        guild = role.guild

        async def revert(inc_id: str):
            if guild.me.guild_permissions.manage_roles:
                await revert_role_delete(self.bot, guild, role.id, inc_id)

        await self.evaluate_event(
            guild=guild,
            action=discord.AuditLogAction.role_delete,
            target_id=role.id,
            required_scope="antinuke.role.delete",
            breach_vector="Role Delete",
            revert_func=revert,
            details_builder=lambda actor: f"Deleted server role @{role.name} (`ID: {role.id}`)"
        )

    # --- 6. ROLE UPDATE & DANGEROUS PERMISSION DEFENSE ---
    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        guild = after.guild

        # Check if dangerous permissions were added
        before_perms = dict(before.permissions)
        after_perms = dict(after.permissions)
        added_perms = [p for p in DANGEROUS_PERMS if not before_perms.get(p) and after_perms.get(p)]

        async def revert(inc_id: str):
            if guild.me.guild_permissions.manage_roles and after < guild.me.top_role:
                try:
                    await after.edit(permissions=before.permissions, reason=f"Shizu Anti-Nuke: Stripped dangerous permissions [{inc_id}]")
                except Exception:
                    pass

        vector = f"Role Perm Escalation (+{', '.join(added_perms)})" if added_perms else "Role Edit"
        await self.evaluate_event(
            guild=guild,
            action=discord.AuditLogAction.role_update,
            target_id=after.id,
            required_scope="antinuke.role.edit",
            breach_vector=vector,
            revert_func=revert,
            details_builder=lambda actor: f"Escalated permissions on @{after.name}: {', '.join(added_perms) if added_perms else 'Settings updated'}"
        )

    # --- 7. DANGEROUS ROLE ASSIGNMENT DEFENSE ---
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        guild = after.guild
        added_roles = [r for r in after.roles if r not in before.roles]
        if not added_roles:
            return

        cfg = await self.bot.db.get_guild_config(guild.id)
        if not cfg.get("antinuke_enabled"):
            return

        entry = await self.get_audit_entry(guild, discord.AuditLogAction.member_role_update, after.id)
        if not entry or not entry.user or entry.user.id == self.bot.user.id or entry.user.id in config.OWNER_IDS:
            return

        actor = entry.user
        incident_id = generate_incident_id()

        for role in added_roles:
            # Check if role carries dangerous administrative permissions
            role_perms = dict(role.permissions)
            has_dangerous_perms = any(role_perms.get(p, False) for p in ("administrator", "ban_members", "manage_guild", "manage_roles"))

            if has_dangerous_perms:
                # Check if actor is authorized to assign this role
                is_authorized = await self.bot.db.has_scope(guild.id, actor, "antinuke.role.assign", role.id)
                if not is_authorized:
                    try:
                        if role < guild.me.top_role:
                            await after.remove_roles(role, reason=f"Shizu Anti-Nuke: Stripped unauthorized admin role [{incident_id}]")
                    except Exception:
                        pass

                    await execute_breach_countermeasures(
                        self.bot, guild, actor, "Dangerous Role Assignment",
                        f"Assigned role @{role.name} carrying Admin/Ban/ManageGuild permissions to {after.mention}",
                        incident_id
                    )
                    return

    # --- 8. ANTI-BOT DEFENSE (COMPLETE MULTI-TIER RULES) ---
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """
        Anti-Bot Enforcement Rules:
        - If antibot is turned on: every bot joining is intercepted!
        - If server owner added: KICK BOT (remind owner to ?antibot off first).
        - If whitelisted user added: BAN BOT; if inviter below Shizu: TIMEOUT & STRIP ROLES.
        - If non-whitelisted user added: BAN BOT & BAN INVITER directly!
        - Hierarchy check: If inviter is above Shizu, damage is reverted and Emergency DM is sent to Owner.
        """
        if not member.bot:
            return

        guild = member.guild
        cfg = await self.bot.db.get_guild_config(guild.id)
        antibot_on = cfg.get("antibot_enabled", False)
        antinuke_on = cfg.get("antinuke_enabled", False)

        # Active if either Anti-Bot or Anti-Nuke is armed
        if not antibot_on and not antinuke_on:
            return

        entry = await self.get_audit_entry(guild, discord.AuditLogAction.bot_add, member.id)
        incident_id = generate_incident_id()
        actor = entry.user if entry else None

        # Bot self-actions bypass
        if actor and actor.id == self.bot.user.id:
            return

        # 1. SERVER OWNER ADDED BOT
        if actor and actor.id == guild.owner_id:
            if antibot_on:
                # Kick the bot!
                try:
                    await member.kick(reason=f"Shizu Anti-Bot: Active on server. Turn off (?antibot off) before adding bots. [{incident_id}]")
                    action_taken = "BOT_KICKED_OWNER_NOTIFIED"
                except Exception as e:
                    action_taken = f"BOT_KICK_FAILED ({e})"

                # Direct Message warning to Server Owner
                try:
                    dm_embed = discord.Embed(
                        title=f"{config.ANIM_WARN} Anti-Bot Protection Active",
                        description=(
                            f"You invited the bot **{member.name}** (`ID: {member.id}`) to **{guild.name}**, "
                            f"but **Anti-Bot is currently ON**.\n\n"
                            f"Shizu automatically **kicked the bot**.\n\n"
                            f"💡 **To add bots to your server:**\n"
                            f"1. Run `?antibot off` to temporarily disable Anti-Bot.\n"
                            f"2. Re-invite your bot.\n"
                            f"3. Run `?antibot on` to re-arm protection."
                        ),
                        color=config.COLOR_WARN
                    )
                    dm_embed.set_thumbnail(url=member.display_avatar.url)
                    dm_embed.set_footer(text=f"Shizu Security v{config.VERSION} • Automated Protection")
                    dm_embed.timestamp = discord.utils.utcnow()
                    await guild.owner.send(embed=dm_embed)
                except Exception:
                    pass

                # Log to Shizu security logs with top-right bot avatar
                await log_security_event(
                    self.bot, guild, actor, "Anti-Bot: Bot Addition Intercepted",
                    action_taken, f"Server Owner added bot {member.mention} while Anti-Bot is enabled. Bot was kicked.",
                    incident_id=incident_id, thumbnail_url=member.display_avatar.url, is_warn=True
                )
                return
            return

        # 2. GLOBAL DEVELOPER IMMUNITY
        if actor and actor.id in config.OWNER_IDS:
            return

        # Check Whitelist status of actor
        is_whitelisted = False
        if actor:
            actor_member = guild.get_member(actor.id) or actor
            is_whitelisted = await self.bot.db.has_scope(guild.id, actor_member, "antinuke.bot.add", member.id)

        # 3. WHITELISTED USER ADDED BOT
        if is_whitelisted and actor:
            # Always ban the newly added bot!
            try:
                await member.ban(reason=f"Shizu Anti-Bot: Whitelisted user added bot while Anti-Bot enabled [{incident_id}]")
                bot_action = "BOT_BANNED"
            except Exception as e:
                bot_action = f"BOT_BAN_FAILED ({e})"

            actor_member = guild.get_member(actor.id)
            bot_member = guild.me
            can_punish_member = (
                actor_member and
                bot_member.guild_permissions.moderate_members and
                bot_member.top_role > actor_member.top_role and
                actor_member != guild.owner
            )

            if can_punish_member:
                # Timeout member (1 hour) & strip dangerous roles
                try:
                    await actor_member.timeout(datetime.timedelta(hours=1), reason=f"Shizu Anti-Bot: Added bot while Anti-Bot active [{incident_id}]")
                except Exception:
                    pass

                roles_to_strip = [
                    r for r in actor_member.roles
                    if not r.is_default() and r < bot_member.top_role and any(dict(r.permissions).get(p, False) for p in DANGEROUS_PERMS)
                ]
                if roles_to_strip:
                    try:
                        await actor_member.remove_roles(*roles_to_strip, reason=f"Shizu Anti-Bot: Stripped elevated roles [{incident_id}]")
                    except Exception:
                        pass

                user_action = "MEMBER_TIMED_OUT_AND_ROLES_STRIPPED"
                is_hierarchy_block = False
            else:
                user_action = "MEMBER_HIERARCHY_PROTECTED"
                is_hierarchy_block = True

            action_summary = f"{bot_action} + {user_action}"

            # Log to security logs & dispatch owner DM
            await log_security_event(
                self.bot, guild, actor, "Anti-Bot: Whitelisted Bot Addition",
                action_summary, f"Whitelisted user {actor.mention} added bot {member.mention} while Anti-Bot is enabled.",
                incident_id=incident_id, thumbnail_url=member.display_avatar.url
            )
            await dispatch_owner_security_dm(
                self.bot, guild, actor, "Anti-Bot: Whitelisted Bot Added",
                action_summary, f"Added bot {member.name} (`ID: {member.id}`). Bot was banned.",
                incident_id=incident_id, thumbnail_url=member.display_avatar.url,
                is_hierarchy_escalation=is_hierarchy_block
            )
            return

        # 4. NON-WHITELISTED USER ADDED BOT -> BAN BOT & BAN USER!
        try:
            await member.ban(reason=f"Shizu Anti-Bot: Rogue bot added by unwhitelisted user [{incident_id}]")
            bot_action = "BOT_BANNED"
        except Exception as e:
            bot_action = f"BOT_BAN_FAILED ({e})"

        actor_action = "NO_ACTOR_FOUND"
        is_hierarchy_block = False

        if actor:
            actor_member = guild.get_member(actor.id)
            bot_member = guild.me
            can_ban_actor = (
                actor_member and
                bot_member.guild_permissions.ban_members and
                bot_member.top_role > actor_member.top_role and
                actor_member != guild.owner
            )

            if can_ban_actor:
                try:
                    await guild.ban(actor_member, reason=f"Shizu Anti-Nuke: Invited unauthorized bot [{incident_id}]")
                    actor_action = "ACTOR_BANNED"
                except Exception as e:
                    actor_action = f"ACTOR_BAN_FAILED ({e})"
            else:
                if actor_member and bot_member.top_role <= actor_member.top_role:
                    actor_action = "ACTOR_HIERARCHY_PROTECTED"
                    is_hierarchy_block = True
                else:
                    try:
                        await guild.ban(discord.Object(id=actor.id), reason=f"Shizu Anti-Nuke: Invited unauthorized bot [{incident_id}]")
                        actor_action = "ACTOR_BANNED_BY_ID"
                    except Exception:
                        actor_action = "ACTOR_BAN_FAILED"

        action_summary = f"{bot_action} + {actor_action}"
        await log_security_event(
            self.bot, guild, actor or "Unknown User", "Anti-Bot: Unauthorized Bot Addition",
            action_summary, f"Unwhitelisted user added bot {member.mention}. Bot was banned.",
            incident_id=incident_id, thumbnail_url=member.display_avatar.url
        )
        await dispatch_owner_security_dm(
            self.bot, guild, actor or "Unknown User", "Anti-Bot: Unauthorized Bot Added",
            action_summary, f"Unwhitelisted user added bot {member.name} (`ID: {member.id}`). Bot was banned.",
            incident_id=incident_id, thumbnail_url=member.display_avatar.url,
            is_hierarchy_escalation=is_hierarchy_block
        )

    # --- 9. WEBHOOK CREATION DEFENSE ---
    @commands.Cog.listener()
    async def on_webhooks_update(self, channel: discord.abc.GuildChannel):
        guild = channel.guild

        async def revert(inc_id: str):
            try:
                if guild.me.guild_permissions.manage_webhooks and hasattr(channel, "webhooks"):
                    webhooks = await channel.webhooks()
                    for wh in webhooks:
                        await wh.delete(reason=f"Shizu Anti-Nuke: Deleted rogue webhook [{inc_id}]")
            except Exception:
                pass

        await self.evaluate_event(
            guild=guild,
            action=discord.AuditLogAction.webhook_create,
            target_id=None,
            required_scope="antinuke.webhook.manage",
            breach_vector="Webhook Create",
            revert_func=revert,
            details_builder=lambda actor: f"Created unauthorized webhook in #{channel.name}"
        )

    # --- 10. MEMBER BAN DEFENSE ---
    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        async def revert(inc_id: str):
            try:
                if guild.me.guild_permissions.ban_members:
                    await guild.unban(user, reason=f"Shizu Anti-Nuke: Unbanned victim of rogue ban [{inc_id}]")
            except Exception:
                pass

        await self.evaluate_event(
            guild=guild,
            action=discord.AuditLogAction.ban,
            target_id=user.id,
            required_scope="antinuke.member.ban",
            breach_vector="Member Ban",
            revert_func=revert,
            details_builder=lambda actor: f"Executed unauthorized ban against {user.mention} (`ID: {user.id}`)"
        )

    # --- 11. MEMBER KICK DEFENSE ---
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild = member.guild
        if member.bot:
            return

        await self.evaluate_event(
            guild=guild,
            action=discord.AuditLogAction.kick,
            target_id=member.id,
            required_scope="antinuke.member.kick",
            breach_vector="Member Kick",
            revert_func=None,  # Discord cannot force a kicked member back; alert + log generated
            details_builder=lambda actor: f"Kicked member {member.mention} (`ID: {member.id}`)"
        )

    # --- 12. GUILD SETTINGS TAMPER DEFENSE ---
    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        guild = after

        async def revert(inc_id: str):
            if guild.me.guild_permissions.manage_guild and before.name != after.name:
                await after.edit(name=before.name, reason=f"Shizu Anti-Nuke: Restored server name [{inc_id}]")

        changes = []
        if before.name != after.name:
            changes.append(f"Name ('{before.name}' -> '{after.name}')")
        if before.vanity_url_code != after.vanity_url_code:
            changes.append(f"Vanity ('{before.vanity_url_code}' -> '{after.vanity_url_code}')")

        await self.evaluate_event(
            guild=guild,
            action=discord.AuditLogAction.guild_update,
            target_id=None,
            required_scope="antinuke.guild.edit",
            breach_vector="Guild Edit",
            revert_func=revert,
            details_builder=lambda actor: f"Tampered server settings: {', '.join(changes) if changes else 'Settings updated'}"
        )

    # --- 13. ANTI-MASS PING (@everyone / @here) DEFENSE ---
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        # Check if @everyone or @here is pinged
        if message.mention_everyone:
            guild = message.guild
            cfg = await self.bot.db.get_guild_config(guild.id)
            if not cfg.get("antinuke_enabled"):
                return

            actor = message.author
            if actor.id == guild.owner_id or actor.id in config.OWNER_IDS:
                return

            # Check if whitelisted
            is_whitelisted = await self.bot.db.has_scope(guild.id, actor, "automod.bypass.mentions", None)
            if is_whitelisted:
                return

            # UNWHITELISTED MASS PING -> PURGE MESSAGE & TIMEOUT/BAN
            incident_id = generate_incident_id()
            try:
                await message.delete()
            except Exception:
                pass

            bot_member = guild.me
            action_taken = "MESSAGE_PURGED"
            is_hierarchy_block = False

            if bot_member.guild_permissions.moderate_members and bot_member.top_role > actor.top_role:
                try:
                    await actor.timeout(datetime.timedelta(hours=1), reason=f"Shizu Anti-Nuke: Unauthorized @everyone ping [{incident_id}]")
                    action_taken = "MESSAGE_PURGED_ACTOR_TIMED_OUT"
                except Exception:
                    pass
            elif bot_member.top_role <= actor.top_role:
                is_hierarchy_block = True
                action_taken = "MESSAGE_PURGED_ACTOR_HIERARCHY_PROTECTED"

            await log_security_event(
                self.bot, guild, actor, "Anti-Nuke: Mass Ping (@everyone)",
                action_taken, f"Sent unauthorized mass ping in {message.channel.mention}. Message purged.",
                incident_id=incident_id, is_hierarchy_escalation=is_hierarchy_block
            )
            await dispatch_owner_security_dm(
                self.bot, guild, actor, "Anti-Nuke: Mass Ping (@everyone)",
                action_taken, f"Sent unauthorized mass ping in {message.channel.mention}. Message purged.",
                incident_id=incident_id, is_hierarchy_escalation=is_hierarchy_block
            )

    # --- 14. EMOJI MODIFICATION DEFENSE ---
    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild: discord.Guild, before: List[discord.Emoji], after: List[discord.Emoji]):
        deleted_emojis = [em for em in before if em not in after]
        if not deleted_emojis:
            return

        await self.evaluate_event(
            guild=guild,
            action=discord.AuditLogAction.emoji_delete,
            target_id=deleted_emojis[0].id if deleted_emojis else None,
            required_scope="antinuke.emoji.manage",
            breach_vector="Emoji Delete",
            revert_func=None,
            details_builder=lambda actor: f"Deleted {len(deleted_emojis)} server emojis ({', '.join(e.name for e in deleted_emojis[:3])})"
        )

async def setup(bot):
    await bot.add_cog(AntiNukeEvents(bot))
