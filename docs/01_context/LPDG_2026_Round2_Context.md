# LPDG Innovation Hub 2026 — Round 2 Working Context

## SECTION 1 — Round 2 Overview
- Source Document: FAQ — Round Two, and final (Published week of 07 September 2026).
- Prepared by: Tarun Gupta, LPDG. Audience: Candidates.
- Scope: Represents the final official set of answers before project hand-in. It complements and extends 03-FAQ-Round-1.pdf rather than replacing it.
- Binding Hand-in Deadline: Wednesday 16 September 2026. (Note: Institutional NEXORA submission email sets the deadline at 20:00 IST, whereas LPDG sets 23:59 IST. The stricter 20:00 IST deadline must be honored).
- Nature of Round 2: Re-emphasizes that Part 1 is an unyielding pass/fail gate. It clarifies critical evaluation mechanics (such as the definition and accounting of fault episodes), underscores the necessity of cost-driven evaluation over standard ML metrics, and details the expectations for the live evaluation session.

---

## SECTION 2 — Every Official Round-2 Clarification

### 1. What this is, and what comes after it
- §1.1 Competition of Ideas / Originality: NOT a competition of ideas or novelty. It is a recruitment assessment with a fixed operational task: rank 15 gateways a week and build one area deeply around it. Originality is scored strictly under Judgement (what was questioned, rejected, and defended).
- §1.2 Mentorship: No mentorship during the challenge; the assessment mirrors an examination setting where all information is shared equally via FAQs.
- §1.3 Internship Outcome: A strong submission leads to an interview before the selection panel and an invitation to the live session.
- §1.4 Area Selection: Part 2 selection signals candidate strength and intended focus, but does not lock the candidate in permanently. The panel evaluates whether a candidate demonstrated mastery in other disciplines as well.
- §1.5 Post-Deadline Work: Only work committed and pushed by the deadline (16 September) is marked. Live sessions require running and modifying the exact code submitted.

### 2. Deliverables, and what goes in the repository
- §2.1 Screen Recording: 6 to 8 minutes. Must be linked in README.md (unlisted YouTube/Vimeo or public Drive/OneDrive link). Must open cleanly in an incognito/private browser window without requiring permissions. Files under 25 MB may be committed, but a link is preferred.
- §2.2 Derived Model Artefacts: Candidates MAY commit small learned parameter files (a few KB of JSON, weights, thresholds, input hashes, version strings). Candidates MUST NOT commit raw telemetry slices or the 104 MB dataset disguised as model artifacts. Cached intermediates must be rebuilt by the pipeline, not committed.
- §2.3 API Deployment: Running locally on localhost is expected (via docker compose up, make run, ./run.sh). Cloud deployment is neither required nor rewarded; any failure of a cloud instance fails the gate.
- §2.4 Features Beyond Minimum: Evaluated strictly against the chosen area's 6 bullet points. Extraneous, half-finished features harm the Judgement score. Finish the core bullets first.
- §2.5 Additional Python Libraries: Any library is permitted provided it runs offline without internet access, logins, or runtime downloads. All package versions must be pinned.
- §2.6 Data and Tool Sufficiency: The supplied bundle contains 100% of required data. No external APIs or paid services are needed.

### 3. The data, and what it covers
- §3.1 Date Ranges:
  - telemetry: 2025-08-01 to 2026-03-31, hourly (1,433,387 rows across 8 partitions).
  - meter_read_success.csv: weeks 2025-08-04 to 2026-01-26 (7,226 rows; ends prior to the scored window).
  - field_visits.csv: visited_on 2025-02-05 to 2026-02-14; requested_on 2025-02-03 to 2026-01-30 (642 rows).
  - engineer_review_2026-02.xlsx: single day, 2026-02-15 (120 rows).
  - gateway_master.csv: 332 rows, static asset register.
- §3.2 Handling Odd, Wrong, or Missing Values: Do not infer data shape from column names; inspect actual values. Decide per column rather than applying blanket fillna(0). Distinguish between a value being wrong versus absent. Document data cleaning costs in DECISIONS.md.
- §3.3 Missing Data Sensitivity: Missing data significantly impacts rankings. Candidates should run an experiment comparing rankings with and without specific missing-data handling.
- §3.4 Telemetry Silence: Silence has multiple causes (hardware failure, power outage, benign unmonitored state). Physical telemetry layout is sparse: hours without readings are absent rows, not zero-filled rows. Loader logic must check whether absence is represented as a row or a missing record.
- §3.5 Recent Data Weighting: Trade-off between fast, noisy signals and steady, delayed signals. The asymmetric cost structure (recurring 600 EUR vs one-time 380 EUR) favors early detection.
- §3.6 Score Ties & Determinism: Ranks must be 1 to 15 without repeats. Ties must be broken deterministically using an explicit secondary key (e.g., gateway_id or meter count). Random tie-breaking is strictly unacceptable.
- §3.7 Incomplete Telemetry: Excluding incomplete gateways risks ignoring degraded devices; scoring on partial data compares sparse hours against full 168-hour baselines. Candidates must defend their choice.

### 4. Scoring, episodes and the cost model
- §4.1 Episode Mechanics & Repeat Visits:
  - Fault episodes are computed from the held-out ground truth alone before candidate submissions are evaluated.
  - An episode is a maximal run of consecutive faulty weeks. A single healthy week separates episodes.
  - Only the EARLIEST visit within an episode counts. The episode incurs 600 EUR/week from its onset up to and including the week visited.
  - Re-picking a gateway later within the same episode confers zero benefit; it wastes a 380 EUR visit and consumes one of the 15 weekly slots.
  - A new fault episode occurring after a healthy week must be caught separately.
  - Telemetry is static; only cost accounting is counterfactual.
- §4.2 Cost vs. Statistical Metrics: Models are judged strictly on total operational cost, NOT accuracy, precision, recall, or F1. F1 incorrectly treats false positives and false negatives as equal.
- §4.3 Ground Truth Separation: Final grading relies on hidden ground truth, not field visit outcomes or engineer reviews.
- §4.4 Unvisited Gateways: Unvisited gateways cannot be assumed healthy. They represent unlabelled data in a positive-unlabelled (PU) learning setting.
- §4.5 Future Telemetry for Labeling: Future historical telemetry (prior to the decision cutoff) may be used to engineer training labels, provided target leakage into feature sets is strictly prevented.

### 5. How you will be read, and how to defend it
- §5.1 Core Data Science Criteria:
  1. A formal, defensible definition of needs a visit, including rejected alternatives.
  2. An honest evaluation declaring what the test cannot prove.
  3. Reporting performance ranges and uncertainty across gateway cohorts.
  4. Explicit translation of 380 EUR and 600 EUR into a calibrated decision threshold.
  5. Executive-ready reporting tailored to an operations manager.
- §5.2 Validation Rigor: Validation must be device-disjoint and forward-in-time. Random splits of hourly telemetry carry zero evidentiary weight (devices are memorized). Report fold-to-fold variance.
- §5.3 Common Deficiencies: Inability to navigate own code, claiming unverified scalability, defensive attitudes toward identified weaknesses, process-heavy write-ups lacking conclusions, DECISIONS.md lacking rejected alternatives, hiding limitations, and failing to narrate during live debugging.
- §5.4 Two-Week Roadmap: Must be concrete, prioritized, and costed.
- §5.5 Live Session Criteria: Evaluates code familiarity, structured error reading, hypothesis generation, and understanding of load-bearing components.

### 6. Area-specific clarifications
- §6.1-§6.5 Software Development: Focus on API modularity, decoupled ranking logic, test fixtures over full datasets, dynamic data reload on /run without restarting containers.
- §6.6 Data Engineering: Focus on pipeline resilience, schema assertions, and handling unexpected data corruptions.
- §6.7 Dataset Combinations: Permissible to combine all provided files, provided cutoff rules are honored.
- §6.8 Baseline Modification: Modifying baseline logic pertains to Part 1 ranking; Part 2 focuses on discipline-specific depth.
- §6.9 ML Validation Strategy: Must feature unseen gateways and future weeks. Report metric spread.
- §6.10-§6.11 MLOps: CLI-based rollback with clear runbooks is fully acceptable. Offline execution is mandatory at runtime.
- §6.12 Dashboards: Earns zero marks against Part 2 60% weight. For Data Science, clear static charts for the operations manager are preferred.

### 7. The live session
- §7.1 Unseen Data Partition: An additional month partition (e.g., month=2026-04) will be dropped into data/telemetry/. Schema and conventions remain identical. Gateway population may change (some devices quiet, new devices added). Hard-coding 8 partitions or March 2026 as the terminal month will break execution.
- §7.2 Rehearsal: Verify execution in a clean environment, practice the area-specific modification, and ensure training is fully decoupled from inference.

---

## SECTION 3 — Our Two Questions and Their Answers / Status

### Question 1: Fault Episode Boundary Accounting & Re-visit Penalties
- Formulated Question: If a gateway is visited in week k and that visit ends the 600 EUR accrual, how does the scorer determine whether a later visit belongs to the same episode or a new episode given static telemetry?
- Status: ANSWERED FULLY IN §4.1.
- Official Mechanism:
  1. Hidden ground truth pre-defines episodes as maximal runs of consecutive faulty weeks.
  2. A single healthy week between faulty stretches establishes a new episode.
  3. Only the earliest visit within an episode counts.
  4. Subsequent visits within the same episode cost 380 EUR, consume a slot, and provide zero cost reduction.
- Architectural Consequence: Dispatch logic must incorporate an operational cooldown / suppression memory (e.g., masking visited gateways for 2-3 weeks unless a distinct re-emergence signature is detected).

### Question 2: Telemetry Silence as a Failure Signal vs. Observability Artifact
- Formulated Question: For an active gateway with complete telemetry silence, is absence of data a failure signal or an observability issue?
- Status: INTENTIONALLY LEFT OPEN AS CANDIDATE INVESTIGATION (§3.3, §3.4, §4.6, §8).
- Official Clarification: LPDG explicitly refuses to declare whether silence is a fault or nuisance. Physical telemetry is sparse (missing hours are omitted rows). Candidates must inspect the data, formulate a hypothesis, test whether silence correlates with meter read deficits or technician dispatches, and defend their silence-handling policy.

---

## SECTION 4 — Section 8 Unanswerable-Question Analysis
(Refer to dedicated artifact: ROUND2_UNANSWERABLE_QUESTIONS_ANALYSIS.md for comprehensive breakdown).
- Core Insight: Questions probing empirical data facts (e.g., whether reboot spikes correlate with failures) were rejected because candidates can measure them directly in under an hour.
- Assessment Intent: LPDG evaluates the scientific method: Hypothesis -> Empirical Test -> Result -> Acknowledged Limitation -> Decision.

---

## SECTION 5 — New Confirmed Rules
1. Episode Construction: Consecutive faulty weeks in hidden truth = 1 episode; separated by >=1 healthy week. [CONFIRMED BY LPDG: FAQ §4.1]
2. Earliest Visit Primacy: Only the first visit within an episode halts 600 EUR accrual. [CONFIRMED BY LPDG: FAQ §4.1]
3. Repeat Visit Penalty: Re-dispatching to an already-cured episode costs 380 EUR, burns a slot, and yields 0 EUR benefit. [CONFIRMED BY LPDG: FAQ §4.1]
4. Fixed 45,600 EUR Dispatch Baseline: All valid 120-row submissions pay identical visit costs; cost variation occurs entirely on the 600 EUR unaddressed fault side. [CONFIRMED BY LPDG: FAQ §3.4, §5.2]
5. Primary Evaluation Metric: Total operational cost dominates accuracy, precision, recall, and F1. [CONFIRMED BY LPDG: FAQ §4.2]
6. Static Telemetry Counterfactuals: Telemetry does not react to visits; counterfactuals apply solely to cost accounting. [CONFIRMED BY LPDG: FAQ §4.1, §5.2]
7. Model Artefact Commits: Small JSON/parameter files (<1-2 MB) are permitted in Git; raw data disguised as models is prohibited. [CONFIRMED BY LPDG: FAQ §2.2]
8. Dynamic Partition Ingestion: Ingestion code must dynamically discover partitions under data/telemetry/ without hardcoding 8 months. [CONFIRMED BY LPDG: FAQ §7.1]
9. Deterministic Ranking: Secondary sorting key is required; random tie-breaking is considered a critical defect. [CONFIRMED BY LPDG: FAQ §3.6]
10. Stricter Institutional Deadline: NEXORA institutional submission deadline is Wednesday 16 September 2026, 20:00 IST via official Google Form. [CONFIRMED BY SUBMISSION EMAIL]

---

## SECTION 6 — New Candidate Decisions
1. State-Aware Cooldown Policy: Formulate a 2- to 3-week suppression filter following a dispatch to prevent burning 380 EUR on redundant picks.
2. Silence Detector Formulation: Define an explicit missingness threshold (e.g., >=48 consecutive missing hourly records) as a distinct operational risk feature.
3. Imputation Strategy: Avoid global fillna(0); implement per-column imputation and track dropped gateway-weeks.
4. Validation Window Topology: Structure 4-fold device-disjoint cross-validation combined with expanding forward temporal validation on January 2026.
5. Primary Secondary Sort Key: Standardize on gateway_id (or n_meters_installed) for deterministic tie-breaking.

---

## SECTION 7 — Open Questions Intentionally Left by LPDG
1. Operational Definition of needs a visit: LPDG will not provide a ground-truth formula.
2. Temporal Horizon for Early Detection: How many weeks in advance a deteriorating gateway must be flagged.
3. Acceptable False Alarm Rate: Determining where the precision-cost trade-off balances.
4. Relative Metric Importance: Determining whether RF noise, reboot counts, or backhaul dropouts represent primary failure drivers.
5. Bad Signal with Intact Meter Reads: Whether a gateway with poor signal quality but normal meter transmission constitutes a visitable fault.
6. Decision Threshold Calibration: Mathematical location of the operating cutoff.

---

## SECTION 8 — Data Science & Machine Learning Implications
- Loss Function Alignment: Models must optimize expected cost savings rather than cross-entropy or F1.
- Target Engineering: Supervised labels derived from future historical telemetry must focus on unrecoverable failure states (e.g., terminal dropouts or persistent meter reading collapse).
- Explainability: Every recommended gateway must have a human-readable reason string (<=300 chars) that explains the operational diagnosis to a field supervisor.
- Simplicity and Load-Bearing Design: Complex architectures that cannot be modified live in 10 minutes represent severe operational liabilities.

---

## SECTION 9 — Validation Implications
- Sceptic-Proof Validation: Random row splitting is prohibited. Validation must split along two orthogonal axes:
  1. Device-disjoint (models tested on gateways never seen in training).
  2. Forward-in-time (models trained on months M1..Mt and evaluated on Mt+1).
- Uncertainty and Spread: Point estimates must be replaced by performance ranges across folds.

---

## SECTION 10 — Economic & Cost Implications
- Fixed Cost: 45,600 EUR (120 x 380 EUR) across 8 weeks.
- Variable Penalty: 600 EUR per gateway per week left faulty.
- Opportunity Cost of Sub-optimal Picks: A slot allocated to a healthy gateway or a redundant visit wastes 380 EUR and forfeits the opportunity to stop an active 600 EUR/week bleed.

---

## SECTION 11 — Submission Implications
- File Schema: predictions.csv must have 120 rows, 5 columns (week_start, rank, gateway_id, score, reason), ranks 1..15.
- Deliverable Bundle: README.md, DECISIONS.md (5 choices with rejected alternatives), AI-USAGE.md, video recording link, resume PDF (<Registration_Id.pdf>), and model weights in repo.
- Submission Channel: Official Google Form (https://forms.gle/qHZqsRRPGWf8ja5S6) using official student email by 20:00 IST on 16 September 2026.

---

## SECTION 12 — Live-Session Implications
- Environment: Process executes on localhost with mounted data/ folder; no internet or GPU access.
- Live Modification Muscle: Candidates will be asked to make one live change (e.g., move decision threshold, adapt model to unseen partition, or rollback). Code must be clean, modular, and well-understood.
- Narration: Candidates must vocalize hypotheses and diagnostic steps when errors occur.

---

## SECTION 13 — High-Value Experiments Suggested by Round 2
1. Impact of Missing Data Handling: Run end-to-end ranking with vs. without explicit handling of missing telemetry rows (FAQ §3.3).
2. Silence vs. Failure Correlation: Measure whether prolonged timestamp gaps precede meter read drops or technician dispatches (FAQ §3.4).
3. Metric Information Content: Quantify correlation between offline duration, reboot frequency, and subsequent meter reading failure (FAQ §8).
4. Cooldown Duration Optimization: Simulate cost impacts of 1-week, 2-week, 3-week, and permanent suppression of visited gateways across the 8-week horizon.
5. Grouped vs. Random Split Performance Gap: Quantify the drop in metric performance when moving from random CV to device-disjoint CV.

---

## SECTION 14 — Things We Must NOT Assume
- Do NOT assume missing telemetry produces zero-filled rows (records are entirely omitted).
- Do NOT assume a visit cures telemetry in the dataset (telemetry is unreactive).
- Do NOT assume unvisited gateways are healthy (PU learning setting).
- Do NOT assume official scoring scales by meter count (flat 600 EUR per gateway).
- Do NOT assume March 2026 is the final partition (unseen months will be provided).
- Do NOT assume a low F1 score indicates a failed model if operational cost is reduced.

---

## SECTION 15 — Things We Should Investigate Before Modeling
1. Empirical distribution of timestamp gaps across active gateways.
2. Signal-to-failure correlation of reboot and load spikes.
3. Meter read deficit baseline across all gateways prior to February 2026.
4. Exact behavior of baseline_3sigma.py on silent vs. noisy gateways.

---

## SECTION 16 — Updated Project Strategy
1. Phase 1: Establish leakage-free data loader supporting dynamic partition discovery and deterministic tie-breaking.
2. Phase 2: Implement offline cost simulator incorporating multi-week episode tracking and repeat-visit penalties.
3. Phase 3: Execute empirical feature-utility experiments suggested by Section 8.
4. Phase 4: Construct device-disjoint, forward-in-time validation harness.
5. Phase 5: Train and validate interpretable models; calibrate decision thresholds against operational economics.
6. Phase 6: Package containerized, reproducible pipeline and compile all required documentation.

---

## SECTION 17 — Risks and Failure Modes
- Risk 1: Silent failure during live session due to hard-coded partition paths or gateway counts.
- Risk 2: Severe cost penalties caused by repeated selection of already-cured gateways.
- Risk 3: Pipeline crash on unseen gateways or complete telemetry silence.
- Risk 4: Disqualification due to late submission past the institutional 20:00 IST deadline.
- Risk 5: Disqualification due to private repository or broken video recording link.

---

## SECTION 18 — Source References
- 01-Challenge-Brief.pdf (LPDG Innovation Hub, Tarun Gupta)
- 02-Data-Dictionary.pdf (LPDG Innovation Hub)
- 03-FAQ-Round-1.pdf (LPDG Innovation Hub, 31 August 2026)
- FAQ — Round Two, and final (LPDG Innovation Hub, 07 September 2026)
- NEXORA 2026 Project Submission Email (RGMCET CSEDS Department, 15 September 2026)
- baseline_3sigma.py & validate_submission.py
