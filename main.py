import os
import sys
import asyncio
import logging
from dotenv import load_dotenv
import discord
from discord.ext import commands
from utils.config import ConfigManager

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("System")

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    logger.critical("DISCORD_TOKEN is missing from environment variables.")
    sys.exit(1)

config = ConfigManager("config.json")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True

def get_prefix(client, message):
    return client.config.get_prefix()

bot = commands.Bot(command_prefix=get_prefix, intents=intents, help_command=None)
bot.config = config

COGS = [
    "cogs.admin",
    "cogs.ai",
    "cogs.voice",
    "cogs.stats",
    "cogs.help"
]

@bot.event
async def on_ready():
    if not config.get("owner_ids"):
        app_info = await bot.application_info()
        if app_info.owner:
            config.add_owner(app_info.owner.id)

    try:
        synced = await bot.tree.sync()
        logger.info(f"Connected as {bot.user} (ID: {bot.user.id}). Synchronized {len(synced)} application commands.")
    except Exception as exc:
        logger.error(f"Command synchronization failed: {exc}")

@bot.event
async def on_command(ctx: commands.Context):
    logger.info(f"Command executed: '{ctx.message.content}' by {ctx.author} (ID: {ctx.author.id}) in #{getattr(ctx.channel, 'name', 'DM')}")

@bot.event
async def on_command_error(ctx: commands.Context, error: Exception):
    if isinstance(error, commands.CommandNotFound):
        return
    logger.error(f"Command error in '{ctx.message.content}': {error}")

async def main():
    async with bot:
        for cog in COGS:
            await bot.load_extension(cog)
            logger.info(f"Loaded extension: {cog}")
        await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
