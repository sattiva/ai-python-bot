import aiohttp
import json
import base64

OPENAI_COMPATIBLE_ENDPOINTS = {
    "groq": "https://api.groq.com/openai/v1/chat/completions",
    "openai": "https://api.openai.com/v1/chat/completions",
    "deepseek": "https://api.deepseek.com/chat/completions",
    "together": "https://api.together.xyz/v1/chat/completions",
    "openrouter": "https://openrouter.ai/api/v1/chat/completions"
}

async def generate_response(
    provider: str,
    api_key: str,
    model: str,
    system_prompt: str,
    messages: list[dict[str, str]],
    prompt: str,
    images: list[tuple[str, str]] | None = None
) -> tuple[str | None, str | None]:
    if not api_key:
        return f"API key is not configured for provider: {provider}", None

    provider_lower = provider.lower()

    if provider_lower in OPENAI_COMPATIBLE_ENDPOINTS:
        return await _generate_openai_compatible(
            endpoint=OPENAI_COMPATIBLE_ENDPOINTS[provider_lower],
            api_key=api_key,
            model=model,
            system_prompt=system_prompt,
            messages=messages,
            prompt=prompt,
            images=images
        )

    if provider_lower == "anthropic":
        return await _generate_anthropic(
            api_key=api_key,
            model=model,
            system_prompt=system_prompt,
            messages=messages,
            prompt=prompt,
            images=images
        )

    if provider_lower == "gemini":
        return await _generate_gemini(
            api_key=api_key,
            model=model,
            system_prompt=system_prompt,
            messages=messages,
            prompt=prompt,
            images=images
        )

    return f"Unsupported provider: {provider}", None

async def _generate_openai_compatible(
    endpoint: str,
    api_key: str,
    model: str,
    system_prompt: str,
    messages: list[dict[str, str]],
    prompt: str,
    images: list[tuple[str, str]] | None = None
) -> tuple[str | None, str | None]:
    payload_messages = []
    if system_prompt:
        payload_messages.append({"role": "system", "content": system_prompt})

    for item in messages:
        payload_messages.append({"role": item["role"], "content": item["content"]})

    if images:
        user_content = []
        user_content.append({"type": "text", "text": prompt if prompt else "Extract all text and describe this image."})
        for mime_type, b64_data in images:
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{b64_data}"}
            })
        payload_messages.append({"role": "user", "content": user_content})
    else:
        payload_messages.append({"role": "user", "content": prompt})

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": payload_messages,
        "temperature": 0.7
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    return f"HTTP {resp.status}: {text}", None
                data = await resp.json()
                choices = data.get("choices", [])
                if not choices:
                    return "No completions returned from provider.", None
                content = choices[0].get("message", {}).get("content", "")
                return None, content.strip()
    except Exception as exc:
        return str(exc), None

async def _generate_anthropic(
    api_key: str,
    model: str,
    system_prompt: str,
    messages: list[dict[str, str]],
    prompt: str,
    images: list[tuple[str, str]] | None = None
) -> tuple[str | None, str | None]:
    payload_messages = []
    for item in messages:
        payload_messages.append({"role": item["role"], "content": item["content"]})

    if images:
        user_content = []
        for mime_type, b64_data in images:
            user_content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": mime_type,
                    "data": b64_data
                }
            })
        user_content.append({"type": "text", "text": prompt if prompt else "Extract all text and describe this image."})
        payload_messages.append({"role": "user", "content": user_content})
    else:
        payload_messages.append({"role": "user", "content": prompt})

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "max_tokens": 4096,
        "messages": payload_messages,
        "temperature": 0.7
    }

    if system_prompt:
        payload["system"] = system_prompt

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    return f"HTTP {resp.status}: {text}", None
                data = await resp.json()
                content_blocks = data.get("content", [])
                if not content_blocks:
                    return "No content blocks returned from Anthropic.", None
                text_result = content_blocks[0].get("text", "")
                return None, text_result.strip()
    except Exception as exc:
        return str(exc), None

async def _generate_gemini(
    api_key: str,
    model: str,
    system_prompt: str,
    messages: list[dict[str, str]],
    prompt: str,
    images: list[tuple[str, str]] | None = None
) -> tuple[str | None, str | None]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    contents = []

    for item in messages:
        role = "user" if item["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": item["content"]}]})

    user_parts = []
    user_parts.append({"text": prompt if prompt else "Extract all text and describe this image."})
    if images:
        for mime_type, b64_data in images:
            user_parts.append({
                "inlineData": {
                    "mimeType": mime_type,
                    "data": b64_data
                }
            })

    contents.append({"role": "user", "parts": user_parts})

    payload: dict = {"contents": contents}
    if system_prompt:
        payload["systemInstruction"] = {
            "parts": [{"text": system_prompt}]
        }

    headers = {"Content-Type": "application/json"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    return f"HTTP {resp.status}: {text}", None
                data = await resp.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    return "No candidates returned from Gemini.", None
                parts = candidates[0].get("content", {}).get("parts", [])
                if not parts:
                    return "No text parts returned from Gemini.", None
                return None, parts[0].get("text", "").strip()
    except Exception as exc:
        return str(exc), None
