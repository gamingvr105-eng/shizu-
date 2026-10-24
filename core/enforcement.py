"""
Shizu Security - Zero-Trust Enforcement & Logging Kernel
Handles actor resolution, fixed sliding-window burst limits, the Revert Map,
incident ticketing, hierarchy-safe punishment, 2-channel logging, and Owner DM alerts.
"""

import time
import uuid
import random
import json
import datetime
import discord
from collections import defaultdict
from typing import Optional, Tuple, Dict, Any, List
from config import config

class BurstTracker:
    def __init__(self, max_burst: int = config.MAX_BURST_ACTIONS, window: float = config.BURST_WINDOW):
        self.max_burst = max_burst
        self.window = window
        self.history: Dict[Tuple[int, int], List[float]] = defaultdict(list)

    def record_and_check(self, guild_id: int, actor_id: int) -> bool:
        """
        Records an action timestamp for (guild_id, actor_id) and cleans stale records.
        Returns True if the actor has exceeded the fixed burst limit (mass breach).
        """
        now = time.time()
        key = (guild_id, actor_id)
        timestamps = self.history[key]

        # Prune expired timestamps
        cutoff = now - self.window
        self.history[key] = [t for t in timestamps if t > cutoff]

        # Append new timestamp
        self.history[key].append(now)

        # Breach condition: strictly greater than allowed burst limit
        return len(self.history[key]) > self.max_burst

    def reset(self, guild_id: int, actor_id: int):
        key = (guild_id, actor_id)
        if key in self.history:
            del self.history[key]

# Global singleton burst tracker
burst_tracker = BurstTracker()

def generate_incident_id() -> str:
    """Generates an alphanumeric incident ticket ID (e.g. #INC-7A9B)."""
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    code = "".join(random.choices(chars, k=4))
    return f"#INC-{code}"


async def log_security_event(
    bot,
    guild: discord.Guild,
    actor: Any,
    trigger_event: str,
    action_taken: str,
    details: str,
    incident_id: Optional[str] = None,
    thumbnail_url: Optional[str] = None,
    is_warn: bool = False,
    is_hierarchy_escalation: bool = False,
    revert_status: str = "Restored"
):
    """
    Dispatches a high-end dark embed alert to the configured Shizu security log channel.
    Features:
    - Clean obsidian theme with top-right thumbnail (avatar).
    - Tasteful animated emojis.
    - Full forensic breakdown and audit tracking.
    """
    cfg = await bot.db.get_guild_config(guild.id)
    # Channel fallback: log_security / log_antinuke
    log_cid = cfg.get("log_antinuke")
    if not log_cid:
        return

    log_channel = guild.get_channel(log_cid)
    if not log_channel:
        return

    inc_id = incident_id or generate_incident_id()
    actor_id = actor.id if hasattr(actor, "id") else (actor if isinstance(actor, int) else None)
    actor_mention = actor.mention if hasattr(actor, "mention") else (f"<@{actor_id}>" if actor_id else str(actor))
    actor_tag = str(actor) if hasattr(actor, "__str__") else f"ID {actor_id}"

    # Determine Embed Aesthetics & Title
    if is_hierarchy_escalation:
        embed_title = f"{config.ANIM_ALERT} Emergency Hierarchy Escalation"
        embed_color = 0xDC2626  # Pure Red
    elif is_warn:
        embed_title = f"{config.ANIM_WARN} Whitelist Security Notice"
        embed_color = 0xF59E0B  # Amber/Yellow
    elif "bot" in trigger_event.lower():
        embed_title = f"{config.ANIM_SHIELD} Anti-Bot Interception Alert"
        embed_color = 0x0F172A  # Obsidian Dark
    else:
        embed_title = f"{config.ANIM_ALERT} Anti-Nuke Security Alert"
        embed_color = 0x000000  # Shizu Signature Pure Black

    embed = discord.Embed(
        title=embed_title,
        description=f"Automated defense intercepted an unauthorized server event.\n**Incident Ticket:** `{inc_id}`",
        color=embed_color
    )

    # Top-right thumbnail avatar
    thumb = thumbnail_url
    if not thumb and hasattr(actor, "display_avatar"):
        thumb = actor.display_avatar.url
    elif not thumb and guild.icon:
        thumb = guild.icon.url

    if thumb:
        embed.set_thumbnail(url=thumb)

    # Clean structured fields
    embed.add_field(
        name="👤 Offender",
        value=f"{actor_mention}\n`ID: {actor_id or 'Unknown'}`",
        inline=True
    )
    embed.add_field(
        name="🛡️ Trigger Vector",
        value=f"**`{trigger_event}`**\n`Ticket: {inc_id}`",
        inline=True
    )
    embed.add_field(
        name="⚡ Action Taken",
        value=f"**{action_taken}**",
        inline=True
    )
    embed.add_field(
        name="🔄 Self-Healing Status",
        value=f"**{config.ANIM_SUCCESS} {revert_status}**",
        inline=True
    )
    embed.add_field(
        name="📋 Forensic Details",
        value=details,
        inline=False
    )

    embed.set_footer(
        text=f"{config.BOT_NAME} v{config.VERSION} • Automated Server Defense",
        icon_url=guild.icon.url if guild.icon else None
    )
    embed.timestamp = discord.utils.utcnow()

    try:
        await log_channel.send(embed=embed)
    except Exception:
        pass


# Backward compatibility alias
log_security_breach = log_security_event


async def dispatch_owner_security_dm(
    bot,
    guild: discord.Guild,
    actor: Any,
    trigger_event: str,
    action_taken: str,
    details: str,
    incident_id: Optional[str] = None,
    thumbnail_url: Optional[str] = None,
    is_hierarchy_escalation: bool = False
):
    """
    Sends an urgent, high-priority Direct Message to the Guild Owner for EVERY Anti-Nuke and Anti-Bot trigger.
    Includes technical forensics, recovery status, and actionable owner guidance.
    """
    owner = guild.owner
    if not owner:
        try:
            owner = await bot.fetch_user(guild.owner_id)
        except Exception:
            return

    if not owner:
        return

    inc_id = incident_id or generate_incident_id()
    actor_id = actor.id if hasattr(actor, "id") else (actor if isinstance(actor, int) else "Unknown")
    actor_tag = str(actor) if hasattr(actor, "__str__") else f"ID {actor_id}"

    if is_hierarchy_escalation:
        title = f"{config.ANIM_ALERT} URGENT: HIERARCHY ESCALATION ALERT"
        color = 0xDC2626
        header_text = (
            f"**Action Reverted, but Offender has Higher Hierarchy!**\n"
            f"Shizu Security successfully reverted the damage to your server, but the offending member "
            f"has a **higher or equal role hierarchy than Shizu**. Discord permission rules prevent Shizu "
            f"from banning them automatically.\n\n"
            f"🚨 **IMMEDIATE OWNER ACTION REQUIRED:** Please ban or demote the offending user manually!"
        )
    else:
        title = f"{config.ANIM_WARN} SECURITY ALERT FOR SERVER OWNER"
        color = 0xF59E0B
        header_text = (
            f"An Anti-Nuke trigger was executed on your server. Shizu Security automatically intercepted "
            f"the event, neutralized the threat, and restored your server's state."
        )

    embed = discord.Embed(
        title=title,
        description=f"👑 **Server:** **{guild.name}** (`ID: {guild.id}`)\n\n{header_text}",
        color=color
    )

    # Top-right thumbnail
    thumb = thumbnail_url
    if not thumb and hasattr(actor, "display_avatar"):
        thumb = actor.display_avatar.url
    elif not thumb and guild.icon:
        thumb = guild.icon.url

    if thumb:
        embed.set_thumbnail(url=thumb)

    embed.add_field(name="👤 Triggered By", value=f"{actor_tag}\n`ID: {actor_id}`", inline=True)
    embed.add_field(name="🛡️ Trigger Vector", value=f"`{trigger_event}`", inline=True)
    embed.add_field(name="⚡ Action Taken", value=f"**{action_taken}**", inline=True)
    embed.add_field(name="🔄 Incident Ticket", value=f"`{inc_id}`", inline=True)
    embed.add_field(name="📋 Details", value=details, inline=False)

    if not is_hierarchy_escalation:
        embed.add_field(
            name="💡 Recommended Owner Action",
            value=(
                "The server has been self-healed. If this staff member was authorized, "
                "add them to the whitelist via `?whitelist add @user`."
            ),
            inline=False
        )

    embed.set_footer(
        text=f"{config.BOT_NAME} v{config.VERSION} • 24/7 Server Owner Guard",
        icon_url=guild.icon.url if guild.icon else None
    )
    embed.timestamp = discord.utils.utcnow()

    try:
        await owner.send(embed=embed)
    except Exception:
        pass


async def execute_breach_countermeasures(
    bot,
    guild: discord.Guild,
    actor: Any,
    breach_vector: str,
    details: str,
    incident_id: Optional[str] = None
) -> Tuple[str, str]:
    """
    Executes the direct Stop-and-Punish protocol against an actor.
    - If unwhitelisted: Ban directly.
    - If actor has higher hierarchy: Revert damage and dispatch hierarchy escalation DM to Owner.
    - Sends DM to Server Owner for every trigger.
    Returns (action_taken, incident_id).
    """
    inc_id = incident_id or generate_incident_id()
    actor_id = actor.id if hasattr(actor, "id") else int(actor)

    # 1. Global Developer check (Immunity with diagnostic audit)
    if actor_id in config.OWNER_IDS:
        await bot.db.log_security_audit(
            guild.id, actor_id, breach_vector, "developer.override", None, "ALLOWED", inc_id, "Global developer diagnostic override"
        )
        return "DEVELOPER_DIAGNOSTIC_OVERRIDE", inc_id

    # 2. Server Owner check (Discord cannot ban or strip server owner)
    if actor_id == guild.owner_id:
        action_taken = "REVERT_AND_ALERT_OWNER"
        await log_security_event(bot, guild, actor, breach_vector, "Reverted Incident & Alerted Owner", details, incident_id=inc_id, is_warn=True)
        await dispatch_owner_security_dm(bot, guild, actor, breach_vector, "Reverted & Alerted", details, incident_id=inc_id)
        await bot.db.log_security_audit(
            guild.id, actor_id, breach_vector, "owner.breach", None, "BREACH_STOPPED", inc_id, f"Server owner action reverted: {details}"
        )
        return action_taken, inc_id

    # Resolve member object if possible
    member = guild.get_member(actor_id)
    bot_member = guild.me

    action_taken = "STOP_FAILED"
    is_hierarchy_block = False

    if member and bot_member:
        # Check hierarchy: cannot ban if actor is higher than or equal to bot
        can_ban = (bot_member.guild_permissions.ban_members and
                   bot_member.top_role > member.top_role and
                   member != guild.owner)

        # STOP: Strip dangerous roles
        dangerous_perms = {"administrator", "manage_guild", "ban_members", "manage_roles", "manage_channels"}
        roles_to_remove = []
        for r in member.roles:
            if r.is_default() or r >= bot_member.top_role:
                continue
            r_perms = dict(r.permissions)
            if any(r_perms.get(p, False) for p in dangerous_perms):
                roles_to_remove.append(r)

        if roles_to_remove:
            try:
                await member.remove_roles(*roles_to_remove, reason=f"Shizu Security: Dangerous roles stripped [{inc_id}]")
            except Exception:
                pass

        # PUNISH: Ban the actor directly
        if can_ban:
            try:
                await guild.ban(
                    member,
                    reason=f"Shizu Anti-Nuke: {breach_vector} [{inc_id}]",
                    delete_message_days=0
                )
                action_taken = "PERMANENTLY_BANNED"
            except Exception as e:
                action_taken = f"BAN_FAILED ({e})"
        else:
            action_taken = "HIERARCHY_PROTECTED_ACTION_REVERTED"
            is_hierarchy_block = True
    else:
        # User not cached or left server: attempt guild ban by user ID
        try:
            await guild.ban(
                discord.Object(id=actor_id),
                reason=f"Shizu Anti-Nuke: {breach_vector} [{inc_id}]"
            )
            action_taken = "BANNED_BY_ID"
        except Exception:
            action_taken = "BAN_FAILED_NOT_IN_GUILD"

    # Log to audit database & alert channel
    await bot.db.log_security_audit(
        guild.id, actor_id, breach_vector, "none", None, "BREACH_STOPPED", inc_id, details
    )
    
    # 1. Log to Shizu security logs with top-right avatar
    await log_security_event(
        bot, guild, actor, breach_vector, action_taken, details,
        incident_id=inc_id, is_hierarchy_escalation=is_hierarchy_block
    )

    # 2. Dispatch warning DM to Server Owner for EVERY trigger
    await dispatch_owner_security_dm(
        bot, guild, actor, breach_vector, action_taken, details,
        incident_id=inc_id, is_hierarchy_escalation=is_hierarchy_block
    )

    return action_taken, inc_id


# --- Revert Map Helpers ---

async def revert_channel_delete(bot, guild: discord.Guild, channel_id: int, incident_id: str) -> Optional[discord.abc.GuildChannel]:
    """Recreates a deleted channel with exact permissions from saved snapshot."""
    snap = await bot.db.get_channel_snapshot(guild.id, channel_id)
    if not snap:
        return None

    try:
        category = None
        if snap.get("category_id"):
            category = guild.get_channel(snap["category_id"])

        overwrites = {}
        if snap.get("overwrites_json"):
            try:
                raw_ow = json.loads(snap["overwrites_json"])
                for target_id, ow_data in raw_ow.items():
                    target = guild.get_role(int(target_id)) or guild.get_member(int(target_id))
                    if target:
                        allow = discord.Permissions(ow_data.get("allow", 0))
                        deny = discord.Permissions(ow_data.get("deny", 0))
                        overwrites[target] = discord.PermissionOverwrite.from_pair(allow, deny)
            except Exception:
                pass

        ch_type = snap.get("channel_type", "text")
        new_ch = None

        if ch_type == "text":
            new_ch = await guild.create_text_channel(
                name=snap["name"],
                category=category,
                topic=snap.get("topic"),
                slowmode_delay=snap.get("slowmode_delay", 0),
                nsfw=snap.get("nsfw", False),
                overwrites=overwrites,
                reason=f"Shizu Anti-Nuke: Auto-recreated nuked channel [{incident_id}]"
            )
        elif ch_type == "voice":
            new_ch = await guild.create_voice_channel(
                name=snap["name"],
                category=category,
                overwrites=overwrites,
                reason=f"Shizu Anti-Nuke: Auto-recreated nuked voice channel [{incident_id}]"
            )
        elif ch_type == "category":
            new_ch = await guild.create_category(
                name=snap["name"],
                overwrites=overwrites,
                reason=f"Shizu Anti-Nuke: Auto-recreated nuked category [{incident_id}]"
            )

        return new_ch
    except Exception:
        return None


async def revert_role_delete(bot, guild: discord.Guild, role_id: int, incident_id: str) -> Optional[discord.Role]:
    """Recreates a deleted role from snapshot."""
    snap = await bot.db.get_role_snapshot(guild.id, role_id)
    if not snap:
        return None

    try:
        new_role = await guild.create_role(
            name=snap["name"],
            permissions=discord.Permissions(snap.get("permissions", 0)),
            color=discord.Color(snap.get("color", 0)),
            hoist=snap.get("hoist", False),
            mentionable=snap.get("mentionable", False),
            reason=f"Shizu Anti-Nuke: Auto-recreated nuked role [{incident_id}]"
        )
        return new_role
    except Exception:
        return None
