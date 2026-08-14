import discord
from discord.ext import commands
from discord import app_commands
from utils.config import ConfigManager
from utils.ui import create_error_embed, create_success_embed

class VoiceCog(commands.Cog):
    def __init__(self, bot: commands.Bot, config: ConfigManager):
        self.bot = bot
        self.config = config

    @app_commands.command(name="join", description="Join")
    async def join_voice(self, interaction: discord.Interaction):
        if not interaction.guild:
            embed = create_error_embed("Servers only.", self.config.get_embed_color())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if not self.config.is_whitelisted(interaction.user, interaction.channel):
            embed = create_error_embed("Unauthorized.", self.config.get_embed_color())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        member = interaction.user if isinstance(interaction.user, discord.Member) else interaction.guild.get_member(interaction.user.id)
        if not member or not member.voice or not member.voice.channel:
            embed = create_error_embed("Join a voice channel first.", self.config.get_embed_color())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        target_channel = member.voice.channel
        voice_client = interaction.guild.voice_client

        try:
            if voice_client:
                if voice_client.channel.id == target_channel.id:
                    embed = create_success_embed(
                        title="Connected",
                        message=f"Connected to {target_channel.mention}.",
                        color=self.config.get_embed_color()
                    )
                    await interaction.followup.send(embed=embed)
                    return
                await voice_client.move_to(target_channel)
            else:
                await target_channel.connect(timeout=15.0, reconnect=True, self_deaf=True)

            embed = create_success_embed(
                title="Connected",
                message=f"Connected to {target_channel.mention}.",
                color=self.config.get_embed_color()
            )
            await interaction.followup.send(embed=embed)
        except Exception as exc:
            embed = create_error_embed(f"Connection failed: {exc}", self.config.get_embed_color())
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="leave", description="Leave")
    async def leave_voice(self, interaction: discord.Interaction):
        if not interaction.guild:
            embed = create_error_embed("Servers only.", self.config.get_embed_color())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if not self.config.is_whitelisted(interaction.user, interaction.channel):
            embed = create_error_embed("Unauthorized.", self.config.get_embed_color())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        voice_client = interaction.guild.voice_client
        if not voice_client:
            embed = create_error_embed("Not connected.", self.config.get_embed_color())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        try:
            await voice_client.disconnect(force=True)
            embed = create_success_embed(
                title="Disconnected",
                message="Disconnected.",
                color=self.config.get_embed_color()
            )
            await interaction.followup.send(embed=embed)
        except Exception as exc:
            embed = create_error_embed(f"Failed: {exc}", self.config.get_embed_color())
            await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    config: ConfigManager = bot.config
    await bot.add_cog(VoiceCog(bot, config))
