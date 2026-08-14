```markdown
# AGENT.md

## Core Guidelines
* Write zero inline comments (`//`, `#`, `/* */`). Code must be entirely self-documenting through direct naming and structural clarity.
* Eliminate unnecessary abstractions, complex inheritance hierarchies, and boilerplate wrappers.
* Prefer clean object lookups, direct operations, and tuple or structured error patterns.
* Keep implementations concise, high-performance, and resistant to common vulnerabilities.

---

## Security Essentials

* **Input Safety:** Validate inputs at entry boundaries. Parameterize all SQL/database queries and escape untrusted data before command execution.
* **Secret Handling:** Require ambient environment variables for credentials. Fail immediately on execution if required keys are missing.
* **Token Verification:** Perform cryptographic constant-time comparisons when validating HMAC signatures or auth tokens to prevent timing attacks.
* **Data Sanitization:** Never echo raw errors or return entire user records. Filter sensitive keys before serialization.

---

## Pattern Rules by Example

### 1. JavaScript / Node.js (Express Auth Middleware)
*Fail-fast environment checks and timing-safe header validation.*

```javascript
import crypto from 'crypto';

const SECRET_KEY = process.env.API_SECRET;
if (!SECRET_KEY) throw new Error('FATAL: API_SECRET missing');

export const authGuard = (req, res, next) => {
  const token = req.headers['x-api-key'];
  if (!token || typeof token !== 'string') return res.status(401).json({ error: 'Unauthorized' });

  const tokenBuffer = Buffer.from(token);
  const secretBuffer = Buffer.from(SECRET_KEY);

  if (tokenBuffer.length !== secretBuffer.length || !crypto.timingSafeEqual(tokenBuffer, secretBuffer)) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  next();
};

```

---

### 2. TypeScript (Discord.js Command Handler)

*Object map routing without switch statement chains.*

```typescript
import { Client, GatewayIntentBits, Interaction } from 'discord.js';

const client = new Client({ intents: [GatewayIntentBits.Guilds] });

const commands: Record<string, (i: Interaction) => Promise<void>> = {
  ping: async (i) => {
    if (i.isChatInputCommand()) await i.reply({ content: 'pong', ephemeral: true });
  },
  status: async (i) => {
    if (i.isChatInputCommand()) await i.reply({ content: 'operational', ephemeral: true });
  }
};

client.on('interactionCreate', async (interaction) => {
  if (!interaction.isChatInputCommand()) return;
  const handler = commands[interaction.commandName];
  if (handler) await handler(interaction);
});

client.login(process.env.BOT_TOKEN);

```

---

### 3. Go (Web API & Parameterized SQLite Query)

*Tuple-style error handling, explicit struct instantiation, and safe database access.*

```go
package main

import (
	"database/sql"
	"net/http"
	_ "[github.com/mattn/go-sqlite3](https://github.com/mattn/go-sqlite3)"
)

type User struct {
	ID    string `json:"id"`
	Email string `json:"email"`
}

func getUser(db *sql.DB, id string) (*User, error) {
	var u User
	err := db.QueryRow("SELECT id, email FROM users WHERE id = ? AND active = 1", id).Scan(&u.ID, &u.Email)
	if err != nil {
		return nil, err
	}
	return &u, nil
}

func handleUser(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		id := r.URL.Query().Get("id")
		if id == "" {
			http.Error(w, "missing id", http.StatusBadRequest)
			return
		}
		user, err := getUser(db, id)
		if err != nil {
			http.Error(w, "not found", http.StatusNotFound)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"id":"` + user.ID + `","email":"` + user.Email + `"}`))
	}
}

```

---

### 4. C++ (Memory-Mapped File Loader)

*RAII, direct system calls, zero superfluous allocation logic.*

```cpp
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
#include <utility>

class MappedFile {
    int fd = -1;
    void* data = nullptr;
    size_t size = 0;

public:
    MappedFile(const char* path) {
        fd = open(path, O_RDONLY);
        if (fd < 0) return;
        struct stat sb;
        if (fstat(fd, &sb) < 0) return;
        size = sb.st_size;
        data = mmap(nullptr, size, PROT_READ, MAP_PRIVATE, fd, 0);
    }

    ~MappedFile() {
        if (data && data != MAP_FAILED) munmap(data, size);
        if (fd >= 0) close(fd);
    }

    const char* get() const { return static_cast<const char*>(data); }
    size_t len() const { return size; }
};

```

---

### 5. Python (Async Rate-Limited Web Scraping)

*Async context management, tuple error returns, and connection pooling.*

```python
import asyncio
import aiohttp
import os

async def fetch_url(session, url):
    try:
        async with session.get(url, timeout=5) as response:
            if response.status == 200:
                return None, await response.text()
            return f"HTTP {response.status}", None
    except Exception as e:
        return str(e), None

async def process_urls(urls):
    connector = aiohttp.TCPConnector(limit=10)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [fetch_url(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        return results

```

---

### 6. Rust (Fast Safe HTTP State Guard)

*Zero-copy data checks, direct pattern matching, zero extra dependencies.*

```rust
use std::collections::HashMap;
use std::sync::Arc;

pub struct AuthCache {
    tokens: HashMap<String, u64>,
}

impl AuthCache {
    pub fn validate(&self, token: &str, now: u64) -> bool {
        match self.tokens.get(token) {
            Some(&expiry) if expiry > now => true,
            _ => false,
        }
    }
}

pub fn check_request(cache: Arc<AuthCache>, token: &str, now: u64) -> Result<(), &'static str> {
    if cache.validate(token, now) {
        Ok(())
    } else {
        Err("Unauthorized")
    }
}

```

---

### 7. SQL (PostgreSQL Dynamic Schema Optimization)

*Atomic update, indexes on queried keys, and automated expiration cleanup.*

```sql
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NOT NULL,
    token_hash VARCHAR(64) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sessions_token_lookup 
ON user_sessions (token_hash) 
WHERE expires_at > NOW();

INSERT INTO user_sessions (user_id, token_hash, expires_at)
VALUES (1001, 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', NOW() + INTERVAL '24 hours')
ON CONFLICT (id) DO UPDATE 
SET expires_at = EXCLUDED.expires_at;

```

```

```

# AGENTS.md Task Description & Architecture Specification

## Framework & Structural Requirements
* **Framework:** Python 3.11+ utilizing `discord.py` (v2.x).
* **UI Architecture:** Use Discord UI Components V2 (`ActionRow`, `Button`, `Select`) and Containers V2 structures for all embeds and message responses.
* **Code Formatting Guidelines:** 
  * Structure the bot across separate files (e.g., `main.py`, `cogs/ai.py`, `cogs/admin.py`, `cogs/voice.py`, `utils/config.py`).
  * Strict constraint: Do NOT write any inline comments (`#` comment lines) anywhere in the Python files.
  * Strict constraint: Do NOT include any techy, gamer, or AI slang/jargon in the code base, command outputs, or user-facing messages.

---

## Architecture & Data Persistence

### Secret Storage (`.env`)
* `DISCORD_TOKEN`: Bot application token.

### Configuration Engine (`config.json`)
Maintain a structured JSON configuration storing:
* `owner_ids`: Array of Discord user IDs with full administrative privileges.
* `default_embed_color`: Colorless/neutral hex code (default `0x2B2D31`).
* `api_keys`: Map storing credentials for external API providers (`groq`, `gemini`, `deepseek`, `anthropic`, `openai`, `together`, `openrouter`, `deepgram`).
* `whitelists`: Separate tracking arrays for whitelisted user IDs, role IDs, and target channel IDs.
* `prompts`: Global system default prompt string and individual user-level prompt overrides.
* `rate_limits`: Default global cooldown duration (default: 5 seconds) and user/role bypass arrays.
* `tts_settings`: Configured active TTS provider (defaulting to Deepgram) and voice ID parameters.

---

## Required Command Specifications

### 1. AI Text Queries
* **Prefix Commands:** `.ai <prompt>` and `.ask <prompt>`.
* Restricted to whitelisted users/roles if a whitelist rule is active.
* Restricted to whitelisted channels if channel restriction is active.
* Applies rate limiting checks (default 5s) unless the executing user or their role is set in the bypass list.

### 2. Owner Administrative Management (`/set` Slash Subcommands)
* `/set api_key <provider> <key>`: Select from providers including Groq, Gemini, DeepSeek, Anthropic, OpenAI, Together, OpenRouter, and Deepgram. Restricted strictly to `owner_ids`.
* `/set channel <channel> [restriction_mode]`: Set target channels where AI commands are active.
* `/set rate_limit seconds <int>`: Updates global question cooldown interval.
* `/set rate_limit bypass user <user>` / `/set rate_limit bypass role <role>`: Toggle rate limit bypass statuses.
* `/set tts_api provider <provider> voice <voice_id>`: Set active TTS provider and voice identifier (Deepgram enabled by default).
* `/set embed color <hex_code>`: Dynamically updates the global embed accent color.
* `/set embed mode <response_type>`: Customizes the layout structure for bot responses.

### 3. System Prompt Management
* `/set prompt set <text> [scope: global|personal]`: Configures system prompts. Available to owners (for global) and whitelisted users (for personal).
* `/set prompt view`: Displays active system prompt configuration using Container V2 layout.
* `/set prompt clear`: Resets user-specific prompt overrides back to the global default.

### 4. Voice Channel (VC) Integration
* `/join`: Connects the bot to the executor's active Voice Channel.
* `/leave`: Disconnects the bot from the Voice Channel.
* While connected in a VC, executing `.ai` or `.ask` sends the standard text response to the chat channel while simultaneously converting the response to audio via the configured TTS provider (Deepgram) and streaming it live into the voice channel.

### 5. Additional System Commands
* `/ai model [provider] [model_name]`: Allows whitelisted users to switch active underlying LLM models for a given provider.
* `/ai history [action: view|clear|export]`: View, clear, or export active conversational context logs.
* `/set usage_limit <user|role> <daily_quota>`: Owner command to enforce daily message allocations.
* `/ai summarize [channel/message_link] [length]`: Generates executive summaries of recent channel messages inside Container V2 layout embeds.
* `/bot stats`: Displays active API latencies, voice connection status, total prompts processed, active rate limits, and memory usage in a colorless Container V2 embed.