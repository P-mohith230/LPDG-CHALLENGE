# Data Availability & Temporal Cutoff Reference
**LPDG Innovation Hub Selection Challenge 2026**  
*The Authoritative Master Anti-Data-Leakage Specification*

---

## 1. The Core Temporal Principle

The objective of the LPDG challenge is to simulate an operational deployment where a model makes ranked maintenance dispatch recommendations at the beginning of each week.

> [!IMPORTANT]
> **The Strict Historical Cutoff Rule**:  
> For any prediction week starting on Monday $T$ (e.g., `2026-02-09`), the decision pipeline may **ONLY** observe information that physically existed in the operational utility systems strictly before Monday 00:00:00 UTC.  
> Formally:
> $$\text{Data Available for Week } k = \{ d \in \mathcal{D} \mid \text{timestamp}(d) < T_k \}$$
> where $T_k = \text{Monday } 00:00:00\text{ UTC of week } k$.

Using data timestamped at or after $T_k$ to generate predictions for week $k$ constitutes **catastrophic temporal data leakage** and will result in disqualification or failure during the live evaluation session.

---

## 2. Legal Data Availability by Scoring Week

The evaluation scores predictions for exactly 8 consecutive calendar Mondays in February and March 2026. The table below establishes the legal boundary for each input file.

| Scored Week | Prediction Monday | Legitimate Telemetry Cutoff (`ts_utc`) | Legitimate `meter_read_success` Data | Legitimate `field_visits` Cutoff | Legitimate `engineer_review` Availability |
|---|---|---|---|---|---|
| **Week 1** | `2026-02-02` | `ts_utc < 2026-02-02 00:00:00Z` (1,073,239 rows) | `week_start <= 2026-01-26` (7,226 rows) | `requested_on < 2026-02-02` (642 work orders) | **STRICTLY UNAVAILABLE** (Created 2026-02-15) |
| **Week 2** | `2026-02-09` | `ts_utc < 2026-02-09 00:00:00Z` (1,115,327 rows) | `week_start <= 2026-01-26` (7,226 rows) | `requested_on < 2026-02-09` (642 work orders) | **STRICTLY UNAVAILABLE** (Created 2026-02-15) |
| **Week 3** | `2026-02-16` | `ts_utc < 2026-02-16 00:00:00Z` (1,157,681 rows) | `week_start <= 2026-01-26` (7,226 rows) | `requested_on < 2026-02-16` (642 work orders) | **AVAILABLE** (Snapshot dated 2026-02-15) |
| **Week 4** | `2026-02-23` | `ts_utc < 2026-02-23 00:00:00Z` (1,200,388 rows) | `week_start <= 2026-01-26` (7,226 rows) | `requested_on < 2026-02-23` (642 work orders) | Available (Snapshot dated 2026-02-15) |
| **Week 5** | `2026-03-02` | `ts_utc < 2026-03-02 00:00:00Z` (1,243,524 rows) | `week_start <= 2026-01-26` (7,226 rows) | `requested_on < 2026-03-02` (642 work orders) | Available (Snapshot dated 2026-02-15) |
| **Week 6** | `2026-03-09` | `ts_utc < 2026-03-09 00:00:00Z` (1,286,953 rows) | `week_start <= 2026-01-26` (7,226 rows) | `requested_on < 2026-03-09` (642 work orders) | Available (Snapshot dated 2026-02-15) |
| **Week 7** | `2026-03-16` | `ts_utc < 2026-03-16 00:00:00Z` (1,331,254 rows) | `week_start <= 2026-01-26` (7,226 rows) | `requested_on < 2026-03-16` (642 work orders) | Available (Snapshot dated 2026-02-15) |
| **Week 8** | `2026-03-23` | `ts_utc < 2026-03-23 00:00:00Z` (1,375,881 rows) | `week_start <= 2026-01-26` (7,226 rows) | `requested_on < 2026-03-23` (642 work orders) | Available (Snapshot dated 2026-02-15) |

---

## 3. Dataset-Specific Leakage Boundaries

### 3.1 Telemetry Partitions (`data/telemetry/month=YYYY-MM/`)
- The workspace includes partitions through March 2026 (`month=2026-03`) spanning to `2026-03-31 23:00:00Z`.
- **Enforcement Mechanism**:
  ```python
  # CORRECT:
  telemetry_window = full_telemetry[full_telemetry["ts_utc"] < monday_start_utc]
  
  # DISQUALIFYING BUG:
  # Computing global z-scores, rolling statistics, or min/max scalers across
  # the entire telemetry dataframe before slicing into weekly decision sets.
  ```
- **Timezone Boundary**: `ts_utc` is continuous UTC. `DateDt` and `hour` are local German time (`Europe/Berlin`), which shifts by $\pm 1$ hour during Daylight Saving Time (DST). To avoid fence-post errors, **always filter on `ts_utc`**.

### 3.2 Expert Review (`engineer_review_2026-02.xlsx`)
- **Inspection Fact**: The file contains a single inspection date: `2026-02-15` (Sunday before Week 3).
- **Leakage Hazard**: If used as a training label or feature input for Week 1 (`2026-02-02`) or Week 2 (`2026-02-09`), it introduces future expert hindsight that was not physically available on those dates.
- **Protocol**: If incorporated into modeling, it must be gated behind a temporal condition:
  $$\text{Use allowed if } T_k \ge \text{2026-02-16}$$

### 3.3 Meter Read Aggregates (`meter_read_success.csv`)
- **Inspection Fact**: Records terminate on `2026-01-26` (prior to Week 1).
- **Operational Reality**: Utility billing aggregates smart meter reads on a delayed weekly batch cycle. No contemporary meter read records exist during February or March 2026.
- **Rule**: Historical meter reading performance up to `2026-01-26` may be used as a static baseline property for all 8 weeks, but models cannot assume fresh meter read data arrives during the scored weeks.

### 3.4 Maintenance Work Orders (`field_visits.csv`)
- **Inspection Fact**: Contains work orders with `requested_on` up to `2026-01-30` and `visited_on` up to `2026-02-14`.
- **Leakage Hazard**: A work order requested on day $T$ only records its `outcome` and `parts_replaced` after the technician visit on $T + \Delta$.
- **Rule**: Information regarding field visit outcomes may only be referenced on dates strictly after `visited_on`.

### 3.5 Asset Register (`gateway_master.csv`)
- **Inspection Fact**: 11 gateways have `installed_on` dates in May–July 2026.
- **Rule**: Gateways with $\text{installed\_on} > T_k$ are not yet physically installed and must be masked out of candidate ranking pools for week $k$.
- Gateways with $\text{decommissioned\_on} < T_k$ must similarly be excluded from consideration.

---

## 4. Construction of Training Labels (FAQ Round 2 §4.5)

Round 2 FAQ §4.5 provides a vital clarification on future telemetry:
> *"Future historical telemetry may be used to engineer training labels for historical dates, provided target leakage into feature sets is strictly prevented."*

### How to Use Future Telemetry Legally:
When constructing training datasets from the historical period (e.g. August 2025 – January 2026):
1. Choose an arbitrary historical decision Monday $T_{\text{train}}$.
2. Compute feature matrix $X$ using telemetry strictly in $[T_{\text{train}} - 28\text{d}, T_{\text{train}})$.
3. Construct target label $Y$ using telemetry or outcomes in $[T_{\text{train}}, T_{\text{train}} + 7\text{d})$.
4. Ensure feature extraction logic has zero visibility into the label window $[T_{\text{train}}, T_{\text{train}} + 7\text{d})$.

### Disqualifying Label Construction Bugs:
- Leaking the future label $Y$ into feature transformations (e.g., target encoding without out-of-fold temporal cross-validation).
- Computing rolling statistics centered on $T$ (which peek into $T + 12\text{h}$).
- Using future March telemetry to adjust February predictions.

---

## 5. Temporal Leakage Verification Checklist

Before committing any model output or pipeline script, verify:
- [ ] Are all telemetry filters based strictly on `ts_utc < monday_start_utc`?
- [ ] Are rolling windows backward-looking only (e.g., `closed='left'` or strictly past timestamps)?
- [ ] Is `engineer_review_2026-02.xlsx` strictly masked out for Week 1 and Week 2?
- [ ] Are future uninstalled gateways ($\text{installed\_on} > T$) excluded from predictions?
- [ ] Are decommissioned gateways ($\text{decommissioned\_on} < T$) excluded from predictions?
- [ ] Does the feature pipeline execute identically when fed a single historical cutoff date in isolation?
