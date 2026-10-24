"""
Shizu Security - Zero-Trust Canonical Scopes & Definitions
Defines all granular permissions, sections, and Supreme sets.
"""

from typing import List, Dict, Set

# --- Canonical Scope Registry ---

SCOPES_CHANNELS = {
    "antinuke.channel.create": "Create channels & categories",
    "antinuke.channel.edit": "Modify channel permissions, topics, names",
    "antinuke.channel.delete": "Delete channels & categories"
}

SCOPES_ROLES = {
    "antinuke.role.create": "Create new server roles",
    "antinuke.role.edit": "Modify role permissions, colors, positions",
    "antinuke.role.delete": "Delete existing roles",
    "antinuke.role.assign": "Assign existing roles to members (Hard-blocked on Admin/Ban/ManageGuild)"
}

SCOPES_MEMBERS = {
    "antinuke.member.ban": "Ban members from the server",
    "antinuke.member.kick": "Kick members from the server"
}

SCOPES_WEBHOOKS_BOTS = {
    "antinuke.webhook.manage": "Create, edit, or delete webhooks",
    "antinuke.bot.add": "Invite / add external bots to the server"
}

SCOPES_SERVER_EMOJIS = {
    "antinuke.guild.edit": "Modify server name, icon, vanity, widget, features",
    "antinuke.emoji.manage": "Create, modify, or delete server emojis & stickers"
}

SCOPES_AUTOMOD_BYPASS = {
    "automod.bypass.all": "Bypass all AutoMod filters",
    "automod.bypass.spam": "Bypass Anti-Spam / Flood detector",
    "automod.bypass.invite": "Bypass Anti-Invite detector",
    "automod.bypass.link": "Bypass Anti-Link filter",
    "automod.bypass.badwords": "Bypass Bad Words filter",
    "automod.bypass.caps": "Bypass Anti-Caps filter",
    "automod.bypass.mention": "Bypass Mass-Mention filter",
    "automod.bypass.emoji": "Bypass Emoji-Spam filter"
}

SCOPES_MODERATION = {
    "mod.ban": "Execute ?ban command",
    "mod.kick": "Execute ?kick command",
    "mod.timeout": "Execute ?timeout / ?untimeout",
    "mod.warn": "Execute ?warn command",
    "mod.purge": "Execute ?purge command",
    "mod.lock": "Execute ?lock / ?unlock command",
    "mod.hide": "Execute ?hide / ?unhide command",
    "mod.slowmode": "Execute ?slowmode command",
    "mod.role": "Execute ?role add / remove command",
    "mod.nick": "Execute ?setnick command",
    "mod.snipe": "Execute ?snipe command"
}

SCOPES_RECOVERY = {
    "backup.create": "Execute ?backup layout snapshot",
    "backup.restore": "Execute ?restore channels / roles"
}

# Administrative Scopes (Strictly restricted to Guild Owner and Extra Owners)
SCOPES_ADMIN = {
    "whitelist.manage": "Add, remove, or modify whitelist entries and scopes",
    "extraowner.manage": "Assign or remove designated Extra Owners",
    "security.configure": "Toggle security rules, change punishments, bind log channels",
    "lockdown.toggle": "Engage or disengage emergency server lockdown (?lockdown / ?unlockdown)"
}

# Categorized Sections for Whitelist UI Multi-Select
SCOPE_SECTIONS: Dict[str, Dict[str, str]] = {
    "Channels": SCOPES_CHANNELS,
    "Roles": SCOPES_ROLES,
    "Members": SCOPES_MEMBERS,
    "Webhooks & Bots": SCOPES_WEBHOOKS_BOTS,
    "Server & Emojis": SCOPES_SERVER_EMOJIS,
    "AutoMod Bypass": SCOPES_AUTOMOD_BYPASS,
    "Moderation": SCOPES_MODERATION,
    "Recovery": SCOPES_RECOVERY
}

# Supreme Scope Bundle: Grants every operational, AutoMod, and recovery scope.
# Note: STRICTLY EXCLUDES SCOPES_ADMIN.
ALL_OPERATIONAL_SCOPES: Set[str] = set()
for section_scopes in SCOPE_SECTIONS.values():
    ALL_OPERATIONAL_SCOPES.update(section_scopes.keys())

def get_scope_label(scope: str) -> str:
    """Returns human-readable label for a given scope."""
    for s_dict in list(SCOPE_SECTIONS.values()) + [SCOPES_ADMIN]:
        if scope in s_dict:
            return s_dict[scope]
    return scope

def is_admin_scope(scope: str) -> bool:
    """Checks whether a scope is reserved strictly for Owner / Extra Owner."""
    return scope in SCOPES_ADMIN
