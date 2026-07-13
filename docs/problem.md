# Cogni Problem Definition (AP Lang Fallacy Tutor)

## Objective
Build a small fine-tuned language model that teaches AP English Language students to identify logical fallacies through a strict, repeatable instructional sequence.

## Educational Problem
Students preparing for AP English Language and Composition often memorize fallacy definitions but struggle to recognize reasoning patterns in authentic arguments and transfer them to new contexts.

Prompted general models can often name fallacies, but they are unreliable tutors. They frequently skip steps, name multiple fallacies, reuse the student's scenario instead of teaching transfer, or simply judge correctness rather than teaching reasoning.

## Research Question
Can supervised fine-tuning teach a small language model to consistently identify one primary fallacy (or none) and teach it through a novel cross-domain analogy more reliably than prompting alone?

## Users
- Primary: AP English Language and Composition students.
- Secondary: Teachers who need consistent structured tutoring examples.

## Scope
In scope:
- Fallacy-focused AP tutoring behavior.
- Behavior-spec-driven dataset generation, training, and evaluation.
- Base-vs-tuned proof on a held-out benchmark.

Out of scope:
- Essay grading or AP score prediction.
- General writing tutoring.
- Broad English instruction beyond this behavior.

## Why Fine-Tuning (Not Prompting)
The target is not raw capability; it is protocol reliability. The model must execute the same seven-step instructional behavior every time, including adversarial attempts to bypass the process.
