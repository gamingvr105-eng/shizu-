import discord
from discord.ext import commands
from typing import Optional, Union
import config
from core.checks import top_role_check

class ModerationCases(commands.Cog, name="Cases"):
    """Case lookup, warning history, and moderation audit trail."""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="case", usage="case <case_id>")
    @commands.guild_only()
    @commands.has_permissions(moderate_members=True)
    async def case_view(self, ctx, case_id: int):
        """Displays full details of a specific moderation case."""
        case = await self.bot.db.get_case(ctx.guild.id, case_id)
        if not case:
            return await ctx.reply_error(f"Moderation Case `#{case_id}` was not found for this server.")

        embed = discord.Embed(
            title=f"{config.ANIM_SHIELD} Moderation Case #{case['case_id']}",
            color=config.COLOR_DARK
        )
        embed.add_field(name="Action", value=f"**{case['action']}**", inline=True)
        embed.add_field(name="Target", value=f"{case['target_name']} (`{case['target_id']}`)", inline=True)
        embed.add_field(name="Moderator", value=f"{case['moderator_name']} (`{case['moderator_id']}`)", inline=True)
        embed.add_field(name="Reason", value=case['reason'], inline=False)
        embed.add_field(name="Timestamp (UTC)", value=case['timestamp'][:19].replace("T", " "), inline=False)
        embed.set_footer(text=f"Shizu Security v{config.VERSION}", icon_url=self.bot.user.display_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="modlogs", aliases=["cases", "history"], usage="modlogs <user>")
    @commands.guild_only()
    @commands.has_permissions(moderate_members=True)
    async def modlogs(self, ctx, user: Union[discord.Member, discord.User]):
        """Displays recent moderation actions taken against a user."""
        cases = await self.bot.db.get_cases_for_target(ctx.guild.id, user.id, limit=10)
        if not cases:
            return await ctx.reply_warning(f"No moderation cases on record for {user.mention} (`{user.id}`).")

        entries = []
        for c in cases:
            date_str = c['timestamp'][:10]
            entries.append(
                f"• **Case #{c['case_id']}** [`{c['action']}`] — *{date_str}*\n"
                f"  Reason: {c['reason']}\n"
                f"  Mod: {c['moderator_name']}"
            )

        embed = discord.Embed(
            title=f"{config.ANIM_SHIELD} Moderation Logs — {user}",
            description="\n\n".join(entries),
            color=config.COLOR_DARK
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=f"Total shown: {len(cases)} case(s)")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="warnings", aliases=["warns"], usage="warnings <member>")
    @commands.guild_only()
    @commands.has_permissions(moderate_members=True)
    async def warnings(self, ctx, member: discord.Member):
        """Displays all recorded warnings for a member."""
        warns = await self.bot.db.get_warnings(ctx.guild.id, member.id)
        if not warns:
            return await ctx.reply_warning(f"{member.mention} has no recorded warnings on this server.")

        entries = []
        for w in warns:
            mod = ctx.guild.get_member(w['moderator_id'])
            mod_str = mod.name if mod else f"Mod ID `{w['moderator_id']}`"
            date_str = w['timestamp'][:10]
            entries.append(f"• **Warn ID `#{w['warn_id']}`** — *{date_str}*\n  Reason: {w['reason']}\n  Issued by: {mod_str}")

        embed = discord.Embed(
            title=f"{config.ANIM_WARN} Warnings History — {member} ({len(warns)})",
            description="\n\n".join(entries),
            color=config.COLOR_DARK
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Use {ctx.prefix}clearwarns {member.id} [warn_id] to remove warnings")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="clearwarns", aliases=["clearwarnings", "delwarn"], usage="clearwarns <member> [warn_id]")
    @commands.guild_only()
    @top_role_check()
    @commands.has_permissions(moderate_members=True)
    async def clearwarns(self, ctx, member: discord.Member, warn_id: Optional[int] = None):
        """Clears all warnings or a specific warning ID for a member."""
        cleared = await self.bot.db.clear_warnings(ctx.guild.id, member.id, warn_id)
        if cleared == 0:
            if warn_id:
                return await ctx.reply_error(f"Warning ID `#{warn_id}` for {member.mention} was not found.")
            return await ctx.reply_warning(f"{member.mention} has no warnings to clear.")

        if warn_id:
            await ctx.reply_success(f"Cleared warning `#{warn_id}` for {member.mention}.")
        else:
            await ctx.reply_success(f"Cleared all **{cleared}** warning(s) for {member.mention}.")

async def setup(bot):
    await bot.add_cog(ModerationCases(bot))
