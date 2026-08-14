import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Select, Button
from utils.config import ConfigManager
from utils.ui import create_embed

class HelpSelect(Select):
    def __init__(self, config: ConfigManager, prefix: str):
        self.config = config
        self.cmd_prefix = prefix
        options = [
            discord.SelectOption(label="Overview", description="General system summary", value="overview", default=True),
            discord.SelectOption(label="AI", description="Text generation and analysis", value="ai"),
            discord.SelectOption(label="Voice", description="Voice channel and audio playback", value="voice"),
            discord.SelectOption(label="Settings", description="Administrative and system configuration", value="settings"),
            discord.SelectOption(label="System", description="Metrics and status", value="system")
        ]
        super().__init__(placeholder="Select a category", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        for option in self.options:
            option.default = (option.value == self.values[0])

        category = self.values[0]
        color = self.config.get_embed_color()
        embed = self._build_category_embed(category, color)
        await interaction.response.edit_message(embed=embed, view=self.view)

    def _build_category_embed(self, category: str, color: int) -> discord.Embed:
        if category == "ai":
            desc = (
                "### AI Generation & Analysis\n"
                f"> `{self.cmd_prefix}ai [prompt] [attachments]`\n"
                "> Query active model with optional file or OCR image attachments.\n\n"
                f"> `{self.cmd_prefix}ask [prompt] [attachments]`\n"
                "> Alias for AI text and multimodal queries.\n\n"
                "> `/ai model [provider] [model]`\n"
                "> Inspect active provider/model or switch model.\n\n"
                "> `/ai history <view|clear|export>`\n"
                "> Manage conversational memory context.\n\n"
                "> `/ai summarize [target] [lines]`\n"
                "> Generate executive summary of recent messages.\n"
                "-# Attachments supported: images (OCR/vision), code, logs, and text documents."
            )
            return create_embed(description=desc, color=color)

        if category == "voice":
            desc = (
                "### Voice Channel Interface\n"
                "> `/join`\n"
                "> Connect bot to your active voice channel.\n\n"
                "> `/leave`\n"
                "> Disconnect bot from the voice channel.\n\n"
                "> `❌ Stop Audio`\n"
                "> Interactive button attached to AI responses to terminate speech live.\n"
                "-# Supports Deepgram, OpenAI TTS, and ElevenLabs speech engines."
            )
            return create_embed(description=desc, color=color)

        if category == "settings":
            desc = (
                "### Settings & Administration\n"
                "> `/set prefix <prefix>` — Set custom command prefix.\n"
                "> `/set provider <provider>` — Change default LLM provider.\n"
                "> `/set memory <count>` — Set conversation message retention limit.\n"
                "> `/set owner <add|remove> <user>` — Manage bot administrators.\n"
                "> `/set api_key <provider> <key>` — Save API credentials.\n"
                "> `/set channel <channel> <allow|remove>` — Whitelist channels.\n"
                "> `/set cooldown <action> [seconds] [user] [role]` — Manage rate limits.\n"
                "> `/set tts [provider] [voice] [filter] [enabled]` — Configure voice.\n"
                "> `/set embed [color] [mode]` — Configure theme and appearance.\n"
                "> `/set usage_limit <type> <id> <limit>` — Daily request quota.\n"
                "> `/set prompt <view|set|clear> [text] [scope]` — System instructions.\n"
                "-# Restricted to configured owner user IDs."
            )
            return create_embed(description=desc, color=color)

        if category == "system":
            desc = (
                "### Diagnostics & Telemetry\n"
                "> `/stats`\n"
                "> View gateway latency, memory usage, voice status, and query count.\n\n"
                f"> `/help` or `{self.cmd_prefix}help`\n"
                "> Display interactive command guide.\n"
                "-# Built with discord.py v2.7 & Containers V2."
            )
            return create_embed(description=desc, color=color)

        active_p = self.config.get("active_provider", "gemini")
        active_m = self.config.get("active_model", "gemini-3.5-flash")
        desc = (
            "### Command Guide & Navigation\n"
            f"> **Prefix**: `{self.cmd_prefix}`\n"
            f"> **Provider**: `{active_p}`\n"
            f"> **Model**: `{active_m}`\n\n"
            "Select a category from the dropdown menu below to view detailed command references.\n"
            "-# Containers V2 Interface"
        )
        return create_embed(description=desc, color=color)

class HelpView(View):
    def __init__(self, config: ConfigManager, prefix: str, timeout: float = 180.0):
        super().__init__(timeout=timeout)
        self.add_item(HelpSelect(config, prefix))

class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot, config: ConfigManager):
        self.bot = bot
        self.config = config
        self.bot.help_command = None

    @commands.command(name="help")
    async def help_prefix(self, ctx: commands.Context):
        prefix = self.config.get_prefix()
        color = self.config.get_embed_color()
        active_p = self.config.get("active_provider", "gemini")
        active_m = self.config.get("active_model", "gemini-3.5-flash")

        desc = (
            "### Command Guide & Navigation\n"
            f"> **Prefix**: `{prefix}`\n"
            f"> **Provider**: `{active_p}`\n"
            f"> **Model**: `{active_m}`\n\n"
            "Select a category from the dropdown menu below to view detailed command references.\n"
            "-# Containers V2 Interface"
        )

        embed = create_embed(description=desc, color=color)
        view = HelpView(self.config, prefix)
        await ctx.reply(embed=embed, view=view, mention_author=False)

    @app_commands.command(name="help", description="Guide")
    async def help_slash(self, interaction: discord.Interaction):
        prefix = self.config.get_prefix()
        color = self.config.get_embed_color()
        active_p = self.config.get("active_provider", "gemini")
        active_m = self.config.get("active_model", "gemini-3.5-flash")

        desc = (
            "### Command Guide & Navigation\n"
            f"> **Prefix**: `{prefix}`\n"
            f"> **Provider**: `{active_p}`\n"
            f"> **Model**: `{active_m}`\n\n"
            "Select a category from the dropdown menu below to view detailed command references.\n"
            "-# Containers V2 Interface"
        )

        embed = create_embed(description=desc, color=color)
        view = HelpView(self.config, prefix)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def setup(bot: commands.Bot):
    config: ConfigManager = bot.config
    await bot.add_cog(HelpCog(bot, config))
