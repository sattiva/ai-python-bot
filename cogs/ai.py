import discord
from discord.ext import commands
from discord import app_commands
import io
import re
import base64
from utils.config import ConfigManager
from utils.providers import generate_response
from utils.tts import synthesize_speech, create_audio_source
from utils.ui import create_embed, create_error_embed, create_success_embed, VoiceControlView, ContainerV2, send_container_response

import logging
logger = logging.getLogger("AI")

class AICog(commands.Cog):
    def __init__(self, bot: commands.Bot, config: ConfigManager):
        self.bot = bot
        self.config = config
        self.total_prompts_processed = 0

    async def _handle_ai_query(self, ctx: commands.Context, prompt: str) -> None:
        file_contents = []
        images = []
        image_extensions = (".png", ".jpg", ".jpeg", ".webp", ".gif")

        if ctx.message and ctx.message.attachments:
            for attachment in ctx.message.attachments:
                try:
                    raw_bytes = await attachment.read()
                    filename_lower = attachment.filename.lower()
                    is_image = filename_lower.endswith(image_extensions) or (attachment.content_type and attachment.content_type.startswith("image/"))

                    if is_image:
                        b64_str = base64.b64encode(raw_bytes).decode("utf-8")
                        mime = attachment.content_type if (attachment.content_type and attachment.content_type.startswith("image/")) else "image/png"
                        images.append((mime, b64_str))
                        logger.info(f"Loaded image for OCR/vision: {attachment.filename} ({len(raw_bytes)} bytes)")
                    else:
                        text_content = raw_bytes.decode("utf-8", errors="replace")
                        file_contents.append(f"--- File: {attachment.filename} ---\n{text_content}\n--- End File ---")
                        logger.info(f"Read text attachment: {attachment.filename} ({len(text_content)} chars)")
                except Exception as file_err:
                    logger.error(f"Failed processing attachment {attachment.filename}: {file_err}")

        full_prompt = prompt.strip() if prompt else ""
        if file_contents:
            joined_files = "\n\n".join(file_contents)
            full_prompt = f"{joined_files}\n\n{full_prompt}" if full_prompt else joined_files

        if not full_prompt and not images:
            embed = create_error_embed("Please provide a prompt, image, or text file.", self.config.get_embed_color())
            await ctx.reply(embed=embed, mention_author=False)
            return

        if not self.config.is_whitelisted(ctx.author, ctx.channel):
            embed = create_error_embed("Unauthorized.", self.config.get_embed_color())
            await ctx.reply(embed=embed, mention_author=False)
            return

        allowed_rate, remaining = self.config.check_rate_limit(ctx.author)
        if not allowed_rate:
            embed = create_error_embed(f"Wait {remaining}s.", self.config.get_embed_color())
            await ctx.reply(embed=embed, mention_author=False)
            return

        allowed_usage, current_count, max_limit = self.config.check_daily_usage(ctx.author)
        if not allowed_usage:
            embed = create_error_embed(f"Daily limit reached ({current_count}/{max_limit}).", self.config.get_embed_color())
            await ctx.reply(embed=embed, mention_author=False)
            return

        self.config.record_rate_limit(ctx.author)
        self.config.record_daily_usage(ctx.author)
        self.total_prompts_processed += 1

        provider = self.config.get("active_provider", "gemini")
        model = self.config.get("active_model") or self.config.get_active_model(provider)
        api_key = self.config.get_api_key(provider)

        if not api_key:
            embed = create_error_embed(f"API key missing for provider: {provider}", self.config.get_embed_color())
            await ctx.reply(embed=embed, mention_author=False)
            return

        system_prompt = self.config.get_system_prompt(ctx.author.id)
        history = self.config.get_history(ctx.author.id)

        logger.info(f"Query dispatching to {provider} ({model}) for {ctx.author.name} (images: {len(images)})")

        async with ctx.typing():
            err, response_text = await generate_response(
                provider=provider,
                api_key=api_key,
                model=model,
                system_prompt=system_prompt,
                messages=history,
                prompt=full_prompt,
                images=images
            )

        if err:
            logger.error(f"Provider error ({provider}): {err}")
            embed = create_error_embed(f"Error ({provider}): {err}", self.config.get_embed_color())
            await ctx.reply(embed=embed, mention_author=False)
            return

        if not response_text:
            embed = create_error_embed("Empty response.", self.config.get_embed_color())
            await ctx.reply(embed=embed, mention_author=False)
            return

        self.config.append_history(ctx.author.id, "user", full_prompt[:500])
        self.config.append_history(ctx.author.id, "assistant", response_text)

        color = self.config.get_embed_color()
        voice_client = ctx.guild.voice_client if ctx.guild else None
        voice_view = VoiceControlView(voice_client) if (voice_client and voice_client.is_connected()) else None

        container = ContainerV2(accent_color=color)
        container.add_text(response_text)
        container.add_separator(divider=True)
        container.add_text(f"-# {provider} / {model}")

        await send_container_response(ctx, container, view=voice_view, bot=self.bot)

        voice_client = ctx.guild.voice_client if ctx.guild else None
        if voice_client and voice_client.is_connected():
            tts_settings = self.config.get("tts_settings", {})
            tts_provider = tts_settings.get("provider", "deepgram")
            tts_key = self.config.get_api_key(tts_provider)
            voice_id = tts_settings.get("voice_id", "aura-asteria-en")
            tts_speed = float(tts_settings.get("speed", 1.0))
            tts_fx = tts_settings.get("audio_fx", "none")
            tts_filters = self.config.get("tts_filters", {"asterisks": True, "brackets": True, "code": True})

            if not tts_key:
                logger.warning(f"TTS API key missing for provider '{tts_provider}'")
            else:
                logger.info(f"Synthesizing voice via {tts_provider} ({voice_id}, speed={tts_speed}x, fx={tts_fx})")
                tts_err, audio_bytes = await synthesize_speech(
                    provider=tts_provider,
                    api_key=tts_key,
                    text=response_text,
                    voice_id=voice_id,
                    filters=tts_filters,
                    speed=tts_speed
                )
                if tts_err:
                    logger.error(f"TTS synthesis error: {tts_err}")
                elif audio_bytes:
                    try:
                        if voice_client.is_playing():
                            voice_client.stop()
                        audio_source = create_audio_source(audio_bytes, speed=tts_speed, audio_fx=tts_fx)
                        voice_client.play(
                            audio_source,
                            after=lambda err: logger.error(f"Voice playback error: {err}") if err else None
                        )
                        logger.info("Voice audio streamed to channel")
                    except Exception as play_exc:
                        logger.error(f"Voice playback initialization failed: {play_exc}")

    @commands.command(name="ai")
    async def ai_prefix(self, ctx: commands.Context, *, prompt: str = ""):
        await self._handle_ai_query(ctx, prompt)

    @commands.command(name="ask")
    async def ask_prefix(self, ctx: commands.Context, *, prompt: str = ""):
        await self._handle_ai_query(ctx, prompt)

    ai_group = app_commands.Group(name="ai", description="AI")

    @ai_group.command(name="model", description="Models")
    @app_commands.describe(provider="Provider", model_name="Model")
    @app_commands.choices(provider=[
        app_commands.Choice(name="Groq", value="groq"),
        app_commands.Choice(name="Gemini", value="gemini"),
        app_commands.Choice(name="DeepSeek", value="deepseek"),
        app_commands.Choice(name="Anthropic", value="anthropic"),
        app_commands.Choice(name="OpenAI", value="openai"),
        app_commands.Choice(name="Together", value="together"),
        app_commands.Choice(name="OpenRouter", value="openrouter")
    ])
    async def ai_model(self, interaction: discord.Interaction, provider: str | None = None, model_name: str | None = None):
        if not self.config.is_whitelisted(interaction.user, interaction.channel):
            embed = create_error_embed("Unauthorized.", self.config.get_embed_color())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if not provider and not model_name:
            curr_p = self.config.get("active_provider", "gemini")
            curr_m = self.config.get("active_model", self.config.get_active_model(curr_p))
            embed = create_embed(
                title="Active Model",
                description=f"Provider: `{curr_p}`\nModel: `{curr_m}`",
                color=self.config.get_embed_color()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if provider:
            p_lower = provider.lower()
            self.config.set("active_provider", p_lower)
            if model_name:
                m_clean = model_name.strip()
                self.config.set("active_model", m_clean)
                self.config.set_active_model(p_lower, m_clean)
            else:
                m_existing = self.config.get_active_model(p_lower)
                if m_existing:
                    self.config.set("active_model", m_existing)
        elif model_name:
            m_clean = model_name.strip()
            self.config.set("active_model", m_clean)
            curr_p = self.config.get("active_provider", "gemini")
            self.config.set_active_model(curr_p, m_clean)

        active_p = self.config.get("active_provider", "gemini")
        active_m = self.config.get("active_model", "")

        embed = create_success_embed(
            title="Saved",
            message=f"Active provider set to `{active_p}` with model `{active_m}`.",
            color=self.config.get_embed_color()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @ai_group.command(name="history", description="History")
    @app_commands.describe(action="Action")
    @app_commands.choices(action=[
        app_commands.Choice(name="view", value="view"),
        app_commands.Choice(name="clear", value="clear"),
        app_commands.Choice(name="export", value="export")
    ])
    async def ai_history(self, interaction: discord.Interaction, action: str):
        if not self.config.is_whitelisted(interaction.user, interaction.channel):
            embed = create_error_embed("Unauthorized.", self.config.get_embed_color())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        history = self.config.get_history(interaction.user.id)

        if action == "clear":
            self.config.clear_history(interaction.user.id)
            embed = create_success_embed(
                title="Cleared",
                message="History cleared.",
                color=self.config.get_embed_color()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if not history:
            embed = create_embed(
                title="History",
                description="No history.",
                color=self.config.get_embed_color()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if action == "view":
            lines = []
            for item in history[-6:]:
                role = item["role"].capitalize()
                snippet = item["content"][:100] + ("..." if len(item["content"]) > 100 else "")
                lines.append(f"**{role}**: {snippet}")
            embed = create_embed(
                title="History",
                description="\n\n".join(lines),
                color=self.config.get_embed_color(),
                footer=f"Total: {len(history)}"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if action == "export":
            export_text = ""
            for item in history:
                export_text += f"[{item['role'].upper()}]\n{item['content']}\n\n"
            file_data = io.BytesIO(export_text.encode("utf-8"))
            file = discord.File(file_data, filename="history.txt")
            await interaction.response.send_message(content="Exported history:", file=file, ephemeral=True)

    @ai_group.command(name="summarize", description="Summarize")
    @app_commands.describe(
        target="Target",
        length="Lines"
    )
    async def ai_summarize(self, interaction: discord.Interaction, target: str | None = None, length: int = 5):
        if not self.config.is_whitelisted(interaction.user, interaction.channel):
            embed = create_error_embed("Unauthorized.", self.config.get_embed_color())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await interaction.response.defer(thinking=True)

        target_channel = interaction.channel
        if target:
            channel_match = re.search(r"<#(\d+)>", target)
            if channel_match:
                cid = int(channel_match.group(1))
                found = interaction.guild.get_channel(cid) if interaction.guild else None
                if found:
                    target_channel = found
            elif target.isdigit():
                found = interaction.guild.get_channel(int(target)) if interaction.guild else None
                if found:
                    target_channel = found

        if not hasattr(target_channel, "history"):
            embed = create_error_embed("Cannot read history.", self.config.get_embed_color())
            await interaction.followup.send(embed=embed)
            return

        collected_messages = []
        async for msg in target_channel.history(limit=50):
            if not msg.author.bot and msg.content:
                collected_messages.append(f"{msg.author.display_name}: {msg.content}")

        if not collected_messages:
            embed = create_error_embed("No messages found.", self.config.get_embed_color())
            await interaction.followup.send(embed=embed)
            return

        collected_messages.reverse()
        corpus = "\n".join(collected_messages)

        prompt = f"Provide a clean, direct summary in exactly {length} bullet points based on the following conversation:\n\n{corpus}"

        provider = self.config.get("default_provider", "groq")
        api_key = self.config.get_api_key(provider)
        model = self.config.get_active_model(provider)

        err, summary_text = await generate_response(
            provider=provider,
            api_key=api_key,
            model=model,
            system_prompt="Provide concise and direct summaries without filler.",
            messages=[],
            prompt=prompt
        )

        if err or not summary_text:
            embed = create_error_embed(f"Failed: {err or 'Empty'}", self.config.get_embed_color())
            await interaction.followup.send(embed=embed)
            return

        embed = create_embed(
            title=f"Summary: #{getattr(target_channel, 'name', 'Direct')}",
            description=summary_text,
            color=self.config.get_embed_color(),
            footer=f"{len(collected_messages)} messages"
        )
        await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    config: ConfigManager = bot.config
    await bot.add_cog(AICog(bot, config))
