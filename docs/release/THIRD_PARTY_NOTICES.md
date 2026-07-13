# Third-Party Dataset Evidence

This is a provenance and release-gating record, not legal advice.

## Argotario English data

- Source: <https://github.com/UKPLab/argotario>
- Local evidence: `datasets/raw/fallacy/source_files/argotario/README.md`
- Dataset declaration: the upstream README states that the English data in
  `data/arguments-en-2018-01-15.tsv` are available under CC0 1.0.
- Status: approved for public dataset use, with citation requested by the authors.

## Logical Fallacy Detection / LogicClimate

- Source: <https://github.com/causalNLP/logical-fallacy>
- Local evidence: `datasets/raw/fallacy/source_files/logical-fallacy/README.md`
- Finding: the repository snapshot contains no LICENSE/COPYING file. “Feel free to
  access” is not treated as an explicit redistribution license.
- Status: blocked from public redistribution until the owners provide terms.

## Logical Fallacy Detection intermediate quiz corpus

- Source location:
  `codes_to_get_data/intermediate_data_files/20210901_final_data.csv`
- Finding: aggregated quiz-derived content has no clear redistribution grant in the
  repository and may carry third-party rights.
- Status: blocked from public redistribution and should be excluded from a public
  dataset/model release unless permission is established.

## MAFALDA gold and unannotated data

- Source: <https://github.com/ChadiHelwe/MAFALDA>
- Local evidence: `datasets/raw/fallacy/source_files/MAFALDA/README.md`
- Finding: the repository snapshot contains no license file and the README supplies a
  citation but no explicit redistribution license. The unannotated set also incorporates
  material from underlying corpora whose terms must be traced.
- Status: blocked from public redistribution until explicit terms are obtained.

## Release consequence

The current mixed-source dataset and model must remain private. A public release can
proceed only after either:

1. written permission/license evidence is added for every blocked source, or
2. a new dataset and model are built exclusively from approved sources.
