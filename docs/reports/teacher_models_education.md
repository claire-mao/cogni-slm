# Teacher Models on Educational Assessment Benchmarks (as of July 9, 2026)

This report summarizes published benchmark evidence for:

- essay grading
- rubric following
- educational feedback
- logical fallacy identification
- argument quality assessment
- consistency across repeated evaluations

Scope notes:

- I used benchmark papers, technical reports, and official docs where available.
- For some requested models, direct education-task benchmarks are still sparse; in those cases, I list the closest available published evidence and explicitly mark gaps.
- No model recommendation is made in this document.

## GPT-5

- Essay grading: In a K-12 rubric-scoring study (MCAS-based), GPT-5 showed high agreement in math (`QWK 0.951`, `PRMSE 0.946`, `83.9%` exact agreement), moderate results in science (`QWK 0.831`, `PRMSE 0.854`), and weaker ELA writing alignment (`QWK 0.495`, `PRMSE 0.231`, `30.9%` exact agreement). [1]
- Rubric following: In RuVerBench rubric verification (agentic tasks), GPT-5.4 scored `91.4` (Deep Research overall) and `89.4` (Agentic Coding overall) on Avg Balanced Accuracy. [2]
- Educational feedback: The same K-12 study reports teacher/student acceptance was stronger for narrative AI feedback than for numeric scores; GPT-5 was part of that comparison set. [1]
- Logical fallacy identification: No direct published fallacy-identification benchmark result for GPT-5 was located.
- Argument quality assessment: No direct published argument-quality benchmark result for GPT-5 was located.
- Consistency across repeated evaluations: In RuVerBench error-profile analysis, GPT-5.4 exhibited a distinct judge profile (more strict on some coding rubrics), indicating non-trivial variance by rubric type/domain. [2]

## o3

- Essay grading: No direct o3 essay-grading benchmark with human-rater statistics was located.
- Rubric following: No direct o3 result in the rubric-verification benchmarks used here (RubricEval, RuVerBench).
- Educational feedback: In the "Arena for Learning" benchmark (`N=189` educators for interactions, `N=206` expert judges), Gemini 2.5 Pro was preferred over OpenAI o3 in `74.2%` of head-to-head pedagogical-quality matchups (excluding ties). [3]
- Logical fallacy identification: No direct published fallacy benchmark result for o3 was located.
- Argument quality assessment: No direct published argument-quality benchmark result for o3 was located.
- Consistency across repeated evaluations: No direct repeated-run reliability study for o3 on educational grading was located.

## Claude Opus 4

- Essay grading: No direct published Opus-4 essay-grading benchmark with human-rater agreement metrics was located.
- Rubric following: In RuVerBench, Claude Opus 4.7 scored `91.7` (Deep Research) and `85.0` (Agentic Coding) Avg Balanced Accuracy. [2]
- Educational feedback: No direct Opus-4 educational-feedback benchmark in classroom grading/tutoring settings was located.
- Logical fallacy identification: No direct published Opus-4 fallacy-identification result was located.
- Argument quality assessment: No direct published Opus-4 argument-quality benchmark result was located.
- Consistency across repeated evaluations: RuVerBench reports low overlap between error sets of top models (including Opus 4.7), implying model-specific rubric failure modes rather than one common failure set. [2]

## Claude Sonnet 4

- Essay grading: In the K-12 MCAS-based rubric study, Sonnet 4 had math `QWK 0.808` (`PRMSE 0.730`), science `QWK 0.818` (`PRMSE 0.843`), and ELA writing `QWK 0.755` (`PRMSE 0.668`, `44.0%` exact agreement). [1]
- Rubric following: In RuVerBench, Sonnet 4.6 scored `89.4` (Deep Research) and `83.0` (Agentic Coding) Avg Balanced Accuracy. [2]
- Educational feedback: Direct Sonnet-4-specific comparative feedback-quality benchmarks are limited in public literature; available educational-feedback studies are stronger for Claude 3.x and mixed-model cohorts. [4][5]
- Logical fallacy identification: No direct Sonnet-4 fallacy-identification benchmark result was located.
- Argument quality assessment: No direct Sonnet-4 argument-quality benchmark result was located.
- Consistency across repeated evaluations: Domain gaps in [1] (math/science vs ELA) and category gaps in [2] (e.g., lower Tools score) indicate materially different behavior across task types.

## Gemini 2.5 Pro

- Essay grading: In one higher-education rubric essay-scoring study (67 essays, three replications/model), Gemini 2.5 had low human agreement (`QWK 0.00`, non-significant) and weak within-model concordance in repeated runs (reported with low Kendall's W patterns). [4]
- Rubric following: No direct Gemini 2.5 Pro entry in RuVerBench (Gemini 3.1 is evaluated there), but RubricEval shows rubric-level judging remains difficult even for strong frontier judges. [6][2]
- Educational feedback: In Arena for Learning, Gemini 2.5 Pro ranked first overall and was preferred in `73.2%` of matchups (excluding ties), with leading pedagogy-rubric outcomes in that benchmark. [3]
- Logical fallacy identification: No direct Gemini 2.5 Pro fallacy-identification benchmark result was located.
- Argument quality assessment: No direct Gemini 2.5 Pro argument-quality benchmark result was located.
- Consistency across repeated evaluations: Evidence is mixed by context: strong pedagogy preference in [3], but weak score reproducibility/alignment in one essay-scoring setup in [4].

## DeepSeek R1

- Essay grading: In a Scientific Reports higher-education grading benchmark, DeepSeek-R1 is reported as the closest to human evaluation in both numeric grading and feedback quality among six tested models. [5]
- Rubric following: No direct DeepSeek-R1 result in RuVerBench (DeepSeek V4 variants are reported there). [2]
- Educational feedback: In [5], DeepSeek-R1 led textual similarity/quality metrics against human feedback in that course-specific setting.
- Logical fallacy identification: In ArgBench, fallacy detection is one of the core evaluated skills; DeepSeek-R1-32B is among the strongest open-weight families on several argumentation subtasks. [7]
- Argument quality assessment: ArgBench reports DeepSeek-R1-32B as top on argument rating (`F1 0.562`) in its leave-one-task-out setup, with transfer gains for the DeepSeek-R1 family on argument-rating tasks. [7]
- Consistency across repeated evaluations: Cross-study evidence differs by setup; in [4], DeepSeek v2 (not R1) was closer to human scores than peers in that dataset, while [5] reports strong R1 alignment in a different course and rubric design.

## Qwen3

- Essay grading: No direct published Qwen3 essay-grading benchmark with human-rater agreement metrics was located.
- Rubric following: RuVerBench includes Qwen3.6 Max and Qwen3.5 variants; Qwen3.6 Max scored `90.6` (Deep Research) and `79.9` (Agentic Coding) Avg Balanced Accuracy, with smaller Qwen variants lower. [2]
- Educational feedback: No direct Qwen3 educational-feedback benchmark in classroom tutoring/grading was located.
- Logical fallacy identification: ArgBench includes fallacy-detection tasks and reports Qwen3-family failure modes under chain-of-thought prompting (including frequent unfinished reasoning traces for Qwen3-32B in long argument tasks). [7]
- Argument quality assessment: ArgBench shows larger Qwen3 models outperform smaller Qwen3 models on macro argumentation scores, but argument-quality tasks remain difficult overall. [7]
- Consistency across repeated evaluations: ArgBench error analysis reports token-budget/exhaustion behaviors for Qwen3-32B that can degrade stable completion in long-form reasoning settings. [7]

## Llama 4 Maverick

- Essay grading: A 2026 essay-assessment framework paper (Computers and Education: AI) explicitly includes Llama 4 Maverick in repeated-run reliability and human-alignment analysis; full numeric tables are not openly accessible in this environment, but the abstract reports substantial inter-model differences in reproducibility and alignment. [8]
- Rubric following: No direct Llama 4 Maverick result in RubricEval or RuVerBench.
- Educational feedback: No direct Llama 4 Maverick educational-feedback benchmark with classroom feedback-quality metrics was located.
- Logical fallacy identification: No direct Llama 4 Maverick fallacy-identification benchmark result was located.
- Argument quality assessment: No direct Llama 4 Maverick argument-quality benchmark result was located.
- Consistency across repeated evaluations: Public, model-specific repeated-run educational-grading evidence for Maverick remains limited; most detailed consistency studies still report Llama 3.x or mixed open-weight cohorts. [9][10]

## Cross-Model Observations from Published Benchmarks

- Essay grading remains domain-sensitive: closed-ended/procedural subjects score much higher than open-ended ELA writing in the same pipelines. [1]
- Rubric verification performance is high for top frontier models but still leaves meaningful residual error, especially in long, tool-using traces. [2][6]
- Educational-feedback quality and numeric-score agreement can diverge: several studies report acceptable feedback usefulness but weak human-score agreement/reliability for some settings. [1][4][5]
- Argument quality and fallacy-related tasks remain difficult even for strong models; improvements are task- and prompt-regime dependent rather than uniform. [7]

## References

[1] Tian et al. (2026). *Creating and Evaluating K-12 GenAI Assessment Graders Through Context Engineering*. arXiv:2606.12422. https://arxiv.org/abs/2606.12422  
[2] Peng et al. (2026). *Can LLM-as-a-Judge Reliably Verify Rubrics in Agentic Scenarios?* arXiv:2606.29920. https://arxiv.org/abs/2606.29920  
[3] LearnLM Team Google (2025). *Evaluating Gemini in an Arena for Learning*. arXiv:2505.24477. https://arxiv.org/abs/2505.24477  
[4] Gaggioli et al. (2025). *Assessing the Reliability and Validity of Large Language Models for Automated Assessment of Student Essays in Higher Education*. arXiv:2508.02442. https://arxiv.org/abs/2508.02442  
[5] Saez et al. (2026). *Evaluating large language models for AI-assisted grading: a framework and case study in higher education*. Scientific Reports 16, 18035. https://doi.org/10.1038/s41598-026-48656-3  
[6] Pan et al. (2026). *RubricEval: A Rubric-Level Meta-Evaluation Benchmark for LLM Judges in Instruction Following*. arXiv:2603.25133. https://arxiv.org/abs/2603.25133  
[7] Ajjour et al. (2026). *ArgBench: Benchmarking LLMs on Computational Argumentation Tasks*. arXiv:2604.17366. https://arxiv.org/abs/2604.17366  
[8] *A framework for evaluation of large language models in essay assessment: Reliability, alignment, and causal reasoning*. Computers and Education: Artificial Intelligence (2026), Article S2666920X26000275. https://www.sciencedirect.com/science/article/pii/S2666920X26000275  
[9] Mathew et al. (2026). *LLMs Do Not Grade Essays Like Humans*. arXiv:2603.23714. https://arxiv.org/abs/2603.23714  
[10] Kucia et al. (2026). *LLM Essay Scoring Under Holistic and Analytic Rubrics: Prompt Effects and Bias*. arXiv:2604.00259. https://arxiv.org/abs/2604.00259
