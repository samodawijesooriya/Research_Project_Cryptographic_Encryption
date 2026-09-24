# Review notes — Final Thesis V05.docx

Reviewed against `DataCollection/Final Thesis V05.docx` (2026-09-22) and cross-checked against
`processed/data_quality_stage_log.csv`, `processed/aes_summary_by_size.csv`,
`processed/original_sensitivity.csv`, and `processed/validation/validation_run1/validation_summary.csv`.
This file only records what to change — the docx itself was not touched.

## Part A — Previously flagged issues: confirmed fixed

No action needed on these; listed so you can verify against your own checklist.

1. **Table 7/18 duplicate (4.7.1 vs 5.5.6)** — fixed by deleting the duplicate one-tailed table
   from 4.7.1 and renumbering every table from old-Table-8 onward down by one. New sequence
   runs Table 3 → Table 18 with no gaps or repeats.
2. **Table 11 typos (now Table 10, 5.4.5)** — "61" corrected to "64"; ".135" corrected to "0.135".
3. **Table 3 "AES-128-GCm"** — corrected to "AES-128-GCM".
4. **Table 15 (now Table 14, 5.5.1) 128-byte row** — corrected to AES A = 1841.6 µs,
   AES_COLD B = 203.2 µs, Difference = 1639. This now matches `aes_summary_by_size.csv`
   (mean_time at size=128 is 1841.64 µs) and the Table 11 regression (88.4 + 0.897×128 = 203.2 µs),
   and restores the pattern with the neighbouring rows.
5. **Outdated pp.65–66 paragraphs in 6.2.1** — the two paragraphs re-deriving the break-even
   from the withdrawn Campaign A intercepts (15.03/30.14 µJ) and calling the 206-vs-347 gap
   "expected" have been removed. 6.2.1 now reasons only from the validated Campaign B numbers.

## Part B — New issues found in V05

### B1. Table 15 (5.5.1, "Power and energy did not agree") has a genuine extra column — not a typo, a table-structure defect

This is the most important one. I opened the underlying table XML: the table has **10 grid
columns**, but column 2 is only **13 twips wide** (compare: column 1 is 1063, column 3 is 847) —
i.e. a sliver column, invisible or near-invisible on screen, sitting between "Payload (B)" and
"ASCON A Power (mW)". It duplicates the header text ("Payload(B)" appears twice) and every data
row has a spurious extra value in it — e.g. the 16-byte row reads
`16 | 20.3 | 20.3 | 75.1 | 24.2 | 63.8 | 27.9 | 4.35 | 42.1 | 6.56` (10 values) instead of the
correct 9: `16 | 20.3 | 75.1 | 24.2 | 63.8 | 27.9 | 4.35 | 42.1 | 6.56`.

This looks like an accidental column split (e.g. a stray "Split Cells" or a dragged column
border) introduced while editing the table, not a data error — every value is correct once the
sliver column is removed, they're just shifted one slot right of where the header says they
should be.

**Fix:** select that near-invisible 2nd column and delete it (Table Tools → Layout → Delete →
Delete Columns), for all 9 rows. After deletion the table should read exactly as the header
promises: Payload(B), ASCON A Power, ASCON B power, AES A power, AES_COLD B power, ASCON A
energy, ASCON B energy, AES A energy, AES_COLD B energy — 9 columns, matching the surrounding
prose ("Campaign A power was 20 to 25 mW... against 64 to 75 mW in Campaign B").

### B2. Table 5 caption is missing its number

Section 4.5.2, the "Comparison by size" table, is captioned:

> Table -Comparison by size

It should read **"Table 5-Comparison by size"** (matches the List of Tables entry, "Table
5-Comparison by size … 43").

### B3. Cross-reference to the wrong table — 4.7.1 still points at the old table number

4.7.1 reads: *"They are re-run two sided and with Holm correction in 5.5.6 (Table 18)."*
After the Table 7/18 duplicate was removed and everything shifted down by one, the "Campaign A
per-size tests" table in 5.5.6 is now **Table 17**, not 18 (Table 18 is now "Resource cost before
encryption" in 6.2.1 — an unrelated table). Change **"(Table 18)" → "(Table 17)"**.

### B4. Two citations of "Table 12" that should say "Table 11"

Both of these name "the fitted lines" (slope/intercept values), which live in **Table 11 — Linear
fits of energy per call against payload size** (2.91, 5.57 µJ intercepts; 0.0889, 0.0619 µJ/B
slopes). Table 12 is a different table ("Fine sweep around the break-even" — the per-size µJ
differences), not fitted-line values.

- 5.4.6: *"The fitted lines of Table 12 give an independent estimate: (5.57 − 2.91) /
  (0.0889 − 0.0619) ≈ 99 bytes…"* → change **"Table 12" → "Table 11"**.
- 6.2.1: *"…and variable costs of 0.0889 and 0.0619 µJ per byte (Table 12)."* → change
  **"(Table 12)" → "(Table 11)"**.

### B5. 6.2.2 cites "Table 14" for a figure that's actually in Table 13

*"…the choice of cipher changed total cycle energy by between 0.1% and 3.6% (Table 14)."*
Table 14 is "Time per operation in Campaign A and Campaign B" — unrelated. The 0.1%–3.6% cycle-energy
figures are in **Table 13 — Effect of the cipher on modelled cycle energy**. Change
**"(Table 14)" → "(Table 13)"**. (This looks like a leftover from the pre-renumbering draft,
where this table was one number higher.)

### B6. Dangling reference to a "Table 20" that doesn't exist

4.1 (Chapter 4 introduction) reads: *"…chapter 5 states which findings stand, which are replaced
and why (Table 20)."* There is no Table 20 anywhere in the document (the List of Tables stops at
Table 18). This was already present in the version I reviewed earlier and I missed it at the
time — flagging it now. Either point it at an actual table (Table 3 in `04_Chapter4_revised.md`'s
sibling summary doesn't map to one single table here — the closest match is the qualitative
summary in 5.8/6.5, which isn't tabulated) or drop the parenthetical entirely, e.g.: *"…chapter 5
states which findings stand, which are replaced and why."*

### B7. Table 16 (5.5.5) row counts still don't match Table 3 — needs a caption note, not a number change

Table 16's "IQR k = 1.5 (used)" column reads 45,735 / 42,868 rows, while Table 3 and the 4.2.3
text both say 45,745 / 42,870. I checked this against your own data files:
`processed/data_quality_stage_log.csv` (the main pipeline, used everywhere else) gives 45,745 /
42,870; `processed/original_sensitivity.csv` (the file this sensitivity table was built from,
row labelled "IQR k=1.5 (thesis)") gives 45,735 / 42,868. So this ~10-row gap is real, not a typo
— the sensitivity check held calibration constants fixed across all three trimming variants
(none / k=3 / k=1.5) for a clean comparison, rather than re-deriving them per variant the way the
main pipeline does.

**Fix:** don't change the numbers. Add a caption note, e.g.:

> *Table 16 – Sensitivity of Campaign A to outlier trimming. Calibration constants were held
> fixed across all three variants for comparability; the k = 1.5 row counts therefore differ
> from Table 3 by up to 10 rows.*

### B8. Minor: duplicated chapter label in 1.9

*"Chapter 5: Chapter 05: Validation of the Measurements – Audits the measurement method…"*
— "Chapter 5:" is written twice. Delete the first "Chapter 5: " so it reads "Chapter 05:
Validation of the Measurements – Audits…", matching the style of the other chapter entries in 1.9.

## Part C — Still-outstanding minor items from the original review (unchanged since last pass)

These were on the original list and remain as-is; low priority, included for completeness:

- Table 9 (5.4.2, "Time per operation") — no in-text "(Table 9)" citation; the paragraph after it
  just says "Time was linear in payload size for all variants…". Add "(Table 9)" once.
- Table 10 (5.4.5, "Energy per operation and per byte") — same, no explicit "(Table 10)" citation.
- Table 15 (5.5.1, second table) — "Power and energy did not agree:" still doesn't name the table
  number inline. Once B1 is fixed, add "(Table 15)" after that sentence.
- Table 16 (5.5.5) — "The analysis was repeated without trimming and with k = 3…:" — add
  "(Table 16)".
- Table 17 (5.5.6) — "The tests were repeated two-sided and Holm-corrected:" — add "(Table 17)".

## Part D — Not checked in this pass

- Figure numbering/placement (only table and cross-reference text was audited).
- Page numbers in the List of Figures/Tables/Equations — these are normally Word TOC fields;
  do a "Update Field" / F9 on the whole document before final export rather than hand-checking them.
- The References list (Table 19 internally, unlabelled in the List of Tables) — roughly two-thirds
  of entries are missing their `[Author, Year]` short-form first cell while the rest have it
  populated (e.g. `[Arghire, 2024]` present, `Agugliaro et al., 2024` absent). This is a
  formatting inconsistency in the citation-key column, not a content error, and wasn't in scope
  of the original ask — flagging only in case it's an artifact of whatever reference manager
  produced this table.
