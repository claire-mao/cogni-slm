# Cogni Literature Review

## 1. Purpose and Scope
This review summarizes relevant prior work to guide Cogni's implementation phase.

It focuses on:
- logical fallacy tutoring and fallacy-focused NLP
- analogical reasoning in education
- transfer learning in education-related NLP
- instruction tuning and behavior alignment
- parameter-efficient fine-tuning methods (LoRA, QLoRA, PEFT, Unsloth)
- base model selection rationale for Qwen3-1.7B

No experimental outcomes are reported for Cogni in this document.

## 2. Existing Work on Logical Fallacy Tutoring

### 2.1 Educational interventions and tutoring formats
Work on explicit fallacy instruction includes both course interventions and interactive tools.

Key examples:
- **Argotario** introduced a serious-game format for fallacy practice in everyday argumentation.
- Behavioral-education studies (for example, equivalence-based instruction protocols) show that fallacy identification can be explicitly trained.
- Online interventions for informal fallacy detection (including fake-news contexts) indicate measurable learning gains are possible with short instructional modules.

Implication for Cogni:
- A tutoring model should prioritize practice-oriented feedback loops (attempt -> critique -> correction), not only static definitions.

### 2.2 Computational fallacy analysis as infrastructure
Recent NLP work contributes datasets and benchmarks rather than tutoring flows.

Key examples:
- LOGIC/LogicClimate frame fallacy detection as supervised NLP classification.
- MAFALDA consolidates fallacy resources into a benchmark-oriented structure.
- CoCoLoFa expands scale with crowd/LLM-assisted annotation.
- LOGICOM studies LLM susceptibility to fallacious arguments in debate settings.

Implication for Cogni:
- Existing corpora and taxonomies can bootstrap evaluation and coverage planning, but tutoring behavior design still needs dedicated scaffolding.

## 3. Analogical Reasoning in Education

### 3.1 Cognitive foundations
Structure-mapping theory defines analogy as relational mapping between source and target domains, emphasizing relation structure over superficial similarity.

Analogical encoding research in educational psychology links comparison-based instruction to better transfer.

### 3.2 Educational synthesis
Education reviews highlight analogy as a mechanism for higher-order reasoning and transfer when mappings are explicit and constraints are stated.

Implication for Cogni:
- The behavior specification requirement for `analogy.mapping` and `analogy.limits` is consistent with literature that warns against surface-level metaphors.

## 4. Transfer Learning in Education-Oriented NLP

### 4.1 General NLP transfer paradigm
The text-to-text transfer framing (for example, T5) demonstrates that broad pretraining plus task-specific finetuning can generalize across heterogeneous tasks.

### 4.2 Education-task evidence
Education-focused NLP tasks (for example, automated essay scoring and reading-comprehension scoring) show practical transfer patterns:
- gains from pretrained encoders
- cross-prompt or out-of-domain transfer setups
- importance of careful domain shift handling

Implication for Cogni:
- A small, broadly capable base model with targeted supervision is a credible strategy for an educational fallacy tutor.

## 5. Instruction Tuning and Behavior Alignment

Instruction-following work (FLAN) established multi-task instruction tuning as a strong zero-shot and transfer lever.

Alignment work then expanded behavior control:
- InstructGPT (SFT + preference optimization pipeline)
- Constitutional AI / RLAIF-style critique-revision principles
- DPO-style direct preference optimization without explicit reward-model PPO loops

Implication for Cogni:
- Behavior alignment should be treated as first-class model objective, not a post-hoc prompt patch.
- Cogni's current behavior contract and planned critique-revision data generation are directionally aligned with this literature.

## 6. QLoRA, LoRA, PEFT, and Unsloth

### 6.1 LoRA and QLoRA
- **LoRA** introduces low-rank adapters on frozen base weights to reduce trainable parameters.
- **QLoRA** combines LoRA with 4-bit quantized base weights to reduce memory while preserving strong finetuning behavior.

For Cogni, these are relevant because they allow iterative alignment experiments on modest hardware budgets.

### 6.2 PEFT ecosystem
Hugging Face PEFT/Transformers integration provides operational adapter workflows:
- adapter attach/train/save/load
- multi-adapter management
- quantized base model support for QLoRA-style workflows

This lowers engineering overhead for experiment velocity and reproducibility.

### 6.3 Unsloth as practical execution stack
Unsloth documentation positions LoRA/QLoRA as default-efficient routes before full finetuning, with support for low-memory paths and model-specific fine-tuning guides.

Implication for Cogni:
- Unsloth is a practical implementation accelerator for the planned PEFT-first training approach.

## 7. Why Qwen3-1.7B is an Appropriate Base Model

Based on public model-card and technical-report material, Qwen3-1.7B is a strong fit for Cogni's constraints.

### 7.1 Fit to project constraints
- **Scale fit**: 1.7B parameters support small-model objectives.
- **License fit**: Apache 2.0 supports open research/development workflows.
- **Context fit**: 32k context length supports richer tutoring prompts and multi-part outputs.
- **Instruction/reasoning fit**: Qwen3 family design includes both thinking and non-thinking mode controls.
- **Language fit**: broad multilingual support can support future expansion.

### 7.2 Operational fit
- broad ecosystem compatibility (Transformers, vLLM, SGLang, quantization toolchains)
- active adapter and finetune ecosystem on Hugging Face

### 7.3 Caveats and assumptions to validate
- A1: Qwen3-1.7B can maintain high behavior-spec compliance after domain tuning.
- A2: reasoning mode controls do not conflict with deterministic output-structure requirements.
- A3: 1.7B capacity is sufficient for high-quality analogy generation plus fallacy discrimination.

## 8. Synthesis for Cogni Implementation
The reviewed literature supports a concrete implementation posture:
- behavior-aligned instruction tuning over generic generation
- explicit analogy mapping and limitation fields for educational transfer
- PEFT-first training strategy (LoRA/QLoRA), with optional Unsloth acceleration
- benchmark design that tests both fallacy correctness and pedagogy robustness

## 9. References

Logical fallacy tutoring and fallacy NLP:
- Argotario: Computational Argumentation Meets Serious Games (arXiv): https://arxiv.org/abs/1707.06002
- Comparing equivalence-based instruction protocols for teaching logical fallacies (Wiley): https://onlinelibrary.wiley.com/doi/10.1002/bin.1772
- Learning critical thinking skills online with informal fallacy focus (PMC): https://pmc.ncbi.nlm.nih.gov/articles/PMC10103667/
- Learning about informal fallacies and fake news intervention (PMC): https://pmc.ncbi.nlm.nih.gov/articles/PMC10057814/
- Logical Fallacy Detection (LOGIC/LogicClimate): https://arxiv.org/abs/2202.13758
- MAFALDA benchmark: https://arxiv.org/abs/2311.09761
- CoCoLoFa dataset: https://arxiv.org/abs/2410.03457
- LOGICOM susceptibility benchmark: https://arxiv.org/abs/2308.09853

Analogical reasoning in education:
- Structure-mapping theory (Gentner, 1983): https://www.sciencedirect.com/science/article/pii/S0364021383800093
- Learning and transfer via analogical encoding (Gentner et al., 2003): https://experts.illinois.edu/en/publications/learning-and-transfer-a-general-role-for-analogical-encoding/
- Analogy, higher order thinking, and education (Richland, 2015): https://wires.onlinelibrary.wiley.com/doi/10.1002/wcs.1336
- Relational reasoning in education (npj Science of Learning): https://www.nature.com/articles/npjscilearn20164

Transfer learning and alignment:
- T5 transfer learning framework: https://www.jmlr.org/papers/v21/20-074.html
- BERT transfer in AES (out-of-domain transfer): https://arxiv.org/abs/2205.03835
- Automated reading-comprehension scoring with pretrained LMs: https://arxiv.org/abs/2205.09864
- FLAN instruction tuning: https://arxiv.org/abs/2109.01652
- Flan Collection: https://arxiv.org/abs/2301.13688
- InstructGPT / RLHF: https://arxiv.org/abs/2203.02155
- Constitutional AI: https://arxiv.org/abs/2212.08073
- DPO: https://arxiv.org/abs/2305.18290

PEFT and model/tooling stack:
- LoRA: https://arxiv.org/abs/2106.09685
- QLoRA: https://arxiv.org/abs/2305.14314
- PEFT in Transformers docs: https://huggingface.co/docs/transformers/main/peft
- Unsloth fine-tuning guide: https://unsloth.ai/docs/get-started/fine-tuning-llms-guide
- Unsloth repository: https://github.com/unslothai/unsloth

Qwen3 sources:
- Qwen3 Technical Report: https://arxiv.org/abs/2505.09388
- Qwen3-1.7B model card: https://huggingface.co/Qwen/Qwen3-1.7B
