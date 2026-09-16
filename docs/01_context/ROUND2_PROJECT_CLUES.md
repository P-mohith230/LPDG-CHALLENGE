# Actionable Project Clues: Round 2 FAQ & Official Guidance
**LPDG Innovation Hub Selection Challenge 2026**  
*Systematic Extraction, Classification, and Operational Ranking of 34 Technical Clues*

---

## Executive Overview

Every sentence in *FAQ — Round Two, and final* and the institutional submission instructions contains actionable guidance for project design. Below, we extract, classify, and prioritize the **34 core project clues** that directly govern our data pipeline, feature engineering, modeling, validation, economic evaluation, and submission packaging.

---

## Priority Group 1: CRITICAL CLUES (Immediate Pass/Fail & Cost Traps)

### Clue 1: Part 1 is an Absolute Pass/Fail Gate
- **SOURCE**: FAQ Round 2 §1.1, Round 1 §1.3, Brief p. 2
- **STATUS**: CONFIRMED BY LPDG
- **CLUE**: Part 1 either works or it does not. A broken Part 1 halts evaluation immediately; Part 2 is never scored regardless of sophistication.
- **WHY IT MATTERS**: An overly ambitious ML model that fails to produce a valid `predictions.csv` via one command scores zero.
- **PROJECT IMPACT**: Execution reliability, validation, and container/runner health take precedence over hyperparameter tuning.
- **ACTION WE SHOULD TAKE**: Lock down the execution runner (`run.sh` / Docker) and automated smoke tests first.

### Clue 2: One-Command End-to-End Execution on a Foreign Machine
- **SOURCE**: FAQ Round 2 §2.3, §7.2, Round 1 §2.1, Brief p. 2
- **STATUS**: CONFIRMED BY LPDG
- **CLUE**: The reviewer will clone the repo, mount data into `./data/` at the root, and execute one command (`docker compose up`, `make run`, or `./run.sh`). No manual steps.
- **WHY IT MATTERS**: Hardcoded laptop paths (e.g. `C:\Users\...`) cause instant gate failure.
- **PROJECT IMPACT**: Path resolution must be relative to project root or use `--data` flags.
- **ACTION WE SHOULD TAKE**: Parameterize the data directory with `./data` as default; test on clean, isolated environment.

### Clue 3: Strict Validation Contract of `predictions.csv`
- **SOURCE**: FAQ Round 2 §1.1, §3.6, Round 1 §1.3, Brief p. 2, `validate_submission.py`
- **STATUS**: CONFIRMED BY SCRIPT
- **CLUE**: Exactly 120 rows (15 rows × 8 weeks), exactly columns `week_start, rank, gateway_id, score, reason`, rank 1..15 with no duplicates within a week, non-null numeric scores, non-empty reasons $\le 300$ chars.
- **WHY IT MATTERS**: Any missing row, NaN score, or duplicated ID causes `validate_submission.py` to exit with code 1.
- **PROJECT IMPACT**: Automated post-processing assertion pipeline is mandatory.
- **ACTION WE SHOULD TAKE**: Embed `python validate_submission.py predictions.csv` into the CI and primary runner.

### Clue 4: Operational Cost, NOT Statistical Accuracy / F1, Governs Evaluation
- **SOURCE**: FAQ Round 2 §4.2, Brief p. 4
- **STATUS**: CONFIRMED BY LPDG
- **CLUE**: *"A model with a better F1 and a worse cost has lost, and saying so yourself is worth more than hoping we do not check."* Accuracy and F1 treat FP and FN as equal; in reality, a missed fault costs €600/week recurring, while a false alarm costs €380 once.
- **WHY IT MATTERS**: Standard classification metrics are dangerously misleading. Optimizing F1 will produce an economically sub-optimal ranking.
- **PROJECT IMPACT**: Loss functions and threshold tuning must directly minimize total simulated euro cost.
- **ACTION WE SHOULD TAKE**: Implement our custom `CostEvaluator` evaluating the official cost matrix as the primary optimization metric.

### Clue 5: Fault Episode Boundaries and Repeat-Visit Penalties
- **SOURCE**: FAQ Round 2 §4.1
- **STATUS**: CONFIRMED BY LPDG
- **CLUE**: An episode is a maximal run of consecutive faulty weeks in hidden truth, separated by $\ge 1$ healthy week. Only your EARLIEST visit within an episode counts. Re-picking the same gateway in subsequent weeks of the same episode buys zero penalty reduction, wastes €380, and burns one of the 15 slots.
- **WHY IT MATTERS**: Static telemetry does not heal. An algorithm that re-picks the same failing gateway across multiple consecutive weeks commits the most expensive mistake in the challenge.
- **PROJECT IMPACT**: Dispatch policy must be state-aware, applying an operational cooldown filter on previously visited gateways.
- **ACTION WE SHOULD TAKE**: Formulate and test a 2- to 3-week suppression filter after dispatch in our simulation harness.

### Clue 6: Counterfactual Telemetry Invariance
- **SOURCE**: FAQ Round 2 §4.1, Round 1 §5.2
- **STATUS**: CONFIRMED BY LPDG
- **CLUE**: Dispatched visits do not modify telemetry records in subsequent weeks. Telemetry was pre-generated. Only cost accounting is counterfactual.
- **WHY IT MATTERS**: Prevents candidates from expecting telemetry to show recovery after a simulated visit.
- **PROJECT IMPACT**: Models must recognize that post-visit telemetry will still appear degraded.
- **ACTION WE SHOULD TAKE**: Rely on algorithm-level state tracking rather than expecting telemetry signals to normalize.

### Clue 7: Hidden Ground Truth is Decoupled from Field Visits & Engineer Reviews
- **SOURCE**: FAQ Round 2 §4.3, Round 1 §4.1
- **STATUS**: CONFIRMED BY LPDG
- **CLUE**: Final scoring uses a hidden, separate truth per gateway per week over the 8 weeks. It is neither `field_visits.csv` nor `engineer_review.xlsx`.
- **WHY IT MATTERS**: Treating field visit outcomes as gold-standard ground truth leads to severe model misspecification.
- **PROJECT IMPACT**: Target definitions must be explicitly labeled as candidate definitions and defended on operational principles.
- **ACTION WE SHOULD TAKE**: Formulate a principled multi-signal proxy target capturing telemetry collapse and meter deficits.

### Clue 8: Strict Runtime Offline Execution (Zero Network, Zero GPU)
- **SOURCE**: FAQ Round 2 §2.1, §2.5, §6.11, Round 1 §2.1
- **STATUS**: CONFIRMED BY LPDG
- **CLUE**: Reviewer's machine has no internet, no GPU, no pre-existing cloud tokens. Any runtime `pip install`, HuggingFace download, or cloud API call fails the gate.
- **WHY IT MATTERS**: All dependencies and pre-trained model weights must be pre-packaged and bundled locally.
- **PROJECT IMPACT**: Lightweight CPU-only libraries (scikit-learn, LightGBM, XGBoost) running in seconds.
- **ACTION WE SHOULD TAKE**: Pin all requirements, test offline with network disabled, and commit model weights into git.

### Clue 9: Dynamic Partition Ingestion (Never Hardcode 8 Partitions)
- **SOURCE**: FAQ Round 2 §7.1
- **STATUS**: CONFIRMED BY LPDG
- **CLUE**: In the live session, an unseen month (e.g. `month=2026-04`) will be dropped into `data/telemetry/`. Code that hardcodes 8 partitions or assumes March 2026 is terminal will crash.
- **WHY IT MATTERS**: Hardcoding partition lists is an immediate failure mode during live evaluation.
- **PROJECT IMPACT**: Ingestion code must dynamically discover all directories matching `data/telemetry/month=*`.
- **ACTION WE SHOULD TAKE**: Use `sorted(glob("data/telemetry/month=*"))` dynamically in all data loaders.

### Clue 10: Institutional Submission Deadline is 20:00 IST (Stricter than LPDG)
- **SOURCE**: NEXORA 2026 Project Submission Email vs. FAQ Round 1 §1.1
- **STATUS**: CONFIRMED BY SUBMISSION EMAIL
- **CLUE**: RGMCET institutional submission closes at **20:00 IST on Wednesday 16 September 2026** via Google Form (`https://forms.gle/qHZqsRRPGWf8ja5S6`). LPDG's deadline is 23:59 IST.
- **WHY IT MATTERS**: Submitting at 21:00 IST satisfies LPDG but fails the institutional gate!
- **PROJECT IMPACT**: All internal development, packaging, and video recording must freeze by 18:00 IST on 16 September.
- **ACTION WE SHOULD TAKE**: Align all countdowns and checklists strictly to 20:00 IST on 16 September 2026.

---

## Priority Group 2: HIGH IMPORTANCE CLUES (Modeling, Validation & Evaluation)

### Clue 11: Future Historical Telemetry May Be Used for Labeling Without Leakage
- **SOURCE**: FAQ Round 2 §4.5, Round 1 §6.13
- **STATUS**: CONFIRMED BY LPDG
- **CLUE**: Deriving a label from what happened next within the historical window (prior to the decision cutoff) is valid and encouraged. Feature sets for week $k$ must not use telemetry from week $k+1$.
- **WHY IT MATTERS**: Enables training supervised models on actual downstream gateway failures in 2025 data.
- **PROJECT IMPACT**: We can construct forward-looking ground-truth failure targets in historical data.
- **ACTION WE SHOULD TAKE**: Build lead-time targets ($T+7$ days) strictly on historical data prior to 2026-02-02.

### Clue 12: Selection Bias in Field Visits (Unvisited Gateways are Unlabelled)
- **SOURCE**: FAQ Round 2 §4.4, Round 1 §4.4
- **STATUS**: CONFIRMED BY LPDG
- **CLUE**: Gateways in `field_visits.csv` were already suspected. Quietly broken gateways were never visited. Unvisited $
e$ healthy.
- **WHY IT MATTERS**: Naive binary classification treating unvisited as negative induces severe confirmation bias.
- **PROJECT IMPACT**: Frame target modeling around positive-unlabelled (PU) learning or objective physical telemetry degradation.
- **ACTION WE SHOULD TAKE**: Explicitly document this selection bias in `DECISIONS.md` and avoid treating unvisited as true negatives.

### Clue 13: Telemetry Silence is Intentionally Ambiguous
- **SOURCE**: FAQ Round 2 §3.4, §8, Round 1 §4.6
- **STATUS**: CONFIRMED BY LPDG
- **CLUE**: Telemetry layout is sparse; missing hours are absent rows. Silence has multiple causes. Loader logic must distinguish absent rows from zero values.
- **WHY IT MATTERS**: Pure rolling statistics (like 3-sigma baseline) are mathematically blind to missing rows.
- **PROJECT IMPACT**: We must build an explicit "Missingness / Silence Detector" that counts absent hours.
- **ACTION WE SHOULD TAKE**: Create a complete time-grid reindexing step to measure consecutive missing hours per gateway.

### Clue 14: Adversarial Validation Must Be Grouped AND Forward
- **SOURCE**: FAQ Round 2 §5.2, §6.9, Round 1 §6.12
- **STATUS**: CONFIRMED BY LPDG
- **CLUE**: Validation must test on gateways the model has never seen (device-disjoint) AND on weeks after training (forward-in-time). Random hourly splits carry zero evidentiary value (memorize device ID).
- **WHY IT MATTERS**: A high CV score on random splits will be dismissed as zero information by reviewers (25% Judgement).
- **PROJECT IMPACT**: Implement GroupKFold on `gateway_id` combined with expanding temporal train/test splits.
- **ACTION WE SHOULD TAKE**: Build our validation harness with device-disjoint GroupKFold and temporal holdout on January 2026.

### Clue 15: Validation Spread and Stability Must Be Reported
- **SOURCE**: FAQ Round 2 §5.2, Brief p. 4
- **STATUS**: CONFIRMED BY LPDG
- **CLUE**: Quoting a single number to three decimals is penalized. Candidates must quote performance ranges and fold-to-fold variation.
- **WHY IT MATTERS**: Fleet size is small (~320 devices); variance across gateway cohorts is naturally high.
- **PROJECT IMPACT**: All evaluation tables must report Mean $\pm$ Std or Min–Max ranges across folds.
- **ACTION WE SHOULD TAKE**: Structure all validation outputs to report metric ranges across folds.

### Clue 16: Deterministic Tie-Breaking is Mandatory
- **SOURCE**: FAQ Round 2 §3.6
- **STATUS**: CONFIRMED BY LPDG
- **CLUE**: Random tie-breaking without a seed is considered a bug. An explicit secondary sort key (e.g. `gateway_id` or `n_meters_installed`) is required.
- **WHY IT MATTERS**: Discrepancies between consecutive runs will be caught during live evaluation.
- **PROJECT IMPACT**: Every ranking operation must have a deterministic multi-column sort key.
- **ACTION WE SHOULD TAKE**: Enforce `.sort_values(by=['score', 'n_meters_installed', 'gateway_id'], ascending=[False, False, True])`.

### Clue 17: Operational Definition of "Needs a Visit" Must Be Defended
- **SOURCE**: FAQ Round 2 §5.1, Round 1 §4.1, Brief p. 3
- **STATUS**: CONFIRMED BY LPDG
- **CLUE**: Must write down an operational definition, defend it, state what alternatives were rejected, and state what it gets wrong.
- **WHY IT MATTERS**: Core 25% Judgement component. LPDG evaluates the ability to establish domain criteria.
- **PROJECT IMPACT**: Must be clearly articulated in `DECISIONS.md`.
- **ACTION WE SHOULD TAKE**: Formalize our hybrid failure definition and document rejected alternatives.

### Clue 18: Decision Threshold Must Be Tied to Cost Economics
- **SOURCE**: FAQ Round 2 §5.1, Brief p. 4
- **STATUS**: CONFIRMED BY LPDG
- **CLUE**: Turn €380 and €600 into an actual threshold with priced consequences of moving it in each direction.
- **WHY IT MATTERS**: Required deliverable for Data Science track and live session modification.
- **PROJECT IMPACT**: Provide sensitivity curves showing total cost as a function of dispatch threshold $	au$.
- **ACTION WE SHOULD TAKE**: Script a parametric cost-curve generator showing $\Delta 	ext{Cost} / \Delta 	au$.

### Clue 19: Limitations ("What It Cannot Do") is a Marked Strength
- **SOURCE**: FAQ Round 2 §5.3, §5.4, Brief p. 2, 4
- **STATUS**: CONFIRMED BY LPDG
- **CLUE**: Candidates who list three real, costed weaknesses outrank candidates who claim perfection.
- **WHY IT MATTERS**: Demonstrates engineering maturity and critical self-awareness.
- **PROJECT IMPACT**: Dedicated section in `DECISIONS.md` or standalone `LIMITATIONS.md`.
- **ACTION WE SHOULD TAKE**: Explicitly document 3 architectural limitations and their operational cost.

### Clue 20: Decouple Training from Prediction
- **SOURCE**: FAQ Round 2 §7.2, Round 1 §6.14, Brief p. 4, 5
- **STATUS**: CONFIRMED BY LPDG
- **CLUE**: Anything that retrains a model during inference will not finish in the 35-minute room. Pre-train, serialize, and load weights for inference.
- **WHY IT MATTERS**: Re-training on 1.4M rows takes minutes and introduces non-deterministic live failures.
- **PROJECT IMPACT**: Strict two-stage architecture: `train.py` saves model artifact; `predict.py` loads artifact.
- **ACTION WE SHOULD TAKE**: Separate `src/train.py` and `src/predict.py`; commit serialized model artifact.

---

## Priority Group 3: MEDIUM IMPORTANCE CLUES (Design & Strategy)

### Clue 21: Small Derived Model Artefacts May Be Committed
- **SOURCE**: FAQ Round 2 §2.2
- **STATUS**: CONFIRMED BY LPDG
- **CLUE**: A few KB of JSON/parameters/weights is candidate work product. Raw dataset slices are strictly forbidden.
- **PROJECT IMPACT**: Model weights can be committed directly to git for offline loading.
- **ACTION WE SHOULD TAKE**: Ensure serialized model artifacts (`model.pkl` / `weights.json`) are $<2	ext{ MB}$.

### Clue 22: Recent Data Weighting Trade-off
- **SOURCE**: FAQ Round 2 §3.5
- **STATUS**: CANDIDATE DECISION / REASONABLE INFERENCE
- **CLUE**: Weighting recent hours reacts faster but is noisier. Historical baselines are steadier but delayed.
- **PROJECT IMPACT**: Build dual-window features ($T-24	ext{h}$, $T-7	ext{d}$, $T-28	ext{d}$).
- **ACTION WE SHOULD TAKE**: Implement exponential decay or multi-window aggregations and test in Experiment E-06.

### Clue 23: Handling Incomplete Telemetry per Gateway
- **SOURCE**: FAQ Round 2 §3.7
- **STATUS**: CANDIDATE DECISION
- **CLUE**: Excluding incomplete gateways misses degraded devices; scoring on partial data compares sparse hours against 168.
- **PROJECT IMPACT**: Compute normalized hourly intensity rates rather than raw sums.
- **ACTION WE SHOULD TAKE**: Use hourly rate indicators (`metric_per_reporting_hour`) with a reporting confidence penalty.

### Clue 24: Gateway Population Churn (Dynamic Fleet)
- **SOURCE**: FAQ Round 2 §7.1, Data Audit
- **STATUS**: CONFIRMED BY LPDG & OBSERVED IN DATA
- **CLUE**: Gateway fleet fluctuates (280 in Aug 2025 to 308 in Mar 2026). Do not assume static 320 IDs.
- **PROJECT IMPACT**: Pipelines must handle new gateway IDs gracefully without key errors.
- **ACTION WE SHOULD TAKE**: Implement default/prior imputations for newly appearing gateway IDs.

### Clue 25: Dashboard Earns Zero Marks in ML Track
- **SOURCE**: FAQ Round 2 §6.12
- **STATUS**: CONFIRMED BY LPDG
- **CLUE**: A dashboard earns zero marks against the 60% ML track. In Data Science, static charts for operations managers are preferred.
- **PROJECT IMPACT**: Do not waste time building Streamlit dashboards or web UIs.
- **ACTION WE SHOULD TAKE**: Generate clean, publication-quality static SVG/PNG charts for the README and report.

### Clue 26: Synthetic Fixtures for Unit Testing
- **SOURCE**: FAQ Round 2 §6.2
- **STATUS**: CONFIRMED BY LPDG
- **CLUE**: Test fixtures must be small, synthetic, hand-built data (inline or tiny CSVs), not sliced raw dataset files.
- **PROJECT IMPACT**: Enables fast unit testing in CI without committing 104 MB dataset.
- **ACTION WE SHOULD TAKE**: Create synthetic test fixtures in `tests/fixtures/` with 3 mock gateways over 48 hours.

### Clue 27: Reason String Must Speak to Operations Manager
- **SOURCE**: FAQ Round 2 §5.3, Round 1 §3.5
- **STATUS**: CONFIRMED BY LPDG
- **CLUE**: Reasons must be diagnostic explanations in plain language ($\le 300$ chars), not raw feature vectors.
- **PROJECT IMPACT**: Format: `"[Severity] Primary diagnostic breach (e.g. 48h offline, CRC fail >90%), N meters at risk."`
- **ACTION WE SHOULD TAKE**: Implement rule-based reason generator template producing actionable operational text.

### Clue 28: Live Session Tests Code Understanding, Not Perfect Accuracy
- **SOURCE**: FAQ Round 2 §5.5, §7.1, §7.2
- **STATUS**: CONFIRMED BY LPDG
- **CLUE**: Reviewers evaluate whether candidates understand load-bearing parts of their code and narrate hypotheses during errors.
- **PROJECT IMPACT**: Clean, readable, modular code is vastly superior to complex, convoluted logic.
- **ACTION WE SHOULD TAKE**: Write concise, modular functions with descriptive docstrings and clear seams.

---

## Priority Group 4: LOW IMPORTANCE / HYGIENE CLUES

### Clue 29: Screen Recording Linking Format
- **SOURCE**: FAQ Round 2 §2.1
- **STATUS**: CONFIRMED BY LPDG
- **CLUE**: Unlisted YouTube/Vimeo link or public Google Drive link in `README.md`. Must open in private browser window.
- **ACTION WE SHOULD TAKE**: Record 6–8 minute walkthrough, upload as unlisted YouTube, test in incognito window.

### Clue 30: Resume Naming Convention
- **SOURCE**: NEXORA 2026 Submission Email
- **STATUS**: CONFIRMED BY SUBMISSION EMAIL
- **CLUE**: Place resume in root repository directory named `<Registration_Id.pdf>` (e.g. `23091a3286.pdf`).
- **ACTION WE SHOULD TAKE**: Ensure resume is placed at repository root with exact student ID filename.

### Clue 31: Duplicate Submission Ban
- **SOURCE**: NEXORA 2026 Submission Email
- **STATUS**: CONFIRMED BY SUBMISSION EMAIL
- **CLUE**: Only the first submission via Google Form is considered. Subsequent submissions are summarily rejected.
- **ACTION WE SHOULD TAKE**: Perform full end-to-end rehearsal before submitting the Google Form once.

### Clue 32: In-Person Evaluation Logistics
- **SOURCE**: NEXORA 2026 Submission Email
- **STATUS**: CONFIRMED BY SUBMISSION EMAIL
- **CLUE**: In-person evaluation at RGMCET campus on 18 September 2026, 9:00 AM.
- **ACTION WE SHOULD TAKE**: Rehearse live demonstration on personal laptop ensuring full offline capability.

### Clue 33: Two-Week Roadmap Prioritization
- **SOURCE**: FAQ Round 2 §5.4
- **STATUS**: CONFIRMED BY LPDG
- **CLUE**: Provide a prioritized, costed list of 3 specific improvements rather than vague claims.
- **ACTION WE SHOULD TAKE**: Include a structured, costed 2-week engineering roadmap in `DECISIONS.md`.

### Clue 34: No Traffic Classification or Security Intrusion Modeling
- **SOURCE**: FAQ Round 2 §8
- **STATUS**: CONFIRMED BY LPDG
- **CLUE**: This challenge is utility fleet health, not cybersecurity or network intrusion detection.
- **ACTION WE SHOULD TAKE**: Focus exclusively on hardware, power, antenna, and connectivity failures.
