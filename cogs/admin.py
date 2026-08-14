import discord
from discord.ext import commands
from discord import app_commands
from utils.config import ConfigManager
from utils.ui import create_embed, create_error_embed, create_success_embed

class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot, config: ConfigManager):
        self.bot = bot
        self.config = config

    set_group = app_commands.Group(name="set", description="Settings")

    @set_group.command(name="api_key", description="Keys")
    @app_commands.describe(
        provider="Provider",
        key="Key"
    )
    @app_commands.choices(provider=[
        app_commands.Choice(name="Groq", value="groq"),
        app_commands.Choice(name="Gemini", value="gemini"),
        app_commands.Choice(name="DeepSeek", value="deepseek"),
        app_commands.Choice(name="Anthropic", value="anthropic"),
        app_commands.Choice(name="OpenAI", value="openai"),
        app_commands.Choice(name="Together", value="together"),
        app_commands.Choice(name="OpenRouter", value="openrouter"),
        app_commands.Choice(name="Deepgram", value="deepgram"),
        app_commands.Choice(name="ElevenLabs", value="elevenlabs")
    ])
    async def set_api_key(self, interaction: discord.Interaction, provider: str, key: str):
        if not self.config.is_owner(interaction.user.id):
            embed = create_error_embed("Unauthorized.", self.config.get_embed_color())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        keys = self.config.get("api_keys", {})
        keys[provider.lower()] = key.strip()
        self.config.set("api_keys", keys)

        embed = create_success_embed(
            title="Saved",
            message=f"Key for `{provider}` saved.",
            color=self.config.get_embed_color()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @set_group.command(name="prefix", description="Prefix")
    @app_commands.describe(prefix="Prefix")
    async def set_prefix(self, interaction: discord.Interaction, prefix: str):
        if not self.config.is_owner(interaction.user.id):
            embed = create_error_embed("Unauthorized.", self.config.get_embed_color())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        clean_prefix = prefix.strip()
        if not clean_prefix:
            embed = create_error_embed("Invalid prefix.", self.config.get_embed_color())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        self.config.set_prefix(clean_prefix)
        embed = create_success_embed(
            title="Saved",
            message=f"Prefix set to `{clean_prefix}`.",
            color=self.config.get_embed_color()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @set_group.command(name="provider", description="Provider")
    @app_commands.describe(provider="Provider")
    @app_commands.choices(provider=[
        app_commands.Choice(name="Groq", value="groq"),
        app_commands.Choice(name="Gemini", value="gemini"),
        app_commands.Choice(name="DeepSeek", value="deepseek"),
        app_commands.Choice(name="Anthropic", value="anthropic"),
        app_commands.Choice(name="OpenAI", value="openai"),
        app_commands.Choice(name="Together", value="together"),
        app_commands.Choice(name="OpenRouter", value="openrouter")
    ])
    async def set_provider(self, interaction: discord.Interaction, provider: str):
        if not self.config.is_owner(interaction.user.id):
            embed = create_error_embed("Unauthorized.", self.config.get_embed_color())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        provider_lower = provider.lower()
        self.config.set("active_provider", provider_lower)
        active_model = self.config.get_active_model(provider_lower)

        embed = create_success_embed(
            title="Saved",
            message=f"Default provider set to `{provider_lower}` (`{active_model}`).",
            color=self.config.get_embed_color()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @set_group.command(name="memory", description="Memory")
    @app_commands.describe(count="Messages")
    async def set_memory(self, interaction: discord.Interaction, count: int):
        if not self.config.is_owner(interaction.user.id):
            embed = create_error_embed("Unauthorized.", self.config.get_embed_color())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        self.config.set_memory_limit(count)
        embed = create_success_embed(
            title="Saved",
            message=f"Memory limit set to `{max(0, count)}` messages.",
            color=self.config.get_embed_color()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @set_group.command(name="owner", description="Owners")
    @app_commands.describe(action="Action", user="User")
    @app_commands.choices(action=[
        app_commands.Choice(name="add", value="add"),
        app_commands.Choice(name="remove", value="remove")
    ])
    async def set_owner(self, interaction: discord.Interaction, action: str, user: discord.User):
        if not self.config.is_owner(interaction.user.id):
            embed = create_error_embed("Unauthorized.", self.config.get_embed_color())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if action == "add":
            self.config.add_owner(user.id)
            status = "added"
        else:
            self.config.remove_owner(user.id)
            status = "removed"

        embed = create_success_embed(
            title="Saved",
            message=f"Owner {user.mention} {status}.",
            color=self.config.get_embed_color()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @set_group.command(name="channel", description="Channels")
    @app_commands.describe(
        channel="Channel",
        restriction_mode="Action"
    )
    @app_commands.choices(restriction_mode=[
        app_commands.Choice(name="allow", value="allow"),
        app_commands.Choice(name="remove", value="remove")
    ])
    async def set_channel(self, interaction: discord.Interaction, channel: discord.TextChannel, restriction_mode: str = "allow"):
        if not self.config.is_owner(interaction.user.id):
            embed = create_error_embed("Unauthorized.", self.config.get_embed_color())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        whitelists = self.config.get("whitelists", {})
        channels = whitelists.setdefault("channels", [])

        if restriction_mode == "allow":
            if channel.id not in channels:
                channels.append(channel.id)
                self.config.set("whitelists", whitelists)
            message = f"Channel {channel.mention} added."
        else:
            if channel.id in channels:
                channels.remove(channel.id)
                self.config.set("whitelists", whitelists)
            message = f"Channel {channel.mention} removed."

        embed = create_success_embed(title="Updated", message=message, color=self.config.get_embed_color())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @set_group.command(name="cooldown", description="Cooldowns")
    @app_commands.describe(
        action="Action",
        seconds="Seconds",
        user="User",
        role="Role"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="set (cooldown interval)", value="set"),
        app_commands.Choice(name="bypass_user (toggle user bypass)", value="bypass_user"),
        app_commands.Choice(name="bypass_role (toggle role bypass)", value="bypass_role")
    ])
    async def set_cooldown(
        self,
        interaction: discord.Interaction,
        action: str,
        seconds: int | None = None,
        user: discord.User | None = None,
        role: discord.Role | None = None
    ):
        if not self.config.is_owner(interaction.user.id):
            embed = create_error_embed("Unauthorized.", self.config.get_embed_color())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        rate_limits = self.config.get("rate_limits", {})

        if action == "set":
            if seconds is None:
                embed = create_error_embed("Please specify seconds parameter.", self.config.get_embed_color())
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            rate_limits["seconds"] = max(0, seconds)
            self.config.set("rate_limits", rate_limits)
            embed = create_success_embed(
                title="Updated",
                message=f"Cooldown set to `{max(0, seconds)}` seconds.",
                color=self.config.get_embed_color()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if action == "bypass_user":
            if not user:
                embed = create_error_embed("Please specify target user.", self.config.get_embed_color())
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            bypass_users = rate_limits.setdefault("bypass_users", [])
            if user.id in bypass_users:
                bypass_users.remove(user.id)
                status = "removed"
            else:
                bypass_users.append(user.id)
                status = "added"
            self.config.set("rate_limits", rate_limits)
            embed = create_success_embed(
                title="Updated",
                message=f"User {user.mention} {status}.",
                color=self.config.get_embed_color()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if action == "bypass_role":
            if not role:
                embed = create_error_embed("Please specify target role.", self.config.get_embed_color())
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            bypass_roles = rate_limits.setdefault("bypass_roles", [])
            if role.id in bypass_roles:
                bypass_roles.remove(role.id)
                status = "removed"
            else:
                bypass_roles.append(role.id)
                status = "added"
            self.config.set("rate_limits", rate_limits)
            embed = create_success_embed(
                title="Updated",
                message=f"Role {role.mention} {status}.",
                color=self.config.get_embed_color()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @set_group.command(name="embed", description="Appearance")
    @app_commands.describe(
        color="Hexadecimal color, e.g. 0x2B2D31",
        mode="Layout format: standard or plain"
    )
    @app_commands.choices(mode=[
        app_commands.Choice(name="standard", value="standard"),
        app_commands.Choice(name="plain", value="plain")
    ])
    async def set_embed(
        self,
        interaction: discord.Interaction,
        color: str | None = None,
        mode: str | None = None
    ):
        if not self.config.is_owner(interaction.user.id):
            embed = create_error_embed("Unauthorized.", self.config.get_embed_color())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if not color and not mode:
            embed = create_error_embed("Please specify color and/or mode.", self.config.get_embed_color())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed_settings = self.config.get("embed_settings", {})
        changes = []

        if color:
            clean_hex = color.strip()
            try:
                val = int(clean_hex.replace("#", "0x"), 16)
                embed_settings["color"] = hex(val)
                changes.append(f"Color: `{hex(val)}`")
            except ValueError:
                embed = create_error_embed("Invalid hexadecimal color format.", self.config.get_embed_color())
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

        if mode:
            embed_settings["mode"] = mode
            changes.append(f"Mode: `{mode}`")

        self.config.set("embed_settings", embed_settings)
        embed = create_success_embed(
            title="Updated",
            message=" | ".join(changes),
            color=self.config.get_embed_color()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @set_group.command(name="tts", description="Voice and speech synthesis configuration")
    @app_commands.describe(
        provider="TTS provider",
        voice="Voice identifier",
        speed="Speech playback speed (e.g. 0.8, 1.0, 1.25)",
        filter_target="Speech filter target to toggle",
        filter_enabled="Filter toggle state"
    )
    @app_commands.choices(provider=[
        app_commands.Choice(name="Deepgram", value="deepgram"),
        app_commands.Choice(name="OpenAI", value="openai"),
        app_commands.Choice(name="ElevenLabs", value="elevenlabs")
    ], filter_target=[
        app_commands.Choice(name="asterisks (*text*)", value="asterisks"),
        app_commands.Choice(name="brackets ([text])", value="brackets"),
        app_commands.Choice(name="parentheses ((text))", value="parentheses"),
        app_commands.Choice(name="braces ({text})", value="braces"),
        app_commands.Choice(name="code (```code```)", value="code"),
        app_commands.Choice(name="all", value="all")
    ])
    async def set_tts(
        self,
        interaction: discord.Interaction,
        provider: str | None = None,
        voice: str | None = None,
        speed: float | None = None,
        filter_target: str | None = None,
        filter_enabled: bool | None = None
    ):
        if not self.config.is_owner(interaction.user.id):
            embed = create_error_embed("Unauthorized.", self.config.get_embed_color())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        changes = []
        tts_settings = self.config.get("tts_settings", {})

        if provider:
            tts_settings["provider"] = provider.lower()
            changes.append(f"Provider: `{provider.lower()}`")

        if voice:
            tts_settings["voice_id"] = voice.strip()
            changes.append(f"Voice: `{voice.strip()}`")

        if speed is not None:
            clamped_speed = round(max(0.5, min(2.0, float(speed))), 2)
            tts_settings["speed"] = clamped_speed
            changes.append(f"Speed: `{clamped_speed}x`")

        if provider or voice or (speed is not None):
            self.config.set("tts_settings", tts_settings)

        if filter_target is not None:
            enabled_val = True if filter_enabled is None else filter_enabled
            current_filters = self.config.get("tts_filters", {
                "asterisks": True,
                "brackets": True,
                "parentheses": False,
                "braces": False,
                "code": True
            })
            if filter_target == "all":
                for k in ["asterisks", "brackets", "parentheses", "braces", "code"]:
                    current_filters[k] = enabled_val
            else:
                current_filters[filter_target] = enabled_val
            self.config.set("tts_filters", current_filters)
            status_text = "enabled" if enabled_val else "disabled"
            changes.append(f"Filter `{filter_target}`: `{status_text}`")

        if not changes:
            curr_p = tts_settings.get("provider", "deepgram")
            curr_v = tts_settings.get("voice_id", "aura-asteria-en")
            curr_s = tts_settings.get("speed", 1.0)
            embed = create_embed(
                title="TTS Configuration",
                description=f"Provider: `{curr_p}`\nVoice: `{curr_v}`\nSpeed: `{curr_s}x`",
                color=self.config.get_embed_color()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = create_success_embed(
            title="Saved",
            message=" | ".join(changes),
            color=self.config.get_embed_color()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @set_group.command(name="prompt", description="System prompts")
    @app_commands.describe(
        action="Action: view, set, or clear",
        text="Prompt text (for set action)",
        scope="Scope: personal or global (owners only)"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="view", value="view"),
        app_commands.Choice(name="set", value="set"),
        app_commands.Choice(name="clear", value="clear")
    ], scope=[
        app_commands.Choice(name="personal", value="personal"),
        app_commands.Choice(name="global", value="global")
    ])
    async def set_prompt(
        self,
        interaction: discord.Interaction,
        action: str = "view",
        text: str | None = None,
        scope: str = "personal"
    ):
        if not self.config.is_whitelisted(interaction.user, interaction.channel):
            embed = create_error_embed("Unauthorized.", self.config.get_embed_color())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        prompts = self.config.get("prompts", {})

        if action == "view":
            global_prompt = prompts.get("global", "None")
            personal_prompt = prompts.get("users", {}).get(str(interaction.user.id), "Default")
            fields = [
                ("Global", global_prompt[:1000], False),
                ("Personal", personal_prompt[:1000], False)
            ]
            embed = create_embed(title="Prompts", color=self.config.get_embed_color(), fields=fields)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if action == "clear":
            user_prompts = prompts.setdefault("users", {})
            user_key = str(interaction.user.id)
            if user_key in user_prompts:
                del user_prompts[user_key]
                self.config.set("prompts", prompts)
            embed = create_success_embed(title="Reset", message="Prompt reset to default.", color=self.config.get_embed_color())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if action == "set":
            if not text or not text.strip():
                embed = create_error_embed("Please provide prompt text.", self.config.get_embed_color())
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            if scope == "global":
                if not self.config.is_owner(interaction.user.id):
                    embed = create_error_embed("Unauthorized.", self.config.get_embed_color())
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
                prompts["global"] = text.strip()
                self.config.set("prompts", prompts)
                embed = create_success_embed(title="Saved", message="Global prompt saved.", color=self.config.get_embed_color())
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            user_prompts = prompts.setdefault("users", {})
            user_prompts[str(interaction.user.id)] = text.strip()
            self.config.set("prompts", prompts)
            embed = create_success_embed(title="Saved", message="Personal prompt saved.", color=self.config.get_embed_color())
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @set_group.command(name="usage_limit", description="Quotas")
    @app_commands.describe(
        target_type="Type",
        target_id="ID",
        daily_quota="Limit"
    )
    @app_commands.choices(target_type=[
        app_commands.Choice(name="user", value="user"),
        app_commands.Choice(name="role", value="role")
    ])
    async def set_usage_limit(self, interaction: discord.Interaction, target_type: str, target_id: str, daily_quota: int):
        if not self.config.is_owner(interaction.user.id):
            embed = create_error_embed("Unauthorized.", self.config.get_embed_color())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if not target_id.isdigit():
            embed = create_error_embed("Invalid identifier.", self.config.get_embed_color())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        usage_limits = self.config.get("usage_limits", {})
        bucket = usage_limits.setdefault(f"{target_type}s", {})
        bucket[target_id] = max(0, daily_quota)
        self.config.set("usage_limits", usage_limits)

        embed = create_success_embed(
            title="Saved",
            message=f"Daily limit for {target_type} `{target_id}` set to `{max(0, daily_quota)}`.",
            color=self.config.get_embed_color()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    config: ConfigManager = bot.config
    await bot.add_cog(AdminCog(bot, config))
