"""
Shizu Security - Zero-Trust Whitelist & Anti-Nuke Commands
Features interactive multi-select section authorization, Supreme grants,
optional target & expiry modals, role whitelisting, and snapshot recovery.
"""

import discord
from discord.ext import commands
from typing import Optional, Literal, Union, List, Dict
import json
import datetime
import re

from config import config
from core.checks import is_guild_owner_or_extra, is_bot_owner
from core.scopes import (
    SCOPE_SECTIONS,
    ALL_OPERATIONAL_SCOPES,
    get_scope_label,
    is_admin_scope
)
from core.enforcement import generate_incident_id

def parse_duration_string(dur_str: str) -> Optional[datetime.datetime]:
    """Parses duration string like '24h', '7d', '30d' into an UTC expiration datetime."""
    if not dur_str or not dur_str.strip():
        return None
    dur_str = dur_str.strip().lower()
    match = re.match(r"^(\d+)([mhd])$", dur_str)
    if not match:
        return None
    val, unit = int(match.group(1)), match.group(2)
    now = datetime.datetime.utcnow()
    if unit == "m":
        return now + datetime.timedelta(minutes=val)
    elif unit == "h":
        return now + datetime.timedelta(hours=val)
    elif unit == "d":
        return now + datetime.timedelta(days=val)
    return None

class TargetExpiryModal(discord.ui.Modal, title="Configure Target & Expiration"):
    target_input = discord.ui.TextInput(
        label="Target ID (Optional)",
        placeholder="Channel or Role ID (Leave empty for Global)",
        required=False,
        max_length=22
    )
    expiry_input = discord.ui.TextInput(
        label="Expiration (Optional)",
        placeholder="e.g. 24h, 7d, 30d (Leave empty for Permanent)",
        required=False,
        max_length=10
    )

    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view

    async def on_submit(self, interaction: discord.Interaction):
        target_val = self.target_input.value.strip()
        expiry_val = self.expiry_input.value.strip()

        t_id = None
        if target_val:
            try:
                t_id = int(target_val)
            except ValueError:
                return await interaction.response.send_message("❌ Invalid Target ID! Must be a numeric snowflake ID.", ephemeral=True)

        exp_dt = None
        if expiry_val:
            exp_dt = parse_duration_string(expiry_val)
            if not exp_dt:
                return await interaction.response.send_message("❌ Invalid format! Use `24h`, `7d`, or `30d`.", ephemeral=True)

        self.parent_view.target_id = t_id
        self.parent_view.expires_at = exp_dt.isoformat() if exp_dt else None
        self.parent_view.expiry_raw = expiry_val or "Permanent"

        await interaction.response.send_message(
            f"{config.ANIM_SUCCESS} Applied configuration: Target: `{t_id or 'Global'}` | Expiration: `{self.parent_view.expiry_raw}`",
            ephemeral=True
        )
        await self.parent_view.update_message()

class WhitelistAddView(discord.ui.View):
    def __init__(self, bot, author: discord.Member, target_entity: Union[discord.Member, discord.Role]):
        super().__init__(timeout=180)
        self.bot = bot
        self.author = author
        self.target_entity = target_entity
        self.is_role = isinstance(target_entity, discord.Role)
        self.selected_sections: List[str] = []
        self.is_supreme: bool = False
        self.target_id: Optional[int] = None
        self.expires_at: Optional[str] = None
        self.expiry_raw: str = "Permanent"
        self.message: Optional[discord.Message] = None

        # Build Section Multi-Select
        options = []
        for sec_name in SCOPE_SECTIONS.keys():
            options.append(discord.SelectOption(
                label=sec_name,
                value=sec_name,
                description=f"Grant all scopes in {sec_name}"
            ))

        self.section_select = discord.ui.Select(
            placeholder="Select authorization sections to grant...",
            min_values=1,
            max_values=len(options),
            options=options,
            row=0
        )
        self.section_select.callback = self.section_select_callback
        self.add_item(self.section_select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ This whitelist configuration panel is not for you.", ephemeral=True)
            return False
        return True

    async def section_select_callback(self, interaction: discord.Interaction):
        self.selected_sections = self.section_select.values
        self.is_supreme = False
        await interaction.response.defer()
        await self.update_message()

    @discord.ui.button(label="Supreme", style=discord.ButtonStyle.danger, emoji="👑", row=1)
    async def supreme_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.is_supreme = True
        self.selected_sections = list(SCOPE_SECTIONS.keys())
        await interaction.response.defer()
        await self.update_message()

    @discord.ui.button(label="Target & Expiry", style=discord.ButtonStyle.secondary, emoji="⚙️", row=1)
    async def target_expiry_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TargetExpiryModal(self))

    @discord.ui.button(label="Confirm Grant", style=discord.ButtonStyle.success, emoji="✅", row=1)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.selected_sections and not self.is_supreme:
            return await interaction.response.send_message("❌ Please select at least one section or click **Supreme**.", ephemeral=True)

        # Collect scopes
        granted_scopes = []
        if self.is_supreme:
            granted_scopes = list(ALL_OPERATIONAL_SCOPES)
        else:
            for sec in self.selected_sections:
                if sec in SCOPE_SECTIONS:
                    granted_scopes.extend(SCOPE_SECTIONS[sec].keys())

        # Save to database
        entity_type = "role" if self.is_role else "user"
        await self.bot.db.add_whitelist_entity(
            guild_id=interaction.guild_id,
            entity_id=self.target_entity.id,
            entity_type=entity_type,
            scopes=granted_scopes,
            created_by=self.author.id,
            target_id=self.target_id,
            expires_at=self.expires_at,
            is_supreme=self.is_supreme
        )

        # Log to security audit trail
        incident_id = generate_incident_id()
        await self.bot.db.log_security_audit(
            guild_id=interaction.guild_id,
            actor_id=self.author.id,
            action_type="WHITELIST_GRANT",
            scope_required="whitelist.manage",
            target_id=self.target_entity.id,
            outcome="ALLOWED",
            incident_id=incident_id,
            details=f"Granted {len(granted_scopes)} scopes to {entity_type} {self.target_entity.name} (Supreme: {self.is_supreme}, Expiry: {self.expiry_raw})"
        )

        embed = discord.Embed(
            title=f"{config.ANIM_SUCCESS} Whitelist Authorization Confirmed",
            description=(
                f"Successfully whitelisted **{self.target_entity.mention}** (`{self.target_entity.id}`).\n\n"
                f"• **Entity Type:** `{entity_type.upper()}`\n"
                f"• **Supreme Status:** {'`YES (All Actions)`' if self.is_supreme else '`NO (Granular Sections)`'}\n"
                f"• **Target Binding:** `{self.target_id or 'Global (All Targets)'}`\n"
                f"• **Expiration:** `{self.expiry_raw}`\n"
                f"• **Total Scopes Granted:** `{len(granted_scopes)}`\n"
                f"• **Audit Ticket:** `{incident_id}`"
            ),
            color=config.COLOR_DARK
        )
        if self.is_role:
            embed.set_footer(text="⚠️ Note: Any member below Extra Owner who assigns this whitelisted role triggers an immediate breach.")

        self.clear_items()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.gray, emoji="❌", row=1)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.clear_items()
        await interaction.response.edit_message(
            content=f"{config.ANIM_WARN} Whitelist configuration cancelled.",
            embed=None,
            view=self
        )

    def generate_embed(self) -> discord.Embed:
        entity_name = self.target_entity.mention
        status_mode = "**Supreme (All Operational Scopes)**" if self.is_supreme else (
            f"Sections: **{', '.join(self.selected_sections)}**" if self.selected_sections else "*None selected yet*"
        )

        embed = discord.Embed(
            title=f"{config.ANIM_SHIELD} Zero-Trust Whitelist Configuration",
            description=(
                f"Configuring additive authorization scopes for {entity_name} (`{self.target_entity.id}`).\n\n"
                f"• **Grant Mode:** {status_mode}\n"
                f"• **Target Binding:** `{self.target_id or 'Global (All Channels/Roles)'}`\n"
                f"• **Expiration:** `{self.expiry_raw}`"
            ),
            color=config.COLOR_DARK
        )
        embed.add_field(
            name="Available Sections",
            value="• " + "\n• ".join([f"**{k}:** {len(v)} scopes" for k, v in SCOPE_SECTIONS.items()]),
            inline=False
        )
        embed.set_footer(text="Select sections above or tap Supreme • Confirm to commit")
        return embed

    async def update_message(self):
        if self.message:
            await self.message.edit(embed=self.generate_embed(), view=self)

class AntiNukeCommands(commands.Cog, name="AntiNuke"):
    """Commands for managing Shizu Anti-Nuke, Zero-Trust Whitelist, Extra Owners, and Snapshots."""
    def __init__(self, bot):
        self.bot = bot

    # --- Anti-Nuke Control Group ---
    @commands.group(name="antinuke", aliases=["anti"], invoke_without_command=True)
    @commands.guild_only()
    @is_guild_owner_or_extra()
    async def antinuke(self, ctx):
        """View Anti-Nuke status dashboard."""
        prefix = ctx.prefix
        cfg = await self.bot.db.get_guild_config(ctx.guild.id)
        status_str = f"{config.ANIM_SUCCESS} **Active**" if cfg.get("antinuke_enabled") else f"{config.ANIM_WARN} **Disabled**"
        punishment = (cfg.get("antinuke_punishment") or "ban").upper()

        embed = discord.Embed(
            title=f"{config.ANIM_SHIELD} Shizu Zero-Trust Defense Dashboard",
            description=f"Real-Time Kernel: {status_str} | Breach Countermeasure: **{punishment}**",
            color=config.COLOR_DARK
        )
        embed.add_field(
            name="Defense Modules",
            value=(
                f"`{prefix}antinuke enable` — Arms real-time zero-trust defense\n"
                f"`{prefix}antinuke disable` — Disarms real-time defense\n"
                f"`{prefix}antinuke punishment <ban|kick|strip>` — Configure penalty\n"
                f"`{prefix}antinuke status` — Detailed security diagnostic embed"
            ),
            inline=False
        )
        embed.add_field(
            name="Zero-Trust Whitelist & Scopes",
            value=(
                f"`{prefix}whitelist add <@user|@role>` — Multi-select granular authorization\n"
                f"`{prefix}whitelist remove <@user|@role>` — Revoke all privileges\n"
                f"`{prefix}whitelist check <@user|@role>` — Inspect active scopes & expiration\n"
                f"`{prefix}whitelist list` — Display all whitelisted entities"
            ),
            inline=False
        )
        embed.add_field(
            name="Self-Healing & Disaster Recovery",
            value=(
                f"`{prefix}backup` — Capture layout snapshot into SQLite JSON\n"
                f"`{prefix}restore channels` — Reconstruct deleted channels from snapshot\n"
                f"`{prefix}restore roles` — Reconstruct deleted roles from snapshot\n"
                f"`{prefix}lockdown` / `{prefix}unlockdown` — Server-wide emergency lock"
            ),
            inline=False
        )
        embed.set_footer(text=f"Shizu Security v{config.VERSION} • Default Deny Architecture", icon_url=ctx.author.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()
        await ctx.reply(embed=embed, mention_author=False)

    @antinuke.command(name="enable", aliases=["on", "arm"])
    @commands.guild_only()
    @is_guild_owner_or_extra()
    async def antinuke_enable(self, ctx):
        """Enables the Anti-Nuke defense kernel."""
        cfg = await self.bot.db.get_guild_config(ctx.guild.id)
        if cfg.get("antinuke_enabled"):
            return await ctx.reply_warning("Anti-Nuke protection is already active on this server.")

        missing = []
        if not ctx.guild.me.guild_permissions.administrator:
            missing.append("Administrator")
        if not ctx.guild.me.guild_permissions.manage_roles:
            missing.append("Manage Roles")
        if not ctx.guild.me.guild_permissions.manage_channels:
            missing.append("Manage Channels")
        if not ctx.guild.me.guild_permissions.ban_members:
            missing.append("Ban Members")

        if missing:
            return await ctx.reply_error(
                f"Missing permissions to activate Anti-Nuke: **{', '.join(missing)}**.\n"
                "Please grant the bot **Administrator** and position its role at the top of the hierarchy."
            )

        antinuke_cog = self.bot.get_cog("AntiNukeEvents")
        if antinuke_cog and hasattr(antinuke_cog, "snapshot_guild"):
            await antinuke_cog.snapshot_guild(ctx.guild)

        await self.bot.db.update_guild_config(ctx.guild.id, antinuke_enabled=True)
        await ctx.reply_success(
            f"**Shizu Zero-Trust Defense is now ARMED!**\n"
            f"• Default Deny: Administrative permissions alone do not grant destructive actions.\n"
            f"• Nuked channels and roles will self-heal immediately with exact permissions.\n"
            f"• Fixed mass-action burst limit: **{config.MAX_BURST_ACTIONS} actions in {config.BURST_WINDOW}s**."
        )

    @antinuke.command(name="disable", aliases=["off", "disarm"])
    @commands.guild_only()
    @is_guild_owner_or_extra()
    async def antinuke_disable(self, ctx):
        """Disarms Anti-Nuke countermeasures."""
        await self.bot.db.update_guild_config(ctx.guild.id, antinuke_enabled=False)
        await ctx.reply_warning("Shizu Anti-Nuke defense has been **DISARMED**. The server is now exposed to unmonitored actions.")

    @antinuke.command(name="punishment")
    @commands.guild_only()
    @is_guild_owner_or_extra()
    async def antinuke_punishment(self, ctx, action: Literal["ban", "kick", "strip"]):
        """Configures the default breach countermeasure."""
        await self.bot.db.update_guild_config(ctx.guild.id, antinuke_punishment=action.lower())
        await ctx.reply_success(f"Breach punishment updated to **{action.upper()}**.")

    @antinuke.command(name="status")
    @commands.guild_only()
    @is_guild_owner_or_extra()
    async def antinuke_status(self, ctx):
        """Displays diagnostic security embed."""
        cfg = await self.bot.db.get_guild_config(ctx.guild.id)
        whitelisted = await self.bot.db.get_all_whitelist_entities(ctx.guild.id)
        extra_owners = await self.bot.db.get_extra_owners(ctx.guild.id)

        embed = discord.Embed(
            title=f"{config.ANIM_SHIELD} Shizu Zero-Trust Security Status",
            color=config.COLOR_DARK
        )
        embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else ctx.author.display_avatar.url)
        embed.add_field(name="Kernel State", value=f"{config.ANIM_SUCCESS} ARMED" if cfg.get("antinuke_enabled") else f"{config.ANIM_WARN} DISARMED", inline=True)
        embed.add_field(name="Breach Action", value=f"`{(cfg.get('antinuke_punishment') or 'ban').upper()}`", inline=True)
        embed.add_field(name="Burst Limit", value=f"`{config.MAX_BURST_ACTIONS} actions / {config.BURST_WINDOW}s`", inline=True)
        embed.add_field(name="Whitelisted Entities", value=f"`{len(whitelisted)}` registered", inline=True)
        embed.add_field(name="Extra Owners", value=f"`{len(extra_owners)}` designated", inline=True)
        embed.add_field(name="Audit Log Channel", value=f"<#{cfg.get('log_antinuke')}>" if cfg.get("log_antinuke") else "*Not configured*", inline=True)
        embed.set_footer(text=f"Shizu Security v{config.VERSION}")
        embed.timestamp = discord.utils.utcnow()
        await ctx.reply(embed=embed, mention_author=False)

    # --- Anti-Bot Control Group ---
    @commands.group(name="antibot", invoke_without_command=True)
    @commands.guild_only()
    @is_guild_owner_or_extra()
    async def antibot(self, ctx):
        """Displays the Anti-Bot configuration and active rules."""
        prefix = ctx.prefix
        is_active = await self.bot.db.get_antibot_status(ctx.guild.id)
        status_str = f"{config.ANIM_SUCCESS} **Armed & Active**" if is_active else f"{config.ANIM_WARN} **Disabled**"

        embed = discord.Embed(
            title=f"{config.ANIM_SHIELD} Shizu Anti-Bot Defense",
            description=f"Current Status: {status_str}",
            color=config.COLOR_DARK
        )
        embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else ctx.author.display_avatar.url)
        embed.add_field(
            name="Enforcement Rules",
            value=(
                "• **Unauthorized Bot:** Any bot joining is **banned directly**; inviter is banned.\n"
                "• **Server Owner Addition:** If Anti-Bot is ON, bot is **kicked** (Owner must `?antibot off` first).\n"
                "• **Whitelisted Addition:** Added bot is **banned**; if inviter is below Shizu, they are **timed out & roles stripped**.\n"
                "• **Hierarchy Defense:** If offender is above Shizu, damage is reverted and **Emergency DM** is sent to Owner."
            ),
            inline=False
        )
        embed.add_field(
            name="Commands",
            value=(
                f"`{prefix}antibot on` / `{prefix}antibot enable` — Arms Anti-Bot protection\n"
                f"`{prefix}antibot off` / `{prefix}antibot disable` — Disarms Anti-Bot protection\n"
                f"`{prefix}antibot status` — Inspect live status"
            ),
            inline=False
        )
        embed.set_footer(text=f"Shizu Security v{config.VERSION} • Automated Protection", icon_url=ctx.author.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()
        await ctx.reply(embed=embed, mention_author=False)

    @antibot.command(name="on", aliases=["enable", "arm"])
    @commands.guild_only()
    @is_guild_owner_or_extra()
    async def antibot_on(self, ctx):
        """Enables Anti-Bot protection."""
        await self.bot.db.set_antibot_status(ctx.guild.id, True)
        await ctx.reply_success(
            f"**Anti-Bot Protection Armed!**\nAny unauthorized bots joining **{ctx.guild.name}** will be banned immediately.\n*(Note: If the Server Owner wishes to add a bot, run `{ctx.prefix}antibot off` first)*"
        )

    @antibot.command(name="off", aliases=["disable", "disarm"])
    @commands.guild_only()
    @is_guild_owner_or_extra()
    async def antibot_off(self, ctx):
        """Disables Anti-Bot protection."""
        await self.bot.db.set_antibot_status(ctx.guild.id, False)
        await ctx.reply_warning(
            f"**Anti-Bot Protection Disarmed.**\nBots can now be added to **{ctx.guild.name}**. Remember to run `{ctx.prefix}antibot on` once your bot is added."
        )

    @antibot.command(name="status")
    @commands.guild_only()
    async def antibot_status(self, ctx):
        """Checks live Anti-Bot status."""
        is_active = await self.bot.db.get_antibot_status(ctx.guild.id)
        if is_active:
            await ctx.reply_success(f"Anti-Bot is currently **ACTIVE** on **{ctx.guild.name}**.")
        else:
            await ctx.reply_warning(f"Anti-Bot is currently **DISABLED** on **{ctx.guild.name}**.")

    # --- Whitelist Group ---
    @commands.group(name="whitelist", aliases=["wl"], invoke_without_command=True)
    @commands.guild_only()
    @is_guild_owner_or_extra()
    async def whitelist_cmd(self, ctx):
        """Manage Zero-Trust whitelisted entities and scopes."""
        prefix = ctx.prefix
        embed = discord.Embed(
            title=f"{config.ANIM_SHIELD} Zero-Trust Whitelist Management",
            description=(
                f"`{prefix}whitelist add <@user|@role>` — Opens interactive scope authorization panel\n"
                f"`{prefix}whitelist remove <@user|@role>` — Revokes all scopes from entity\n"
                f"`{prefix}whitelist check <@user|@role>` — Inspect active scopes & expiration\n"
                f"`{prefix}whitelist list` — View all whitelisted users and roles\n"
                f"`{prefix}whitelist reset` — Wipe all whitelisted entities (Owner only)"
            ),
            color=config.COLOR_DARK
        )
        await ctx.reply(embed=embed, mention_author=False)

    @whitelist_cmd.command(name="add")
    @commands.guild_only()
    @is_guild_owner_or_extra()
    async def whitelist_add(self, ctx, entity: Union[discord.Member, discord.Role]):
        """Launches interactive scope configuration panel for a member or role."""
        if isinstance(entity, discord.Member):
            if entity.bot:
                return await ctx.reply_error("External bots cannot be whitelisted.")
            if entity.id == ctx.guild.owner_id:
                return await ctx.reply_warning("The Server Owner already holds unconditional root authority.")

        view = WhitelistAddView(self.bot, ctx.author, entity)
        embed = view.generate_embed()
        msg = await ctx.reply(embed=embed, view=view, mention_author=False)
        view.message = msg

    @whitelist_cmd.command(name="remove")
    @commands.guild_only()
    @is_guild_owner_or_extra()
    async def whitelist_remove(self, ctx, entity: Union[discord.Member, discord.Role]):
        """Completely removes a member or role from the whitelist."""
        removed = await self.bot.db.remove_whitelist_entity(ctx.guild.id, entity.id)
        if not removed:
            return await ctx.reply_error(f"{entity.mention} is not currently in the whitelist.")

        await ctx.reply_success(f"{entity.mention} has been **removed** from the whitelist and all granted scopes revoked.")

    @whitelist_cmd.command(name="check")
    @commands.guild_only()
    @is_guild_owner_or_extra()
    async def whitelist_check(self, ctx, entity: Union[discord.Member, discord.Role]):
        """Inspects an entity's active scopes, targets, and expiration countdown."""
        ent = await self.bot.db.get_whitelist_entity(ctx.guild.id, entity.id)
        scopes = await self.bot.db.get_entity_scopes(ctx.guild.id, entity.id)

        if not ent and not scopes:
            return await ctx.reply_error(f"{entity.mention} is **NOT whitelisted** (Zero Trust / Restricted).")

        is_legacy = ent.get("is_legacy_supreme") if ent else False

        desc = f"**Entity:** {entity.mention} (`{entity.id}`) | **Type:** `{'ROLE' if isinstance(entity, discord.Role) else 'USER'}`\n"
        if is_legacy:
            desc += f"\n⚠️ **LEGACY-SUPREME NOTICE:** Migrated from v2.2. Expires in 30 days — Review required.\n"

        embed = discord.Embed(
            title=f"{config.ANIM_SHIELD} Whitelist Inspection Report",
            description=desc,
            color=config.COLOR_DARK
        )

        now_str = datetime.datetime.utcnow().isoformat()
        active_scopes = []
        for s in scopes:
            exp = s.get("expires_at")
            if exp and exp < now_str:
                continue
            t_id = s.get("target_id")
            target_str = f" [Target: `{t_id}`]" if t_id and t_id != 0 else ""
            exp_str = f" (Expires: {exp[:10]})" if exp else " (Permanent)"
            active_scopes.append(f"• `{s['scope']}`{target_str}{exp_str}")

        if not active_scopes:
            embed.add_field(name="Active Scopes", value="*All scopes have expired.*", inline=False)
        else:
            # Group or chunk
            chunk = active_scopes[:20]
            embed.add_field(name=f"Active Scopes ({len(active_scopes)})", value="\n".join(chunk), inline=False)
            if len(active_scopes) > 20:
                embed.set_footer(text=f"Showing top 20 of {len(active_scopes)} scopes.")

        await ctx.reply(embed=embed, mention_author=False)

    @whitelist_cmd.command(name="list")
    @commands.guild_only()
    @is_guild_owner_or_extra()
    async def whitelist_list(self, ctx):
        """Displays all whitelisted users and roles."""
        entities = await self.bot.db.get_all_whitelist_entities(ctx.guild.id)
        if not entities:
            return await ctx.reply_warning("There are currently no whitelisted entities on this server.")

        users_list = []
        roles_list = []

        for e in entities:
            e_id = e["entity_id"]
            e_type = e["entity_type"]
            scopes = await self.bot.db.get_entity_scopes(ctx.guild.id, e_id)
            legacy_flag = " *(Legacy-Supreme)*" if e.get("is_legacy_supreme") else ""

            if e_type == "role":
                role = ctx.guild.get_role(e_id)
                tag = role.mention if role else f"Deleted Role (`{e_id}`)"
                roles_list.append(f"• {tag} — `{len(scopes)} scopes`{legacy_flag}")
            else:
                member = ctx.guild.get_member(e_id)
                tag = member.mention if member else f"User (`{e_id}`)"
                users_list.append(f"• {tag} — `{len(scopes)} scopes`{legacy_flag}")

        embed = discord.Embed(
            title=f"{config.EMOJI_LIST} Whitelisted Entities ({len(entities)})",
            color=config.COLOR_DARK
        )
        if users_list:
            embed.add_field(name=f"Whitelisted Members ({len(users_list)})", value="\n".join(users_list[:15]), inline=False)
        if roles_list:
            embed.add_field(name=f"Whitelisted Roles ({len(roles_list)})", value="\n".join(roles_list[:15]), inline=False)

        await ctx.reply(embed=embed, mention_author=False)

    @whitelist_cmd.command(name="reset")
    @commands.guild_only()
    async def whitelist_reset(self, ctx):
        """Wipes all whitelisted users and roles (Server Owner only)."""
        if ctx.author.id != ctx.guild.owner_id and ctx.author.id not in config.OWNER_IDS:
            return await ctx.reply_error("Only the Server Owner can execute a full whitelist reset.")

        await self.bot.db.reset_whitelist(ctx.guild.id)
        await ctx.reply_success("All server whitelist entities and scopes have been completely wiped.")

    # --- Extra Owner Group ---
    @commands.group(name="extraowner", aliases=["extraown"], invoke_without_command=True)
    @commands.guild_only()
    async def extraowner_cmd(self, ctx):
        """Manage designated Extra Owners."""
        prefix = ctx.prefix
        embed = discord.Embed(
            title=f"{config.ANIM_SHIELD} Extra Owner Management",
            description=(
                f"`{prefix}extraowner add <@user>` — Designate a co-owner\n"
                f"`{prefix}extraowner remove <@user>` — Revoke co-owner privileges\n"
                f"`{prefix}extraowner list` — View all designated extra owners"
            ),
            color=config.COLOR_DARK
        )
        await ctx.reply(embed=embed, mention_author=False)

    @extraowner_cmd.command(name="add")
    @commands.guild_only()
    async def extraowner_add(self, ctx, member: discord.Member):
        """Designates an Extra Owner (Server Owner only)."""
        if ctx.author.id != ctx.guild.owner_id and ctx.author.id not in config.OWNER_IDS:
            return await ctx.reply_error("Only the Server Owner can designate Extra Owners.")
        if member.bot:
            return await ctx.reply_error("Bots cannot be designated as Extra Owners.")

        success = await self.bot.db.add_extra_owner(ctx.guild.id, member.id)
        if not success:
            return await ctx.reply_warning(f"{member.mention} is already an Extra Owner.")

        await ctx.reply_success(f"{member.mention} has been designated as an **Extra Owner** with administrative defense control.")

    @extraowner_cmd.command(name="remove")
    @commands.guild_only()
    async def extraowner_remove(self, ctx, member: discord.Member):
        """Revokes Extra Owner designation."""
        if ctx.author.id != ctx.guild.owner_id and ctx.author.id not in config.OWNER_IDS:
            return await ctx.reply_error("Only the Server Owner can revoke Extra Owners.")

        removed = await self.bot.db.remove_extra_owner(ctx.guild.id, member.id)
        if not removed:
            return await ctx.reply_error(f"{member.mention} is not an Extra Owner.")

        await ctx.reply_success(f"{member.mention} has been **removed** from Extra Owners.")

    @extraowner_cmd.command(name="list")
    @commands.guild_only()
    @is_guild_owner_or_extra()
    async def extraowner_list(self, ctx):
        """Lists all designated Extra Owners."""
        owner_ids = await self.bot.db.get_extra_owners(ctx.guild.id)
        if not owner_ids:
            return await ctx.reply_warning("There are currently no Extra Owners designated on this server.")

        entries = []
        for oid in owner_ids:
            m = ctx.guild.get_member(oid)
            entries.append(f"• {m.mention if m else f'User ID `{oid}`'}")

        embed = discord.Embed(
            title=f"{config.EMOJI_CROWN} Extra Owners ({len(owner_ids)})",
            description="\n".join(entries),
            color=config.COLOR_DARK
        )
        await ctx.reply(embed=embed, mention_author=False)

    # --- Emergency Lockdown Commands ---
    @commands.command(name="lockdown", aliases=["serverlock"])
    @commands.guild_only()
    @is_guild_owner_or_extra()
    async def lockdown(self, ctx):
        """Freezes all public text channels instantly."""
        msg = await ctx.reply_loading("Engaging emergency server-wide lockdown...")
        locked_cids = []
        for ch in ctx.guild.text_channels:
            try:
                ow = ch.overwrites_for(ctx.guild.default_role)
                if ow.send_messages is not False:
                    ow.send_messages = False
                    await ch.set_permissions(ctx.guild.default_role, overwrite=ow, reason=f"Emergency Lockdown engaged by {ctx.author}")
                    locked_cids.append(ch.id)
            except Exception:
                continue

        await self.bot.db.save_emergency_channels(ctx.guild.id, locked_cids)
        await self.bot.db.update_guild_config(ctx.guild.id, emergency_locked=True)

        embed = discord.Embed(
            title=f"{config.ANIM_ALERT} Server Lockdown Active",
            description=f"Emergency lockdown engaged. **{len(locked_cids)}** public channels frozen.\nUse `{ctx.prefix}unlockdown` to restore permissions.",
            color=config.COLOR_DARK
        )
        await msg.edit(content=None, embed=embed)

    @commands.command(name="unlockdown", aliases=["serverunlock"])
    @commands.guild_only()
    @is_guild_owner_or_extra()
    async def unlockdown(self, ctx):
        """Restores public speaking permissions after lockdown."""
        msg = await ctx.reply_loading("Restoring normal server permissions...")
        cids = await self.bot.db.get_emergency_channels(ctx.guild.id)
        restored_count = 0

        target_channels = [ctx.guild.get_channel(cid) for cid in cids] if cids else ctx.guild.text_channels

        for ch in target_channels:
            if not ch:
                continue
            try:
                ow = ch.overwrites_for(ctx.guild.default_role)
                ow.send_messages = None
                await ch.set_permissions(ctx.guild.default_role, overwrite=ow, reason=f"Lockdown lifted by {ctx.author}")
                restored_count += 1
            except Exception:
                continue

        await self.bot.db.clear_emergency_channels(ctx.guild.id)
        await self.bot.db.update_guild_config(ctx.guild.id, emergency_locked=False)

        embed = discord.Embed(
            title=f"{config.ANIM_SUCCESS} Lockdown Lifted",
            description=f"Server restored to normal operations. **{restored_count}** channel(s) unfrozen.",
            color=config.COLOR_DARK
        )
        await msg.edit(content=None, embed=embed)

    # --- Disaster Recovery Snapshots ---
    @commands.command(name="backup", aliases=["snapshot"])
    @commands.guild_only()
    @is_guild_owner_or_extra()
    async def backup(self, ctx):
        """Captures complete server snapshot into SQLite database."""
        msg = await ctx.reply_loading("Capturing full server snapshot...")
        antinuke_cog = self.bot.get_cog("AntiNukeEvents")
        if antinuke_cog and hasattr(antinuke_cog, "snapshot_guild"):
            await antinuke_cog.snapshot_guild(ctx.guild)

        channels_count = len(ctx.guild.channels)
        roles_count = len([r for r in ctx.guild.roles if not r.is_default()])

        embed = discord.Embed(
            title=f"{config.ANIM_SUCCESS} Disaster Recovery Snapshot Saved",
            description=(
                f"Serialized server structure into SQLite JSON database.\n\n"
                f"• Channels & Overwrites: **{channels_count}**\n"
                f"• Roles, Colors & Perms: **{roles_count}**\n"
                f"• Settings & Emojis: **Saved**\n\n"
                f"Use `{ctx.prefix}restore channels` or `{ctx.prefix}restore roles` if damage occurs."
            ),
            color=config.COLOR_DARK
        )
        await msg.edit(content=None, embed=embed)

    @commands.group(name="restore", invoke_without_command=True)
    @commands.guild_only()
    @is_guild_owner_or_extra()
    async def restore(self, ctx):
        """Disaster recovery restore commands."""
        prefix = ctx.prefix
        embed = discord.Embed(
            title=f"{config.ANIM_SHIELD} Disaster Recovery Restoration",
            description=(
                f"`{prefix}restore channels` — Recreates missing channels with exact overwrites\n"
                f"`{prefix}restore roles` — Recreates missing roles with exact permissions"
            ),
            color=config.COLOR_DARK
        )
        await ctx.reply(embed=embed, mention_author=False)

    @restore.command(name="channels")
    @commands.guild_only()
    @is_guild_owner_or_extra()
    @commands.has_permissions(manage_channels=True)
    async def restore_channels(self, ctx):
        """Reconstructs all missing channels from snapshot."""
        msg = await ctx.reply_loading("Analyzing snapshot and reconstructing missing channels...")
        snapshots = await self.bot.db.get_all_channel_snapshots(ctx.guild.id)
        if not snapshots:
            return await msg.edit(content=None, embed=discord.Embed(
                description=f"{config.ANIM_WARN} No channel snapshot found. Run `{ctx.prefix}backup` first.",
                color=0xFF0000
            ))

        existing_cids = {c.id for c in ctx.guild.channels}
        missing = [s for s in snapshots if s["channel_id"] not in existing_cids]

        if not missing:
            return await msg.edit(content=None, embed=discord.Embed(
                description=f"{config.ANIM_SUCCESS} All **{len(snapshots)}** channels are present. No restoration required.",
                color=config.COLOR_DARK
            ))

        restored_count = 0
        categories_map = {}

        # 1. Restore categories first
        for s in missing:
            if s.get("channel_type") == "category":
                try:
                    cat = await ctx.guild.create_category(
                        name=s["name"],
                        position=s.get("position", 0),
                        reason=f"Shizu Restoration requested by {ctx.author}"
                    )
                    categories_map[s["channel_id"]] = cat
                    restored_count += 1
                except Exception:
                    continue

        # 2. Restore text & voice channels
        for s in missing:
            if s.get("channel_type") != "category":
                try:
                    category = categories_map.get(s.get("category_id")) or ctx.guild.get_channel(s.get("category_id"))
                    overwrites = {}
                    if s.get("overwrites_json"):
                        try:
                            raw_ow = json.loads(s["overwrites_json"])
                            for target_key, vals in raw_ow.items():
                                if target_key.startswith("role_"):
                                    r_id = int(target_key.replace("role_", ""))
                                    role = ctx.guild.get_role(r_id)
                                    if role:
                                        overwrites[role] = discord.PermissionOverwrite.from_pair(
                                            discord.Permissions(vals["allow"]), discord.Permissions(vals["deny"])
                                        )
                        except Exception:
                            pass

                    if s.get("channel_type") == "voice":
                        await ctx.guild.create_voice_channel(
                            name=s["name"],
                            category=category,
                            overwrites=overwrites,
                            position=s.get("position", 0),
                            reason=f"Shizu Restoration requested by {ctx.author}"
                        )
                    else:
                        await ctx.guild.create_text_channel(
                            name=s["name"],
                            category=category,
                            topic=s.get("topic"),
                            nsfw=bool(s.get("nsfw", False)),
                            slowmode_delay=s.get("slowmode_delay", 0),
                            overwrites=overwrites,
                            position=s.get("position", 0),
                            reason=f"Shizu Restoration requested by {ctx.author}"
                        )
                    restored_count += 1
                except Exception:
                    continue

        embed = discord.Embed(
            description=f"{config.ANIM_SUCCESS} Successfully restored **{restored_count}** missing channel(s) with original permissions.",
            color=config.COLOR_DARK
        )
        await msg.edit(content=None, embed=embed)

    @restore.command(name="roles")
    @commands.guild_only()
    @is_guild_owner_or_extra()
    @commands.has_permissions(manage_roles=True)
    async def restore_roles(self, ctx):
        """Reconstructs all missing roles from snapshot."""
        msg = await ctx.reply_loading("Analyzing snapshot and reconstructing missing roles...")
        snapshots = await self.bot.db.get_all_role_snapshots(ctx.guild.id)
        if not snapshots:
            return await msg.edit(content=None, embed=discord.Embed(
                description=f"{config.ANIM_WARN} No role snapshot found. Run `{ctx.prefix}backup` first.",
                color=0xFF0000
            ))

        existing_rids = {r.id for r in ctx.guild.roles}
        missing = [s for s in snapshots if s["role_id"] not in existing_rids]

        if not missing:
            return await msg.edit(content=None, embed=discord.Embed(
                description=f"{config.ANIM_SUCCESS} All snapshotted roles are present. No restoration required.",
                color=config.COLOR_DARK
            ))

        restored_count = 0
        for s in missing:
            try:
                await ctx.guild.create_role(
                    name=s["name"],
                    permissions=discord.Permissions(s.get("permissions", 0)),
                    color=discord.Color(s.get("color", 0)),
                    hoist=bool(s.get("hoist", False)),
                    mentionable=bool(s.get("mentionable", False)),
                    reason=f"Shizu Role Restoration requested by {ctx.author}"
                )
                restored_count += 1
            except Exception:
                continue

        embed = discord.Embed(
            description=f"{config.ANIM_SUCCESS} Successfully restored **{restored_count}** missing role(s) with original colors and permissions.",
            color=config.COLOR_DARK
        )
        await msg.edit(content=None, embed=embed)

async def setup(bot):
    await bot.add_cog(AntiNukeCommands(bot))
