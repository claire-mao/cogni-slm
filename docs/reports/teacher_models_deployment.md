# Teacher Models: Deployment Characteristics (as of July 9, 2026)

Scope:

- Candidate models: GPT-5, o3, Claude Opus 4, Claude Sonnet 4, Gemini 2.5 Pro, DeepSeek R1, Qwen3, Llama 4 Maverick
- Focus fields: pricing, latency, rate limits, API availability, local availability, open weights, commercial usage
- Where providers do not publish fixed latency SLAs or static limits, entries are marked as dynamic/provider-dependent.

## GPT-5

- Pricing:
  - OpenAI model page lists `$1.25 / 1M input`, `$0.125 / 1M cached input`, `$10 / 1M output`.
- Latency:
  - No fixed public p95/p99 SLA published.
  - Latency is workload-dependent (prompt size, output length, reasoning effort level).
- Rate limits:
  - Published by usage tier on model page.
  - Example: Tier 1 `500 RPM`, `500,000 TPM`; Tier 5 `15,000 RPM`, `40,000,000 TPM`.
- API availability:
  - OpenAI API (Responses, Chat Completions, Batch, and related endpoints listed on the model page).
- Local availability:
  - Not available as downloadable weights.
- Open weights:
  - No.
- Commercial usage:
  - Yes via OpenAI API terms/policies.

## o3

- Pricing:
  - OpenAI model page lists `$2.00 / 1M input`, `$0.50 / 1M cached input`, `$8.00 / 1M output`.
- Latency:
  - No fixed public latency SLA published.
  - Positioned as a reasoning model; latency is request-dependent.
- Rate limits:
  - Published by usage tier on model page.
  - Example: Tier 1 `500 RPM`, `30,000 TPM`; Tier 5 `10,000 RPM`, `30,000,000 TPM`.
- API availability:
  - OpenAI API (same core endpoint families as above in model docs).
- Local availability:
  - Not available as downloadable weights.
- Open weights:
  - No.
- Commercial usage:
  - Yes via OpenAI API terms/policies.

## Claude Opus 4

- Pricing:
  - Anthropic pricing page lists Opus 4/4.1 class at `$15 / MTok input`, `$75 / MTok output` (with cache and batch variants).
- Latency:
  - Anthropic does not publish fixed per-model latency SLAs.
  - Fast mode is documented for selected Opus 4.x snapshots (separate rate-limit pool).
- Rate limits:
  - Tier-based org limits; per-model-group limits are documented.
  - Start-tier table shows Opus 4.x at `1,000 RPM`, `2,000,000 ITPM`, `400,000 OTPM`.
- API availability:
  - Claude API; also available through major clouds (AWS/Bedrock, Google Cloud, Microsoft Foundry per model overview).
- Local availability:
  - Not available as downloadable weights.
- Open weights:
  - No.
- Commercial usage:
  - Yes via Anthropic platform terms/policies.

## Claude Sonnet 4

- Pricing:
  - Anthropic pricing page lists Sonnet 4 class at `$3 / MTok input`, `$15 / MTok output` (plus cache/batch modifiers).
- Latency:
  - No fixed public latency SLA.
  - Intended as a higher speed/efficiency tier than Opus class; actual latency depends on workload and service tier.
- Rate limits:
  - Start-tier table shows Sonnet 4.x at `1,000 RPM`, `2,000,000 ITPM`, `400,000 OTPM`.
  - Limits are tiered and can be increased.
- API availability:
  - Claude API + partner cloud availability.
- Local availability:
  - Not available as downloadable weights.
- Open weights:
  - No.
- Commercial usage:
  - Yes via Anthropic platform terms/policies.

## Gemini 2.5 Pro

- Pricing:
  - Gemini API pricing page lists:
    - Standard input: `$1.25 / 1M` (<=200k prompt), `$2.50 / 1M` (>200k prompt)
    - Output (incl. thinking): `$10.00 / 1M` (<=200k), `$15.00 / 1M` (>200k)
- Latency:
  - Google troubleshooting docs note 2.5 Pro can show higher latency because thinking is enabled by default.
  - No fixed public p95/p99 SLA published in Gemini docs.
- Rate limits:
  - Project-level, tier-dependent, model-dependent (RPM/TPM/RPD dimensions).
  - Google explicitly states active limits are viewed in AI Studio and may change by tier/account status.
  - Spend-based safeguards are published (per 10 minutes): Tier 1 `$10`, Tier 2 `$200`, Tier 3 `$200`.
- API availability:
  - Gemini API (AI Studio / developer APIs) and Vertex AI.
- Local availability:
  - Not available as downloadable weights.
- Open weights:
  - No.
- Commercial usage:
  - Yes via Google terms/policies for Gemini API/Vertex AI.

## DeepSeek R1

- Pricing:
  - Current DeepSeek hosted pricing is published for V4 models; `deepseek-reasoner` is a compatibility alias to V4-Flash thinking mode and is scheduled for deprecation on July 24, 2026.
  - `deepseek-v4-flash` published rates: `$0.14 / 1M input (cache miss)`, `$0.28 / 1M output` (plus cache-hit rate).
- Latency:
  - DeepSeek notes API defaults to non-streaming (appears slower); streaming improves interactivity.
  - No fixed public p95/p99 SLA published.
- Rate limits:
  - Concurrency-based limits are published per account:
    - `deepseek-v4-flash`: `2500` concurrent requests
    - `deepseek-v4-pro`: `500` concurrent requests
- API availability:
  - Official DeepSeek API with OpenAI-format base URL and Anthropic-format compatibility endpoint.
- Local availability:
  - Yes (DeepSeek-R1 and distilled checkpoints are downloadable for self-hosting).
- Open weights:
  - Yes (DeepSeek-R1 repo/license indicates MIT license).
- Commercial usage:
  - Open-weight usage is governed by MIT license for released checkpoints.
  - Managed API usage is governed by DeepSeek platform terms.

## Qwen3

- Pricing:
  - Model Studio pricing is model-ID and region specific.
  - Example published rates:
    - `qwen3-235b-a22b` (Global): input `$0.287 / 1M`; output `$1.147 / 1M` (non-thinking) or `$2.868 / 1M` (thinking).
    - `qwen3-max` uses tiered per-request token bands with higher prices at larger context bands.
- Latency:
  - No fixed public p95/p99 SLA published.
  - Throughput/latency behavior is tied to RPM/TPM quotas and deployment mode; docs note degradation when over certain dedicated-service thresholds.
- Rate limits:
  - Published per model and region in Model Studio.
  - Example: `qwen3-max` and `qwen3-235b-a22b` commonly show `600 RPM` and `1,000,000 TPM` entries in published tables (region/model dependent).
  - Temporary TPM increases are supported for eligible regions.
- API availability:
  - Alibaba Cloud Model Studio native API and OpenAI-compatible endpoint mode.
- Local availability:
  - Yes for open-weight Qwen3 checkpoints.
- Open weights:
  - Mixed by model: many Qwen3 open-weight checkpoints are Apache 2.0; `qwen3-max` remains hosted/proprietary.
- Commercial usage:
  - Apache 2.0 checkpoints permit commercial use under license terms.
  - Hosted Model Studio models are under Alibaba platform terms.

## Llama 4 Maverick

- Pricing:
  - Meta does not publish a single universal first-party per-token price for all deployment routes.
  - Pricing is provider-dependent (for example Amazon Bedrock pricing tables/service tiers for Meta Llama models).
- Latency:
  - No fixed public latency SLA from Meta model card.
  - On managed providers (e.g., Bedrock), latency/throughput are tier-dependent (Standard/Priority/Flex/Reserved).
- Rate limits:
  - Provider-dependent.
  - Example from AWS Bedrock quotas: cross-region inference for Meta Llama 4 Maverick V1 is listed at `800 requests/min` per supported region.
- API availability:
  - Available via hosted provider APIs (e.g., Amazon Bedrock model ID `meta.llama4-maverick-17b-instruct-v1:0`).
  - Meta Llama API is also referenced in Meta announcements.
- Local availability:
  - Yes (downloadable weights available via Meta/Hugging Face channels).
- Open weights:
  - Yes (open-weight release), but under the Llama 4 Community License (not Apache/MIT).
- Commercial usage:
  - Allowed under Llama 4 Community License, with additional commercial conditions (including separate licensing requirement for very large MAU entities).

## Sources

- OpenAI GPT-5 model page: https://developers.openai.com/api/docs/models/gpt-5
- OpenAI o3 model page: https://developers.openai.com/api/docs/models/o3
- Anthropic pricing: https://platform.claude.com/docs/en/about-claude/pricing
- Anthropic rate limits: https://platform.claude.com/docs/en/api/rate-limits
- Anthropic models overview: https://platform.claude.com/docs/en/about-claude/models/overview
- Gemini 2.5 Pro model page: https://ai.google.dev/gemini-api/docs/models/gemini-2.5-pro
- Gemini API pricing: https://ai.google.dev/gemini-api/docs/pricing
- Gemini API rate limits: https://ai.google.dev/gemini-api/docs/rate-limits
- Gemini troubleshooting: https://ai.google.dev/gemini-api/docs/troubleshooting
- DeepSeek models & pricing: https://api-docs.deepseek.com/quick_start/pricing
- DeepSeek rate limits: https://api-docs.deepseek.com/quick_start/rate_limit/
- DeepSeek FAQ (latency/streaming notes): https://api-docs.deepseek.com/faq
- DeepSeek-R1 repository/license: https://github.com/deepseek-ai/DeepSeek-R1
- Alibaba Model Studio model pricing: https://www.alibabacloud.com/help/en/model-studio/model-pricing
- Alibaba Model Studio rate limits: https://www.alibabacloud.com/help/en/model-studio/rate-limit
- Alibaba text model matrix (Qwen3 capabilities/context): https://www.alibabacloud.com/help/en/model-studio/text-generation-model
- Qwen3 announcement (open-weight licensing details): https://qwenlm.github.io/blog/qwen3/
- Qwen3 HF model card/license example: https://huggingface.co/Qwen/Qwen3-235B-A22B
- Llama 4 Maverick Bedrock model card: https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-meta-llama-4-maverick-17b-instruct.html
- Amazon Bedrock pricing: https://aws.amazon.com/bedrock/pricing/
- Amazon Bedrock quotas: https://docs.aws.amazon.com/general/latest/gr/bedrock.html
- Llama 4 Maverick HF model card: https://huggingface.co/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8
- Llama 4 Community License text: https://github.com/meta-llama/llama-models/blob/main/models/llama4/LICENSE
