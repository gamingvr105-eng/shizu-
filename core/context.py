import discord
from discord.ext import commands
from typing import Optional, Any
import config

class Context(commands.Context):
    """Custom Context tailored to Shizu design standards with clean replies and animated emojis."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _can_send(self) -> bool:
        if self.guild is None:
            return True
        return self.channel.permissions_for(self.me).send_messages

    async def _warn_no_perms(self) -> None:
        try:
            await self.author.send("I don't have permission to send messages in that channel.")
        except discord.Forbidden:
            pass

    async def send(self, content: Optional[str] = None, **kwargs) -> Optional[discord.Message]:
        if not self._can_send():
            await self._warn_no_perms()
            return None
        return await super().send(content, **kwargs)

    async def reply(self, content: Optional[str] = None, **kwargs) -> Optional[discord.Message]:
        if not self._can_send():
            await self._warn_no_perms()
            return None
        # Default mention_author to False for clean Shizu replies
        if "mention_author" not in kwargs:
            kwargs["mention_author"] = False
        return await super().reply(content, **kwargs)

    # --- Shizu Signature Reply Methods with Animated Emojis ---
    async def reply_success(self, text: str, **kwargs) -> Optional[discord.Message]:
        """Replies with a clean Shizu-style dark embed and animated success tick."""
        embed = discord.Embed(
            description=f"{config.ANIM_SUCCESS} {text}",
            color=config.COLOR_DARK
        )
        return await self.reply(embed=embed, **kwargs)

    async def reply_error(self, text: str, **kwargs) -> Optional[discord.Message]:
        """Replies with a clean Shizu-style dark embed and animated warning flash."""
        embed = discord.Embed(
            description=f"{config.ANIM_WARN} {text}",
            color=0xFF0000
        )
        return await self.reply(embed=embed, **kwargs)

    async def reply_warning(self, text: str, **kwargs) -> Optional[discord.Message]:
        """Replies with an animated warning flash and dark embed."""
        embed = discord.Embed(
            description=f"{config.ANIM_WARN} {text}",
            color=config.COLOR_DARK
        )
        return await self.reply(embed=embed, **kwargs)

    async def reply_loading(self, text: str, **kwargs) -> Optional[discord.Message]:
        """Replies with an animated loading indicator."""
        embed = discord.Embed(
            description=f"{config.ANIM_LOADING} {text}",
            color=config.COLOR_DARK
        )
        return await self.reply(embed=embed, **kwargs)

    async def reply_shield(self, text: str, **kwargs) -> Optional[discord.Message]:
        """Replies with an animated security shield indicator."""
        embed = discord.Embed(
            description=f"{config.ANIM_SHIELD} {text}",
            color=config.COLOR_DARK
        )
        return await self.reply(embed=embed, **kwargs)

    # --- Compatibility Methods ---
    async def send_success(self, description: str, title: Optional[str] = None, **kwargs) -> Optional[discord.Message]:
        return await self.reply_success(f"**{title}**\n{description}" if title else description, **kwargs)

    async def send_error(self, description: str, title: Optional[str] = None, **kwargs) -> Optional[discord.Message]:
        return await self.reply_error(f"**{title}**\n{description}" if title else description, **kwargs)

    async def send_warning(self, description: str, title: Optional[str] = None, **kwargs) -> Optional[discord.Message]:
        return await self.reply_warning(f"**{title}**\n{description}" if title else description, **kwargs)
