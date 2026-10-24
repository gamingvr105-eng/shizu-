import discord
from discord.ext import commands
import config
from typing import Tuple

def is_bot_owner():
    async def predicate(ctx: commands.Context) -> bool:
        if ctx.author.id in config.OWNER_IDS:
            return True
        return await ctx.bot.is_owner(ctx.author)
    return commands.check(predicate)

def is_guild_owner_or_extra():
    async def predicate(ctx: commands.Context) -> bool:
        if not ctx.guild:
            return False
        if ctx.author.id in config.OWNER_IDS or ctx.author.id == ctx.guild.owner_id:
            return True
        is_extra = await ctx.bot.db.is_extra_owner(ctx.guild.id, ctx.author.id)
        if is_extra:
            return True
        embed = discord.Embed(
            title=f"{config.EMOJI_ERROR} Access Denied",
            description="Only the **Server Owner**, **Extra Owners**, or **Bot Developers** can execute this command.",
            color=config.COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return False
    return commands.check(predicate)

def top_role_check():
    async def predicate(ctx: commands.Context) -> bool:
        if not ctx.guild:
            return True
        if ctx.author.id in config.OWNER_IDS or ctx.author.id == ctx.guild.owner_id:
            return True
        
        cfg = await ctx.bot.db.get_guild_config(ctx.guild.id)
        if not cfg.get("topcheck_enabled", True):
            return True

        if ctx.author.top_role.position <= ctx.guild.me.top_role.position:
            embed = discord.Embed(
                title=f"{config.EMOJI_ERROR} Role Position Too Low",
                description="Your highest role must be positioned **strictly above** my highest role to execute this command.",
                color=config.COLOR_ERROR
            )
            await ctx.send(embed=embed)
            return False
        return True
    return commands.check(predicate)

def check_hierarchy(ctx: commands.Context, target: discord.Member) -> Tuple[bool, str]:
    """
    Validates role hierarchy and safety rules before any punishment action.
    Returns (True, "") if action is allowed, or (False, error_reason) if blocked.
    """
    if not ctx.guild:
        return False, "This command can only be used in a server."

    if target.id == ctx.author.id:
        return False, "You cannot execute this moderation action on yourself."

    if target.id == ctx.guild.me.id:
        return False, "You cannot execute this moderation action on me."

    if target.id == ctx.guild.owner_id:
        return False, "The Server Owner cannot be moderated."

    if target.id in config.OWNER_IDS:
        return False, "Bot Developers / Owners cannot be moderated."

    # Check bot permissions relative to target
    if ctx.guild.me.top_role <= target.top_role:
        return False, f"I cannot moderate {target.mention} because their highest role ({target.top_role.name}) is equal to or higher than my highest role ({ctx.guild.me.top_role.name})."

    # Check author permissions relative to target (unless author is server owner or bot developer)
    if ctx.author.id != ctx.guild.owner_id and ctx.author.id not in config.OWNER_IDS:
        if ctx.author.top_role <= target.top_role:
            return False, f"You cannot moderate {target.mention} because their highest role ({target.top_role.name}) is equal to or higher than your highest role ({ctx.author.top_role.name})."

    return True, ""
