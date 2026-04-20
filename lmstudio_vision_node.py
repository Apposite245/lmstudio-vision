import base64
import io
import numpy as np
from PIL import Image

try:
    from openai import OpenAI
except ImportError:
    raise ImportError("openai package required — run: pip install openai")


class LMStudioVisionNode:
    _last_response = ""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "system_prompt": ("STRING", {
                    "multiline": True,
                    "default": "You are a helpful assistant.",
                }),
                "user_prompt": ("STRING", {
                    "multiline": True,
                    "default": "Describe this image.",
                }),
                "base_url": ("STRING", {
                    "default": "http://localhost:1234/v1",
                }),
                "model": ("STRING", {
                    "default": "",
                    "tooltip": "Leave blank to use whichever model is loaded in LM Studio.",
                }),
                "always_refresh": ("BOOLEAN", {
                    "default": True,
                    "label_on": "New prompt each run",
                    "label_off": "Use cached prompt",
                }),
            },
            "optional": {
                "image": ("IMAGE",),
                "max_tokens": ("INT", {
                    "default": 1024, "min": 1, "max": 16384, "step": 1,
                }),
                "temperature": ("FLOAT", {
                    "default": 0.7, "min": 0.0, "max": 2.0, "step": 0.01,
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("response",)
    FUNCTION = "process"
    CATEGORY = "LM Studio"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        if kwargs.get("always_refresh", True):
            return float("nan")
        # Stable value so ComfyUI calls process once then caches the stored response
        return "cached"

    def process(self, system_prompt, user_prompt, base_url, model,
                always_refresh=True, image=None, max_tokens=1024, temperature=0.7):
        if not always_refresh:
            return (LMStudioVisionNode._last_response,)

        if image is not None:
            img_np = (image[0].cpu().numpy() * 255).clip(0, 255).astype(np.uint8)
            pil_img = Image.fromarray(img_np)
            buf = io.BytesIO()
            pil_img.save(buf, format="PNG")
            img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            user_content = [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
                {"type": "text", "text": user_prompt},
            ]
        else:
            user_content = user_prompt

        client = OpenAI(
            base_url=base_url,
            api_key="lm-studio",  # LM Studio ignores the key but the field is required
        )

        resolved_model = model.strip() or "local-model"

        response = client.chat.completions.create(
            model=resolved_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )

        LMStudioVisionNode._last_response = response.choices[0].message.content
        return (LMStudioVisionNode._last_response,)


NODE_CLASS_MAPPINGS = {
    "LMStudioVision": LMStudioVisionNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LMStudioVision": "LM Studio Vision",
}
