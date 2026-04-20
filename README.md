# ComfyUI LM Studio Vision Node

A ComfyUI custom node that sends an image (optional), system prompt, and user prompt to a local [LM Studio](https://lmstudio.ai/) server and returns the model's text response.

## Requirements

- [LM Studio](https://lmstudio.ai/) with the local server enabled
- A vision-capable model loaded in LM Studio (e.g. LLaVA, Qwen-VL, Phi-3-vision) when using image input
- Any model when using text-only mode

## Installation

1. Clone or download this repo into your `ComfyUI/custom_nodes/` folder:
   ```
   cd ComfyUI/custom_nodes
   git clone https://github.com/Apposite245/comfyui-lmstudio-vision
   ```
2. Install the dependency:
   ```
   pip install openai
   ```
3. Restart ComfyUI.

The node appears under the **LM Studio** category.

## Inputs

| Input | Required | Description |
|---|---|---|
| `system_prompt` | Yes | System message for the model |
| `user_prompt` | Yes | User message |
| `base_url` | Yes | LM Studio server URL (default: `http://localhost:1234/v1`) |
| `model` | Yes | Model name — leave blank to use whichever is loaded |
| `always_refresh` | Yes | Toggle between generating a new response each run or reusing the last one |
| `image` | No | Image to send — if not connected the node runs in text-only mode |
| `max_tokens` | No | Max tokens to generate (default: 1024) |
| `temperature` | No | Sampling temperature (default: 0.7) |

## Output

`STRING` — the model's response, compatible with any node that accepts text.

## The refresh toggle

- **New prompt each run** — calls LM Studio on every queue run
- **Use cached prompt** — returns the last generated response without calling LM Studio, useful for locking in a response you want to reuse downstream
