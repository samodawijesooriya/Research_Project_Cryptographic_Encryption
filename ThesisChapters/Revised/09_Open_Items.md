# Open items: things only you can confirm, and things not yet done

## Confirm or verify (the revised text has bracketed markers for these)

**[VERIFY 1] Deep-sleep current.** The previous draft used 5 µA from the *ESP32-C3* datasheet. Use the **ESP32** datasheet's deep-sleep figure for the "RTC timer + RTC memory" configuration (your firmware keeps state in RTC memory). I believe it is 10 µA, but I could not check it here. Then set E_sleep = 3.3 V × I × 60 s (990 µJ at 5 µA, 1,980 µJ at 10 µA) and pick the row of Table 11 that matches. The break-even does not depend on it.

**[CONFIRM 2] The wake timer during collection.** You asked me to use 60 s. The text describes 60 s as the *modelled* interval, which is accurate. But what the firmware did during collection needs one honest sentence in 3.3.4:
- The firmware in the repository has `DEEP_SLEEP_SECONDS 1`.
- `git log -S` shows earlier commits with `60`; the `1` first appears in the post-collection commit (17 Sep).
- About 127,000 trials at 60 s each is about 88 days, longer than the time between your first commit (21 Aug) and the analysis commit (17 Sep), so a 60 s timer cannot have been used for all trials.

Check the value your data actually used (your notes, earlier builds, or the interval between `id`s in the logs if timestamps exist) and write that value in 3.3.4. If the value was 60 s for part of the data, say which part. **Do not state in the dissertation that the trials were collected with a 60-second sleep unless you can show it.**

**[VERIFY 3] mbedTLS version.** ESP-IDF v5.3.1 bundles its own mbedTLS. The draft says 2.16.2. Read the version from the build log or `build/` and correct 3.4.2.

## Not yet done (I can do these)

1. **Plots** for Chapter 4 from the validation data (list in `07_Figures_and_Appendices.md`).
2. **Calibration-constant sensitivity** for Campaign A (offset 5.2 to 6.5 mA): only relevant to Appendix C, since Campaign A is no longer used for energy.
3. **Re-measure the task-create overhead** (my first measurement returned a negative value because of a wrong subtraction; it is not used in the text).
4. **Optional cold-start experiment** (the first cipher call after wake from deep sleep, timing only). It would test the one open explanation (5.2.5) and about 20 minutes of board time. It is not required for submission if you keep the sentence as an untested possibility.

## Decisions for you

- **Title:** keep, or add "with a Modelled Sleep Phase"? The text is already honest about scope; the title is your and your supervisor's call.
- **Campaign A in the final document:** the revised chapters keep it (memory results, sensitivity, limitation). Your supervisor may prefer it in an appendix only.
- **Appendix G** (change log): include for the supervisor, or leave it out.

## Files created or changed (nothing was committed)

- New: `validation_fw/` (firmware, capture script, both logs), `scripts/04_validation_analysis.py`, `scripts/05_original_sensitivity.py`, `processed/validation/`, `processed/original_sensitivity.csv`, `ThesisChapters/Revised/`.
- Untouched: original firmware in `main/`, original raw data, and your existing `ThesisChapters/Chapter*_Draft.md`.
- The board is currently flashed with the validation firmware. To collect anything with the original firmware again, reflash it from the project root.
