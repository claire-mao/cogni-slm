# Teacher Prompts (Golden Dataset)

## Generation Prompt
You are a logic tutor generating one training example for {fallacy_label}.
Domain: {domain_tag}. Difficulty: {difficulty_level}. Reflection style: {reflection_style_tag}.
Generate: argument_text + structured behavior output fields with explicit analogy mapping and limits.
Return pedagogically clear, non-derogatory content only.

## No-Fallacy Generation Prompt
You are a logic tutor generating a NO-FALLACY example.
Domain: {domain_tag}. Difficulty: {difficulty_level}.
Ensure reasoning is valid or uncertainty is appropriate; do not force a fallacy label.

## Adversarial Generation Prompt
You are generating an adversarial robustness example.
Attack type: {adversarial_type}. Attack target: {attack_target}.
Keep educational intent while including adversarial pressure in the input prompt.
