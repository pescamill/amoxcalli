# Roadmap · iterative development

Updated 14 October 2026. Based on a hands-on test of the app (desktop and phone), the API, and the test suite on a fresh clone and on the working folder.

This file replaces scattered planning across dated reports. **Each iteration ships one change a reader can see, measured against a baseline before and after.** Iterations are 1–2 weeks. Linguistic review is a separate, explicit milestone, never assumed.

## Where things stand

| Area | Today | Main gap |
|---|---|---|
| Readings | 6 guided readings · 24 passages · every word clickable, interlinear gloss | Little content; no learner trial yet |
| Word study | 77% exact segmentation (52-form gold set), 41.8% of classical tokens linked to a dictionary root | Small dictionary (~530 forms); some visible errors (below) |
| Archive | 16,111 aligned passages; ~10k are *not* classical (Puebla 2,884 · Morelos 1,938 · Central 1,543 · Huasteca 1,596 · unlabeled 2,157) | Search is spelling-sensitive; analyzer is classical-only |
| Documentary lookup | BM25 + citation validator + abstention | Ranking puts glyph elements above the dictionary entry for "¿Qué significa xochitl?" |
| Model lab | Qwen3‑0.6B + LoRA: best 22.4 chrF++ with RAG, below "top BM25 passage" (27.2) | The LLM has no product role yet |
| Engineering | Python stdlib server, vanilla JS PWA, 258 tests | A fresh clone is not runnable end to end (below) |

### Found while testing

1. **Fresh clone fails.** 46 of 258 tests fail or error on a clean checkout. Tracked code depends on ~200 untracked files and folders that exist only in the working folder (`configs/documentary-evaluation-v1.json`, `reports/documentary-*.json`, `reports/iterations/state.json`, editorial releases…). The Glifos page was broken for the same reason (fixed: catalog now tracked).
2. **Tests write into the repo.** They create `editorial/*-test-*` and `reports/*test-*` folders, which pile up wherever deletion isn't allowed.
3. **Empty responses on server errors** (fixed: now 500 JSON + local traceback).
4. **Cold start blocks for ~55 s.** The first `/api/word` call after a fresh install waits for the derived caches; afterwards it takes 2–30 ms.
5. **Same word, three disjoint searches.** Archive search gives *kuali* 74, *cualli* 294, *qualli* 42 results, with almost no overlap. The phonemic key exists, but search doesn't use it, and the key itself treats modern `ku+V`/`ts` differently from classical `cu+V`/`tz` (*kuali → kwali* but *cualli → qalli*).
6. **Visible analyzer errors.** *Motecuhçoma* → "your" + root (names read as possessed nouns). *mictlan* → *m-ic-tlan*. *tlaca* → pluperfect. The particle *in* shows 4,576 "same-root" passages, including *tin* and *intzalan*.
7. **Noisy gloss hints on some roots.** *mopohua* → «milpa, nuestra, dejó»; *nechmaca* → «qual, doy, tengo».
8. **Phone layout.** About 310 px of header and navigation before any content.
9. **Offline images.** Glyph images are loaded from external sites, so the installed app shows "La imagen no está disponible" offline.

## Iterations

### 0 · Clone, test, demo (do first; the interview depends on it)
- Split **inputs** (configs, corpus, editorial releases) from **generated outputs** (reports). Commit the inputs; regenerate the outputs with one command. `reports/` currently holds about 90 dated files.
- Tests use `tempfile` only. Mark the ML-dependent tests (torch, sacrebleu) as optional extras.
- GitHub Actions: unit tests plus one Playwright smoke test (open a reading, click a word, toggle the interlinear gloss).
- `make demo`: install, prebuild `data/derived/`, serve. While caches build, the UI shows "preparando análisis" instead of hanging.
- **Done when:** fresh clone → `make test` is green, and `make demo` serves the first analysis in under 10 s.

### 1 · One search across spellings
- Fix the key so `ku+V`, `kw` and `qu+a` map to the same symbol, and `ts ≡ tz`. Add a "loose" search key that also collapses `ll→l` and drops `h` (modern Huasteca *kuali* = *cualli*).
- Use the key in archive search and dictionary search. Results show the original spelling and are grouped by variety.
- **Measure:** a 50-pair spelling-variant query set, comparing recall of the union before and after. Re-run the morphology evaluation to check nothing regresses.
- **Why:** it opens the classical archive to speakers who write in modern (SEP/INALI) orthography, and modern examples to classical learners.

### 2 · Precision where readers notice it
- Particles: concordance by whole form only (no prefix/suffix stripping).
- Proper names: a capitalized token outside sentence-initial position gets a `name` basis, plus a small list of place and ruler names.
- Fix the error families in item 6 above. Gloss hints: a stopword list, a minimum association score, and showing nothing rather than noise.
- With a linguist: grow the gold set from 52 to about 200 forms, and label the 60-row concordance sample (this gives concordance precision for the first time).
- **Measure:** exact segmentation on the test split, concordance precision, and the share of hints judged useful.

### 3 · A larger lexicon (the real bottleneck)
- Common nouns such as *cihuatl*, *tlacatl*, *teotl* and *ilhuicatl* have no entry, so 58% of tokens get no dictionary link.
- Candidate sources, by licence: Molina 1571 (public domain; check the licence of whichever transcription is used), Wiktionary (CC BY-SA), GDN/UNAM (ask for permission). Ingest with per-entry provenance and keep the "extracción automática" label.
- **Measure:** token root-link coverage, from 41.8% now toward about 65%.

### 4a · Retrieval with evidence, no LLM (done 15 October 2026)
- `#preguntar` and `GET /api/ask`: one word or short question → analysis, dictionary entries, classical passages sharing the root, other varieties via a loose spelling key, and Spanish → root candidates from the inverted IBM-1 hints. Abstains without evidence. The empty Dictionary search now routes Spanish words here instead of the analyzer.
- **Measured** on `evaluation/evidence-questions-v1.json` (32 held-out queries): entry top-1 92% vs 42% for exact search; at least one relevant passage 100% vs 76%; modern spellings 0% → 100%. Guide: [EVIDENCIA.md](EVIDENCIA.md).
- Partly covers iteration 1 for retrieval only (the analyzer's own key is unchanged).

### 4b · Cited explanations and one word mechanism (15 October 2026)
- Every Preguntar answer has a 2–5 sentence explanation where each sentence cites evidence IDs; a validator rejects uncited sentences, IDs outside the evidence and «quoted» forms not found in the cited text. The extractive writer (no model) is the default; Claude (`--explain-model claude`, opt-in because it sends the question and passages to Anthropic) is used only when its answer validates, otherwise the extractive one is shown with the reason. 46/46 extractive explanations validate; Claude is not yet measured.
- Aprender now uses the same word mechanism as Leer: every word is analyzable and the interlinear gloss is available during cloze exercises, with only the blank hidden; the passage is restored after a correct answer; editorial word help shows the automatic analysis inline.

### 4 · Grounded explanation agent (the LLM's product role)
- The LLM *explains*; it does not translate from memory. It is a tool-using agent over `analyze_word`, `concordance`, `dictionary`, `gloss_hints` and `archive_search`. Every claim cites passage or entry IDs, and the existing citation validator rejects anything that doesn't. It abstains when the evidence is missing.
- Off by default. Model is swappable: a hosted model (e.g., Claude via API) or a local one (the LoRA lab).
- First fix documentary ranking: strip question words, and rank a dictionary form above glyph elements for "¿qué significa X?" questions.
- **Measure:** a 40-question set ("what does X mean here?", "why this form?") scored on citation validity, faithfulness and correct abstention. Compare against retrieval-only answers and the LoRA model.
- **Interview story:** symbolic components give grounded evidence; the LLM adds language on top and stays accountable to it.

### 5 · Learner loop
- Use word study to propose new readings faster: rank archive passages by root coverage, then auto-draft word help for editorial review. Target: 6 → 12 readings.
- Review saved words with spaced repetition, using concordance examples rather than isolated words.
- Compact navigation on phones. Offline fallback for glyph images (cache them where permitted, or a text description).
- Run the beginner trial with 5 people that has been pending since September.
- **Measure:** task completion and comprehension in the trial; returning use of Mis palabras.

### 6 · Researchers
- Exports: concordance as CSV and Leipzig-style IGT (later CoNLL-U), stable permalinks per passage and per analysis, documented local API.
- **Measure:** one researcher completes a concordance → export → citation task without help.

## Working agreements
- One change per iteration that a reader can see, one metric, one short entry in this file. Don't write per-cycle report files.
- Every number in the README comes from a command that regenerates it.
- Linguistic claims carry their basis (dictionary / table / corpus / rules) and stay labeled "pendiente de revisión" until a named reviewer signs off.
