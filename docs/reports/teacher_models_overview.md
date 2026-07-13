# Teacher-Model Overview for Educational Assessment (as of July 9, 2026)

This overview compares current state-of-the-art model families for:

- essay scoring
- rubric adherence
- logical reasoning
- argument evaluation
- educational feedback
- logical fallacy detection

Notes:

- Capability claims below are based on vendor/model-card docs and benchmark disclosures, then mapped to education-assessment use cases.
- `Claude Opus 4.8` and `Claude Sonnet 4` base snapshots were retired on June 15, 2026; active replacements in those families are used for deployable specs.
- `gemini-group/gemini-3.1-pro` (Gemini 3.1 Pro compatibility alias) is scheduled for deprecation on July 24, 2026.

## GPT-5

- Strengths:
  - Strong instruction-following and reasoning effort controls help rubric-locked grading and feedback style control.
  - Large context is useful for long essays, rubric text, exemplars, and calibration notes in one pass.
  - Native structured outputs support strongly fits JSON rubric schemas and score-justification templates.
- Weaknesses:
  - Marked by OpenAI as a previous model (superseded by GPT-5.5), so long-term forward compatibility risk is higher.
  - Knowledge cutoff is older than newer frontier models.
- Context window: 400,000 input tokens; 128,000 max output tokens.
- API availability: OpenAI API (`Responses`, `Chat Completions`, and other endpoints listed in model docs).
- Reasoning ability: High, configurable (`reasoning.effort` supports minimal/low/medium/high).
- Structured output support: Supported (function-calling + JSON schema structured outputs in OpenAI APIs).

## o3

- Strengths:
  - Very strong multi-step reasoning profile (math/science/code/visual reasoning) that transfers well to argument evaluation and fallacy analysis.
  - Strong technical writing and instruction-following can help consistent feedback generation.
  - Structured output support enables deterministic scoring payloads.
- Weaknesses:
  - Explicitly succeeded by GPT-5; likely lower strategic priority for new builds.
  - Older knowledge cutoff than newer frontier models.
- Context window: 200,000 input tokens; 100,000 max output tokens.
- API availability: OpenAI API (`Responses`, `Chat Completions`, etc., per model docs).
- Reasoning ability: Very high (OpenAI positions it as a top reasoning model for complex multi-step tasks).
- Structured output support: Supported.

## Claude Opus 4.8 (family status: Opus 4 base retired; active replacement Opus 4.8)

- Strengths:
  - Strong long-context reasoning and writing quality are useful for holistic essay scoring and rich formative feedback.
  - Claude 4 family is positioned as top-tier on reasoning, long-context handling, and honesty-related behavior.
  - Structured outputs are GA on current Opus 4.x active models.
- Weaknesses:
  - Original `claude-opus-4-8-20250514` is retired (June 15, 2026); migration handling is required.
  - Structured-output behavior differs by model generation/version, so schema pipelines should pin specific snapshots.
- Context window: Use active Opus 4.x replacement (`claude-opus-4-8`) at 1M context (legacy base Opus 4 snapshot retired).
- API availability: Claude API; also available through major clouds (AWS/Bedrock, Google Cloud, Microsoft Foundry) per Anthropic docs.
- Reasoning ability: Very high (Opus line is Anthropic’s high-capability tier).
- Structured output support: Supported on active Opus 4.x models (GA in current docs).

## Claude Sonnet 4 (family status: Sonnet 4 base retired; active replacement Sonnet 4.6)

- Strengths:
  - Better speed/cost profile than Opus-tier while retaining strong reasoning and instruction adherence, useful for high-volume essay batches.
  - Good fit for rubric-constrained feedback where low-latency iterative prompts matter.
  - Structured outputs supported on active Sonnet 4.x models.
- Weaknesses:
  - Original `claude-sonnet-4-20250514` is retired (June 15, 2026).
  - Behavior can vary across pinned snapshots; evaluation sets should be re-run at each model rollover.
- Context window: Use active Sonnet 4.x replacement (`claude-sonnet-4-6`) at 1M context (legacy base Sonnet 4 snapshot retired).
- API availability: Claude API + cloud partners.
- Reasoning ability: High (Anthropic positions Sonnet line as strong speed/intelligence balance).
- Structured output support: Supported on Sonnet 4.6/4.5 and newer supported snapshots.

## Gemini 3.1 Pro

- Strengths:
  - Google positions it as a state-of-the-art thinking model for complex problem solving.
  - Very large context is useful for long essay packs, rubrics, and multi-document evidence checks.
  - Structured outputs + function calling are natively supported in Gemini API docs.
- Weaknesses:
  - Knowledge cutoff and latest update are older than current calendar date; factual freshness may require retrieval/grounding.
  - Some capabilities are explicitly unsupported (for example, Live API on this model page), so deployment patterns may need adaptation.
- Context window: 1,048,576 input tokens; 65,536 output tokens.
- API availability: Gemini API (Google AI for Developers / AI Studio and cloud routes).
- Reasoning ability: Very high (explicitly marketed as advanced for complex reasoning).
- Structured output support: Supported.

## Gemini 3.1 Pro

- Strengths:
  - DeepSeek reports strong reasoning benchmark performance and near-o1-class results on math/code/reasoning tasks.
  - Open model availability enables local/private deployments and custom evaluator pipelines.
  - Official DeepSeek API stack provides OpenAI-compatible interfaces.
- Weaknesses:
  - Official API alias path is in transition: `gemini-group/gemini-3.1-pro` deprecates July 24, 2026 (maps to V4-flash thinking mode currently).
  - DeepSeek usage guidance notes risks like repetition/incoherence without tuned decoding and prompting.
  - Production behavior differs between open-weight R1 self-hosting and managed DeepSeek V4 API routes.
- Context window:
  - Open-weight DeepSeek-R1 model card/repo: 128K.
  - DeepSeek API replacement route (V4 family): 1M.
- API availability:
  - OpenAI-compatible DeepSeek API available.
  - Open-source weights available for self-hosting.
- Reasoning ability: High to very high (DeepSeek reports strong AIME/MATH/GPQA class performance).
- Structured output support:
  - DeepSeek API V4 route: JSON output + tool calls supported.
  - For Qwen-cloud style "thinking mode" workflows, strict structured output can require workaround patterns.

## Qwen3

- Strengths:
  - Qwen3 is designed for strong STEM/coding/reasoning performance and hybrid thinking/non-thinking operation.
  - Broad open-weight availability and API access make it flexible for experimentation and private deployment.
  - Strong structured-output/tool ecosystem in Alibaba Model Studio for many Qwen3 variants.
- Weaknesses:
  - Capability is highly variant-specific (`max`, `235b`, `thinking`, `instruct`, `3.5/3.6` families), so portability across SKUs is limited.
  - Structured output is not uniformly available in thinking mode for all routes.
- Context window:
  - Core Qwen3 flagship variants in Model Studio are commonly 256k (for example `qwen3-max`, `qwen3-235b-a22b` lines).
  - Newer Qwen3.5/3.6 variants can reach 1M depending on model ID.
- API availability:
  - Alibaba Model Studio (OpenAI-compatible mode and native DashScope APIs).
  - Open weights on Hugging Face/ModelScope for self-hosting.
- Reasoning ability: High (Qwen reports notable gains in reasoning/STEM/coding vs prior generations).
- Structured output support: Supported for many variants; not universal in thinking mode.

## Llama 4 Maverick

- Strengths:
  - Strong open-weight multimodal model with reported competitive reasoning/coding benchmark performance.
  - 1M context in Meta model card supports long essay/rubric/evidence workflows.
  - Broad deployment options: self-host, partner clouds, and emerging Llama API ecosystem.
- Weaknesses:
  - Structured-output guarantees are stack-dependent; for example, AWS Bedrock marks structured outputs as not supported for this model card.
  - API surface is fragmented across providers; output limits and feature flags vary by host.
- Context window: 1M (Meta model card for Maverick instruct).
- API availability:
  - Download/open weights on llama.com and Hugging Face.
  - Llama API announced by Meta as preview including Llama 4 models.
  - Managed partner APIs (for example Bedrock) are available with provider-specific limits.
- Reasoning ability: High (Meta-reported benchmark strength on reasoning/coding; competitive frontier-class profile in its segment).
- Structured output support:
  - No universal native guarantee at model level.
  - Provider-dependent; e.g., Bedrock model card indicates structured outputs not supported.

## Sources

- OpenAI GPT-5 model docs: https://developers.openai.com/api/docs/models/gpt-5
- OpenAI o3 model docs: https://developers.openai.com/api/docs/models/o3
- OpenAI structured outputs guide: https://developers.openai.com/api/docs/guides/structured-outputs
- Anthropic models overview: https://platform.claude.com/docs/en/about-claude/models/overview
- Anthropic model deprecations: https://platform.claude.com/docs/en/about-claude/model-deprecations
- Anthropic structured outputs / consistency docs:
  - https://platform.claude.com/docs/en/build-with-claude/structured-outputs
  - https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/increase-consistency
- Gemini 3.1 Pro model page: https://ai.google.dev/gemini-api/docs/models/gemini-3.1-pro
- DeepSeek API quickstart + models/pricing:
  - https://api-docs.deepseek.com/guides/reasoning_model
  - https://api-docs.deepseek.com/quick_start/pricing/
- DeepSeek-R1 official repository/model summary: https://github.com/deepseek-ai/DeepSeek-R1
- Qwen3 official blog: https://qwenlm.github.io/blog/qwen3/
- Alibaba Model Studio text model matrix: https://www.alibabacloud.com/help/en/model-studio/text-generation-model
- Qwen structured output docs: https://docs.qwencloud.com/developer-guides/text-generation/structured-output
- Meta Llama 4 release post: https://ai.meta.com/blog/llama-4-multimodal-intelligence/
- Meta LlamaCon / Llama API preview post: https://ai.meta.com/blog/llamacon-llama-news/
- Meta Llama 4 Maverick model card (HF): https://huggingface.co/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8
- AWS Bedrock Llama 4 Maverick model card: https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-meta-llama-4-maverick-17b-instruct.html
