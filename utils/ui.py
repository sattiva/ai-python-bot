import discord
from discord.ui import View, Button, Select
from discord.http import Route, MultipartParameters

FLAG_COMPONENTS_V2 = 1 << 15

class ContainerV2:
    def __init__(self, accent_color: int = 0x2B2D31, spoiler: bool = False):
        self.accent_color = accent_color
        self.spoiler = spoiler
        self.components: list[dict] = []

    def add_text(self, content: str) -> "ContainerV2":
        self.components.append({"type": 10, "content": content})
        return self

    def add_separator(self, divider: bool = True) -> "ContainerV2":
        self.components.append({"type": 14, "divider": divider})
        return self

    def add_section(self, content: str, accessory: dict | None = None) -> "ContainerV2":
        sec = {"type": 9, "components": [{"type": 10, "content": content}]}
        if accessory:
            sec["accessory"] = accessory
        self.components.append(sec)
        return self

    def add_action_row(self, components: list[dict]) -> "ContainerV2":
        self.components.append({"type": 1, "components": components})
        return self

    def to_dict(self) -> dict:
        return {
            "type": 17,
            "accent_color": self.accent_color,
            "spoiler": self.spoiler,
            "components": self.components
        }

def button_dict(label: str, custom_id: str, style: int = 2, emoji: dict | None = None, disabled: bool = False) -> dict:
    btn = {
        "type": 2,
        "style": style,
        "label": label,
        "custom_id": custom_id,
        "disabled": disabled
    }
    if emoji:
        btn["emoji"] = emoji
    return btn

def select_option(label: str, value: str, description: str | None = None, default: bool = False, emoji: dict | None = None) -> dict:
    opt = {"label": label, "value": value, "default": default}
    if description:
        opt["description"] = description
    if emoji:
        opt["emoji"] = emoji
    return opt

def select_dict(custom_id: str, options: list[dict], placeholder: str = "Select a category") -> dict:
    return {
        "type": 3,
        "custom_id": custom_id,
        "placeholder": placeholder,
        "options": options
    }

async def send_container_response(
    target,
    container: ContainerV2,
    view: View | None = None,
    ephemeral: bool = False,
    bot: discord.Client | None = None
) -> discord.Message | None:
    container_dict = container.to_dict()

    if isinstance(target, discord.Interaction):
        if not target.response.is_done():
            try:
                payload = {
                    "type": 4,
                    "data": {
                        "flags": FLAG_COMPONENTS_V2 | (64 if ephemeral else 0),
                        "components": [container_dict]
                    }
                }
                adapter = target._client._connection.http
                route = Route("POST", f"/interactions/{target.id}/{target.token}/callback")
                await adapter.request(route, json=payload)
                return None
            except Exception:
                pass
        else:
            try:
                payload = {
                    "flags": FLAG_COMPONENTS_V2 | (64 if ephemeral else 0),
                    "components": [container_dict]
                }
                adapter = target._client._connection.http
                route = Route("PATCH", f"/webhooks/{target.application_id}/{target.token}/messages/@original")
                await adapter.request(route, json=payload)
                return None
            except Exception:
                pass

    channel = target.channel if hasattr(target, "channel") else target
    http_client = bot.http if bot else (target._state.http if hasattr(target, "_state") else None)

    if http_client and hasattr(channel, "id"):
        try:
            payload = {
                "flags": FLAG_COMPONENTS_V2,
                "components": [container_dict]
            }
            if hasattr(target, "message") and target.message:
                payload["message_reference"] = {
                    "message_id": target.message.id,
                    "channel_id": channel.id,
                    "fail_if_not_exists": False
                }
            params = MultipartParameters(payload=payload)
            msg_data = await http_client.send_message(channel.id, params=params)
            state = target._state if hasattr(target, "_state") else bot._connection
            return discord.Message(state=state, channel=channel, data=msg_data)
        except Exception:
            pass

    embed = build_fallback_embed(container)
    if isinstance(target, discord.Interaction):
        if not target.response.is_done():
            await target.response.send_message(embed=embed, view=view, ephemeral=ephemeral)
        else:
            await target.followup.send(embed=embed, view=view, ephemeral=ephemeral)
        return None

    if hasattr(target, "reply"):
        return await target.reply(embed=embed, view=view, mention_author=False)
    return await channel.send(embed=embed, view=view)

def build_fallback_embed(container: ContainerV2) -> discord.Embed:
    embed = discord.Embed(color=container.accent_color)
    text_blocks = []
    for comp in container.components:
        comp_type = comp.get("type")
        if comp_type == 10:
            text_blocks.append(comp.get("content", ""))
        elif comp_type == 9:
            inner = comp.get("components", [])
            for item in inner:
                if item.get("type") == 10:
                    text_blocks.append(item.get("content", ""))
    embed.description = "\n\n".join(text_blocks)
    return embed

class ResponseView(View):
    def __init__(self, timeout: float = 180.0):
        super().__init__(timeout=timeout)

class VoiceControlView(View):
    def __init__(self, voice_client: discord.VoiceClient, timeout: float = 120.0):
        super().__init__(timeout=timeout)
        self.voice_client = voice_client

    @discord.ui.button(label="Stop Audio", style=discord.ButtonStyle.secondary, emoji="❌")
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.voice_client and self.voice_client.is_connected() and self.voice_client.is_playing():
            self.voice_client.stop()
            button.disabled = True
            button.label = "Audio Stopped"
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
        description=f"> {message}",
        color=color
    )

def create_success_embed(title: str, message: str, color: int = 0x2B2D31) -> discord.Embed:
    return create_embed(
        title=title,
        description=f"> {message}",
        color=color
    )
