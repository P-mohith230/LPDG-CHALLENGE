# Complete Reproducibility & Execution Protocol
**LPDG Innovation Hub Selection Challenge 2026**  
*Clean-Machine Execution Runbook, Pinned Environment, Determinism Controls, and Verification Commands*

---

## 1. Master Reproducibility Contract

In accordance with FAQ Round 1 §1.4, FAQ Round 2 §2.3, §2.5, §7.1, and the official submission brief:
1. **Offline Execution**: The solution must execute completely offline with zero runtime internet access, API calls, or remote downloads.
2. **Single Command Execution**: Reviewers evaluate the submission using a single command:
   ```bash
   # Option A: Standard Shell
   ./run.sh --data ./data/
   
   # Option B: Make
   make run
   
   # Option C: Docker
   docker compose up
   ```
3. **Execution Budget**: Total pipeline execution on a standard laptop (4–8 CPU cores, 8–16 GB RAM, no GPU) must complete comfortably within the **5-minute reviewer evaluation window**.

---

## 2. Environment & Dependency Specifications

### 2.1 Pinned Runtime Environment
- **Operating System**: Platform independent (Tested on Windows 11 & Ubuntu 22.04 LTS).
- **Python Version**: `Python 3.13.5` (Compatible with Python $\ge 3.10$).
- **Virtual Environment**: Standard `venv` or `conda`.

### 2.2 Core Dependency Manifest (`requirements.txt`)
All dependencies are standard open-source numerical and machine learning packages with pinned semantic versions:

```text
numpy==2.2.3
pandas==2.2.3
pyarrow==19.0.1
scipy==1.15.2
scikit-learn==1.6.1
openpyxl==3.1.5
```

*Note: No proprietary packages, GPU drivers (CUDA), or specialized C++ extensions are required.*

---

## 3. Determinism & Random Seed Controls

To comply with FAQ Round 2 §3.6 (prohibiting random tie-breaking or non-deterministic rankings):
1. **Global Seed Enforcement**:
   - Python `random.seed(42)`
   - NumPy `np.random.seed(42)`
2. **Deterministic Tie-Breaking**:
   - Every ranking operation specifies a composite deterministic sort key:
     ```python
     # Deterministic tie-breaking on score, followed by gateway_id
     ranked = candidates.sort_values(
         by=["score", "gateway_id"], 
         ascending=[False, True]
     )
     ```
3. **Reproducibility Assertion**:
   - Re-running the pipeline on identical input data produces an identical SHA-256 hash for `predictions.csv`.

---

## 4. Clean-Machine Execution Procedure

Reviewers or evaluators setting up from a fresh machine should follow this exact sequence:

```bash
# Step 1: Clone the public GitHub repository
git clone https://github.com/<username>/<repo-name>.git
cd <repo-name>

# Step 2: Create and activate an isolated Python virtual environment
python -m venv .venv

# On Linux / macOS:
source .venv/bin/activate
# On Windows PowerShell:
.venv\Scripts\Activate.ps1

# Step 3: Install pinned dependencies (offline wheel cache or pre-installed environment)
pip install -r requirements.txt

# Step 4: Ensure dataset is available at ./data/ (or pass --data <path>)
# Note: Raw challenge data is NOT stored in git; place the 'data' directory in the project root.

# Step 5: Execute the end-to-end pipeline
python src/pipeline.py --data ./data/ --output predictions.csv

# Step 6: Validate output schema compliance
python validate_submission.py predictions.csv
```

---

## 5. Live Session Dynamic Mounting Protocol (FAQ Round 2 §7.1)

In the live evaluation session, reviewers will test the solution by mounting an unseen telemetry partition:
- **Partition Format**: `data/telemetry/month=YYYY-MM/` (e.g. `month=2026-04`).
- **Dynamic Partition Loading**:
  - The loader must discover partitions dynamically using globbing (`sorted(glob.glob("data/telemetry/month=*"))`).
  - Hard-coding 8 partitions or assuming March 2026 is the final month is strictly forbidden and will break during live testing.
- **Dynamic Fleet Handling**:
  - The pipeline gracefully handles gateways that cease reporting and new gateways that appear for the first time.

---

## 6. Expected Output Artifacts

Upon completion of execution, the pipeline guarantees the generation of:
1. `predictions.csv`: 120-row compliant submission file matching `validate_submission.py`.
2. `reports/metrics_summary.json`: Local execution summary, elapsed runtime, and cohort breakdown.
3. `reports/figures/`: Static visualization charts for the operations manager.
