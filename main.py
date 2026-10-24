import asyncio
import logging
import sys
import os
import discord
from discord.ext import commands

import config
from core.bot import ShizuSecurity

# Setup rich console logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("ShizuSecurity.Main")

bot = ShizuSecurity()

@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    """Global centralized error handling for user feedback."""
    # Unwrap CommandInvokeError
    if isinstance(error, commands.CommandInvokeError):
        error = error.original

    if isinstance(error, commands.CommandNotFound):
        return  # Ignore invalid commands silently

    if isinstance(error, commands.MissingPermissions):
        perms = ", ".join(f"`{p.replace('_', ' ').title()}`" for p in error.missing_permissions)
        return await ctx.send(
            embed=discord.Embed(
                title=f"{config.EMOJI_ERROR} Missing Permissions",
                description=f"You require the following permission(s) to execute this command: {perms}",
                color=config.COLOR_ERROR
            )
        )

    if isinstance(error, commands.BotMissingPermissions):
        perms = ", ".join(f"`{p.replace('_', ' ').title()}`" for p in error.missing_permissions)
        return await ctx.send(
            embed=discord.Embed(
                title=f"{config.EMOJI_ERROR} Bot Missing Permissions",
                description=f"I need the following Discord permission(s) to execute this action: {perms}\n"
                            f"Please ensure my role has these permissions and is placed high in role hierarchy.",
                color=config.COLOR_ERROR
            )
        )

    if isinstance(error, commands.CommandOnCooldown):
        return await ctx.send(
            embed=discord.Embed(
                title=f"{config.EMOJI_TIMEOUT} Cooldown Active",
                description=f"This command is on cooldown. Please retry in **{error.retry_after:.1f}** seconds.",
                color=config.COLOR_WARNING
            )
        )

    if isinstance(error, commands.MissingRequiredArgument):
        usage = f"`{ctx.prefix}{ctx.command.usage}`" if ctx.command.usage else f"`{ctx.prefix}{ctx.command.name} {ctx.command.signature}`"
        return await ctx.send(
            embed=discord.Embed(
                title=f"{config.EMOJI_ERROR} Missing Argument: `{error.param.name}`",
                description=f"Correct command syntax: {usage}",
                color=config.COLOR_ERROR
            )
        )

    if isinstance(error, commands.BadArgument):
        return await ctx.send(
            embed=discord.Embed(
                title=f"{config.EMOJI_ERROR} Invalid Argument",
                description=str(error),
                color=config.COLOR_ERROR
            )
        )

    if isinstance(error, commands.NoPrivateMessage):
        return await ctx.send(
            embed=discord.Embed(
                title=f"{config.EMOJI_ERROR} Server Only",
                description="This command can only be used within a Discord server.",
                color=config.COLOR_ERROR
            )
        )

    if isinstance(error, commands.CheckFailure):
        return  # Specific custom checks already send formatted error embeds

    logger.error(f"Unhandled error in command '{ctx.command}': {error}", exc_info=error)
    try:
        await ctx.send(
            embed=discord.Embed(
                title=f"{config.EMOJI_ERROR} Execution Error",
                description=f"An unexpected error occurred while executing `{ctx.command}`:\n```{error}```",
                color=config.COLOR_ERROR
            )
        )
    except Exception:
        pass

async def main():
    token = config.TOKEN
    if not token or token.strip() == "YOUR_BOT_TOKEN_HERE":
        logger.error(
            "CRITICAL: No Discord bot token provided!\n"
            "Please create a .env file and set DISCORD_TOKEN=your_token_here\n"
            "Refer to .env.example for details."
        )
        print("\n[ERROR] Missing DISCORD_TOKEN in environment or .env file.")
        print("Copy .env.example to .env and insert your bot token.\n")
        return

    # Start optional web health server if PORT is defined (for Koyeb, Render, Railway, Fly.io)
    port = os.getenv("PORT")
    if port:
        try:
            from aiohttp import web
            app = web.Application()
            async def health(_):
                return web.Response(text="Shizu Security Bot is online.")
            app.router.add_get("/", health)
            app.router.add_get("/health", health)
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, "0.0.0.0", int(port))
            await site.start()
            logger.info(f"Healthcheck web server running on port {port}")
        except Exception as e:
            logger.warning(f"Could not start healthcheck server: {e}")

    async with bot:
        await bot.start(token)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Process interrupted by user. Exiting.")
