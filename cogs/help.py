import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Select
from discord.http import Route
from utils.config import ConfigManager
from utils.ui import ContainerV2, send_container_response, build_fallback_embed, select_option, select_dict, FLAG_COMPONENTS_V2

class HelpSelect(Select):
    def __init__(self, config: ConfigManager, prefix: str):
        self.config = config
        self.cmd_prefix = prefix
        options = [
            discord.SelectOption(label="Overview", description="General system summary", value="overview", default=True),
            discord.SelectOption(label="AI", description="Text generation and analysis", value="ai"),
            discord.SelectOption(label="Voice", description="Voice channel and audio playback", value="voice"),
            discord.SelectOption(label="Settings", description="Administrative configuration", value="settings"),
            discord.SelectOption(label="System", description="Diagnostics and metrics", value="system")
        ]
        super().__init__(placeholder="Select a category", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        for option in self.options:
            option.default = (option.value == self.values[0])

        category = self.values[0]
        color = self.config.get_embed_color()
        container = self._build_category_container(category, color)

        adapter = getattr(interaction._client._connection, "http", None)
        if adapter:
            try:
                payload = {
                    "type": 7,
                    "data": {
                        "flags": FLAG_COMPONENTS_V2,
                        "components": [container.to_dict()]
                    }
                }
                route = Route("POST", "/interactions/{interaction_id}/{interaction_token}/callback", interaction_id=interaction.id, interaction_token=interaction.token)
                await adapter.request(route, json=payload)
                return
            except Exception:
                pass

        embed = build_fallback_embed(container)
        await interaction.response.edit_message(embed=embed, view=self.view)

    def _build_category_container(self, category: str, color: int) -> ContainerV2:
        container = ContainerV2(accent_color=color)

        if category == "ai":
            container.add_text("## AI Generation & Analysis")
            container.add_separator(divider=True)
            container.add_text(
                f"**Command:** `{self.cmd_prefix}ai` / `{self.cmd_prefix}ask`\n"
                f"**Syntax:** `{self.cmd_prefix}ai [prompt] [attachments]`\n"
                "**Description:** Query active provider with optional OCR images, code, or logs."
            )
            container.add_separator(divider=True)
            container.add_text(
                "**Command:** `/ai model`\n"
                "**Syntax:** `/ai model [provider] [model_name]`\n"
                "**Description:** Inspect or switch active LLM model."
            )
            container.add_separator(divider=True)
            container.add_text(
                "**Command:** `/ai history`\n"
                "**Syntax:** `/ai history <view|clear|export>`\n"
                "**Description:** Manage active conversation context."
            )
            container.add_separator(divider=True)
            container.add_text("-# Multimodal OCR & Vision supported across providers.")

        elif category == "voice":
            container.add_text("## Voice Channel Controls")
            container.add_separator(divider=True)
            container.add_text(
                "**Command:** `/join`\n"
                "**Syntax:** `/join`\n"
                "**Description:** Connect bot to active voice channel."
            )
            container.add_separator(divider=True)
            container.add_text(
                "**Command:** `/leave`\n"
                "**Syntax:** `/leave`\n"
                "**Description:** Disconnect bot from voice channel."
            )
            container.add_separator(divider=True)
            container.add_text(
                "**Control:** `❌ Stop Audio`\n"
                "**Description:** Interactive button attached to responses for instant speech cutoff."
            )
            container.add_separator(divider=True)
            container.add_text("-# Synthesizers: Deepgram, OpenAI TTS, ElevenLabs.")

        elif category == "settings":
            container.add_text("## Settings & Configuration")
            container.add_separator(divider=True)
            container.add_text(
                "**Syntax:** `/set prefix <prefix>` — Set command prefix\n"
                "**Syntax:** `/set provider <provider>` — Change default provider\n"
                "**Syntax:** `/set memory <count>` — Set context retention\n"
                "**Syntax:** `/set owner <add|remove> <user>` — Manage owners\n"
                "**Syntax:** `/set api_key <provider> <key>` — Save credentials\n"
                "**Syntax:** `/set channel <channel> <allow|remove>` — Whitelist channels\n"
                "**Syntax:** `/set cooldown <action> [seconds] [user] [role]` — Rate limits\n"
                "**Syntax:** `/set tts [provider] [voice] [filter] [enabled]` — Voice & filters\n"
                "**Syntax:** `/set embed [color] [mode]` — Appearance\n"
                "**Syntax:** `/set prompt <view|set|clear> [text] [scope]` — System prompts"
            )
            container.add_separator(divider=True)
            container.add_text("-# Restricted to configured owner user IDs.")

        elif category == "system":
            container.add_text("## Diagnostics & Metrics")
            container.add_separator(divider=True)
            container.add_text(
                "**Command:** `/stats`\n"
                "**Syntax:** `/stats`\n"
                "**Description:** Display latency, memory, voice state, and query count."
            )
            container.add_separator(divider=True)
            container.add_text(
                f"**Command:** `/help` / `{self.cmd_prefix}help`\n"
                "**Description:** Interactive category help menu."
            )
            container.add_separator(divider=True)
            container.add_text("-# Built with discord.py v2.7 & Containers V2.")

        else:
            active_p = self.config.get("active_provider", "gemini")
            active_m = self.config.get("active_model", "gemini-3.5-flash")
            container.add_text("## Command Guide & Overview")
            container.add_separator(divider=True)
            container.add_text(
                f"**Prefix:** `{self.cmd_prefix}`\n"
                f"**Provider:** `{active_p}`\n"
                f"**Model:** `{active_m}`\n\n"
                "Select a category from the dropdown menu below to view specific commands."
            )
            container.add_separator(divider=True)
            container.add_text("-# Containers V2 Architecture")

        options = [
            select_option("Overview", "overview", "General system summary", default=(category == "overview")),
            select_option("AI", "ai", "Text generation and analysis", default=(category == "ai")),
            select_option("Voice", "voice", "Voice channel and audio playback", default=(category == "voice")),
            select_option("Settings", "settings", "Administrative configuration", default=(category == "settings")),
            select_option("System", "system", "Diagnostics and metrics", default=(category == "system"))
        ]
        select_menu = select_dict("help_category_select", options)
        container.add_action_row([select_menu])

        return container

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
        selector = HelpSelect(self.config, prefix)
        container = selector._build_category_container("overview", color)
        view = HelpView(self.config, prefix)
        await send_container_response(ctx, container, view=view, bot=self.bot)

    @app_commands.command(name="help", description="Guide")
    async def help_slash(self, interaction: discord.Interaction):
        prefix = self.config.get_prefix()
        color = self.config.get_embed_color()
        selector = HelpSelect(self.config, prefix)
        container = selector._build_category_container("overview", color)
        view = HelpView(self.config, prefix)
        await send_container_response(interaction, container, view=view, ephemeral=True, bot=self.bot)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.component:
            custom_id = interaction.data.get("custom_id")
            if custom_id == "help_category_select":
                values = interaction.data.get("values", [])
                if values:
                    category = values[0]
                    prefix = self.config.get_prefix()
                    color = self.config.get_embed_color()
                    selector = HelpSelect(self.config, prefix)
                    container = selector._build_category_container(category, color)

                    adapter = getattr(interaction._client._connection, "http", None)
                    if adapter:
                        payload = {
                            "type": 7,
                            "data": {
                                "flags": FLAG_COMPONENTS_V2,
                                "components": [container.to_dict()]
                            }
                        }
                        route = Route("POST", "/interactions/{interaction_id}/{interaction_token}/callback", interaction_id=interaction.id, interaction_token=interaction.token)
                        await adapter.request(route, json=payload)

async def setup(bot: commands.Bot):
    config: ConfigManager = bot.config
    await bot.add_cog(HelpCog(bot, config))
