# Where to start

Plan: **keep the thesis, insert a Validation chapter, patch the rest.**

| Order | File | What it is | What you do with it |
|---|---|---|---|
| 1 | `10_Cross_Check_Report.md` | What the thesis said vs what the validation found, what changed and why (claim by claim, with thesis page numbers), plus the five supervisor comments and other errors found | Read first; give to your supervisor |
| 2 | `11_Validation_Chapter.md` | The new **Chapter 05** (full text, tables, figure references) | Insert after Chapter 4 |
| 3 | `12_Targeted_Edits_Existing_Thesis.md` | Exact edits to the abstract and Chapters 1 to 4, replacement text for the Discussion and Conclusions sections that depended on the 347-byte result, cross-reference renumbering | Work through top to bottom |
| 4 | `figures/` | All figures (PNG for Word, PDF vector) | Insert as listed in `07_Figures_and_Appendices.md` (A.4) |
| 5 | `09_Open_Items.md` | Three facts only you can confirm: sleep current [VERIFY 1], wake timer used [CONFIRM 2], mbedTLS version [VERIFY 3] | Confirm, then replace the markers |
| 6 | `07_Figures_and_Appendices.md` | Flowchart redraw instructions (supervisor comment 1), figure list, appendices A to G | Draw Figure 1 and Figure 2; write the appendices |
| 7 | `08_Validation_Experiment_Summary.md` | Plain-language summary and the "why should we trust this" argument | For your viva preparation |

Superseded (reference only, do not paste): `03_Chapter3_revised.md`, `04_Chapter4_revised.md`, `05_Chapter5_revised.md`, `06_Chapter6_revised.md`. Still valid: `00_Abstract.md`, `01_Chapter1_edits.md`, `02_Chapter2_edits.md`.

Nothing in your existing thesis files, firmware or raw data was modified. Everything new is in `ThesisChapters/Revised/`, `validation_fw/`, `scripts/04` to `06`, and `processed/validation/`.
