# Master Project Source Index
**LPDG Innovation Hub Selection Challenge 2026**  
*Comprehensive Authority Index of All Challenge Materials, Scripts, Data Assets, and Institutional Notices*

---

## Source-of-Truth Hierarchy
1. **Level 1 (Highest Authority)**: Official LPDG FAQ Round 2 & final (`FAQ — Round Two, and final`)
2. **Level 2**: Official LPDG FAQ Round 1 (`03-FAQ-Round-1.pdf`)
3. **Level 3**: Institutional Submission Email (NEXORA 2026 / RGMCET CSEDS Department)
4. **Level 4**: Official LPDG Challenge Brief (`01-Challenge-Brief.pdf`)
5. **Level 5**: Official LPDG Data Dictionary (`02-Data-Dictionary.pdf`)
6. **Level 6**: Official Baseline & Validator Scripts (`baseline_3sigma.py`, `validate_submission.py`)
7. **Level 7**: Empirical Dataset Observations (`data/`)
8. **Level 8 (Lowest Authority)**: Candidate Inference & Design Decisions

---

## Master Source Registry

### 1. `FAQ — Round Two, and final`
- **TYPE**: Official Clarification PDF (11 pages)
- **AUTHORITY LEVEL**: Level 1 (Highest Authority — supersedes earlier documents on conflicting points)
- **PURPOSE**: Binding final answers to candidate questions; defines episode mechanics, cost evaluation primacy, live session format, and Section 8 unanswerable questions.
- **RELEVANT SECTIONS**: §1.1–§1.5 (Assessment scope), §2.1–§2.6 (Deliverables/libraries), §3.1–§3.7 (Data ranges/silence/determinism), §4.1–§4.5 (Episode accounting/cost/labels), §5.1–§5.5 (Defense/validation/criteria), §6.9 (ML validation), §7.1–§7.2 (Live session unseen partition), §8 (Assessment syllabus).
- **LAST VERIFIED**: 15 September 2026
- **NOTES**: Explicitly states no further questions will be answered before hand-in.

### 2. `03-FAQ-Round-1.pdf`
- **TYPE**: Official Clarification PDF (12 pages)
- **AUTHORITY LEVEL**: Level 2
- **PURPOSE**: First round of official answers; establishes 18-day schedule, 45,600 EUR fixed visit baseline, Monday 00:00 UTC temporal cutoff, and separate hidden ground truth.
- **RELEVANT SECTIONS**: §1.1 (Replaced schedule table), §2.1 (Offline execution), §3.4 (15-visit cap), §3.6–§3.8 (Cutoff dates & engineer review availability), §4.1–§4.4 (Ground truth & PU learning), §5.1–§5.4 (Cost model).
- **LAST VERIFIED**: 15 September 2026
- **NOTES**: Retains full authority where not modified by Round 2.

### 3. NEXORA 2026 Project Submission Email
- **TYPE**: Institutional Notification Email (from `hcseds@rgmcet.edu.in`)
- **AUTHORITY LEVEL**: Level 3 (Binding for local institutional submission)
- **PURPOSE**: Institutional submission instructions for RGMCET candidates; sets earlier deadline (20:00 IST), Google Form link, official email requirement, resume naming convention, and in-person presentation schedule.
- **RELEVANT SECTIONS**: Items 1–10 (Submission link `https://forms.gle/qHZqsRRPGWf8ja5S6`, resume `<Registration_Id.pdf>`, model inclusion in repo).
- **LAST VERIFIED**: 15 September 2026
- **NOTES**: Imposes the critical 20:00 IST deadline (almost 4 hours earlier than LPDG's 23:59 IST deadline).

### 4. `01-Challenge-Brief.pdf`
- **TYPE**: Official Challenge Specification PDF (6 pages)
- **AUTHORITY LEVEL**: Level 4
- **PURPOSE**: Original challenge problem statement, background context, Part 1 requirements, 6 specialization tracks, marking weights, and cost matrix.
- **RELEVANT SECTIONS**: p. 2 (The situation, Part 1 basics, cost table), p. 3–4 (Part 2 tracks A–F, marking weights 60/25/15), p. 5 (Live session intro, hand-in basics).
- **LAST VERIFIED**: 15 September 2026
- **NOTES**: Dates table on page 6 was superseded by FAQ Round 1 §1.1.

### 5. `02-Data-Dictionary.pdf`
- **TYPE**: Official Data Schema PDF (7 pages)
- **AUTHORITY LEVEL**: Level 5
- **PURPOSE**: Comprehensive documentation of all supplied files, table schemas, grain, datatypes, and column descriptions.
- **RELEVANT SECTIONS**: p. 1 (File overview, memory benchmarks, German terms), p. 2–5 (57 telemetry columns), p. 5–6 (Asset register, meter read success, field visits, engineer review), p. 6 (predictions.csv schema).
- **LAST VERIFIED**: 15 September 2026
- **NOTES**: Notes that firmware counters are reported as the gateway firmware records them.

### 6. `validate_submission.py`
- **TYPE**: Python Executable Validator Script (131 lines)
- **AUTHORITY LEVEL**: Level 6
- **PURPOSE**: Programmatic gatekeeper verifying syntactic compliance of `predictions.csv`.
- **RELEVANT SECTIONS**: Lines 23–26 (Required columns, 120 row count, 8 weeks), Lines 28–39 (ID normalization regex), Lines 87–98 (Score and reason length constraints), Lines 99–109 (Rank 1..15 uniqueness).
- **LAST VERIFIED**: 15 September 2026
- **NOTES**: Exit code 0 is mandatory for grading.

### 7. `baseline_3sigma.py`
- **TYPE**: Python Reference Implementation Script (120 lines)
- **AUTHORITY LEVEL**: Level 6
- **PURPOSE**: Working reference baseline implementing 3-sigma anomaly detection on trailing 28 days of 3 telemetry metrics.
- **RELEVANT SECTIONS**: Lines 30–35 (Metrics and constants), Lines 50–74 (Windowing and flagging logic), Lines 77–99 (Rank construction and fallback padding).
- **LAST VERIFIED**: 15 September 2026
- **NOTES**: Benchmarking bar for Track E (Machine Learning).

### 8. `README.txt`
- **TYPE**: Quickstart Text Document (41 lines)
- **AUTHORITY LEVEL**: Level 6
- **PURPOSE**: Unzip instructions, quick start commands, and folder naming rules.
- **RELEVANT SECTIONS**: Lines 11–13 (Folder name must be `data`), Lines 25–27 (Quick start run).
- **LAST VERIFIED**: 15 September 2026
- **NOTES**: Warns that the brief and scripts expect `./data/`.

### 9. Challenge Dataset (`03-challenge-data/data/`)
- **TYPE**: Raw Tabular & Parquet Data Assets (104 MB uncompressed)
- **AUTHORITY LEVEL**: Level 7 (Empirical Reality)
- **PURPOSE**: Operational IoT telemetry, asset metadata, meter read logs, work orders, and engineer reviews.
- **RELEVANT ASSETS**: `telemetry/month=YYYY-MM/*.parquet` (1.43M rows), `gateway_master.csv` (332 rows), `field_visits.csv` (642 rows), `meter_read_success.csv` (7,226 rows), `engineer_review_2026-02.xlsx` (120 rows).
- **LAST VERIFIED**: 15 September 2026
- **NOTES**: Contains real-world noise, missing rows, Latin1 encoding, and counter overflows.
