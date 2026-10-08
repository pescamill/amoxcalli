# amoxcalli · Scriptorium

[Español](../README.md)

**Learn Nahuatl by reading: find a word, recognize it in another passage, and follow it back to its source.**

Scriptorium brings short readings, a dictionary, documented glyph references and a bilingual archive into a local application. It starts with Classical Nahuatl. The wider archive preserves variety labels without treating all Nahuatl varieties as interchangeable. The aim is to give words context: where they appear, how they are written, what their sources support and what remains uncertain.

`amoxcalli` is the repository for this work in progress. Reading, search, practice and contributions already work. Linguistic review, primary-source checks and trials with learners are still needed. The model laboratory exposes experiments and their failures; generated translations are currently poor.

## Try it

With Python 3.11 or later, from the project directory:

```bash
bash scripts/plataforma.sh
```

Open [http://127.0.0.1:8766](http://127.0.0.1:8766). Reading, dictionary, archive and contribution features use Python's standard library. The interface is Spanish-first.

A small expedition: open **Flores y cantos**, hide the Spanish and click a familiar form. Save the word, find another example in the archive, then return to the exercise. Or try **Aves** and see what changes between a bird in poetry and birds in a narrative. Following these threads is part of the fun.

## What you can use it for

| Space | Current use |
| --- | --- |
| **Aprender / Leer** | Guided readings, contextual word help, optional Spanish and exercises that preserve source spelling; four source-based comprehension questions in Aves; browse the selected passages and notes. |
| **Diccionario** | Look up senses and historical forms, inspect documented visual references and follow citations. The first page keeps 24 representative entries; the rest sorts alphabetically in Nahuatl. Queries rank exact matches first and can continue into the archive when an entry is missing. |
| **Mis palabras** | Save words and practise at spaced intervals. Keep the source passage with a saved word and return to it during review. Progress belongs to the current browser; no account is required. |
| **Archivo y herramientas** | Search Spanish or Nahuatl, filter by work, variety or period, inspect sources and prepare exports with rights notes. |
| **Laboratorio** | Try example retrieval, limited lexical rules or experimental generation; inspect Spanish/Nahuatl training pairs and model reports. |
| **Aportar · Voces** | Propose text, voice, translations, forms and connections; record variety and permissions, review or withdraw contributions. |

Uses include personal study, textual research, preparing reading activities, collaborative editing and exploring model training. Classroom effectiveness still needs testing with people. The app is installable through the browser; mobile installation and microphone access require HTTPS. The local server must remain running, and the offline screen does not queue submissions. See the [installation guide](WEBAPP.md).

## Current content and open questions

Inventory incorporated on **30 September 2026**:

- **6 guided readings / 24 passages / 6 works**: flowers; Sun and Moon; land, house and hill; water and land; flowers and songs; birds.
- **575 dictionary entries/senses**: 26 curated and 549 automatically transcribed Molina/GDN entries, with 578 written forms.
- **140 visual-reference records**: 139 entries have source images, using 24 distinct documentary image URLs; 436 entries still need visual evidence.
- **16,111 Axolotl bilingual pairs**, with 33 identified works and original variety labels.
- **650 pairs actually visited by the historical adapter**, available in the training-data viewer.
- **5,462 pairs in the current Classical Nahuatl preparation**: 2,161 training, 2,049 validation and 1,252 test, split by work. Existing weights were trained on an earlier preparation.
- **36 reading-review tasks**: 1 resolved editorially, 4 blocked and 31 open. Primary-context checks for the target senses remain pending.

A visual link may show a whole-word glyph, a component, iconography or related contextual evidence. These are labelled separately. A source illustration does not establish how an entire sentence was written. Historical dictionary transcriptions also need interpretation; they are not automatically modern definitions or morphological analyses.

The [latest reading report](../reports/LECTURAS_002_2026-09-30.md) records changes and preservation checks. The previous local full run executed 179 tests with one expected failure for a disabled orthographic feature; six groups of interface checks passed. These establish technical behaviour, not philological correctness.

## Growing in batches

The [editorial pipeline](EDITORIAL_PIPELINE.md) gathers candidates from cached sources, prepares up to 50 entries and 100 concordances, verifies transcriptions and dependencies, separates exceptions and produces a reviewable proposal. Publication adds records with backups and preservation checks. Extraction and linking use scripts without LLM calls.

The [reading builder](LECTURAS_PIPELINE.md) uses explicit recipes: passage IDs, selected forms, notes and known distractors. It checks source hashes, connections and source-exact exercise answers. Selection and linguistic judgement remain editorial work.

```bash
python3 -m nahuatl_local.lesson_audit
python3 -m nahuatl_local.editorial_release --help
python3 -m nahuatl_local.lesson_builder --help
```

`batch-007-v9` is incorporated. `batch-009-v11` was prepared and verified but remains unpublished. The comprehension update on 7 October changed the reading hash; prepare a fresh batch ID using the local source-page cache before continuing. The earlier `batch-008-v10` became stale when the readings changed.

The next useful growth is more good contexts and fewer mistaken connections: expand readings through repeatable recipes, resolve ambiguities against primary sources, add images where evidence exists, and test whether learners understand the activities. The [iteration plan](LEARNING_ITERATION_PLAN.md) and [progress record](PROGRESO_INTERNO.md) retain decisions and open work.

## What happened to the LLM?

It is **Qwen3-0.6B adapted with LoRA**, with 1,146,880 trainable parameters: a 400-step pilot, a failed continuation and a corrected 250-step continuation. No base model was pretrained from scratch. It can repeat words, invent forms or alter meaning.

The laboratory shows training pairs, loss curves, outputs and historical metrics. Lower loss or a higher chrF++ on a small sample does not establish faithful translation. Results from different samples and preparations remain separate. Editing readings, expanding the dictionary or saving proposed pairs does not train the model.

For optional local generation, use Python 3.11/3.12:

```bash
bash scripts/iniciar.sh --enable-model
```

The first run installs dependencies and downloads the pinned base (~1.5 GB). Experimental `best` adapters are included; the base and optimizer states are excluded. Reports can be inspected without loading weights. This checkout cannot exactly resume the historical optimizer state.

A useful next experiment is to review alignments, then compare retrieval, the base and the adapter on the same held-out phrases. See the [model card](../MODEL_CARD.md), [model status](ESTADO_MODELO.md), [laboratory guide](LABORATORIO.md), [improvement guide](MEJORAR.md) and [staged training guide](AUTOTRAIN.md).

## Contributions, code and rights

Voces records independent publication and training permissions for text and audio. Manual or CSV training-pair proposals remain pending review. Profiles, recordings, submissions, SQLite databases and local backups are excluded from Git. Preserve and back up `data/community/` when updating; saved words and reading progress live in browser storage. See [Voces](VOCES.md) and the [architecture guide](PLATAFORMA.md).

The application uses Python, SQLite and HTML/CSS/JavaScript. Optional generation uses PyTorch, Transformers and PEFT; no external inference API is required.

```bash
python3 -m unittest discover -s tests
```

For interface checks (Node.js, development only):

```bash
npm ci --ignore-scripts
npm run test:ui
npm run test:offline
```

Some training and editorial integration checks require extra dependencies, prepared data or cached source pages, as described in their guides.

Original code and documentation use [MIT](../LICENSE). Qwen uses Apache-2.0; Elotl's distribution declares MPL-2.0. Rights in each underlying work, edition and translation need separate review. Texts, images and derived adapters are not relicensed as MIT. Images are linked with source attribution; no generated images are added. See [sources](FUENTES.md) and [third-party notices](../THIRD_PARTY_NOTICES.md) before reusing or redistributing content.
