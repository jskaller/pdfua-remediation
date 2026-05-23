# OpenClaw Gateway Configuration Guide
## Montefiore PDF/UA Remediation Suite

This document is the single reference for configuring the AI model gateway.
It is written for team members who may have never touched this system before.
No code changes are required for any configuration described here — everything
is controlled through the `.env` file.

---

## How the gateway works

The remediation suite makes calls to two AI models:

| Role | Purpose | Requirement |
|------|---------|-------------|
| **Primary model** | All audit, repair, and packaging decisions | Reasoning + tool calling + JSON mode |
| **Visual QA model** | Post-repair rendered page comparison | Vision/image input capability |

Both models must be accessible via an **OpenAI-compatible API endpoint** —
meaning any provider that accepts requests in the standard
`POST /v1/chat/completions` format. This includes NVIDIA NIM, OpenAI,
Anthropic, OpenRouter, StepFun direct, and local Ollama.

The primary and visual QA model can come from **the same provider or different
providers**. If you use a provider where one model handles both text and vision
(OpenAI, Anthropic, OpenRouter with a capable model), you only need to
configure one set of credentials.

---

## Quick start by provider

Copy the relevant block into your `.env` file. Replace placeholder keys with
your actual credentials.

---

### NVIDIA NIM (project default)
Single API key, access to 100+ models including both text and vision.

```bash
PRIMARY_PROVIDER_BASE_URL=https://integrate.api.nvidia.com/v1
PRIMARY_PROVIDER_API_KEY=nvapi-your-key-here
PRIMARY_MODEL=stepfun-ai/step-3.5-flash

# Vision — same provider, different model
VISION_PROVIDER_BASE_URL=
VISION_PROVIDER_API_KEY=
VISION_MODEL=nvidia/nemotron-3-nano-omni-reasoning-30b-a3b
```
Get a key at: https://build.nvidia.com/settings/api-keys

---

### OpenAI (Codex / GPT)
One model handles both text reasoning and vision.

```bash
PRIMARY_PROVIDER_BASE_URL=https://api.openai.com/v1
PRIMARY_PROVIDER_API_KEY=sk-your-key-here
PRIMARY_MODEL=gpt-4.1

# Vision — same model, leave provider blank to reuse primary credentials
VISION_PROVIDER_BASE_URL=
VISION_PROVIDER_API_KEY=
VISION_MODEL=gpt-4.1
```
Get a key at: https://platform.openai.com/api-keys

---

### Anthropic (Claude)
One model handles both text reasoning and vision.

```bash
PRIMARY_PROVIDER_BASE_URL=https://api.anthropic.com/v1
PRIMARY_PROVIDER_API_KEY=sk-ant-your-key-here
PRIMARY_MODEL=claude-sonnet-4-5

# Vision — same model, leave provider blank to reuse primary credentials
VISION_PROVIDER_BASE_URL=
VISION_PROVIDER_API_KEY=
VISION_MODEL=claude-sonnet-4-5
```
Get a key at: https://console.anthropic.com/settings/keys

---

### OpenRouter (aggregator — access any model with one key)
Useful if you want to mix models from different providers without managing
multiple accounts.

```bash
PRIMARY_PROVIDER_BASE_URL=https://openrouter.ai/api/v1
PRIMARY_PROVIDER_API_KEY=sk-or-your-key-here
PRIMARY_MODEL=stepfun/step-3.5-flash

# Vision — same provider, different model
VISION_PROVIDER_BASE_URL=
VISION_PROVIDER_API_KEY=
VISION_MODEL=nvidia/nemotron-3-nano-omni-reasoning-30b-a3b
```
Get a key at: https://openrouter.ai/settings/keys
Browse available models at: https://openrouter.ai/models

---

### StepFun direct + NIM for vision (split provider)
Use StepFun's own endpoint for the primary model, NIM for visual QA.

```bash
PRIMARY_PROVIDER_BASE_URL=https://api.stepfun.ai/v1
PRIMARY_PROVIDER_API_KEY=your-stepfun-key-here
PRIMARY_MODEL=step-3.5-flash

# Vision — different provider
VISION_PROVIDER_BASE_URL=https://integrate.api.nvidia.com/v1
VISION_PROVIDER_API_KEY=nvapi-your-nim-key-here
VISION_MODEL=nvidia/nemotron-3-nano-omni-reasoning-30b-a3b
```
Get StepFun keys at: https://platform.stepfun.ai

---

### Local Ollama (no API cost, runs on your machine)
Requires a GPU with sufficient VRAM. Useful for development and testing.

```bash
PRIMARY_PROVIDER_BASE_URL=http://localhost:11434/v1
PRIMARY_PROVIDER_API_KEY=ollama
PRIMARY_MODEL=qwen3:32b

VISION_PROVIDER_BASE_URL=http://localhost:11434/v1
VISION_PROVIDER_API_KEY=ollama
VISION_MODEL=qwen2.5vl:7b
```
Install Ollama at: https://ollama.ai
Pull models with: `ollama pull qwen3:32b && ollama pull qwen2.5vl:7b`

---

## How blank vision fields work

If `VISION_PROVIDER_BASE_URL` is blank, vision calls go to
`PRIMARY_PROVIDER_BASE_URL`.

If `VISION_PROVIDER_API_KEY` is blank, vision calls use
`PRIMARY_PROVIDER_API_KEY`.

This means single-provider setups (OpenAI, Anthropic, OpenRouter, Ollama)
only need to set the primary credentials — vision calls automatically
reuse them.

---

## Setup procedure

```bash
# 1. Clone the repository
git clone https://github.com/jskaller/pdfua-remediation.git
cd pdfua-remediation/openclaw_migration

# 2. Create your .env from the template
cp .env.example .env

# 3. Open .env and fill in your provider credentials
# (use one of the Quick Start blocks above)

# 4. Build and start the container
docker compose up --build

# 5. Verify everything is working
docker compose exec remediation python3 tools/audit/smoke_test.py
```

First build takes several minutes (veraPDF installer, fonts, Python deps).
Subsequent starts are fast.

---

## Switching providers mid-project

Edit `.env` with the new provider block, then restart the container:

```bash
docker compose restart remediation
```

Verify the active configuration:
```bash
docker compose exec remediation env | grep -E 'MODEL|PROVIDER'
```

---

## Choosing a primary model

The primary model handles reasoning, tool use, and structured JSON output
across all repair and audit tasks. Requirements:

- Tool calling / function calling support
- JSON mode or reliable structured output
- At least 32K context window (128K+ strongly preferred for large documents)
- Strong instruction following

**Recommended options by priority:**

| Provider | Model | Strengths |
|---------|-------|-----------|
| NIM | `stepfun-ai/step-3.5-flash` | Fast, strong agentic, 256K context, cheap |
| NIM | `qwen/qwen3-235b-a22b` | Highest reasoning quality on NIM |
| NIM | `nvidia/nemotron-3-super-49b-v1` | 1M context for very large documents |
| OpenAI | `gpt-4.1` | Excellent tool calling, reliable |
| Anthropic | `claude-sonnet-4-5` | Strong instruction following, 200K context |
| OpenRouter | `stepfun/step-3.5-flash` | Same model via aggregator |
| Ollama | `qwen3:32b` | Local, no cost, strong reasoning |

---

## Choosing a visual QA model

The visual QA model receives rendered PDF page images and makes qualitative
judgments about visual fidelity after repair. Requirements:

- Image input / vision capability
- Ability to reason about document layout and rendering
- Strong document intelligence (DocVQA performance matters)

**Recommended options:**

| Provider | Model | Notes |
|---------|-------|-------|
| NIM | `nvidia/nemotron-3-nano-omni-reasoning-30b-a3b` | Default. Document intelligence + reasoning |
| OpenAI | `gpt-4.1` | Excellent vision, same model as primary |
| Anthropic | `claude-sonnet-4-5` | Excellent vision, same model as primary |
| OpenRouter | `nvidia/nemotron-3-nano-omni-reasoning-30b-a3b` | Same model via aggregator |
| Ollama | `qwen2.5vl:7b` | Local, best document VQA in class |

**Do not use** text-only models (DeepSeek-R1, Step 3.5 Flash without vision)
as the visual QA model — they cannot process images.

---

## Troubleshooting

**smoke_test.py fails on veraPDF check**
```bash
docker compose exec remediation /opt/verapdf/verapdf --version
```
If this fails, rebuild: `docker compose up --build --no-cache`

**401 Unauthorized from model API**
Your API key is invalid or expired. Check it with your provider's dashboard.

**404 Not Found for model**
The model ID string is wrong for the provider. Model IDs are
provider-specific — a NIM model ID like `stepfun-ai/step-3.5-flash`
is different from the OpenRouter version `stepfun/step-3.5-flash`.
Check the provider's model catalog for the exact string.

**Vision model returns error on image input**
The selected vision model may not support image inputs at your provider.
Verify the model has multimodal/vision capability in the provider's docs.

**`.env` not found error on docker compose up**
Run `cp .env.example .env` first, then fill in your credentials.

---

*For questions, contact the repository owner.*
*Last updated: May 2026.*
