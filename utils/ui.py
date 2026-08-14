import discord
from discord.ui import View

class ResponseView(View):
    def __init__(self, timeout: float = 180.0):
        super().__init__(timeout=timeout)

def create_embed(
    title: str | None = None,
    description: str | None = None,
    color: int = 0x2B2D31,
    fields: list[tuple[str, str, bool]] | None = None,
    footer: str | None = None,
    author_name: str | None = None,
    author_icon_url: str | None = None
) -> discord.Embed:
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )
    if fields:
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
    if footer:
        embed.set_footer(text=footer)
    if author_name:
        embed.set_author(name=author_name, icon_url=author_icon_url)
    return embed

def create_error_embed(message: str, color: int = 0x2B2D31) -> discord.Embed:
    return create_embed(
        title="Error",
        description=message,
        color=color
    )

def create_success_embed(title: str, message: str, color: int = 0x2B2D31) -> discord.Embed:
    return create_embed(
        title=title,
        description=message,
        color=color
    )
