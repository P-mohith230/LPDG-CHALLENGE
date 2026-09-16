# LPDG Innovation Hub 2026 — Project Context & Working Memory

## Purpose
Persistent working context for the LPDG Innovation Hub Selection Challenge 2026. Treat this as the primary working reference, synchronized with the official challenge brief, data dictionary, supplied scripts, datasets, and official LPDG FAQs (Round 1 & Round 2 published; Submission Email incorporated).

## Source-of-Truth Hierarchy
1. Latest official LPDG FAQ/clarifications (Round 1 FAQ supersedes earlier conflicting brief text)
2. Official LPDG challenge brief
3. Official data dictionary
4. Official supplied scripts/validator (baseline_3sigma.py, validate_submission.py)
5. Actual supplied-data observations
6. Candidate inference/design decisions

Rule: Never silently reconcile conflicts. Label conclusions explicitly as CONFIRMED BY LPDG, OBSERVED IN DATA, REASONABLE INFERENCE, CANDIDATE DECISION, or AMBIGUOUS.

---

## Challenge Timeline & Operating Schedule (All Times IST)
Note: Reconciled across FAQ Round 1 §1.1, FAQ Round 2 §1.5, and NEXORA Institutional Submission Instructions:
- Sat 29 Aug 2026, 23:00 IST: Challenge materials released & clock started.
- Mon 31 Aug 2026, 22:00 IST: Written questions Round 1 closed.
- Sat 05 Sep 2026, 22:00 IST: Written questions Round 2 & final closed.
- Week of 07 Sep 2026: Second set of answers (Round 2 FAQ, and final) published.
- Fri 11 Sep 2026, 23:59 IST: Optional check-in (push a repository that starts; unmarked smoke-test).
- **Wed 16 Sep 2026, 20:00 IST**: **CRITICAL INSTITUTIONAL DEADLINE** via Google Form (https://forms.gle/qHZqsRRPGWf8ja5S6). Only first submission considered; duplicate submissions summarily rejected.
- Wed 16 Sep 2026, 23:59 IST: LPDG Challenge Portal final deadline. (All work must freeze by 18:00 IST to honor the stricter 20:00 IST institutional cutoff).
- Fri 18 Sep 2026, 09:00 AM IST: In-person evaluation presentation at RGMCET campus.

---

## Core Operational Problem
- The System: LPDG operates a smart utility wireless telemetry network connecting residential and commercial utility meters across several German federal states (Bayern, Nordrhein-Westfalen, Baden-Wuerttemberg, Hessen, Niedersachsen, Sachsen).
- The Hardware: ~320 gateways installed on rooftops, in basements, in boiler rooms (Heizraum), inside control cabinets (Schaltschrank), or on outdoor masts (Aussenmast). Each gateway relays LoRa radio transmissions from 40 to 822 smart meters (62,748 total meters connected) over cellular backhaul (TelekomDE, VodafoneDE, O2DE).
- The Failure Mode: Gateways experience silent degradation and outages. Meters continue broadcasting locally, but data does not reach central utility systems. Failures produce no loud alarm and are discovered weeks later via unbilled utility consumption, costly manual meter readings, and customer disputes.
- The Capacity Limit: Operations can dispatch a maximum of 15 physical site visits per week.

---

## Submission Contract & Technical Constraints
predictions.csv must meet every assertion in validate_submission.py:
- Exactly 120 rows (15 rows for each of the 8 scored weeks).
- The 8 scored weeks: 2026-02-02, 2026-02-09, 2026-02-16, 2026-02-23, 2026-03-02, 2026-03-09, 2026-03-16, 2026-03-23.
- Columns: week_start, rank, gateway_id, score, reason.
- Ranks strictly 1 to 15 within each week, no repeats, no duplicate gateway in the same week.
- Gateway IDs: 12-char bare hex or 17-char colon hex.
- Numeric, non-empty score (any consistent scale).
- Non-empty reason string, maximum 300 characters, written for the operations manager.

Key Clarifications from FAQ Round 1 on Submission:
- Fixed Visit Component: Because 15 rows/week are mandatory, every valid submission incurs an identical visit cost: 15 visits/week x 8 weeks x 380 EUR = 45,600 EUR.
- Sub-15 Logistical Thresholds: If candidate logic identifies fewer than 15 faulty gateways (e.g. only 9 in Week 3), predictions.csv still requires 15 rows. Rows 10-15 must be filled with the next highest candidates. The saving from withholding those 6 visits is documented in DECISIONS.md.
- Rank Order vs Cost: The scoring script evaluates the set of 15 gateways for the week; it does not weight costs by rank order. However, human reviewers evaluate the ranking order first (top ranks should be strongest picks).
- Offline & Portability: Must run offline in a single command (docker compose up, make run, ./run.sh) reading ./data/ by default and accepting --data <path>. No internet, no GPU, no runtime model downloads. Normal laptop resources (8-16 GB RAM). Reviewers evaluate on a 5-minute clock.

---

## Official Cost Model & Ground Truth

Cost Mechanics (FAQ Round 1 §5.1–§5.4 & FAQ Round 2 §4.1–§4.2):
- Dispatched Visit Cost: 380 EUR once per visit (45,600 EUR fixed across all 120 slots for every valid submission).
- Unaddressed Fault Cost: 600 EUR per faulty gateway per week, flat (not scaled by n_meters_installed).
- Episode Accounting (FAQ Round 2 §4.1):
  * Hidden ground truth pre-defines episodes as maximal runs of consecutive faulty weeks.
  * Episodes are separated by at least one healthy week.
  * Only the EARLIEST visit within an episode counts.
  * Re-picking a gateway later in the same episode saves ZERO euros, wastes 380 EUR, and burns a weekly slot.
  * A new episode (following a healthy week) must be caught separately.
- Evaluation Primacy: Scored strictly on total operational cost, NOT accuracy, precision, recall, or F1 (FAQ Round 2 §4.2).
- Telemetry Invariance: Realized telemetry does NOT change counterfactually; only cost accounting is counterfactual.

Official Hidden Ground Truth:
- Held separately by LPDG per gateway, per week, over the scored window.
- NOT derived from field_visits.csv and NOT engineer_review Kategorie. Those are historical operational records, not the answer key.
- Accounts for gateways not in service in a given week.
- Scorer evaluates precision@15, recall of active faults, and total operational cost compared to the baseline, a reference ranker, and a no-dispatch policy.

---

## Strict Temporal Boundary Rules
- For any prediction week starting Monday T (e.g. 2026-02-09), use ONLY information that existed strictly before that Monday began.
- Baseline boundary: ts_utc < monday_start_utc (Monday 00:00:00 UTC).
- Timezones: ts_utc is UTC. DateDt and hour are Europe/Berlin. Mixing UTC filters on one file and Berlin local on another is a disqualifying bug. Choose one and apply consistently (Monday 00:00:00 UTC is recommended).
- engineer_review_2026-02.xlsx: Dated 15 February 2026. Available ONLY for weeks starting 2026-02-16 onward. Using it for 2026-02-02 or 2026-02-09 is forward-looking leakage.
- meter_read_success.csv: Weekly aggregates. The row for the week being predicted is not available. Earlier weeks are available.

---

## Dataset Audit & Engineering Gotchas

1. gateway_master.csv (332 rows, 10 columns)
- Encoding: Encoded in latin1/cp1252 (German umlauts/characters).
- ID Format: 17-character colon-delimited hex (e.g. 06:39:EA:56:02:C1).
- Gateways: 332 total. 12 decommissioned between 2025-09-22 and 2026-02-25. 52 installed after 2025-08-01 (11 installed in mid-2026 after the scoring period; these have 0 telemetry and must never be dispatched).
- Meters: n_meters_installed range 40 to 822 (Mean 189, Median 156).

2. field_visits.csv (642 rows, 8 columns, 247 unique gateways)
- Encoding: latin1/cp1252.
- ID Format: 17-character colon-delimited hex.
- Outcomes: 390 Kein Fehler gefunden (60.7%), 223 Fehler behoben (34.7%), 29 Kein Zugang (4.5%).
- Selection Bias: Non-random sample. Only contains gateways already suspected. Cannot be used as naive positive/negative ground truth.

3. meter_read_success.csv (7,226 rows, 4 columns, 280 unique gateways)
- Encoding: latin1/cp1252.
- ID Format: 12-character bare hex (e.g. 0202CB0A6B1F).
- Date Range: 26 weeks, 2025-08-04 to 2026-01-26. Contains ZERO records during Feb-Mar 2026 scoring window (simulates real-world billing/metering delay).

4. engineer_review_2026-02.xlsx (120 rows, 5 columns, 120 unique gateways)
- Date: Exactly one date: 2026-02-15.
- Reviewer: Single engineer (M. Hoffmann).
- Labels: Exactly 60 Normal and 60 Schlecht.

5. telemetry/month=YYYY-MM/ (1,433,387 rows, 57 columns, 320 unique gateways across 8 partitions)
- Format: Parquet, partitioned by month (Aug 2025 to Mar 2026).
- ID Format: 12-character bare hex (e.g. 0639EA5602C1).
- Counter Semantics: avg_uptime acts as a resetting uptime clock (resets on reboot); offline_duration_sec behaves empirically as an interval/event-duration metric rather than a monotonic cumulative counter (differencing rejected).
- RF Quality: High CRC error ratios (rx_crc_bad / rx_nr_pkts) are widespread and unlikely to be a standalone failure indicator; causal sources require further validation.

---

## Baseline (baseline_3sigma.py)
- Reads trailing 28 days before Monday 00:00 UTC on 3 metrics: offline_duration_sec, disconnection_cnt, reboot_cnt.
- Computes mean and standard deviation per gateway over 28 days.
- Flags hours in the trailing 7 days where metric exceeds mean + 3*std.
- Ranks gateways descending by flagged-hour count; takes top 15.
- Validated locally: Produces 120 rows across 8 weeks and passes validate_submission.py with exit code 0.

---

## Strategic Track Evaluation: Data Science vs Machine Learning

Track D — Data Science:
- Core Focus: Operationalize needs a visit mathematically; turn 380 EUR and 600 EUR into an explicit decision boundary; uncertainty quantification across gateway cohorts; write-up with charts for the operations manager.
- Live Session Test: Move your threshold, and say what it costs in each direction.
- Marking Strength: Directly rewards business reasoning, financial translation, and failure analysis (25% Judgement + 15% Explanation).

Track E — Machine Learning:
- Core Focus: Beat baseline_3sigma.py on total operational cost; transparent feature selection across 57 telemetry signals; adversarial validation (both grouped on unseen gateways AND forward on future weeks).
- Live Session Test: Make your model better on the month it has not seen.
- Marking Strength: Demonstrates advanced modeling capability, provided the model reliably beats baseline cost offline without complex black-box failure modes.

---

## Round 2 FAQ Ingestion Status: FULLY INCORPORATED
All 4 watchlist areas from Round 1 have been officially resolved by FAQ Round 2 and final:
1. Episode Mechanics: Fully answered in §4.1 (consecutive faulty weeks, single healthy week separator, earliest visit only, repeat picks wasted).
2. Cost & Scoring Primacy: Answered in §4.2 (cost strictly dominates accuracy/F1; F1 is invalid for asymmetric costs).
3. Live Session Format: Answered in §7.1 (additional month partition under `data/telemetry/month=YYYY-MM/` dropped into mounted folder, dynamic partition loading required).
4. Section 8 Syllabus: Detailed in §8 (unanswerable questions cataloging candidate empirical discovery tasks).

---

## Current Working Protocol

[KNOWLEDGE BASE CONSOLIDATION (Phases 0–14 + Round 2 + Submission Email)] -> COMPLETE
            |
            v
[EMPIRICAL EXPERIMENTATION (Backlog E-01 through E-14)] -> NEXT PHASE
            |
            v
[OFFLINE COST SIMULATOR & GROUND TRUTH PROXY HARNESS]
            |
            v
[DEVICE-DISJOINT & FORWARD TEMPORAL VALIDATION]
            |
            v
[MODEL TRAINING & DECISION THRESHOLD CALIBRATION]
            |
            v
[ONE-COMMAND PACKAGING & SUBMISSION (Freeze by 16 Sep 18:00 IST)]

Status: Knowledge Base fully synchronized and verified against all Level 1–7 sources. Ready for empirical experimentation phase.
