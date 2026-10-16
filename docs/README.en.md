# Amoxcalli

[Español](../README.md)

**Learn to read Classical Nahuatl through sourced examples: understand a passage, compare it, and return to the document.**

Amoxcalli is a local application with short guided readings, a sourced dictionary, a glyph index and a bilingual archive of 16,111 passages. Every answer points to its evidence: a dictionary entry, an archive passage or a documentary record. Word analysis and lookup work **without an LLM**; the experimental model lives separately in the Laboratory.

**Status (15 October 2026).** You can read, search, analyze words, practise and contribute. Still missing: **linguistic review** of the help and exercises, **checking against primary sources**, and a **trial with beginners** — the collaborations we are looking for ([pilot proposal, ES](PILOTO_INSTITUCIONAL.md), [purpose, ES](PROPOSITO.md)). The current plan is [ROADMAP.md](ROADMAP.md).

## Try it

Python 3.11+ (standard library only):

```bash
make demo
```

Open <http://127.0.0.1:8766>. `make demo` builds the derived analysis caches once (~1 min) and starts the server. One process serves the app, Voces (`/aportar`) and the API; `bash scripts/amoxcalli.sh serve` starts it and `setup` also installs the local model. Options (`--host`, `--port`, `--db`, `--public-origin`, `--disable-model`, `--explain-model claude`) are listed in the [Spanish README](../README.md#probarlo). Phone and HTTPS setup: [WEBAPP.md](WEBAPP.md) (ES).

## What is there

- **Learn / Read:** 12 guided readings (48 passages from 10 works), hideable translation, exercises on the passage's own spelling, 28 comprehension questions keyed to the original translation. Every word can be analyzed; interlinear gloss.
- **Word analysis:** segmentation in the source spelling, dictionary entry, passages sharing the root, parallel-corpus hints, each with its basis. Design: [ARCHITECTURE.md](ARCHITECTURE.md).
- **Ask (Preguntar):** a word in any spelling or a Spanish question → analysis, entries and passages with reasons, plus a short explanation where every sentence cites its evidence; abstains without evidence.
- **Dictionary and Glyphs:** 3,790 senses / 3,978 forms (26 curated, 549 automatic Molina/GDN transcriptions, 3,215 Wiktionary lemmas under CC BY-SA, automatic extraction); 480 pictographic occurrences from 21 Tlachia folios. Every card shows its source and licence.
- **Archive and documentary lookup**, **My words** (spaced review in the browser), **Laboratory** (measurements and the Qwen3-0.6B + LoRA experiment, see [MODEL_CARD.md](../MODEL_CARD.md)), **Contribute · Voces**.

## Numbers and where they come from

| Measurement | Result |
|---|---|
| Morphological segmentation (52 gold forms) | 85% exact; 60.3% of classical tokens linked to a dictionary root (28.0% by exact match) |
| Ask (32 test queries) | correct entry first 92% vs 42% for exact search |
| Documentary lookup (123 development queries) | 119 complete, 770/790 required fields |
| LoRA model (20 test sentences, chrF++) | 22.4 with retrieved context vs 27.2 for returning the nearest passage: **not a translator** |

`make reports` regenerates them, `make check` verifies they are current ([reports/README.md](../reports/README.md)). These are technical checks on small team-written sets, not expert review or evidence of learning.

## Development

```bash
npm ci --ignore-scripts
make test
```

Python suite plus jsdom DOM suites; CI runs the same on a clean clone. A UI-only change is verified by the DOM suite and needs no evidence regeneration; ranking, data, battery or evaluator changes do (`make reports`). History up to today: [HISTORIA.md](HISTORIA.md) (ES).

Code and original documentation: MIT. Texts, images and derived adapters keep their own terms. See [FUENTES.md](FUENTES.md) and [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).
