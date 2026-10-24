"""
Shizu Security - Clean & Professional Help UI
Directly modeled after professional security bot interfaces with simple English,
clean dual dropdown menus, automatic features modal/panel, and interactive navigation.
"""

import discord
from discord.ext import commands
from discord.ui import Select, View, Button
from typing import Optional, Dict, List

from config import config

# --- Command Categories & Simple English Help Directory ---
COMMAND_CATEGORIES = {
    "antinuke": {
        "title": "🛡️ ANTI NUKE COMMANDS",
        "desc": "Real-time automated defense against unauthorized server changes.",
        "commands": [
            ("antinuke enable", "Turns on real-time Anti-Nuke defense"),
            ("antinuke disable", "Turns off Anti-Nuke defense"),
            ("antinuke punishment <ban|kick|strip>", "Sets the penalty when an attack occurs"),
            ("antinuke status", "Shows your server's current Anti-Nuke settings")
        ]
    },
    "antibot": {
        "title": "🤖 ANTI BOT COMMANDS",
        "desc": "Blocks unauthorized bots from joining your server.",
        "commands": [
            ("antibot on", "Arms Anti-Bot defense (bans rogue bots)"),
            ("antibot off", "Disarms Anti-Bot defense (turn off before inviting bots)"),
            ("antibot status", "Shows if Anti-Bot is currently armed or disabled")
        ]
    },
    "automod": {
        "title": "🚨 AUTO MOD COMMANDS",
        "desc": "Automatic chat filtering for spam, links, invites, and bad words.",
        "commands": [
            ("automod enable", "Turns on AutoMod chat protection"),
            ("automod disable", "Turns off AutoMod chat protection"),
            ("automod status", "Shows enabled filters and settings"),
            ("badwords add <word>", "Adds a word to the chat blacklist"),
            ("badwords remove <word>", "Removes a word from the blacklist"),
            ("badwords list", "Lists all blacklisted words in your server"),
            ("badwords clear", "Clears all custom blacklisted words")
        ]
    },
    "whitelist": {
        "title": "👑 WHITELIST COMMANDS",
        "desc": "Manage trusted staff members and roles that can bypass security.",
        "commands": [
            ("whitelist add <@user|@role>", "Opens whitelist setup panel"),
            ("whitelist remove <@user|@role>", "Removes an entity from the whitelist"),
            ("whitelist check <@user|@role>", "Inspects active whitelist permissions"),
            ("whitelist list", "Displays all whitelisted users and roles"),
            ("whitelist reset", "Clears all whitelist entries")
        ]
    },
    "moderation": {
        "title": "❗ MODERATION COMMANDS",
        "desc": "Standard staff moderation tools to manage members.",
        "commands": [
            ("ban <@user> [reason]", "Permanently bans a member from the server"),
            ("unban <user_id> [reason]", "Unbans a previously banned user"),
            ("kick <@user> [reason]", "Kicks a member from the server"),
            ("timeout <@user> <duration> [reason]", "Mutes a user (e.g. 10m, 1h, 1d)"),
            ("untimeout <@user>", "Removes an active timeout from a user"),
            ("warn <@user> [reason]", "Issues a formal warning to a member"),
            ("warnings <@user>", "Views a member's warning history"),
            ("clearwarns <@user>", "Clears all warnings for a member"),
            ("purge <amount>", "Bulk deletes recent messages in channel"),
            ("lock [#channel]", "Locks a channel so members cannot send messages"),
            ("unlock [#channel]", "Unlocks a locked channel"),
            ("slowmode <seconds>", "Sets channel message slowmode delay"),
            ("setnick <@user> <nickname>", "Changes a member's server nickname")
        ]
    },
    "logging": {
        "title": "📋 LOGGING COMMANDS",
        "desc": "Binds your two dedicated log channels for security and moderation.",
        "commands": [
            ("setlog security #channel", "Sets your Shizu Security audit log channel"),
            ("setlog mod #channel", "Sets your Shizu Moderation action log channel")
        ]
    },
    "extraowner": {
        "title": "⚡ EXTRA OWNER COMMANDS",
        "desc": "Designate trusted co-owners who can configure security.",
        "commands": [
            ("extraowner add <@user>", "Grants Extra Owner status to a trusted user"),
            ("extraowner remove <@user>", "Revokes Extra Owner status"),
            ("extraowner list", "Lists all configured Extra Owners")
        ]
    },
    "utility": {
        "title": "⚙️ UTILITY & SETTINGS",
        "desc": "General server settings, diagnostics, and prefix configuration.",
        "commands": [
            ("setprefix <new_prefix>", "Changes the bot's command prefix"),
            ("security", "Displays the live server security dashboard"),
            ("ping", "Checks bot latency and Discord API response time"),
            ("stats", "Displays bot memory, uptime, and guild counts"),
            ("snipe", "Shows the most recently deleted message in channel")
        ]
    },
    "backup": {
        "title": "🛡️ BACKUP & DISASTER RECOVERY",
        "desc": "Capture snapshots of your server layout to restore if nuked.",
        "commands": [
            ("backup", "Saves a complete snapshot of all channels and roles"),
            ("restore channels", "Reconstructs all deleted channels from snapshot"),
            ("restore roles", "Reconstructs all deleted roles from snapshot")
        ]
    },
    "lockdown": {
        "title": "🔒 SERVER LOCKDOWN COMMANDS",
        "desc": "Emergency lockdown to freeze the entire server in case of a raid.",
        "commands": [
            ("lockdown", "Locks all server channels to stop incoming attacks"),
            ("unlockdown", "Restores channels back to normal permissions")
        ]
    }
}


class MainMenuSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Anti Nuke", emoji="🛡️", value="antinuke", description="Server destruction protection"),
            discord.SelectOption(label="Anti Bot", emoji="🤖", value="antibot", description="Block unauthorized bot additions"),
            discord.SelectOption(label="Auto Mod", emoji="🚨", value="automod", description="Anti-spam, links, invites & bad words"),
            discord.SelectOption(label="Whitelist", emoji="👑", value="whitelist", description="Manage trusted staff permissions"),
            discord.SelectOption(label="Moderation", emoji="❗", value="moderation", description="Ban, kick, timeout, warn & purge"),
            discord.SelectOption(label="Logging", emoji="📋", value="logging", description="Security and Mod log channel binding"),
            discord.SelectOption(label="Extra Owner", emoji="⚡", value="extraowner", description="Manage secondary server owners"),
        ]
        super().__init__(placeholder="Main Menu", min_values=1, max_values=1, options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        await self.view.show_category(interaction, self.values[0])


class OtherMenuSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Utility & Settings", emoji="⚙️", value="utility", description="Prefix, latency and server info"),
            discord.SelectOption(label="Backup & Restore", emoji="🛡️", value="backup", description="Save & restore channels and roles"),
            discord.SelectOption(label="Server Lockdown", emoji="🔒", value="lockdown", description="Emergency raid freeze and unfreeze"),
        ]
        super().__init__(placeholder="Other Menu", min_values=1, max_values=1, options=options, row=1)

    async def callback(self, interaction: discord.Interaction):
        await self.view.show_category(interaction, self.values[0])


class HelpView(View):
    def __init__(self, bot, ctx, prefix: str, an_active: bool):
        super().__init__(timeout=180)
        self.bot = bot
        self.ctx = ctx
        self.prefix = prefix
        self.an_active = an_active
        self.current_page = "home"

        # Add initial dropdowns
        self.add_item(MainMenuSelect())
        self.add_item(OtherMenuSelect())

        # Action Buttons
        self.btn_auto = Button(label="Show Automatic Features", style=discord.ButtonStyle.danger, row=2)
        self.btn_auto.callback = self.show_automatic_features
        self.add_item(self.btn_auto)

        invite_url = f"https://discord.com/oauth2/authorize?client_id={self.bot.user.id}&permissions=8&scope=bot%20applications.commands"
        self.add_item(Button(label="Invite Bot", url=invite_url, style=discord.ButtonStyle.link, row=2))
        self.add_item(Button(label="Support Server", url="https://discord.gg/shizu", style=discord.ButtonStyle.link, row=2))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This help menu belongs to someone else. Type `?help` to open your own!", ephemeral=True)
            return False
        return True

    def build_home_embed(self) -> discord.Embed:
        an_status = "🟢 Active" if self.an_active else "🔴 Disabled"
        embed = discord.Embed(
            title="SHIZU HELP MENU",
            color=config.COLOR_DARK
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.description = (
            f"**Prefix :** `{self.prefix}`\n"
            f"**Antinuke Status :** {an_status}\n"
            f"**Total Commands :** `36`\n\n"
            f"```\nhelp <command> for more info regarding that command!\nExample: help ban\n```\n"
            f"──────────────────────────────────────────────\n"
            f"**Main Menu**\n"
            f"🛡️ : Anti Nuke\n"
            f"🤖 : Anti Bot\n"
            f"🚨 : Auto Mod\n"
            f"👑 : Whitelist\n"
            f"❗ : Moderation\n"
            f"📋 : Logging\n"
            f"⚡ : Extra Owner\n\n"
            f"──────────────────────────────────────────────\n"
            f"**Others Menu**\n"
            f"⚙️ : Utility & Settings\n"
            f"🛡️ : Server Backup & Restore\n"
            f"🔒 : Server Lockdown\n\n"
            f"*Select a category from the dropdown below to view its commands.*"
        )
        embed.set_footer(
            text=f"Shizu Security v{config.VERSION} • Developers: {config.DEVELOPER_STRING}",
            icon_url=self.bot.user.display_avatar.url
        )
        embed.timestamp = discord.utils.utcnow()
        return embed

    async def show_home(self, interaction: discord.Interaction):
        self.current_page = "home"
        self.clear_items()
        self.add_item(MainMenuSelect())
        self.add_item(OtherMenuSelect())
        self.add_item(self.btn_auto)

        invite_url = f"https://discord.com/oauth2/authorize?client_id={self.bot.user.id}&permissions=8&scope=bot%20applications.commands"
        self.add_item(Button(label="Invite Bot", url=invite_url, style=discord.ButtonStyle.link, row=2))
        self.add_item(Button(label="Support Server", url="https://discord.gg/shizu", style=discord.ButtonStyle.link, row=2))

        await interaction.response.edit_message(embed=self.build_home_embed(), view=self)

    async def show_category(self, interaction: discord.Interaction, cat_key: str):
        self.current_page = cat_key
        cat = COMMAND_CATEGORIES.get(cat_key)
        if not cat:
            return

        embed = discord.Embed(
            title=cat["title"],
            description=f"{cat['desc']}\n\n**Prefix :** `{self.prefix}` | **Commands :** `{len(cat['commands'])}`\n──────────────────────────────────────────────\n",
            color=config.COLOR_DARK
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        cmd_lines = []
        for cmd_name, cmd_desc in cat["commands"]:
            cmd_lines.append(f"`{self.prefix}{cmd_name}`\n{cmd_desc}\n")

        embed.description += "\n".join(cmd_lines)
        embed.set_footer(text=f"Shizu Security v{config.VERSION} • Tap Home to return", icon_url=self.bot.user.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()

        # Update controls
        self.clear_items()
        self.add_item(MainMenuSelect())
        self.add_item(OtherMenuSelect())

        btn_home = Button(label="Main Menu", style=discord.ButtonStyle.secondary, emoji="🏠", row=2)
        btn_home.callback = self.show_home
        self.add_item(btn_home)
        self.add_item(self.btn_auto)

        await interaction.response.edit_message(embed=embed, view=self)

    async def show_automatic_features(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=f"{config.ANIM_SHIELD} Shizu Automatic 24/7 Server Protections",
            description=(
                "These features run **automatically in the background** to defend your server without needing manual commands:\n\n"
                "🛡️ **Anti-Channel Protection:**\n"
                "• Deletes rogue channels created by attackers.\n"
                "• Automatically re-creates deleted channels with exact permissions.\n\n"
                "🛡️ **Anti-Role Protection:**\n"
                "• Deletes unauthorized rogue roles.\n"
                "• Automatically re-creates deleted roles with exact permissions.\n"
                "• Automatically strips dangerous permissions (`Admin`, `Ban Members`, `Manage Guild`) if someone tries to escalate.\n\n"
                "🤖 **Anti-Bot Defense:**\n"
                "• Instantly kicks bots added by the Server Owner (reminds owner to turn off first).\n"
                "• Permanently bans unauthorized bots and bans unwhitelisted inviters.\n"
                "• If whitelisted staff adds a bot, bans the bot and times out the member.\n\n"
                "⚡ **Anti-Nuke Enforcement:**\n"
                "• Automatically unbans victims of mass rogue bans.\n"
                "• Deletes rogue webhooks immediately.\n"
                "• Restores server name and vanity URL if an attacker tampers with them.\n"
                "• Purges unauthorized `@everyone` and `@here` mass pings.\n\n"
                "👑 **Hierarchy & Owner Protection:**\n"
                "• If an attacker is higher than Shizu in hierarchy, Shizu **still reverts all damage** and immediately sends an **Emergency Alert DM** to the Server Owner!"
            ),
            color=config.COLOR_DARK
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text=f"Shizu Security v{config.VERSION} • Automated Protection")
        embed.timestamp = discord.utils.utcnow()

        self.clear_items()
        self.add_item(MainMenuSelect())
        self.add_item(OtherMenuSelect())

        btn_home = Button(label="Main Menu", style=discord.ButtonStyle.secondary, emoji="🏠", row=2)
        btn_home.callback = self.show_home
        self.add_item(btn_home)

        invite_url = f"https://discord.com/oauth2/authorize?client_id={self.bot.user.id}&permissions=8&scope=bot%20applications.commands"
        self.add_item(Button(label="Invite Bot", url=invite_url, style=discord.ButtonStyle.link, row=2))

        await interaction.response.edit_message(embed=embed, view=self)


class Help(commands.Cog, name="Help"):
    """Clean and professional interactive help center."""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help", aliases=["commands", "cmds", "menu"])
    @commands.guild_only()
    async def help_command(self, ctx, *, command_name: Optional[str] = None):
        """Displays the interactive Shizu help menu."""
        prefix = await self.bot.db.get_prefix(ctx.guild.id)

        # If user asked for a specific command (e.g. ?help ban)
        if command_name:
            clean_name = command_name.lower().strip()
            # Search in categories
            found_cmd = None
            found_cat = None
            for cat_key, cat_data in COMMAND_CATEGORIES.items():
                for cmd_syntax, cmd_desc in cat_data["commands"]:
                    base_name = cmd_syntax.split()[0]
                    if clean_name == base_name or clean_name in cmd_syntax:
                        found_cmd = (cmd_syntax, cmd_desc)
                        found_cat = cat_data["title"]
                        break
                if found_cmd:
                    break

            # Fallback to bot command registry
            bot_cmd = self.bot.get_command(clean_name)
            if found_cmd:
                syntax, desc = found_cmd
                embed = discord.Embed(
                    title=f"Command Information: {clean_name}",
                    description=(
                        f"**Category:** {found_cat}\n"
                        f"**Syntax:** `{prefix}{syntax}`\n"
                        f"**Description:** {desc}\n"
                    ),
                    color=config.COLOR_DARK
                )
                if bot_cmd and bot_cmd.aliases:
                    embed.add_field(name="Aliases", value=", ".join(f"`{a}`" for a in bot_cmd.aliases), inline=False)
                embed.set_thumbnail(url=self.bot.user.display_avatar.url)
                embed.set_footer(text=f"Shizu Security v{config.VERSION}")
                return await ctx.reply(embed=embed, mention_author=False)
            elif bot_cmd:
                embed = discord.Embed(
                    title=f"Command Information: {bot_cmd.name}",
                    description=(
                        f"**Syntax:** `{prefix}{bot_cmd.name} {bot_cmd.signature}`\n"
                        f"**Description:** {bot_cmd.help or 'No description provided.'}\n"
                    ),
                    color=config.COLOR_DARK
                )
                if bot_cmd.aliases:
                    embed.add_field(name="Aliases", value=", ".join(f"`{a}`" for a in bot_cmd.aliases), inline=False)
                embed.set_thumbnail(url=self.bot.user.display_avatar.url)
                embed.set_footer(text=f"Shizu Security v{config.VERSION}")
                return await ctx.reply(embed=embed, mention_author=False)
            else:
                return await ctx.reply_error(f"Command `{command_name}` not found. Type `{prefix}help` to view all commands.")

        # Show Main Help Menu
        cfg = await self.bot.db.get_guild_config(ctx.guild.id)
        an_active = bool(cfg.get("antinuke_enabled"))

        view = HelpView(self.bot, ctx, prefix, an_active)
        embed = view.build_home_embed()
        await ctx.reply(embed=embed, view=view, mention_author=False)


async def setup(bot):
    await bot.add_cog(Help(bot))
