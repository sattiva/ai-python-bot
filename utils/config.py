import json
import os
import time
from datetime import datetime, timezone

class ConfigManager:
    def __init__(self, path: str = "config.json"):
        self.path = path
        self.rate_limit_timestamps: dict[int, float] = {}
        self.conversations: dict[int, list[dict[str, str]]] = {}
        self.data = self._load()

    def _load(self) -> dict:
        if not os.path.exists(self.path):
            raise FileNotFoundError(f"Configuration file not found at {self.path}")
        with open(self.path, "r", encoding="utf-8") as file:
            return json.load(file)

    def save(self) -> None:
        with open(self.path, "w", encoding="utf-8") as file:
            json.dump(self.data, file, indent=2)

    def get(self, key: str, default=None):
        return self.data.get(key, default)

    def set(self, key: str, value) -> None:
        self.data[key] = value
        self.save()

    def get_prefix(self) -> str:
        return self.data.get("prefix", ".")

    def set_prefix(self, prefix: str) -> None:
        self.data["prefix"] = prefix
        self.save()

    def is_owner(self, user_id: int) -> bool:
        owners = self.data.get("owner_ids", [])
        return user_id in owners

    def add_owner(self, user_id: int) -> None:
        owners = self.data.setdefault("owner_ids", [])
        if user_id not in owners:
            owners.append(user_id)
            self.save()

    def remove_owner(self, user_id: int) -> None:
        owners = self.data.setdefault("owner_ids", [])
        if user_id in owners:
            owners.remove(user_id)
            self.save()

    def get_memory_limit(self) -> int:
        return self.data.get("memory_limit", 6)

    def set_memory_limit(self, limit: int) -> None:
        self.data["memory_limit"] = max(0, limit)
        self.save()

    def is_whitelisted(self, user, channel) -> bool:
        whitelists = self.data.get("whitelists", {})
        allowed_users = whitelists.get("users", [])
        allowed_roles = whitelists.get("roles", [])
        allowed_channels = whitelists.get("channels", [])

        if self.is_owner(user.id):
            return True

        if allowed_channels and channel.id not in allowed_channels:
            return False

        if not allowed_users and not allowed_roles:
            return True

        if user.id in allowed_users:
            return True

        if hasattr(user, "roles"):
            for role in user.roles:
                if role.id in allowed_roles:
                    return True

        return False

    def check_rate_limit(self, user) -> tuple[bool, float]:
        if self.is_owner(user.id):
            return True, 0.0

        rate_limits = self.data.get("rate_limits", {})
        bypass_users = rate_limits.get("bypass_users", [])
        bypass_roles = rate_limits.get("bypass_roles", [])

        if user.id in bypass_users:
            return True, 0.0

        if hasattr(user, "roles"):
            for role in user.roles:
                if role.id in bypass_roles:
                    return True, 0.0

        cooldown = float(rate_limits.get("seconds", 5))
        now = time.time()
        last_time = self.rate_limit_timestamps.get(user.id, 0.0)
        elapsed = now - last_time

        if elapsed < cooldown:
            return False, round(cooldown - elapsed, 1)

        return True, 0.0

    def record_rate_limit(self, user) -> None:
        self.rate_limit_timestamps[user.id] = time.time()

    def check_daily_usage(self, user) -> tuple[bool, int, int]:
        if self.is_owner(user.id):
            return True, 0, 0

        usage_limits = self.data.get("usage_limits", {})
        user_limits = usage_limits.get("users", {})
        role_limits = usage_limits.get("roles", {})

        limit = None
        user_key = str(user.id)
        if user_key in user_limits:
            limit = user_limits[user_key]
        elif hasattr(user, "roles"):
            for role in user.roles:
                role_key = str(role.id)
                if role_key in role_limits:
                    role_limit = role_limits[role_key]
                    if limit is None or role_limit > limit:
                        limit = role_limit

        if limit is None or limit <= 0:
            return True, 0, 0

        today_key = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        tracking = self.data.setdefault("usage_tracking", {})
        today_data = tracking.setdefault(today_key, {})
        current_count = today_data.get(user_key, 0)

        if current_count >= limit:
            return False, current_count, limit

        return True, current_count, limit

    def record_daily_usage(self, user) -> None:
        today_key = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        tracking = self.data.setdefault("usage_tracking", {})
        today_data = tracking.setdefault(today_key, {})
        user_key = str(user.id)
        today_data[user_key] = today_data.get(user_key, 0) + 1
        self.save()

    def get_embed_color(self) -> int:
        color_raw = self.data.get("embed_settings", {}).get("color", self.data.get("default_embed_color", "0x2B2D31"))
        if isinstance(color_raw, str):
            if color_raw.startswith("0x") or color_raw.startswith("0X"):
                return int(color_raw, 16)
            if color_raw.startswith("#"):
                return int(color_raw[1:], 16)
            return int(color_raw, 16)
        if isinstance(color_raw, int):
            return color_raw
        return 0x2B2D31

    def get_system_prompt(self, user_id: int) -> str:
        prompts = self.data.get("prompts", {})
        user_prompts = prompts.get("users", {})
        user_key = str(user_id)
        if user_key in user_prompts and user_prompts[user_key]:
            return user_prompts[user_key]
        return prompts.get("global", "You are a concise and helpful assistant.")

    def get_api_key(self, provider: str) -> str:
        keys = self.data.get("api_keys", {})
        key = keys.get(provider.lower(), "")
        if not key:
            env_var_name = f"{provider.upper()}_API_KEY"
            key = os.getenv(env_var_name, "")
        return key

    def get_active_model(self, provider: str) -> str:
        models = self.data.get("active_models", {})
        return models.get(provider.lower(), "")

    def set_active_model(self, provider: str, model_name: str) -> None:
        models = self.data.setdefault("active_models", {})
        models[provider.lower()] = model_name
        self.save()

    def get_history(self, user_id: int) -> list[dict[str, str]]:
        return self.conversations.setdefault(user_id, [])

    def append_history(self, user_id: int, role: str, content: str) -> None:
        history = self.conversations.setdefault(user_id, [])
        history.append({"role": role, "content": content})
        limit = self.get_memory_limit()
        if limit > 0 and len(history) > limit:
            self.conversations[user_id] = history[-limit:]
        elif limit == 0:
            self.conversations[user_id] = []

    def clear_history(self, user_id: int) -> None:
        self.conversations[user_id] = []
