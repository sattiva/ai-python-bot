import discord
from discord.ui import View, Button

class ResponseView(View):
    def __init__(self, timeout: float = 180.0):
        super().__init__(timeout=timeout)

class VoiceControlView(View):
    def __init__(self, voice_client: discord.VoiceClient, timeout: float = 120.0):
        super().__init__(timeout=timeout)
        self.voice_client = voice_client

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.secondary, emoji="❌")
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.voice_client and self.voice_client.is_connected() and self.voice_client.is_playing():
            self.voice_client.stop()
            button.disabled = True
            button.label = "Stopped"
            button.style = discord.ButtonStyle.danger
            await interaction.response.edit_message(view=self)
        else:
            button.disabled = True
            await interaction.response.edit_message(view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

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
