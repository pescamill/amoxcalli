# Amoxcalli

[Español](../README.md)

**Learn to read Classical Nahuatl through sourced examples: understand a passage, compare it, and return to the document.**

Amoxcalli brings together guided readings, short grammar units, a word analyzer, a spelling search (classical, modern and regional spellings), a sourced dictionary, documented glyphs, cards on deities and the calendar, and a bilingual archive of 16,111 passages. Every result says where it comes from: a dictionary entry, an archive passage, a pictographic record or a rule. **Without evidence, the app abstains.** Everything runs without an LLM, on the Python standard library.

**Status (18 October 2026).** Distributed as a download to use on your own computer. You can read, practise, analyze words, search in any spelling, browse deities and the calendar, and contribute. Automatic content (reading help, Wiktionary entries, new units and readings) is labelled as such and **awaits linguistic review**. Still missing: checking against primary sources and a trial with beginners — the collaborations we are looking for ([pilot proposal](PILOTO_INSTITUCIONAL.md), [purpose](PROPOSITO.md), both in Spanish). The current plan is [ROADMAP.md](ROADMAP.md).

## Download and use

Amoxcalli runs on your own computer: no internet or account needed, and whatever you save stays on your machine.

1. Install **Python 3.11 or newer** from <https://www.python.org/downloads/> (on Windows, tick "Add python.exe to PATH").
2. Download the latest release: [**Download Amoxcalli (.zip)**](https://github.com/pescamill/amoxcalli/releases/latest) and unzip it.
3. Double-click **`Abrir Amoxcalli.command`** (macOS) or **`Abrir Amoxcalli.bat`** (Windows). It opens in your browser at <http://127.0.0.1:8766>; the first time it prepares the analysis for about a minute. Keep the black window open while you use it.

On macOS the first launch may show an "unidentified developer" warning: right-click the file → **Open** → **Open**.

From a terminal (Linux, or if you prefer):

```bash
git clone https://github.com/pescamill/amoxcalli.git
cd amoxcalli
make demo        # or: python3 -m nahuatl_local.platform serve --open
```

<details><summary>Server options</summary>

`bash scripts/amoxcalli.sh serve [options]` (or `python3 -m nahuatl_local.platform serve [options]`):

| Option | Effect |
| --- | --- |
| `--open` | Open the app in the browser on start. |
| `--host`, `--port` | Interface and port (default `127.0.0.1:8766`). Phone on the same network: [WEBAPP.md](WEBAPP.md) (ES). |
| `--db path` | Local database of profiles, contributions and proposals (default `data/community/voces.sqlite3`). Goes before `serve`. |
| `--explain-model claude` | Claude-written explanations in Ask; sends the question and the cited passages to the Anthropic API. Without it, nothing leaves the machine. |
| `--demo`, `--public-origin` | For installing it on a public server: [DEPLOYMENT.md](DEPLOYMENT.md). |

</details>

**A five-minute tour:** open **Lecturas → Reconocer una flor**, click *NIQUITTA* (*ni-qu-itta*, "I-it-see") and show the interlinear gloss. Type *kuali* in the search box: *cualli* appears with its spellings by variety and its sources. Ask *¿cómo se dice mujer?* ("how do you say woman?") in **Preguntar** and click the citations in the explanation. Open **Más → Dioses y calendario** and search for *Huitzilopoxtli*.

The interface is in Spanish.

## What is there

| Space | What it does |
| --- | --- |
| **Lecturas** (readings) | 12 guided readings (48 real passages from 10 works): hideable translation, exercises on the passage's own spelling, 28 comprehension questions keyed to the original translation. Every word can be analyzed and there is an interlinear gloss, also during exercises (only the missing word is hidden). Printable workshop sheet. |
| **Unidades de gramática** (under «Más») | 4 short grammar units (absolutive, possessives, locatives, subject and object) with matching, morpheme identification, word building and translation of short passages; spaced review with examples. Automatic drafts whose answers are backed by the passage and the analysis. |
| **Word analysis** | Segmentation in the source spelling, dictionary entry, passages sharing the root and parallel-corpus hints, each with its basis (dictionary, corpus, rules or proper name). [Guide](MORFOLOGIA.md) (ES). |
| **Search in any spelling** | Type a word the way you write it (*kuali*, *kualli*, *qualli*, *cuali*, or with a typo) and see the possibilities at once, with sources, even when that exact spelling is not in the archive. Colonial, ACK and SEP/INALI profiles plus regional features. **It relates spellings; it does not impose a standard.** [Guide](GRAFIAS.md) (ES). |
| **Preguntar** (ask) | A word in any spelling, a Spanish question, **a topic** (*¿qué dice sobre el calendario?*, *dioses de la lluvia*, *¿quién fue Quetzalcóatl?*) or a record ID. For a word: analysis, entries and passages with reasons, and an explanation in which every sentence cites its evidence. For a topic: related readings (published and proposed), deity and calendar cards, units, Carochi notes, works and passages, each with the reason it appears. Abstains without evidence. [Guide](EVIDENCIA.md) (ES). |
| **Dictionary and Glyphs** | 3,790 senses: 26 curated, 549 automatic Molina transcriptions via GDN and 3,215 Wiktionary lemmas (CC BY-SA, automatic extraction). 480 pictographic occurrences from 21 Tlachia folios. Each term gathers its spellings, passages by variety and glyphs with their scope (whole word, component or related meaning). Grammar notes from Carochi (1645). [Guide](DICCIONARIO_PICTOGRAFICO.md) (ES) · [sources](FUENTES.md) (ES). |
| **Dioses y calendario** (under «Más») | 26 deities plus figures, epithets and places, every datum with its source; the tonalpohualli (20 day signs with their Telleriano-Remensis glyph, 13 numerals, 20 trecenas) and the 18 veintenas. Name spellings lead to the same card. Four mythology readings and a calendar unit await review. [Guide](DIOSES_CALENDARIO.md) (ES). |
| **Archivo completo** (under «Más») | 16,111 Axolotl pairs (about 6,000 Classical Nahuatl and 10,000 from present-day varieties) with their variety and work labels; one search for words, spellings and phrases. |
| **Mis palabras** (my words) | Notebook and spaced review in the browser, no account; keeps the source passage. |
| **Aportar · Voces** (contribute) | Propose text, voice, forms and connections with separate publication and training permissions; everything stays pending review and can be withdrawn. [Guide](VOCES.md) (ES). |
| **Laboratorio (histórico)** (under «Más») | What was tried with an experimental translator (Qwen3-0.6B + LoRA), its numbers and why it was retired. The code is archived in [experiments/llm/](../experiments/llm/README.md); the app loads no machine-learning dependencies. |

## Numbers and where they come from

One evaluation produces them all: `make eval` regenerates [reports/EVALUACION.md](../reports/EVALUACION.md) and `make check` re-measures and fails if a number changed without being regenerated. `dev` is used for tuning; `test` only for measuring.

| Measurement | Result (test) |
| --- | --- |
| Morphological segmentation, blind test v2 (91 forms written before measuring) | 78% exact (words 67%, particles 94%, proper names 100%); 89% on set v1 |
| Classical corpus tokens linked to a dictionary root | 60.4% (28.0% by exact match; 41.8% before Wiktionary) |
| Spelling search (`spelling-search-v1`) | Intended word first 94.2%, in the top three 97.1%; no wrong associations |
| Term index (`term-groups-v1`) | Query → correct group 90.5%; glyphs with their scope 100% |
| Topic search in Preguntar (21 test queries) | Expected item in the top five 95%, first 80%; correct abstention 100% |
| Preguntar (32 queries) | Correct entry first 92.3% vs 42% for exact search; always with a relevant passage |
| Records in Preguntar (123 documentary queries) | 780 of 790 fields exact |
| LoRA translator, historical (chrF++) | 22.4 with context vs 27.2 for returning the nearest passage: **not a translator**; retired |

These are technical checks on small team-written sets; they do not replace review by an expert or show that anyone learns.

## Collaborate

We are looking for people to review readings and entries, teachers to try a reading in an accompanied workshop, speakers of present-day varieties who want their way of writing recognized, and institutions willing to let us use their sources. With speakers, community, variety, goals, credit and permissions are agreed first. A concrete question also helps: passage ID, problem, source and proposal. [How to contribute](../CONTRIBUTING.md) (ES).

## Development

```bash
npm ci --ignore-scripts   # jsdom, only for the interface tests
make test                 # Python and interface tests
make eval                 # regenerate the evaluation table
make check                # re-measure and check the published numbers are current
```

CI ([.github/workflows/ci.yml](../.github/workflows/ci.yml)) runs `make check` and `make test` on a clean clone. An interface-only change is verified by the interface tests and moves no number; a change to data, the analyzer, indexes or evaluation sets does (`make eval`). Design: [ARCHITECTURE.md](ARCHITECTURE.md). History: [HISTORIA.md](HISTORIA.md) (ES).

| Folder | Contents |
| --- | --- |
| `corpus/` | Distributed content: Axolotl archive, readings, lexical catalogue, glyphs, entities, editorial batches |
| `editorial/` | Editorial decisions and proposals (readings and units under review) |
| `evaluation/`, `configs/` | Frozen evaluation sets and configurations |
| `nahuatl_local/` | Server, analysis and scripts (Python stdlib); `platform_web/` is the interface |
| `reports/` | Only current, regenerable reports ([index](../reports/README.md)) |
| `docs/` | Guides, mostly in Spanish; in English: this file, [DEPLOYMENT.md](DEPLOYMENT.md), [ARCHITECTURE.md](ARCHITECTURE.md), [ROADMAP.md](ROADMAP.md) |
| `experiments/llm/` | The archived LLM laboratory |

## Licences and sources

Original code and documentation: [MIT](../LICENSE). Third-party texts, images and data keep their own terms and are not relicensed as MIT: the Axolotl corpus (Elotl distribution, MPL-2.0), Wiktionary entries (CC BY-SA 4.0, attributed on every card), Molina's Vocabulario via the Gran Diccionario Náhuatl (UNAM) and the Tlachia catalogue (UNAM; images load from its site, with attribution). No generated images. The wider Gran Diccionario Náhuatl and the Florentine Codex await permission ([draft letters](permisos/)). See [FUENTES.md](FUENTES.md) and [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).
