# AI Usage Disclosure & Verification Log
**Project**: LPDG Innovation Hub Selection Challenge 2026  
**Candidate Registration ID**: `23091a3286`  
**Tool Used**: Antigravity AI Pair Programming Assistant (Google DeepMind)

---

## 1. Scope of AI Assistance

AI assistance was utilized as an interactive pair-programming, statistical auditing, and scaffolding collaborator throughout the project lifecycle:

- **Exploratory Data Analysis & Telemetry Profiling**: Writing automated Python scripts to profile 57 telemetry columns, identify null distributions, quantify meter read ratios, and compute cross-correlation matrices.
- **Hypothesis Testing & Experiment Harnessing**: Structuring the empirical testing suite across Research Questions RQ-01 through RQ-14 and Innovation Experiments E-INNOV-01 through E-INNOV-06.
- **Mathematical Formulations**: Implementing the Borda count rank aggregation, bounded composite deterioration score ($D \in [0, 1]$), and vectorized 7-day vs 21-day rolling window aggregations.
- **Unit Test Generation**: Scaffolding comprehensive test suites (`tests/test_*.py`) ensuring 100% test pass rates and preventing regression bugs.

All architectural decisions, scientific target definitions, leakage firewalls, economic simulator parameters, and model validations were rigorously verified against physical domain constraints.

---

## 2. Concrete Errors Made by the AI and How They Were Caught & Corrected

During the development lifecycle, three critical errors made by the AI were identified, audited, and corrected:

### Error 1: Frozen Register Duplication on `offline_duration_sec`
- **What the AI Did**: The AI originally generated a naive feature summing `offline_duration_sec` across all telemetry packets in the trailing 7-day window (`sum(offline_duration_sec) / 3600.0`).
- **Consequence**: When inspecting model explanation strings and feature distributions, several gateways displayed impossible values such as `3,901.5h` of offline downtime in a 168-hour week!
- **How It Was Caught & Corrected**: 
  - Forensic analysis of raw telemetry for hanging gateways (`02C0F45F31E7`, `0AC437023B18`) revealed that `offline_duration_sec` in the firmware behaves as a frozen register snapshot of the last disconnection event. When a gateway hangs and repeatedly transmits buffered rows, the register value repeats identically across dozens of consecutive rows.
  - The calculation was corrected to take the **peak event duration** in the trailing week, bounded strictly by wall-clock time:
    $$\text{feat\_offline\_hours} = \min\left(168.0, \frac{\max(\text{offline\_duration\_sec})}{3600.0}\right)$$
  - This eliminated impossible explanation values and actually improved target correlation from 0.51 to 0.71.

### Error 2: English String Matching on German Site Categories
- **What the AI Did**: The AI wrote one-hot site classification logic using English string matching: `"Indoor" in site`, `"Outdoor" in site`, `"Pole" in site`, `"Rooftop" in site`.
- **Consequence**: Running feature distribution audits revealed that all 4 site indicator columns had min=0, max=0, mean=0 (100% constant zero variance across all 6,927 dataset rows).
- **How It Was Caught & Corrected**:
  - Direct inspection of `gateway_master.csv` revealed that site types are recorded in German (`Gebäude`, `Heizraum`, `Kellerraum`, `Außenmast`, `Schaltschrank`).
  - Corrected the mapping to parse the German domain terminology:
    - `Gebäude`, `Heizraum`, `Kellerraum` $\to$ `feat_site_Indoor` (70.5% fleet prevalence).
    - `Außenmast`, `Schaltschrank` $\to$ `feat_site_Outdoor` (29.5% fleet prevalence).
    - `Außenmast` $\to$ `feat_site_Pole` (16.0% fleet prevalence).

### Error 3: Row Counting vs Distinct Hour Counting in Telemetry Availability
- **What the AI Did**: The AI originally computed `feat_observed_hours` as `len(gw_telem)`, assuming exactly 1 row per hour.
- **Consequence**: `feat_observed_hours` reached 177.0 (>168.0 max possible in 7 days) because high-traffic gateways occasionally transmit multiple packet bursts within the same clock hour.
- **How It Was Caught & Corrected**:
  - Enforced distinct hourly floor bucketing (`min(168, len(set(timestamps)))`), restoring the exact mathematical physical conservation invariant:
    $$\text{feat\_observed\_hours} + \text{feat\_missing\_hours} = 168.0$$

---

## 3. Human Oversight & Architectural Governance
Every pull request, documentation update, and model candidate was subject to strict programmatic gates:
- Leakage firewall asserting $t < \text{Monday 00:00:00 UTC}$.
- Strict offline reproducibility with fixed random seed (42).
- Continuous unit test coverage across 70 unit tests.
