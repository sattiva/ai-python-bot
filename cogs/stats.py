import discord
from discord.ext import commands
from discord import app_commands
import os
import psutil
from utils.config import ConfigManager
from utils.ui import ContainerV2, send_container_response, create_error_embed

class StatsCog(commands.Cog):
    def __init__(self, bot: commands.Bot, config: ConfigManager):
        self.bot = bot
        self.config = config

    @app_commands.command(name="stats", description="Stats")
    async def stats_command(self, interaction: discord.Interaction):
        if not self.config.is_whitelisted(interaction.user, interaction.channel):
            embed = create_error_embed("Unauthorized.", self.config.get_embed_color())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        process = psutil.Process(os.getpid())
        memory_usage_mb = process.memory_info().rss / (1024 * 1024)

        latency_ms = round(self.bot.latency * 1000, 2)

        voice_status = "Disconnected"
        if interaction.guild and interaction.guild.voice_client:
            vc = interaction.guild.voice_client
            if vc.is_connected():
                voice_status = f"Connected ({vc.channel.name})"

        ai_cog = self.bot.get_cog("AICog")
        total_prompts = ai_cog.total_prompts_processed if ai_cog else 0

        rate_limit_seconds = self.config.get("rate_limits", {}).get("seconds", 5)

        container = ContainerV2(accent_color=self.config.get_embed_color())
        container.add_text("## Telemetry & Diagnostics")
        container.add_separator(divider=True)
        container.add_text(
            f"**Gateway Latency:** `{latency_ms} ms`\n"
            f"**Memory Allocation:** `{memory_usage_mb:.2f} MB`\n"
            f"**Voice Client:** `{voice_status}`\n"
            f"**Total Queries:** `{total_prompts}`\n"
            f"**Active Cooldown:** `{rate_limit_seconds}s`\n"
            f"**Active Guilds:** `{len(self.bot.guilds)}`"
        )

        await send_container_response(interaction, container, ephemeral=True, bot=self.bot)

async def setup(bot: commands.Bot):
    config: ConfigManager = bot.config
    await bot.add_cog(StatsCog(bot, config))
