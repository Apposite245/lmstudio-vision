import base64
import io
import numpy as np
import requests
from PIL import Image

try:
    from server import PromptServer
    from aiohttp import web

    @PromptServer.instance.routes.get("/lmstudio_vision/models")
    async def _route_get_models(request):
        base_url = request.query.get("base_url")
        if not base_url:
            return web.json_response({"error": "base_url required"}, status=400)
        models = _fetch_model_ids(base_url)
        return web.json_response({"models": models})
except Exception:
    pass


def _fetch_model_ids(base_url: str = "http://localhost:1234", timeout: int = 5) -> list[str]:
    try:
        r = requests.get(f"{base_url.rstrip('/')}/api/v1/models", timeout=timeout)
        r.raise_for_status()
        models = r.json().get("models", [])
        keys = [m.get("key", "") for m in models if m.get("type") == "llm"]
        return [k for k in keys if k] or ["(no models found)"]
    except Exception:
        return ["(LM Studio not reachable)"]


class LMStudioVisionNode:
    _last_response = ""

    @classmethod
    def INPUT_TYPES(cls):
        models = _fetch_model_ids()
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
                    "default": "http://localhost:1234",
                }),
                "model": (models,),
                "always_refresh": ("BOOLEAN", {
                    "default": True,
                    "label_on": "New prompt each run",
                    "label_off": "Use cached prompt",
                }),
                "unload_after_run": ("BOOLEAN", {
                    "default": False,
                    "label_on": "Unload model after run",
                    "label_off": "Keep model loaded",
                }),
            },
            "optional": {
                "image": ("IMAGE",),
                "max_output_tokens": ("INT", {
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
        return "cached"

    def _is_model_loaded(self, base_url: str, model: str) -> bool:
        try:
            r = requests.get(f"{base_url.rstrip('/')}/api/v1/models", timeout=5)
            r.raise_for_status()
            for m in r.json().get("models", []):
                if m.get("key") == model and m.get("loaded_instances"):
                    return True
        except Exception:
            pass
        return False

    def _load_model(self, base_url: str, model: str):
        if self._is_model_loaded(base_url, model):
            return
        try:
            r = requests.post(
                f"{base_url.rstrip('/')}/api/v1/models/load",
                json={"model": model},
                timeout=60,
            )
            r.raise_for_status()
        except Exception as e:
            print(f"[LMStudioVision] load warning: {e}")

    def _unload_model(self, base_url: str, instance_id: str):
        try:
            r = requests.post(
                f"{base_url.rstrip('/')}/api/v1/models/unload",
                json={"instance_id": instance_id},
                timeout=10,
            )
            r.raise_for_status()
        except Exception as e:
            print(f"[LMStudioVision] unload warning: {e}")

    def process(self, system_prompt, user_prompt, base_url, model,
                always_refresh=True, unload_after_run=False, image=None,
                max_output_tokens=1024, temperature=0.7):
        if not always_refresh:
            return (LMStudioVisionNode._last_response,)

        if unload_after_run:
            self._load_model(base_url, model)

        if image is not None:
            img_np = (image[0].cpu().numpy() * 255).clip(0, 255).astype(np.uint8)
            pil_img = Image.fromarray(img_np)
            buf = io.BytesIO()
            pil_img.save(buf, format="PNG")
            img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            user_input = [
                {"type": "image", "data_url": f"data:image/png;base64,{img_b64}"},
                {"type": "text",  "text": user_prompt},
            ]
        else:
            user_input = user_prompt

        payload = {
            "model": model,
            "system_prompt": system_prompt,
            "input": user_input,
            "max_output_tokens": max_output_tokens,
            "temperature": temperature,
        }

        r = requests.post(
            f"{base_url.rstrip('/')}/api/v1/chat",
            json=payload,
            timeout=120,
        )
        r.raise_for_status()

        output_blocks = r.json().get("output", [])
        text = next(
            (b["content"] for b in output_blocks if b.get("type") == "message"),
            "",
        )

        LMStudioVisionNode._last_response = text

        if unload_after_run:
            self._unload_model(base_url, model)

        return (LMStudioVisionNode._last_response,)


NODE_CLASS_MAPPINGS = {
    "LMStudioVision": LMStudioVisionNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LMStudioVision": "LM Studio Vision",
}
