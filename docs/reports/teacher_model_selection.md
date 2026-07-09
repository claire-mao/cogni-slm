# Teacher Model Selection Synthesis (as of July 9, 2026)

This report combines:

- `/docs/reports/teacher_models_overview.md`
- `/docs/reports/teacher_models_education.md`
- `/docs/reports/teacher_models_deployment.md`

for model-selection planning in educational assessment.

## GPT-5

- Educational reasoning: Strong on structured K-12 grading workflows, with high agreement in math and moderate results in science; ELA writing alignment was materially weaker in one MCAS-based study.
- Rubric adherence: Strong in rubric-verification benchmarks; among top reported performers in agentic rubric checking.
- Logical reasoning: Strong, with configurable reasoning effort and high performance on multi-step evaluation tasks.
- Hallucination tendencies: Lower than many earlier models in constrained grading prompts, but not eliminated; weaker performance on open-ended writing domains suggests vulnerability when rubric interpretation is ambiguous.
- Cost: API list pricing is moderate-to-high for output-heavy grading pipelines.
- Deployment: API-first deployment via OpenAI; no local/open-weight option.
- Strengths: Strong schema-constrained outputs, large context window, reliable API tooling.
- Limitations: Model generation has been superseded, and published grading quality is uneven across subject types.

## o3

- Educational reasoning: Limited direct education benchmark coverage in the current literature; indirect evidence shows it can be outperformed on pedagogical quality in tutor-style interactions.
- Rubric adherence: No direct published rubric-verification result in the benchmark set used in prior reports.
- Logical reasoning: Very strong general logical/multi-step reasoning profile.
- Hallucination tendencies: Not well quantified for educational grading specifically; behavior depends heavily on prompt scaffolding and verification loops.
- Cost: Higher input pricing than GPT-5 in the compared API schedules.
- Deployment: API-first via OpenAI; no local/open-weight option.
- Strengths: Strong reasoning depth, structured output support, mature API.
- Limitations: Sparse direct educational-assessment evidence and weaker relative pedagogical preference in available head-to-head educational benchmark data.

## Claude Opus 4 (active family snapshots)

- Educational reasoning: Sparse direct essay-grading evidence in public benchmarks; evidence is stronger for general long-context reasoning and rubric verification.
- Rubric adherence: Strong rubric-verification performance in RuVerBench.
- Logical reasoning: Very strong across long-context and complex instruction settings.
- Hallucination tendencies: Better controlled than older generations in many tasks, but still requires strict schema/prompt guardrails for grading reliability.
- Cost: Highest-cost profile among compared mainstream API families.
- Deployment: API deployment through Anthropic and partner clouds; no local/open-weight option.
- Strengths: High capability ceiling, strong rubric-verification performance, long context.
- Limitations: Higher cost and limited direct education-task benchmarking at model-specific granularity.

## Claude Sonnet 4 (active family snapshots)

- Educational reasoning: Mixed but practical profile; stronger than some peers in ELA-writing alignment in one K-12 study, with lower math agreement than GPT-5 in the same setup.
- Rubric adherence: Strong but below top Opus/GPT entries in some rubric-verification slices.
- Logical reasoning: Strong reasoning for production use with better efficiency than Opus class.
- Hallucination tendencies: Generally manageable under constrained prompts; still sensitive to task domain and rubric ambiguity.
- Cost: Mid-tier cost profile, substantially lower than Opus class.
- Deployment: API via Anthropic and partner clouds; no local/open-weight option.
- Strengths: Good cost-performance balance, strong structured output support, scalable for high-volume grading.
- Limitations: Performance variability across task categories and less headroom than highest-capability models.

## Gemini 2.5 Pro

- Educational reasoning: Strong pedagogical interaction quality in Arena for Learning, but mixed evidence in essay-score alignment and repeatability across runs.
- Rubric adherence: No direct model-specific RuVerBench entry in the prior benchmark set; rubric-following performance remains task-sensitive.
- Logical reasoning: Very strong on complex reasoning and long-context synthesis tasks.
- Hallucination tendencies: Can be reduced with grounded prompting, but long-form thinking mode and open-ended tasks still require verification for grading-critical outputs.
- Cost: Competitive for smaller prompts, higher for larger-context and output-heavy jobs.
- Deployment: API via Gemini API/Vertex AI; no open-weight local deployment.
- Strengths: Strong educational feedback interactions, very large context window, robust API ecosystem.
- Limitations: Mixed essay-grading reliability evidence and dynamic/usage-tier quota management.

## DeepSeek R1

- Educational reasoning: Strong in some higher-education grading studies, including reported closeness to human grading and feedback quality in course-specific evaluations.
- Rubric adherence: Direct DeepSeek-R1 rubric-verification evidence is limited in current public benchmark tables.
- Logical reasoning: Strong, especially relative to other open-weight families on reasoning and argumentation tasks.
- Hallucination tendencies: Open-weight reasoning traces can degrade under poor prompting/decoding; completion quality is more sensitive to inference setup than closed APIs.
- Cost: Very low managed-API pricing in current published DeepSeek schedules; can be even lower with optimized local inference depending on hardware.
- Deployment: Both API and local/self-host options; open weights under permissive license.
- Strengths: Cost efficiency, deployment flexibility, strong reasoning value for open model workflows.
- Limitations: Provider transition around alias endpoints, larger ops burden for stable local production behavior, and fewer standardized education benchmarks than top closed models.

## Qwen3

- Educational reasoning: Public education-specific results are limited; strongest evidence is from general reasoning/argument benchmarks and rubric-verification tasks on selected Qwen3.x variants.
- Rubric adherence: Competitive on some rubric-verification benchmarks (especially larger Qwen3.x variants), but with notable variance by model size/version.
- Logical reasoning: Strong across larger variants, with clear performance spread across the family.
- Hallucination tendencies: Documented risk of incomplete or unstable long-form reasoning traces in some variants under high reasoning load.
- Cost: Favorable for many hosted Qwen variants, but pricing varies significantly by model ID, mode (thinking/non-thinking), and region.
- Deployment: API via Model Studio plus local deployment for open-weight checkpoints; mixed proprietary/open model lineup.
- Strengths: Broad model choice, strong cost flexibility, local deployment path for many checkpoints.
- Limitations: High configuration complexity and less predictable portability across variants/providers.

## Llama 4 Maverick

- Educational reasoning: Direct educational-assessment benchmark coverage is still limited; available evidence is more general-purpose and mixed-model.
- Rubric adherence: No strong model-specific public rubric benchmark record in the current report set.
- Logical reasoning: Strong open-weight logical/coding capability profile with long context.
- Hallucination tendencies: Varies by serving stack and prompt policy; lack of universal structured-output guarantees increases risk in strict grading pipelines.
- Cost: Depends heavily on provider (Bedrock/other managed routes) or local hardware economics.
- Deployment: Broad deployment flexibility (API via cloud providers plus local/open-weight deployment), with commercial use governed by Llama community license terms.
- Strengths: 1M context, open-weight access, broad deployment optionality.
- Limitations: Inconsistent structured-output behavior across platforms and sparse education-specific benchmark evidence.

## Single Teacher vs Multiple Teachers

- A single teacher model is simpler to operate: one prompt stack, one calibration curve, one failure profile, and lower orchestration overhead.
- A single teacher model is easier to monitor for drift and easier to audit for compliance because outputs are generated under one model policy surface.
- Multiple teachers can reduce systematic bias: if one model consistently over-penalizes style, another may preserve content quality, improving aggregate supervision.
- Multiple teachers increase complexity: routing, aggregation logic, disagreement handling, version pinning, and cost accounting all become first-class engineering problems.
- Multiple teachers can introduce instability if prompts are not normalized across models; disagreement may come from formatting differences rather than quality differences.

## When an Ensemble Can Improve Supervision Quality

- Cross-domain assessments: combine a strong rubric-follower with a strong reasoning model when tasks mix short-answer scoring and open-ended argument analysis.
- Ambiguous rubric items: use independent scoring and a reconciliation stage when rubric language is subjective or has historically low inter-rater agreement.
- High-stakes evaluation: require consensus or adjudication when score differences cross a defined threshold.
- Feedback generation: pair a scoring-focused teacher with a pedagogy-focused teacher to separate numeric judgment from instructional feedback tone and usefulness.
- Fallacy and argument analysis: combine a reasoning-heavy model with an argumentation-strong open model to reduce missed logical errors.

## Local vs API-Based Teachers

- API-based teachers:
  - Faster to launch, easier to maintain, and usually stronger out of the box.
  - Better for teams prioritizing reliability, managed scaling, and low infrastructure overhead.
  - Tradeoffs: recurring token cost, vendor lock-in risk, external dependency, and tighter policy/rate-limit constraints.
- Local teachers:
  - Better for data residency/privacy constraints, cost control at high volume, and custom fine-tuning workflows.
  - Better for reproducibility control when you pin exact checkpoints and inference settings.
  - Tradeoffs: significant infrastructure and MLOps burden, hardware cost, model-serving optimization work, and higher variance if inference settings are not tightly controlled.
- Hybrid approach:
  - Use API models for highest-stakes or hardest evaluations.
  - Use local models for draft scoring, pre-filtering, or secondary checks.
  - Escalate low-confidence or high-disagreement cases to stronger API teachers.

## Consolidated References

- `/Users/clairemao/Documents/cogni-slm/docs/reports/teacher_models_overview.md`
- `/Users/clairemao/Documents/cogni-slm/docs/reports/teacher_models_education.md`
- `/Users/clairemao/Documents/cogni-slm/docs/reports/teacher_models_deployment.md`
