# Python AI Discord Bot

A Discord AI bot built with Python 3.11+ and discord.py v2. Features multi-provider text generation, OCR image parsing, file attachment analysis, real-time voice speech synthesis, administrative controls, and interactive components.

---

## Features

- Multi-Provider LLM Integration: Groq, Google Gemini, DeepSeek, Anthropic Claude, OpenAI, Together AI, OpenRouter.
- Multimodal OCR & Vision: Attach images (`.png`, `.jpg`, `.jpeg`, `.webp`, `.gif`) for direct text extraction, analysis, and visual reasoning.
- Document & Code Ingestion: Attach text files (`.txt`, `.py`, `.json`, `.csv`, `.md`, `.log`, `.cpp`, `.js`, etc.) to automatically include file content in prompts.
- Real-Time Voice Synthesis: Automatically converts responses to audio in connected voice channels using Deepgram, OpenAI TTS, or ElevenLabs.
- Speech Filtering: Configurable filters to strip asterisks (`*action*`), brackets (`[note]`), parentheses, braces, or code blocks from spoken voice audio.
- Dynamic Configuration: Update prefixes, default models, memory retention, rate limits, daily quotas, system prompts, and allowed channels live via slash commands.
- Interactive Help & Interface: Dropdown category selection built on Discord UI components and neutral container embeds.
- Console Telemetry: Formatted execution logging with timestamps, latencies, and error tracking.

---

## Installation

### Prerequisites
- Python 3.11 or higher
- Git

### Setup

1. Clone the repository:
```bash
git clone https://github.com/sattiva/ai-python-bot.git
cd ai-python-bot
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux / macOS
.venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
Copy `.env.example` to `.env` and insert your Discord bot token:
```env
DISCORD_TOKEN=your_discord_bot_token_here
```

5. Configure application settings:
Copy `config.json.example` to `config.json`:
```bash
cp config.json.example config.json  # Linux / macOS
copy config.json.example config.json # Windows
```

6. Start the bot:
```bash
python main.py
```

---

## Configuration

All runtime settings are managed inside `config.json` or dynamically modified through `/set` slash commands.

### Configuration Schema (`config.json`)

```json
{
  "owner_ids": [423953946827161610],
  "default_embed_color": "0x2B2D31",
  "api_keys": {
    "groq": "",
    "gemini": "",
    "deepseek": "",
    "anthropic": "",
    "openai": "",
    "together": "",
    "openrouter": "",
    "deepgram": "",
    "elevenlabs": ""
  },
  "whitelists": {
    "users": [],
    "roles": [],
    "channels": []
  },
  "prompts": {
    "global": "You are a concise, direct, and helpful assistant.",
    "users": {}
  },
  "rate_limits": {
    "seconds": 5,
    "bypass_users": [],
    "bypass_roles": []
  },
  "tts_settings": {
    "provider": "deepgram",
    "voice_id": "aura-asteria-en"
  },
  "embed_settings": {
    "color": "0x2B2D31",
    "mode": "standard"
  },
  "active_models": {
    "groq": "llama-3.3-70b-versatile",
    "gemini": "gemini-2.5-flash",
    "deepseek": "deepseek-chat",
    "anthropic": "claude-3-5-sonnet-20241022",
    "openai": "gpt-4o-mini",
    "together": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
    "openrouter": "openai/gpt-4o-mini"
  },
  "active_provider": "gemini",
  "active_model": "gemini-2.5-flash",
  "usage_limits": {
    "users": {},
    "roles": {}
  },
  "prefix": ",",
  "memory_limit": 6,
  "tts_filters": {
    "asterisks": true,
    "brackets": true,
    "parentheses": false,
    "braces": false,
    "code": true
  }
}
```

---

## Command Reference

### Prefix Commands

| Command | Arguments | Description |
|---|---|---|
| `<prefix>ai` | `<prompt> [attachments]` | Query active model with optional file or image attachments. Auto-speaks if connected to a voice channel. |
| `<prefix>ask` | `<prompt> [attachments]` | Alias for `<prefix>ai`. |
| `<prefix>help` | None | Open interactive category-based help menu. |

### AI Slash Commands

| Command | Arguments | Description |
|---|---|---|
| `/ai model` | `[provider] [model_name]` | View active provider and model, or switch to a designated model. |
| `/ai history` | `<action: view\|clear\|export>` | View recent conversation turns, reset history, or export logs to a text file. |
| `/ai summarize` | `[target] [lines]` | Generate a structured bullet-point summary of recent channel messages. |

### Voice Commands

| Command | Arguments | Description |
|---|---|---|
| `/join` | None | Connect bot to your active voice channel. |
| `/leave` | None | Disconnect bot from the voice channel. |

### Settings Slash Commands (`/set`, Owner Only)

| Command | Arguments | Description |
|---|---|---|
| `/set api_key` | `<provider> <key>` | Save API key for a target provider (Groq, Gemini, DeepSeek, Anthropic, OpenAI, Together, OpenRouter, Deepgram, ElevenLabs). |
| `/set prefix` | `<prefix>` | Update the command prefix dynamically. |
| `/set provider` | `<provider>` | Change default active LLM provider. |
| `/set memory` | `<count>` | Set the maximum number of recent conversation messages retained in context. |
| `/set owner` | `<action: add\|remove> <user>` | Add or remove bot administrator IDs. |
| `/set channel` | `<channel> <allow\|remove>` | Restrict bot commands to specific whitelisted channels. |
| `/set cooldown` | `<action: set\|bypass_user\|bypass_role> [seconds] [user] [role]` | Set global command rate limit interval or configure bypass rules. |
| `/set tts` | `[provider] [voice] [speed] [filter_target] [filter_enabled]` | Configure active TTS engine, voice identifier, speech playback speed multiplier, and speech text filters. |
| `/set embed` | `[color] [mode]` | Update default embed accent color (hex) and presentation format (standard / plain). |
| `/set usage_limit` | `<target_type: user\|role> <target_id> <daily_quota>` | Enforce maximum daily request limits for users or roles. |
| `/set prompt` | `<action: view\|set\|clear> [text] [scope: personal\|global]` | Configure system instructions globally or per-user. |

### System Commands

| Command | Arguments | Description |
|---|---|---|
| `/stats` | None | Display gateway latency, memory usage, voice status, query count, and server metrics. |
| `/help` | None | Open interactive help view with category selection dropdowns. |

---

## Speech Filtering for Voice

When connected to a voice channel, the bot cleans the text before passing it to the TTS synthesizer. You can toggle filters to ignore:

- Asterisks (`*action*`): Roleplay or action descriptions.
- Brackets (`[text]`): System references or footnotes.
- Parentheses (`(text)`): Parenthetical notes.
- Braces (`{text}`): Structured objects or metadata.
- Code blocks (`` `code` `` or ```` ```code``` ````): Source code snippets.

Example:
```
/set tts filter_target:asterisks filter_enabled:True
```

---

## File Structure

```
.
├── .env.example
├── .gitignore
├── config.json.example
├── requirements.txt
├── main.py
├── utils/
│   ├── config.py
│   ├── providers.py
│   ├── tts.py
│   └── ui.py
└── cogs/
    ├── admin.py
    ├── ai.py
    ├── voice.py
    ├── stats.py
    └── help.py
```

---

## License

MIT License.
