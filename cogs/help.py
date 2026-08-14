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
            fields = [
                (f"{self.cmd_prefix}ai [prompt] [attachments]", "Submit query with optional file attachment", False),
                (f"{self.cmd_prefix}ask [prompt] [attachments]", "Submit query with optional file attachment", False),
                ("/ai model [provider] [model]", "Switch or view active model", False),
                ("/ai history <view|clear|export>", "Manage conversational logs", False),
                ("/ai summarize [target] [lines]", "Generate message summary", False)
            ]
            return create_embed(title="AI Commands", color=color, fields=fields)

        if category == "voice":
            fields = [
                ("/join", "Connect bot to active voice channel", False),
                ("/leave", "Disconnect bot from voice channel", False)
            ]
            return create_embed(title="Voice Commands", color=color, fields=fields)

        if category == "settings":
            fields = [
                ("/set prefix <prefix>", "Update command prefix", False),
                ("/set provider <provider>", "Set default provider", False),
                ("/set memory <count>", "Set conversation context limit", False),
                ("/set owner <add|remove> <user>", "Manage bot owners", False),
                ("/set api_key <provider> <key>", "Save provider credentials", False),
                ("/set channel <channel> <allow|remove>", "Configure allowed channels", False),
                ("/set cooldown <action> [seconds] [user] [role]", "Configure cooldown & bypasses", False),
                ("/set tts [provider] [voice] [filter] [enabled]", "Configure voice & speech filters", False),
                ("/set embed [color] [mode]", "Configure appearance", False),
                ("/set usage_limit <type> <id> <limit>", "Set daily quota", False),
                ("/set prompt <view|set|clear> [text] [scope]", "Manage system prompts", False)
            ]
            return create_embed(title="Settings Commands", color=color, fields=fields)

        if category == "system":
            fields = [
                ("/stats", "Display latencies, memory, voice state, and query count", False),
                (f"{self.cmd_prefix}help / /help", "Display command guide and options", False)
            ]
            return create_embed(title="System Commands", color=color, fields=fields)

        active_p = self.config.get("active_provider", "gemini")
        active_m = self.config.get("active_model", "gemini-3.5-flash")
        fields = [
            ("Prefix", f"`{self.cmd_prefix}`", True),
            ("Provider", f"`{active_p}`", True),
            ("Model", f"`{active_m}`", True),
            ("Categories", "Use the selector below to view specific command groups.", False)
        ]
        return create_embed(
            title="Help Menu",
            description="Select a category from the dropdown to view available commands.",
            color=color,
            fields=fields
        )

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

        fields = [
            ("Prefix", f"`{prefix}`", True),
            ("Provider", f"`{active_p}`", True),
            ("Model", f"`{active_m}`", True),
            ("Categories", "Use the selector below to view specific command groups.", False)
        ]

        embed = create_embed(
            title="Help Menu",
            description="Select a category from the dropdown to view available commands.",
            color=color,
            fields=fields
        )
        view = HelpView(self.config, prefix)
        await ctx.reply(embed=embed, view=view, mention_author=False)

    @app_commands.command(name="help", description="Display command guide and options")
    async def help_slash(self, interaction: discord.Interaction):
        prefix = self.config.get_prefix()
        color = self.config.get_embed_color()
        active_p = self.config.get("active_provider", "gemini")
        active_m = self.config.get("active_model", "gemini-3.5-flash")

        fields = [
            ("Prefix", f"`{prefix}`", True),
            ("Provider", f"`{active_p}`", True),
            ("Model", f"`{active_m}`", True),
            ("Categories", "Use the selector below to view specific command groups.", False)
        ]

        embed = create_embed(
            title="Help Menu",
            description="Select a category from the dropdown to view available commands.",
            color=color,
            fields=fields
        )
        view = HelpView(self.config, prefix)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def setup(bot: commands.Bot):
    config: ConfigManager = bot.config
    await bot.add_cog(HelpCog(bot, config))
