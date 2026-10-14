# amoxcalli · Amoxcalli

[Español](../README.md)

**Learn to read Classical Nahuatl through sourced examples: understand a passage, compare it, and return to the document.**

Amoxcalli brings short readings, a dictionary, documented glyph references and a bilingual archive into a local application. It starts with Classical Nahuatl. The wider archive preserves variety labels without treating all Nahuatl varieties as interchangeable. The aim is to give words context: where they appear, how they are written, what their sources support and what remains uncertain.

`amoxcalli` is the repository for this work in progress. Reading, search, practice and contributions already work. Linguistic review, primary-source checks and trials with learners are still needed. The model laboratory exposes experiments and their failures; generated translations are currently poor.

The priority is a reading that people can understand and verify. Teaching a living variety needs a path agreed with its speakers, their own materials and appropriate review; that course is not available here yet. See [purpose and priorities](PROPOSITO.md), the [proposed institutional pilot](PILOTO_INSTITUCIONAL.md) and [contribution guide](../CONTRIBUTING.md), currently in Spanish. No institutional endorsement or certification is claimed.

## Try it

With Python 3.11 or later, from the project directory:

```bash
bash scripts/plataforma.sh
```

Open [http://127.0.0.1:8766](http://127.0.0.1:8766). Reading, dictionary, archive and contribution features use Python's standard library. The interface is Spanish-first.

A small expedition: open **Flores y cantos**, hide the Spanish and click a familiar form. Save the word, find another example in the archive, then return to the exercise. Or try **Aves** and see what changes between a bird in poetry and birds in a narrative. Following these threads is part of the fun.

The interface follows a reading-book composition: ochre cover, red ink, chapters and notes beside the passages. Documentary glyphs keep their source links; the geometric border is original ornament. The [identity and voice guide](IDENTIDAD_EDITORIAL.md), in Spanish, records the design decisions.

## What you can use it for

| Space | Current use |
| --- | --- |
| **Aprender / Leer** | Twelve guided readings, contextual word help, optional Spanish and exercises that preserve source spelling; 28 comprehension questions quote the original translations; browse the 48 selected passages and notes, consult the dictionary or archive, and return to the same passage using the keyboard. |
| **Analyze any word** | Click any word in a reading to see its segmentation (*ni-qu-itta*: I · it · see), the dictionary entry, other passages sharing the root, and parallel-corpus gloss hints with their supporting passages; toggle an interlinear gloss. Rules + dictionary + corpus statistics; no LLM. [Architecture](ARCHITECTURE.md). |
| **Ficha para taller** | Prepare a textual reading sheet from Leer, print/save PDF with optional translations and answer keys, or download JSON with keys, versions, sources and hashes. |
| **Diccionario** | Look up senses and historical forms, inspect documented visual references and follow citations. The first page keeps 24 representative entries; the rest sorts alphabetically in Nahuatl. Queries rank exact matches first and can continue into the archive when an entry is missing. |
| **Mis palabras** | Save words and practise at spaced intervals. Keep the source passage with a saved word and return to it during review. Progress belongs to the current browser; no account is required. |
| **Archivo y herramientas** | Search Spanish or Nahuatl, filter by work, variety or period, inspect sources and prepare exports with rights notes. |
| **Consultar fichas** | Search words, short phrases or IDs across the dictionary, archive and pictographic catalog; compare originals, senses and sources, then return to the Dictionary to study a word. |
| **Laboratorio** | Inspect measured documentary retrieval alongside models not yet run on that battery, including failures, costs and sources. Try search, limited rules or experimental generation; inspect training pairs and historical model results. |
| **Aportar · Voces** | Propose text, voice, translations, forms and connections; record variety and permissions, review or withdraw contributions. |
| **Proyecto y colaboración** | Find the purpose, intended users, open questions and downloadable collaboration/pilot guides. |

Uses include personal study, textual research, preparing reading activities, collaborative editing and exploring model training. Classroom effectiveness still needs testing with people. The app is installable through the browser; mobile installation and microphone access require HTTPS. The local server must remain running, and the offline screen does not queue submissions. See the [installation guide](WEBAPP.md).

## Current content and open questions

Inventory updated on **8 October 2026**, preserving previous releases:

- **12 guided readings / 48 passages / 10 works**. New selections cover houses, animals, stone and wood, trees and hills, fire and wind, and Sun and Moon in narratives.
- **575 dictionary entries/senses**: 26 curated and 549 automatically transcribed Molina/GDN entries, with 578 written forms.
- **140 visual-reference records**: 139 entries have source images, using 24 distinct documentary image URLs; 436 entries still need visual evidence.
- **16,111 Axolotl bilingual pairs**, with 33 identified works and original variety labels.
- **650 pairs actually visited by the historical adapter**, available in the training-data viewer.
- **5,462 pairs in the current Classical Nahuatl preparation**: 2,161 training, 2,049 validation and 1,252 test, split by work. Existing weights were trained on an earlier preparation.
- **62 reading-review tasks**: 1 resolved editorially, 4 blocked and 57 open. Primary-context checks, specialist review and beginner trials remain pending.

A visual link may show a whole-word glyph, a component, iconography or related contextual evidence. These are labelled separately. A source illustration does not establish how an entire sentence was written. Historical dictionary transcriptions also need interpretation; they are not automatically modern definitions or morphological analyses.

The [latest reading batch](../reports/LECTURAS_003_2026-10-07.md) preserves the six earlier readings and their answer keys. The [September expansion](../reports/LECTURAS_002_2026-09-30.md) and [connected reading report](../reports/RECORRIDO_CONECTADO_2026-10-07.md) retain historical checks. Software tests establish technical behaviour, not philological correctness or educational effectiveness.

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

Review one complete reading and test comprehension before broadening the inventory. For a living variety, agree on community, objectives, coauthorship, recognition or compensation, and permissions first. Missing visual evidence remains visible; it is not filled with an invented link. The proposed small institutional pilot has responsibilities and evaluation criteria to agree, rather than a claim of national readiness.

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

## Pictographic dictionary and the Amoxcalli name

The beginner dictionary and twelve guided readings remain the main learning path. **Glifos** adds a documentary index of 13 selected Tlachia pages across three sets: 297 glyphs, 14 personages, 152 document-scoped element records, 142 distinct designations and 613 contextual components. A short observation exercise compares the designation `calli` with readings recorded in different contexts. Analyses are attributed to Tlachia; primary and specialist checks remain pending.

The [pictographic guide](DICCIONARIO_PICTOGRAFICO.md) documents the model and a bounded, cached batch importer with source hashes, explicit lexical bridges and additive publication. Images remain source links; this index does not authorize training. Amoxcalli replaces the visible Scriptorium name while retaining historical storage keys and format IDs to preserve progress.

The [8 October release](../reports/PICTOGRAFIA_LOTES_004_2026-10-08.md) added 220 occurrences in four backed-up batches, preserving earlier records and lexical bridges. The quantitative target of 300 occurrences is met. Specialist review and learner trials remain pending.

The [documentary battery](EVALUACION_DOCUMENTAL.md) prepares 123 textual queries and 51 catalog observations for development, with 37 and 15 cases held separately in reserve. References preserve original fields, sources and hashes; entry, work and image families are grouped before splitting. Visual observations contain catalog fields and image links; image processing by a model remains pending.

[Documentary lookup](CONSULTA_DOCUMENTAL.md), linked from the Dictionary, Archive and Laboratory, returns records with original fields and verifiable citations. Measurement on all **123 textual development queries** produced **119 complete results**, two partial results and two abstentions, matching 840 of 860 required fields. These questions contain spellings or IDs from known records; the result does not establish general comprehension or translation quality. The reserve remains unevaluated. See [method, failures and tests](../reports/RECUPERACION_006_2026-10-08.md).

The [Laboratory](LABORATORIO.md) presents this measurement alongside the textual model and a multimodal candidate. Both are **not run on this battery**, with scores and costs unmeasured. Historical experiments remain separate; there is no performance comparison between methods yet. The four failures can be reproduced, and public summaries exclude expected answers and reserved cases. See [presentation and validation](../reports/LABORATORIO_007_2026-10-08.md).

The visual preparation viewer presents **51 documentary development cases**, with questions, source links and references initially collapsed. It processes no images and runs no model. It checks installed dependencies and identifies the missing architecture. See [changes and tests](../reports/PREPARACION_VISUAL_016_2026-10-12.md) and the [proposed first local image trial](PRUEBA_VISUAL_LOCAL.md), awaiting authorization.

Laboratory summaries reuse an in-memory cache and check source hashes on every access. In a local sample, five subsequent downloads averaged **9.34 ms**, compared with **2.12 s** previously; the first load still takes about two seconds. Documentary results are unchanged. See [measurement and tests](../reports/CACHE_LABORATORIO_008_2026-10-08.md).

Queries opened from a reading preserve the source passage across the Dictionary, Archive and record comparison. Links carry the current search text, including edits made without submitting the form. Returning focuses that fragment without marking answers or changing progress. Keyboard navigation and 360/390 px viewports were checked; physical phone testing remains pending. [Checks and limits](../reports/CONTINUIDAD_COTEJO_012_2026-10-09.md).

Aves is **available for study**: four sourced passages, eight exercises and a final comparison between the bird in a poem and birds in a narrative. [Open Aves locally](http://127.0.0.1:8766/#aprender/aves). Linguistic review and learner trials remain pending. The [Aves 012 handoff](../reports/reading-review/aves-012/package.md) preserves the material and human tasks as a historical snapshot; it is not regenerated for interface changes. Its previous global validity is not presented as current. See [delivery and revised method](../reports/METODOLOGIA_Y_AVES_014_2026-10-12.md).

Under “¿Hay otra palabra que quieras entender?”, **Comparar aquí** shows up to two passages with the same written word, optional Spanish and sources while keeping the reading open. Full Archive search remains available. See [delivery and checks](../reports/APRENDER_COMPARANDO_015_2026-10-12.md).

The [latest full diagnosis](../reports/iterations/iteration-014/inventory.md) distinguishes technical preparation from human review and preserves the state before this interface improvement. Pending human tasks do not mean every reading is blocked. Priorities are complete learning experiences and observed difficulties; specialist review, beginner trials and new uses of models or images retain their own requirements.

A [lexical candidate script](CANDIDATOS_CONEXIONES_LEXICAS.md) compares pictographic designations with dictionary forms without an LLM. The [first batch of eight pairs](../reports/lexical-link-review/candidatos-013/candidates.md) preserves senses, sources and contextual components for review together. Matching spelling does not establish matching meaning: all candidates remain pending and the nine published links are preserved. Repeated preparation verifies the files and protects existing notes. See [implementation, tests and limits](../reports/CONEXIONES_CANDIDATAS_013_2026-10-12.md).

## Architecture and evaluation

For an engineering overview (data flow, design principles, the new word-study layer, measured results and where an LLM should and should not sit), read [ARCHITECTURE.md](ARCHITECTURE.md). The morphology evaluation is reproducible with `python3 -m nahuatl_local.morphology_evaluation`.
