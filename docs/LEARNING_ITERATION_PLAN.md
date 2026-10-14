# Grow Amoxcalli through small, reviewed learning units

> Current priorities, 12 October 2026: finish a usable learning unit before expanding general infrastructure. [Aves](http://127.0.0.1:8766/#aprender/aves) is available for study with four sourced passages, eight exercises and a final context comparison. Specialist review and learner trials remain separate pending milestones. Follow [PROPOSITO](PROPOSITO.md) and the revised [iteration method](TRABAJO_AUTONOMO.md). The institutional pilot has its own requirements. Dated cycle results below are historical evidence.

For each delivery, identify the learner task, make the change, check the affected behavior and record the result briefly. Do not spend another cycle packaging unchanged material or rerun retrieval measurements for presentation changes. Keep originals, answer keys and study progress. A new reading review packet is needed when its review material changes; navigation changes do not change the underlying passages.

Prepared 30 September 2026. The product remains centered on learning Náhuatl through examples, documented glyphs and their sources. The dictionary and corpus supply evidence; the laboratory explains model experiments. This plan defines the editorial cycle. The flor cycle and a second batch of three readings have been published as disclosed editorial drafts; dated results follow.

## First cycle result · 30 September 2026

[Flor v2 report](../reports/FLOR_CICLO_2026-09-30.md): cuicatl and Cacahuaxochitl entries added, full-word and visual scope clarified, source spelling exercise revised. Original passages and other lessons preserved. Linguistic/primary review and the [prepared beginner trial](../editorial/flor-beginner-trial.md) remain pending. After the first flor cycle the inventory covered 10 target meanings, 9 with images and 3 highlighted forms without exact records; the 8-meaning figures below describe the starting audit. Completed findings retain their original evidence snapshot in the decision history.

## Second reading batch · 30 September 2026

[lecturas-002](../reports/LECTURAS_002_2026-09-30.md) adds water and land, flowers and song, and birds across poems and chronicles. The current app has **6 readings / 24 passages / 6 works**, 12 target meanings with source images and 0 declaring primary-context verification. The original twelve passages and answer keys are unchanged. Existing cielo/lugares practice editions remain 1 while explanation revisions become 2.

The home page no longer promises one glyph per word. Quoted forms and dictionary references are displayed separately. Compound/thematic links and the single Moon passage are explained. Recipes in [the reading builder](LECTURAS_PIPELINE.md) make source/hash/exact-form exercise assembly repeatable; they do not certify linguistic interpretation. The current [audit](../reports/learning-audit-lecturas-002/inventory.md) has 36 tasks: 1 resolved editorially, 4 blocked and 31 open. The water/land preparation gap is now replaced by that reading's source, exercise and learner-trial checks.

Next, review these added contexts, obtain another Moon passage with explicit primary/variety evidence, resolve NIQUITTA/xochitli/tlacuilolcalli with competent linguistic review, and carry out a beginner trial. The dictionary batch batch-009-v11 was ready against the September lessons but became stale after the October comprehension update; the earlier batch-008-v10 lesson hash is also stale.

## Starting baseline

The reproducible [gap inventory](../reports/learning-audit/inventory.md) covers the three shipped lessons and their twelve passages. Detailed review packets preserve original Náhuatl, Spanish, source IDs, hashes, annotations and exercise keys. The audit uses a temporary catalogue of distributed records; it does not inspect or edit private user contributions.

| Finding | Evidence | Next decision |
|---|---|---|
| Linguistic and primary-source review still pending | Learning bundle is `editorial_draft`; source archive locations are rows rather than primary pages | Cotejar each packet; record responsible person, source location and corrections separately |
| Image presence exceeds recorded verification | All 8 target meanings have images; none has a glyph with recorded `documented_context` | Review actual use and scope; do not equate image coverage with correct readings |
| Several highlighted forms have no exact form record | NIQUITTA, Cacahuaxochitl, xochitli, tlacuilolcalli | Decide separately: inflected form, compound entry, spelling variant or thematic comparison; these labels are questions, not automatic analyses |
| A recurrent teaching concept is missing | cuicatl appears in two flor examples but has no exact dictionary form | Obtain lexical evidence and define a reviewed meaning before teaching it as a dictionary entry |
| Moon practice is thin | cielo annotates tonatiuh in 4 examples and metztli in 1 | Add another source passage supporting the moon objective; keep the month meaning separate |
| Sources are concentrated | All 12 selections use La tinta negra y roja | Add another work carefully, keeping context, variety and provenance |
| Exercises emphasize translation comprehension | 9 meaning questions and 3 source-form cloze questions | Ensure each objective also checks recognition of the Náhuatl form |
| Learner testing is not recorded in the lesson files | No trial record accompanies the current bundle | Run a small beginner trial; record observations and corrections rather than a satisfaction score alone |

There are **26 review tasks**, arranged into three lesson packets and shared lexical/visual decisions. This is a checklist, not 26 parallel projects. The initial focus is one packet: **flor**, with cuicatl and the exact status of its highlighted forms. Resolve shared dependencies once and reuse the decision with its appropriate context.

## A repeatable cycle

1. Select a packet and one observable learning objective.
2. Run the audit. It collects existing records and flags gaps without inventing entries, translations or glyph components.
3. Prepare a draft using the [lesson template](../templates/learning/LESSON_TEMPLATE.md). Keep original text and proposed corrections separate.
4. Review lexical meanings, source passages and visual scope. Add only supported records through the existing versioned catalogue workflow.
5. Validate the draft with the existing `Learning` source/hash/span/exercise checks, then exercise the learner interface. Technical validation never marks linguistic review complete.
6. Publish a disclosed reviewed pilot or a completed educational release only after the relevant checks. Run learner trials and incorporate observed corrections.
7. Regenerate the inventory. Keep unresolved evidence in the queue and move to the next packet.

A passage illustration is useful, but it is a different kind of connection from a documented glyph reading. Track those separately. A word with no known glyph may still belong in a good lesson with text evidence; forcing a picture onto every word is not a release requirement.

## Scope and limits for the next batch

**Original Stage A — repair the three initial packets.** Keep the current 12 original passages. The starting 8 target meanings may expand only to resolve an evidenced lesson dependency; flor v2 adds canto and the complete floral name, bringing the total to 10. Limit active work to one lesson packet plus at most two shared lexical/reference tasks. Prioritize P1 items. P2 items follow after the packet's core evidence is sound. A blocked task records the missing source or decision; do not silently turn it into an approved connection.

**Original Stage B — prepare three lesson drafts**, after Stage A identifies reusable evidence:

| Draft | One proposed objective | Candidate meanings | Evidence still needed |
|---|---|---|---|
| Flowers and trees | Recognize a flower/tree word in its source context | xochitl, cuahuitl, xochicuahuitl, itta, cuicatl | Lexical record for cuicatl; reviewed compound/form relationships and suitable original passages |
| Sun and moon | Distinguish the two referents in short passages | tonatiuh, metztli (luna), ihuan | More moon examples. Month and stars are optional later extensions, not extra objectives for this draft |
| Water and land | Recognize place/material words without replacing contextual meanings with literal glosses | atl, tlalli, tepetl, tetl, calli | Four short documented passages, especially for water; review of tepetl where the source translates city |

These are briefs, not populated lessons. Use fewer than five target meanings when it makes the objective clearer. Preserve the existing lugares lesson; any revised or new lesson needs its own version and source review. The batch recipe uses four examples; the UI now supports any positive count. Exercise types remain `meaning` and `cloze`; broader types need an implementation task.

Do not start a full dictionary overhaul, a new LLM training run or an open editing portal within this batch. When the editorial loop works on these small units, repeat it for another batch.

## Batch automation implemented

[Editorial pipeline](EDITORIAL_PIPELINE.md) now processes source pages, all lesson packets, lexical candidates and visual references together. It supports shared review decisions with item exceptions, evidence fingerprints and validated append-only assembly. [Published batch](../reports/PIPELINE_PUBLICACION_2026-09-30.md): 50 lexical entries and 39 contextual references incorporated after automated literal/source comparison; linguistic certification remains pending. All 10 current target meanings now have an image, while 0/10 declare primary-context verification. `run` performs preparation, comparison and assembly; `--apply` publishes an append-only distributed release with backup and preservation checks. The next batch is ready with 50 entries, 4 contextual links and 100 concordances. Concordances and annotation proposals remain unpublished evidence candidates for future lessons. Use the pipeline for subsequent batches instead of repeating manual word-by-word research. Linguistic/primary checks and real learner trials remain explicit exceptions.

## The prepared mechanism

```bash
.venv/bin/python -m nahuatl_local.lesson_audit
```

The command writes generated reports under `reports/learning-audit/`:

- `inventory.md`: readable findings and acceptance conditions.
- `inventory.json`: source-bound details and metrics.
- `flor-packet.json`, `cielo-packet.json`, `lugares-packet.json`: review packets.
- `review-queue.json`: stable task IDs, fingerprints, priority and effective state.

Human decisions belong in **`editorial/lesson-decisions.json`**, which the script never overwrites after creating an empty file. Copy the task ID and fingerprint from the generated queue; the [decision example](../templates/learning/lesson-decision.example.json) shows the structure. Supported states are `open`, `in_progress`, `blocked`, `resolved`, `deferred`. A resolution needs reviewer, date, evidence and an explicit outcome. A changed finding reopens the effective task; the old decision remains intact for inspection. A malformed state stops the audit. Do not edit generated reports as the authoritative review record.

To audit accepted catalogue changes, export a public research snapshot and select it explicitly:

```bash
.venv/bin/python -m nahuatl_local.platform export --purpose research --output editorial/catalog-public-v1.json
.venv/bin/python -m nahuatl_local.lesson_audit --catalog editorial/catalog-public-v1.json
```

The export command refuses to overwrite an existing file; use a new snapshot name. The audit validates that snapshot and rejects private/withdrawn records. `--lessons path/to/draft.json` selects a future lesson bundle in the existing `Learning` format, with real archive IDs and source hashes; it does not import or publish it. Use `--output` to keep a separate report directory for each draft. By default the audit uses the shipped lesson bundle and distributed catalogue, not the private live database; accepted edits become visible to it through the selected public snapshot.

The audit also checks exact forms within the annotated meaning, rather than accepting a homograph in another entry. Historical decisions include their original finding and fingerprint. The audit uses local records, no network or LLM calls. It does not change the live lesson bundle, private catalogue, model weights or training data. The existing glyph-linking script remains a contextual-reference aid; its output is not an editorial approval mechanism. A future review UI can present these packets and decisions once the workflow has been tested manually; it is not implemented by this preparation.

## What to count

Track source/translation review, form→meaning review, documented glyph readings/components, contextual visual aids, exercise review and beginner-trial outcomes separately. Report denominators and scope. At preparation, 8/8 target meanings have source images, while 0/8 have a glyph record declaring primary-context verification; this states the recorded review status, not that all eight connections are linguistically wrong.

Completion of a learning unit means an objective, source-bound examples, reviewed explanations and keys, explicit visual scope, appropriate attribution and a recorded release decision. A reviewed pilot may disclose pending usability testing; it must not claim beginner testing has already happened. No editorial task resolution grants model-training permission or moves reserved evaluation works into training.

## First working session

Open the flor packet and its four source passages. Resolve cuicatl's lexical evidence and the status of NIQUITTA, Cacahuaxochitl and xochitli. Review the existing visual references and exercise explanations against that evidence. Finish with a brief beginner trial of recognizing xochitl in another documented passage. Record decisions, regenerate the queue, and then take up cielo.

## Validation of this preparation

Five audit tests and six existing learning tests pass: stable inventory, distinction between image coverage and primary-context review, custom lesson IDs and missing dependencies, evidence-bound decisions, safe snapshot validation, preservation of human notes and unchanged source lessons. Report: [tests-lesson-audit-2026-09-30.txt](../reports/tests-lesson-audit-2026-09-30.txt). This validates the mechanism, not the linguistic correctness of the material.

## Iteración pictográfica · 7 de octubre de 2026

Se añadió el piloto documental descrito en [DICCIONARIO_PICTOGRAFICO](DICCIONARIO_PICTOGRAFICO.md). Antes de ampliar, probar el recorrido calli con lectores: ¿distinguen la denominación del elemento de la lectura del conjunto y pueden localizar la fuente? Registrar dudas por código de aparición. Revisión especializada pendiente; preservar las seis lecturas, primera página representativa y cuaderno. Ampliar después mediante el script por lotes, con excepciones documentadas y puentes explícitos.
