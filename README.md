# LPDG Innovation Hub Selection Challenge 2026
**Autonomous Gateway Failure Prediction & Technician Dispatch Optimization**  
**Candidate Registration ID**: `23091a3286`  
**Selected Part 2 Track**: **Track E — Machine Learning**  

---

## 1. Executive Summary & Problem Formulation

The **LPDG Innovation Hub Selection Challenge 2026** tasks data science teams with optimizing weekly on-site technician dispatches across a fleet of 320 cellular smart-meter telemetry gateways. 

- **Operational Mission**: Select exactly 15 gateways per week across 8 scored weeks (February 2, 2026 – March 23, 2026), totaling 120 dispatches.
- **Economic Objective**: Minimize total utility operational cost under an asymmetric penalty structure:
  $$\text{Total Cost} = \text{Visit Costs (€380 per dispatch)} + \text{Unaddressed Fault Penalties (€600 per gateway-week)}$$
- **Fixed Component**: Every valid 120-visit submission incurs a fixed dispatch cost of $120 \times €380 = €45,600$.
- **Variable Optimization Goal**: Accurately intercept and halt active multi-week collection deficit episodes before unaddressed €600 penalties compound.
- **Historical Proxy-Target Economic Benchmarks** *(evaluated on historical 16-week proxy targets, not official hidden-ground-truth scores or guaranteed savings)*:
  - **Official 3-Sigma Baseline (`baseline_3sigma.py`)**: **€164,400** (122 unaddressed faults, 67.20% recall).
  - **Frozen Baseline V1 (Stage 9)**: **€128,400** (62 unaddressed faults, 83.33% recall).
  - **Promoted Champion Pipeline (Candidate C3)**: **€115,200** (40 unaddressed faults, 89.25% recall).
  - **Benchmark Impact**: Slashes 16-week proxy operational cost by **€49,200 (-29.93%)** vs the 3-Sigma baseline, cutting unaddressed proxy penalty losses by **67.2%**.

---

## 2. Part 2 Specialization: Track E — Machine Learning

We formally selected **Track E (Machine Learning)** because the core challenge problem is outperforming the unsupervised reference standard under asymmetric financial risk. Our solution demonstrates deep machine learning rigor:

1. **Defeating the Reference Benchmark**: Reduces 16-week operational cost by €49,200 vs `baseline_3sigma.py` with 89.25% recall on severe collection deficits.
2. **Feature Ablation & Redundancy Analysis**: Rigorous empirical proof that telemetry silence, offline duration, and gateway self-baselines provide orthogonal predictive signal, while pruning saturated CRC error metrics ($R = 1.0000$).
3. **Dual Adversarial Validation**:
   - **Temporal Walk-Forward CV (Quarterly Drift)**: Demonstrates stability across seasonal shifts with PR-AUC of **0.8465** and total out-of-time cost of **€132,300** (fold std €3,608).
   - **Spatial Gateway-Disjoint CV (Unseen Gateways)**: Evaluates generalization across 5 folds with 0% device overlap, achieving PR-AUC of **0.7658** and the lowest fold variance (€1,489) in the fleet.
4. **Empirical Innovation Testing**: Formally evaluated 5 modular intelligence innovations, adopting high-signal components and rejecting unsupervised novelty based on telemetry missingness forensics.

---

## 3. Champion Architecture (Candidate C3)

The production pipeline implements Candidate C3, combining 29 audited baseline features with 3 gateway-specific self-history baseline features, pure calibrated risk probabilities, and a 2-week post-visit cooldown:

```text
RAW TELEMETRY + GATEWAY MASTER METADATA
                  │
                  ▼
DATA QUALITY & LIFECYCLE FIREWALL
(Excludes 12 future mid-2026 installs & 12 decommissioned units; enforces t < Monday 00:00:00 UTC)
                  │
                  ▼
LEAKAGE-SAFE FEATURE MATRIX (32 Modeling Features)
├── 29 Audited Baseline Features (Availability, Stability, Radio, Static Context)
└── 3 Gateway-Specific Historical Baseline Features (28d History, 72h Cold-Start Guard)
    ├── feat_gw_relative_anomaly_score
    ├── feat_gw_z_offline
    └── feat_gw_z_missing
                  │
                  ▼
SUPERVISED RISK ESTIMATOR
(HistGradientBoostingClassifier, balanced weights, lr=0.05, max_depth=4, seed=42)
                  │
                  ▼
OPERATIONAL COOLDOWN POLICY
(Suppresses gateways visited within the prior 2 weeks to eliminate duplicate truck rolls)
                  │
                  ▼
DETERMINISTIC TOP-15 SELECTION
(Strict Lexicographical Ordering: -risk_score, gateway_id)
                  │
                  ▼
DIAGNOSTIC EXPLANATION GENERATOR
(Integrates Domain Failure Signatures SIG_01 to SIG_05; reasons strictly <= 300 characters)
                  │
                  ▼
predictions.csv (Exactly 120 rows, 8 weeks, 15 visits/week, ranks 1 to 15)
```

### The 5 Modular Innovations Evaluated:

1. **Innovation 1: Failure Progression / Deterioration Score**
   - *Status*: **PROMOTED AS ANALYTICAL MONITOR & EXPLANATION FEATURE**.
   - Compares trailing 7d telemetry against prior 21d baseline. Reduces temporal fold cost variance by 60%.
2. **Innovation 2: Operational Failure Signatures**
   - *Status*: **PROMOTED AS PRIMARY EXPLANATION ENGINE**.
   - 5 domain-grounded diagnostic rules (`SIG_01`–`SIG_05`) exhibiting relative risk ratios of $9.4\times$ to $20.6\times$ for collection deficits, generating compliant ($\le 300$ chars) diagnostic reason tags.
3. **Innovation 3: Gateway-Specific Historical Baseline**
   - *Status*: **PROMOTED AS CORE CHAMPION FEATURE FAMILY**.
   - 28-day self-reference z-scores with 72h cold-start fallback. Drives the single largest saving: cuts 16-week cost to **€115,200** (-€13,200), boosting unseen-gateway PR-AUC from 0.6777 to **0.7658**.
4. **Innovation 4: Risk × Deterioration Priority Engine**
   - *Status*: **EVALUATED CANDIDATE; RETAINED AS ALTERNATIVE PRIORITY MODULE**.
   - Multiplicative, additive, Borda, and quadrant boost formulations evaluated. While Borda cut repeats from 52 to 50, priority rank adjustments altered probability calibration, incurring €2,400 higher penalty costs than pure C3 risk ranking (€117,600 vs €115,200).
5. **Innovation 5: Unsupervised Fleet Novelty / OOD Detector**
   - *Status*: **REJECTED FROM PRIMARY DISPATCH** (Retained strictly as Auxiliary Drift Auditor).
   - Forensics reveal Isolation Forest anomaly flags are driven by benign telemetry missingness and high-gain Yagi antennas, increasing 16-week cost by +€3,600.

---

## 4. Directory Layout

```text
project-root/
├── run.py                 # Universal single-command entrypoint for predictions.csv
├── run.sh                 # Unix shell wrapper for one-command execution
├── validate_submission.py # Official LPDG submission validator script
├── requirements.txt       # Minimal, verified production dependencies
├── predictions.csv        # Official 120-row competition submission artifact
├── DECISIONS.md           # Five official project decisions, alternatives, and trade-offs
├── AI-USAGE.md            # AI usage disclosure, error detection, and verification log
├── .gitignore             # Strict privacy firewall excluding challenge data and caches
├── docs/
│   ├── SCREEN_RECORDING_SCRIPT.md   # Official 7-minute visual & spoken cue sheet
│   ├── FINAL_SUBMISSION_CHECKLIST.md # Complete verification checklist
│   ├── 01_context/                  # Authoritative challenge briefs and FAQs
│   ├── 02_decisions/                # Project Decision Register (D-01 to D-28)
│   ├── 03_data/                     # Data audits and Feature Registry (Families 1 to 8)
│   ├── 04_ml/                       # Target definition, validation plan, model card
│   ├── 05_experiments/              # Full experiment ledger (E-01 through E-INNOV-06)
│   └── innovation/                  # Innovation Phase deep-dives (01 to 07, FINAL_AUDIT)
├── src/
│   ├── data/              # Ingestion, partition discovery, time grid, normalizer
│   ├── features/          # Feature builders, deterioration dynamics, gateway baselines
│   ├── intelligence/      # Failure signatures, priority engine, novelty detection
│   ├── models/            # Target definition, trainer, decision policy
│   ├── evaluation/        # Economic cost simulator, temporal and spatial splitters
│   ├── prediction/        # Production inference pipeline and diagnostic reason builder
│   └── utils/             # Paths, config, constants, and logging
└── tests/                 # 70 automated unit tests covering all components
```

---

## 5. Verification & Reproduction Instructions

### 1. One-Command Prediction Generation:
From the repository root, execute:
```bash
python run.py
```
*(Or on Unix/Linux: `./run.sh`)*  
*(Optional custom data directory: `python run.py --data /path/to/data`)*  
Generates the official `predictions.csv` deterministically with zero manual input, zero external internet dependencies, and zero runtime API keys.

### 2. Validate Official Submission Artifact:
Run the official challenge grader script:
```bash
python validate_submission.py predictions.csv
```
*Expected Output: `predictions.csv: OK (15 ranked gateways for each of 8 weeks, exit code 0)`.*

### 3. Run Automated Unit Test Suite:
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```
*Expected Output: 70 tests passed, 0 failures, 0 errors (100% GREEN).*

---

## 6. Documented Limitations ("What It Cannot Do")

1. **Sub-Weekly Transient Micro-Outages**: Telemetry is aggregated into trailing 7-day windows aligned with weekly Monday dispatch boundaries; transient mid-week micro-outages that recover before Sunday night are unobserved until the subsequent cycle.
2. **Static Cooldown Window**: The 2-week cooldown is uniform across all assets, regardless of repair complexity. An asset needing an antenna realignment is suppressed for the same 14-day duration as a full gateway replacement.
3. **Operational Proxy Limitation**: The model predicts smart meter collection deficits (<50%), which is an operational business proxy rather than direct physical hardware defect ground truth.

---

## 7. Screen Recording

- **Presentation Script**: Complete 7-minute cue sheet with timestamps and spoken text is documented in [`docs/SCREEN_RECORDING_SCRIPT.md`](docs/SCREEN_RECORDING_SCRIPT.md).
- **Recording Link**: `PENDING` *(To be recorded and uploaded by the candidate prior to the institutional deadline).*

---

## 8. AI Usage Disclosure

AI assistance was utilized as an interactive pair-programming and statistical scaffolding collaborator. All architectural decisions, leakage firewalls, and feature definitions were rigorously verified by the candidate. Complete disclosure and documentation of three concrete AI errors caught and corrected are in [`AI-USAGE.md`](AI-USAGE.md).
