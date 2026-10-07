# Lesson review packet · [stable lesson ID]

Status: draft. This is an authoring checklist, not a file to import directly into the live application. Keep source texts unchanged. `nahuatl_local.lesson_builder` assembles explicit source recipes with hashes and exact-form cloze keys; see [the authoring guide](../../docs/LECTURAS_PIPELINE.md). Use Spanish for learner-facing explanations and identify the historical variety explicitly.

## 1. One learning objective

- Title:
- By the end, the learner can: [one observable action]
- Variety: [ISO / historical variety; do not combine varieties implicitly]
- Prerequisites:
- Approximate duration:
- Target meanings: [about 3–5 `sense_id` references; fewer if the passage requires it]
- Context needed to avoid a misleading literal reading:

## 2. Four source-bound examples

Use this section four times. The fourth example checks transfer to another source passage; it is still a documented example, not generated text. Four examples are the default batch recipe size. The learner UI now counts examples dynamically and supports other positive counts.

- Archive ID:
- Work / edition:
- Original variety label:
- Primary page / folio / location: [pending is acceptable in a draft; do not invent it]
- Archive row / source URL:
- Original Náhuatl, copied exactly:
- Original Spanish, copied exactly:
- Original `source_hash`: SHA256 of `nah + "\0" + es`:
- Review comment or proposed correction, separate from the original:
- Learning context:

For every highlighted expression:

| Exact quote from the original | Existing meaning ID or candidate | Relation to that meaning | Evidence / unresolved question |
|---|---|---|---|
| | | Exact use / inflected form / variant candidate / compound candidate / thematic comparison | |

A form not listed in the dictionary is a review candidate. It does not automatically require a new lemma. Prefer a small number of useful annotations to a fully highlighted paragraph.

## 3. Visual evidence per use

| Target meaning | Glyph record and source location | Relationship | What the evidence supports | What it does not establish | Reviewer / date |
|---|---|---|---|---|---|
| | | Documented reading / documented component / semantic comparison / definition illustration / passage illustration / pending | | | |

The same image can be used in different ways. A picture of the moon alongside an example containing ihuan is an illustration of that example; it is not a glyph of ihuan. A substring of a word does not establish a glyph component. Keep the source's glyph reading separate from the target word.

## 4. Exercises

For each example record:

- Kind: `meaning` or `cloze` (supported by the current application).
- Question in Spanish:
- Distinct answer options:
- Correct option: zero-based index:
- Source evidence supporting the key:
- Explanation of the answer:
- Explanation of likely confusion / distractors:
- Exact blank from the original, for `cloze`:
- What this checks about the objective:

A Spanish-only comprehension question can be useful, but should not be the only way to check recognition of the Náhuatl form. Other exercise types belong in the backlog until supported. Do not use the LLM as an answer key.

## 5. Release record

| Check | Decision and evidence | Responsible person | Date |
|---|---|---|---|
| Source text, primary location and translation checked | | | |
| Form→meaning connections checked | | | |
| Visual relationship and scope checked | | | |
| Exercise keys and explanations checked | | | |
| Source/image rights and attribution checked | | | |
| JSON and source hashes validated | | | |
| Beginner trial completed or explicitly recorded as pending pilot | | | |

Decision: [draft / reviewed pilot / ready for educational release / blocked]. Record why. A reviewed pilot may retain a disclosed learner-trial gap; do not claim usability has been demonstrated. A failed source or linguistic check blocks educational release. Technical validation alone is not editorial approval.

Training eligibility remains separate. Educational use, publication or a resolved review task does not grant permission to train. Preserve existing validation/test reservations if later creating model datasets.

## 6. Beginner trial card

- Task: identify a target form, explain a source connection, answer an exercise, find the original source.
- Observed result per task: completed / help needed / not completed.
- Confusion observed, in the learner's words where appropriate:
- Correction to make:
- Recheck result:

Keep observations minimal and anonymous. Do not record a proposed trial as a completed trial.
