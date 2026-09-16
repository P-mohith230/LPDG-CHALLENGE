# Master Data Audit Report
**LPDG Innovation Hub Selection Challenge 2026**  
*Quantitative Profile, Schema Verification, Integrity Checks, and Telemetry Forensics*

---

## 1. Executive Data Inventory

The official challenge package contains five primary tabular and telemetry data sources located under `03-challenge-data/data/`. All metrics and statistics below reflect exact counts extracted directly from the files in the workspace.

| Dataset Name | File Path | Format & Encoding | Primary Key / Grain | Row Count | Column Count | Unique Gateways | Date Horizon | Role in Challenge |
|---|---|---|---|---|---|---|---|---|
| **Asset Register** | `gateway_master.csv` | CSV (`latin1` / `cp1252`) | `gateway_id` | 332 | 11 | 332 | 2019-03-04 to 2026-07-14 | Static metadata: model, antenna, region, install date, installed meters. |
| **Field Visits** | `field_visits.csv` | CSV (`latin1` / `cp1252`) | Work Order (`visited_on`, `gateway_id`) | 642 | 8 | 247 | `requested_on`: 2025-02-03 to 2026-01-30; `visited_on`: 2025-02-05 to 2026-02-14 | Historical maintenance records; reasons, outcomes, replaced parts. |
| **Meter Reads** | `meter_read_success.csv` | CSV (`latin1` / `cp1252`) | `gateway_id` × `week_start` | 7,226 | 4 | 299 | 2025-08-04 to 2026-01-26 (26 weeks) | Operational performance: expected vs. read smart meter counts. Stops prior to Feb 2026. |
| **Engineer Review** | `engineer_review_2026-02.xlsx` | Excel (`.xlsx`) | `gateway_id` | 120 | 6 | 120 | 2026-02-15 (single snapshot) | Single-expert health classification: 60 Normal, 60 Schlecht. |
| **Hourly Telemetry** | `telemetry/month=YYYY-MM/` | Apache Parquet (8 partition dirs) | `gateway_id` × `ts_utc` | 1,433,387 | 57 | 320 | 2025-08-01 00:00:00Z to 2026-03-31 23:00:00Z | Continuous hourly sensor stream across radio, backhaul, OS, and hardware. |

*Note: `telemetry_sample_2025-08.csv` (181,484 rows, 57 columns) is a plain CSV export of the August 2025 partition provided for initial exploratory inspection.*

---

## 2. Dataset-by-Dataset Audit & Forensic Profile

### 2.1 `gateway_master.csv` (Asset Registry)
- **Dimensions**: 332 rows, 10 columns.
- **Primary Key Integrity**: `gateway_id` is 100% unique (332 distinct values).
- **Encoding & Parsing**: Encoded in `latin1` / `cp1252`. Contains German umlauts and special characters (`Gebäude`, `Außenmast`). Standard UTF-8 loaders throw decoding errors on byte `0xdf` (`ß`).
- **Identifier Format**: 100% of rows use 17-character colon-delimited uppercase hex (`^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$`, e.g., `02:14:06:F5:63:96`).
- **Column Attributes & Categorical Distributions**:
  - `tenant`: `tenant_a` (193, 58.1%), `tenant_b` (73, 22.0%), `tenant_c` (42, 12.7%), `tenant_d` (24, 7.2%).
  - `site_type`: `Gebäude` (151), `Heizraum` (61), `Außenmast` (53), `Schaltschrank` (45), `Kellerraum` (22).
  - `region`: `Bayern` (69), `Nordrhein-Westfalen` (64), `Baden-Württemberg` (62), `Hessen` (56), `Niedersachsen` (46), `Sachsen` (35).
  - `hw_model`: `GW-2100` (182), `GW-2100L` (101), `GW-3400` (48), `GW-8800X` (1 — rare outlier gateway).
  - `antenna_type`: `Omni 3dBi` (131), `Omni 5dBi` (107), `Panel 7dBi` (58), `Yagi 9dBi` (36).
  - `fw_version`: `3.2.0` (124), `2.15.1` (86), `3.3.1` (68), `2.14.3` (54).
  - `n_meters_installed`: Numeric integer, Range [40, 822], Median = 156, Mean = 189.0, Std = 118.3. Total fleet connected meters = 62,748.
- **Lifecycle Anomalies & Critical Edge Cases**:
  - `installed_on`: Range `2019-03-04` to `2026-07-14`.
    - **Future Installations**: 39 gateways have `installed_on > 2025-08-01`. Specifically, 11 gateways have installation dates in May, June, or July 2026 (after the entire Feb–Mar 2026 scoring period). These 11 gateways have zero telemetry rows and must never be recommended for visits.
  - `decommissioned_on`: 12 gateways were decommissioned between `2025-09-22` and `2026-02-25`. Exactly 320 gateways were active at the network start.
  - `fw_updated_on`: 53 gateways received firmware updates in November 2025 (`2025-11-03` to `2025-11-30`); remaining 279 gateways are blank (never updated).

### 2.2 `field_visits.csv` (Historical Maintenance Work Orders)
- **Dimensions**: 642 rows, 8 columns.
- **Coverage**: 215 unique gateways visited across 642 work orders.
- **Date Horizons**:
  - `requested_on`: `2025-02-03` to `2026-01-30` (all dispatches requested prior to the Feb 2026 scoring window).
  - `visited_on`: `2025-02-05` to `2026-02-14` (13 historical visits completed in early February 2026).
- **Reported Dispatch Reasons (`reason_reported`)**:
  - `Haeufige Neustarts` (Frequent reboots): 110 (17.1%)
  - `Kunde meldet Ausfall` (Customer reported outage): 101 (15.7%)
  - `Keine Verbindung` (No connection / backhaul drop): 100 (15.6%)
  - `Auffaellige Statistik` (Suspicious statistics): 87 (13.6%)
  - `Zaehler nicht gelesen` (Meters unread): 86 (13.4%)
  - `Signal schwach` (Weak RF signal): 79 (12.3%)
  - `Routinepruefung` (Routine inspection): 79 (12.3%)
- **Technician Field Outcomes (`outcome`) — Operational Grounding**:
  - `Kein Fehler gefunden`: **390 visits (60.7%)**.
    - *Significance*: 60.7% of historical field visits were recorded as 'Kein Fehler gefunden'; this is evidence of noisy/ambiguous operational labels, not a verified false-alarm rate.
  - `Fehler behoben` (Fault resolved / True positive): **223 visits (34.7%)**.
  - `Kein Zugang` (No site access): **29 visits (4.5%)**.
- **Hardware Interventions (`parts_replaced`)**:
  - None / No part replaced: 476 (74.1%)
  - `Netzteil` (Power supply unit): 39 (6.1%)
  - `Antenne` (External antenna): 37 (5.8%)
  - `Kabel` (RF/Power cabling): 35 (5.5%)
  - `Gateway getauscht` (Complete hardware replacement): 30 (4.7%)
  - `SIM-Karte` (Cellular SIM swapped): 25 (3.9%)
- **Labor Duration (`technician_hours`)**:
  - Range [0.5, 3.8] hours, Mean = 1.67 hours, Median = 1.55 hours.

### 2.3 `meter_read_success.csv` (Weekly Business Meter Reads)
- **Dimensions**: 7,226 rows, 4 columns.
- **Coverage**: 280 unique gateways over 26 consecutive weeks (`2025-08-04` to `2026-01-26`).
- **Critical Architectural Characteristic**:
  - **Complete absence of February and March 2026 data**.
  - This accurately models real-world utility billing: smart meter collection failures are lagging business indicators compiled weeks later. For decisions in Feb–Mar 2026, models cannot rely on contemporary meter read rates.
- **Reading Distribution [OBSERVED IN DATA]**:
  - `meters_expected`: Range [40, 822], Mean = 191.9, Median = 158. Matches `n_meters_installed`.
  - `meters_read`: Range [0, 822], Mean = 176.6, Median = 154.
  - `read_ratio` distribution: Mean = 84.7%, Median = 90.9%, Q05 = 38.6%, Q25 = 85.0%, Q75 = 94.6%.
  - **Zero-Read Failures (`meters_read == 0`)**: Exactly **2 gateway-weeks (0.03%)** (`02C0F45F31E7` on 2025-10-27 and `0A568E79FEF6` on 2025-11-10). Total zero-reads are extraordinarily rare, not 371 as prematurely claimed in pre-audit notes.
  - **Severe Collection Deficit (`read_ratio < 0.50`)**: **567 gateway-weeks (7.85%)**.
  - **Moderate Collection Deficit (`0.50 <= read_ratio < 0.80`)**: **703 gateway-weeks (9.73%)**.
  - **Normal Operation (`0.80 <= read_ratio < 1.00`)**: **5,874 gateway-weeks (81.29%)**.
  - **Full 100% Success (`meters_read == meters_expected`)**: **82 gateway-weeks (1.13%)**. (Almost all normal weeks miss a few meters due to wireless link margins).
  - **Data Integrity**: Zero instances of `meters_read > meters_expected`.

### 2.4 `engineer_review_2026-02.xlsx` (Expert Snapshot)
- **Dimensions**: 120 rows, 5 columns.
- **Observation Date**: Exactly one date: `2026-02-15` (evaluated by engineer `M. Hoffmann`).
- **Label Distribution (`Kategorie`)**:
  - Exactly **60 `Normal` (50.0%)** and **60 `Schlecht` (50.0%)**.
  - A perfectly balanced diagnostic sample across 120 distinct gateways.
- **Temporal Constraint**: Must NOT be utilized for Week 1 (`2026-02-02`) or Week 2 (`2026-02-09`) predictions.

---

## 3. Telemetry Partition Deep Forensics

The core telemetry dataset comprises **1,433,387 rows** across 8 monthly Parquet partitions.

### 3.1 Monthly Partition Forensics Table

| Partition Month | Parquet File Count | Row Count | Gateways Active | UTC Range Start | UTC Range End | Hours per Gateway (Min / Med / Max) | Theoretical Expected Hours |
|---|---|---|---|---|---|---|---|
| `month=2025-08` | 1 | 181,484 | 280 | 2025-08-01 00:00:00Z | 2025-08-31 23:00:00Z | 130 / 689 / 731 | 744 (31 d × 24 h) |
| `month=2025-09` | 1 | 177,308 | 280 | 2025-09-01 00:00:00Z | 2025-09-30 23:00:00Z | 97 / 672 / 724 | 720 (30 d × 24 h) |
| `month=2025-10` | 1 | 178,698 | 279 | 2025-10-01 00:00:00Z | 2025-10-31 23:00:00Z | 44 / 686 / 735 | 744 (31 d × 24 h) |
| `month=2025-11` | 1 | 172,421 | 276 | 2025-11-01 00:00:00Z | 2025-11-30 23:00:00Z | 194 / 673.5 / 722 | 720 (30 d × 24 h) |
| `month=2025-12` | 1 | 175,850 | 274 | 2025-12-01 00:00:00Z | 2025-12-31 23:00:00Z | 178 / 683 / 734 | 744 (31 d × 24 h) |
| `month=2026-01` | 1 | 181,470 | 288 | 2026-01-01 00:00:00Z | 2026-01-31 23:00:00Z | 17 / 691 / 746 | 744 (31 d × 24 h) |
| `month=2026-02` | 1 | 170,151 | 302 | 2026-02-01 00:00:00Z | 2026-02-28 23:00:00Z | 22 / 619 / 661 | 672 (28 d × 24 h) |
| `month=2026-03` | 1 | 196,005 | 308 | 2026-03-01 00:00:00Z | 2026-03-31 23:00:00Z | 158 / 687 / 733 | 744 (31 d × 24 h) |
| **Total** | **8 Partitions** | **1,433,387** | **320 Unique** | **2025-08-01 00:00:00Z** | **2026-03-31 23:00:00Z** | — | **5,832 Total Hours** |

### 3.2 Key Telemetry Observations
1. **Fleet Population Evolution**:
   - Initial active fleet: 280 gateways (August–September 2025).
   - Decommissioning dip: Reaches 274 gateways in December 2025 as failing units are retired.
   - Expansion wave: In January–March 2026, newly installed gateways begin broadcasting, expanding active units to 308 in March 2026.
   - Across the full 8 months, exactly **320 unique gateway IDs** broadcast telemetry.
2. **Duplicate Check**:
   - Exactly **0 duplicate rows** on `(gateway_id, ts_utc)` across all 1,433,387 records. The composite temporal key is completely clean.
3. **Missing Telemetry Representation**:
   - Hours where a gateway is powered off or disconnected do **NOT** generate zero-filled records; they are completely omitted from the Parquet files.
   - A normal gateway records ~672–691 hours per month (approx. 92–95% duty cycle). Severely degraded gateways record as few as 17 hours in a month.
4. **Telemetry Silence Dynamics [OBSERVED IN DATA — Exp E-01]**:
   - 1–3 hour silence spells are pervasive reporting jitter, accounting for **81.62% of all gateway-weeks**. In this baseline state, severe collection deficits occur in only **1.27%** of weeks.
   - Prolonged silence streaks $\ge 12\text{h}$ mark an operational inflection point where severe deficit probability rises to **54.97%** (and **77.50%** for $\ge 24\text{h}$).
   - `tail_silence` immediately preceding the weekly Monday 00:00 UTC decision boundary shows a strong historical association with next-week severe collection deficits: gateways silent for $\ge 24\text{h}$ at Sunday 23:00 UTC historically exhibited a **94.44% probability of severe collection deficit in the subsequent week**.
   - Telemetry silence (missing rows) and backhaul downtime (`offline_duration_sec`) share only 37% common variance ($r = +0.6116$), capturing complementary modes of degradation (power cut/total blackout vs. online backhaul disconnection).

---

## 4. Telemetry Signals & Feature Group Forensics

The telemetry schema includes 57 columns grouped into 6 functional operational domains:

### 4.1 Zero-Variance Schema Artifacts
The following 7 cellular operator columns are **100.0% ZERO** across every single row in the dataset:
- `operator_3AT == 0`
- `operator_A1 == 0`
- `operator_Eplus == 0`
- `operator_OrangeLU == 0`
- `operator_Salt == 0`
- `operator_Swisscom == 0`
- `operator_TmobileA == 0`
*Impact*: These represent unpopulated roaming provider templates for Austria and Switzerland and must be dropped from all feature pipelines.

### 4.2 LoRa Radio & RF Traffic (`rx_*`, `tx_*`)
- `rx_nr_pkts`: Total received LoRa packets. Mean = 285.86, Median = 30, Range [6, 140,852].
  - **Confounding by Antenna Gain [OBSERVED IN DATA — Exp E-05]**: Raw packet counts vary by ~85× depending on antenna type. Gateways with `Yagi 9dBi` directional antennas average 389,623 received packets per week, compared to 4,694 for `Omni 3dBi`, demonstrating strong antenna/site confounding. The underlying physical cause of this packet-volume difference is not established here. Raw packet counts have near-zero correlation with failure ($r = -0.0086$).
- `rx_crc_bad`: Corrupted CRC packets. Mean = 285.57, Median = 30, Range [5, 147,366].
  - **CRC Error Saturation [OBSERVED IN DATA — Exp E-05]**: Correlation between `rx_nr_pkts` and `rx_crc_bad` is exactly $1.0000$. The CRC error ratio is universally saturated at ~0.9996 to 1.0008 across all antenna types, healthy and degraded gateways alike. The correlation between `crc_ratio` and meter-read deficit is $-0.0335$ (no predictive signal). CRC error measurements are widespread and strongly coupled to total packet volume. Their exact physical cause is not established by this analysis; therefore CRC ratio is rejected as a standalone failure indicator.
- `tx_success`: Downlink transmission successes. Mean = 0.47, Median = 0, Range [0, 200]. 89.5% of hours are 0.
  - **Operational Signal [OBSERVED IN DATA — Exp E-05]**: Positively correlates with read ratio ($r = +0.2031$) and negatively with severe deficit ($r = -0.1699$).
- `tx_busy` & `tx_override`: Radio transmitter contention indicators.

### 4.3 Hardware & Operating System Health
- `avg_idletime`: Mean OS idle time.
- `avg_load1`: 1-minute load average. Mean = 0.69, Median = 0.44, Max = 202.0. Spikes $> 2.0$ indicate severe process thrashing.
- `load1_bigger1` & `load1_bigger2`: Counts of sampling checks breaching load 1.0 and 2.0.
- `avg_memfree`: Free RAM (bytes/KB). Range [29,459, 114,706], Mean = 64,030. Rapid collapse below 35,000 indicates memory leaks.
- `avg_uptime`: Firmware uptime counter. *Quirk*: Reaches values up to $1.5 \times 10^9$ due to 32-bit counter roll/representation. Sudden downward discontinuities denote unlogged reboots.

### 4.4 Reboots & Restart Attribution
- `reboot_cnt`: Total reboots in the hour. Mean = 0.041, Median = 0, Max = 32. Normal hours have 0 reboots (98.4%).
- `reboot_duration_sec`: Seconds spent rebooting during the hour.
- `r_cnt_power_cycle` & `r_dur_power_cycle`: Electrical power cuts.
- `r_cnt_reboot` & `r_dur_reboot`: Software/watchdog-triggered reboots.
- `r_cnt_unknown` & `r_dur_unknown`: Unattributed reboot events.
- **Attribution vs Field Outcomes [OBSERVED IN DATA — Exp E-04]**:
  - Trailing 7-day reboots before field visits are $5.41\times$ higher for confirmed repairs (`Fehler behoben`, mean = 43.39) than no-fault visits (`Kein Fehler gefunden`, mean = 8.02).
  - Power-cycle reboots are elevated by $13.44\times$ (mean 20.68 vs 1.54).
  - However, 70.18% of repaired visits had $\le 10$ reboots, and 11.11% of no-fault visits had $>10$ reboots. 60.7% of evaluated field visits were recorded as `Kein Fehler gefunden`, demonstrating substantial outcome ambiguity/noise in the historical visit dataset. Field visits are treated as noisy operational proxies rather than ground truth [REASONABLE INFERENCE supported by observed overlap].
- `reboot_importance`: Internal severity weighting.

### 4.5 Backhaul & Cellular Connectivity
- `disconnection_cnt`: Backhaul dropouts. Mean = 0.78, Median = 0, Max = 55.
- `offline_duration_sec`: Seconds offline within the reporting session. Max = 726,642 seconds.
  - **Empirical Counter Semantics [OBSERVED IN DATA]**: `offline_duration_sec` behaves empirically as an interval/event-duration metric rather than a monotonic cumulative counter. Its exact firmware reporting semantics remain [AMBIGUOUS / NEEDS INVESTIGATION]. In 77.12% of rows, `offline_duration_sec == 0`. Correlation with `disconnection_cnt` is $0.5717$ (row) and $0.7133$ (weekly).
  - **Non-Linear Transfer Function [OBSERVED IN DATA — Exp E-03]**:
    - $<24\text{h}$ offline/week: Severe collection deficit rate is $<0.2\%$ (smart meters buffer reads).
    - $24\text{h}–72\text{h}$ offline/week: Inflection zone; severe deficit jumps to $7.56\%$.
    - $72\text{h}–168\text{h}$ offline/week: Severe deficit jumps to $30.23\%$.
    - $>168\text{h}$ offline/week: Operational collapse; severe deficit reaches $77.32\%$.
    - Correlation between weekly offline seconds and severe deficit is $+0.5741$. Naive differencing ($\Delta x$) must **NEVER** be applied.
- `online_duration_mins`: Minutes online in the hour.
- `no_conn_importance`: Severity score for disconnection events.
- Active cellular operators: `operator_TelekomDE`, `operator_VodafoneDE`, `operator_O2DE`, and `operator_unknown`.

### 4.6 Signal Quality Bins
- `rssi_good`, `rssi_normal`, `rssi_bad`: Received Signal Strength Indication distributions.
- `rscp_rsrp_good`, `rscp_rsrp_normal`, `rscp_rsrp_bad`: 3G/4G signal power distributions.
- `ecio_rsrq_good`, `ecio_rsrq_normal`, `ecio_rsrq_bad`: Signal quality / carrier-to-interference ratios.

---

## 5. Summary of Data Quality Hazards & Gotchas

1. **Latin1 / CP1252 Characters**: Reading CSV files with default UTF-8 crashes on German characters (`ä`, `ö`, `ü`, `ß`). Always pass `encoding="latin1"` or `cp1252`.
2. **ID Inconsistency**: `telemetry` and `meter_read_success.csv` use 12-character bare hex; `gateway_master.csv`, `field_visits.csv`, and `engineer_review` use 17-character colon-delimited hex. Models must maintain a two-way normalization function.
3. **Firmware Counter Semantics [OBSERVED IN DATA]**:
   - `avg_uptime`: Functions as a resetting uptime clock accumulating at 3,600 sec/hr during normal operations and dropping/resetting to ~300 sec upon reboots.
   - `offline_duration_sec`: `offline_duration_sec` behaves empirically as an interval/event-duration metric rather than a monotonic cumulative counter. Its exact firmware reporting semantics remain [AMBIGUOUS / NEEDS INVESTIGATION]. In 77.94% of rows, `offline_duration_sec == 0`, and whenever `disconnection_cnt == 0`, exactly 100.00% of rows have `offline_duration_sec == 0`. Do **NOT** apply differencing.
4. **Timezone Discrepancy**: `ts_utc` is continuous UTC; `DateDt` and `hour` are local German time (`Europe/Berlin`), which shifts during DST on 26 October 2025 and 29 March 2026. All cutoff filters must use `ts_utc`.
5. **Future Uncommissioned Gateways**: Exactly **12 gateways** in `gateway_master.csv` have installation dates in mid-2026 (`installed_on >= 2026-05-07`) and 0 telemetry rows. Recommending them is an immediate €380 waste.
