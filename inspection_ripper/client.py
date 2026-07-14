from __future__ import annotations


import httpx

_GROK_URL = "https://api.x.ai/v1/chat/completions"
_DEFAULT_MODEL = "grok-4.3"
_MAX_TOKENS = 4096


class GrokClient:
    def __init__(self, api_key: str, model: str = _DEFAULT_MODEL) -> None:
        self.api_key = api_key
        self.model = model

    def health_check(self) -> None:
        """Raises ValueError if the API key is missing."""
        if not self.api_key:
            raise ValueError("GROK_API_KEY is not set")

    def call_api(
        self,
        page_images: list[str],   # base64-encoded JPEG strings
        prompt: str,
        timeout: int = 120,
    ) -> tuple[str, dict[str, int]]:
        """Send images + prompt to Grok and return (response_text, tokens_dict).

        Build the content list: one image_url part per page, then the text prompt.
        POST to _GROK_URL with Bearer auth.
        Parse the JSON response and return the first choice's message content
        along with {"input_tokens": N, "output_tokens": N}.
        Raise httpx.HTTPStatusError on non-200 responses.
        """

        # 1. Build the content list for the message
        # Each page is an "image_url" part; the prompt is the "text" at the end
        content = []
        for img in page_images:
            content.append({
                "type": "image_url",
                "image_url": {"url": self.image_to_data_url(img)},
            })
        content.append({"type": "text", "text": prompt})

        # 2. Build the request body
        body = {
            "model": self.model,
            "max_completion_tokens": _MAX_TOKENS,
            "messages": [
                {"role": "user", "content": content}
            ],
        }

        # 3. POST it and raise immediately on any non-2xx status
        response = httpx.post(
            _GROK_URL,
            headers=self._build_headers(),
            json=body,
            timeout=timeout,
        )
        response.raise_for_status()

        # 4. parse the response
        data = response.json()
        text = data["choices"][0]["message"]["content"]
        tokens = {
            "input_tokens": data["usage"]["prompt_tokens"],
            "output_tokens": data["usage"]["completion_tokens"],
        }
        return text, tokens

    def _build_headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    @staticmethod
    def image_to_data_url(b64_jpeg: str) -> str:
        return f"data:image/jpeg;base64,{b64_jpeg}"
