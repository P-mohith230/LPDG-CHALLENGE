# Comprehensive Data Audit & Telemetry Forensics
**LPDG Innovation Hub Selection Challenge 2026**  
*Quantitative Profile, Schema Analysis, and Telemetry Partition Forensics*

---

## Section 1: Overview of All Workspace Datasets (Phase 3)

| Dataset | Format / Encoding | Grain | Row Count | Column Count | Unique Gateways | Date Horizon | Primary Purpose / Role |
|---|---|---|---|---|---|---|---|
| `gateway_master.csv` | CSV (`latin1`) | Gateway | 332 | 10 | 332 | 2019-03-04 to 2026-07-14 | Asset registry, hardware models, antennas, installed meters |
| `field_visits.csv` | CSV (`latin1`) | Work order | 642 | 8 | 215 | 2025-02-03 to 2026-02-14 | Historical maintenance logs, fault outcomes, replaced parts |
| `meter_read_success.csv` | CSV (`latin1`) | Gateway × Week | 7,226 | 4 | 280 | 2025-08-04 to 2026-01-26 | Business performance: expected vs actual meter reads (stops before Feb 2026) |
| `engineer_review_2026-02.xlsx` | Excel (`.xlsx`) | Gateway | 120 | 5 | 120 | 2026-02-15 (single day) | Single-expert health evaluation (60 Normal, 60 Schlecht) |
| `telemetry_sample_2025-08.csv` | CSV (`latin1`) | Gateway × Hour | 181,484 | 57 | 280 | 2025-08-01 to 2025-08-31 | Plain CSV export of August 2025 telemetry for inspection |
| `telemetry/month=YYYY-MM/` | Parquet (8 parts) | Gateway × Hour | 1,433,387 | 57 | 321 | 2025-08-01 to 2026-03-31 | Full hourly operational telemetry stream across 8 months |

---

## Section 2: Individual Dataset Profiles

### 1. `gateway_master.csv` (Asset Registry)
- **Rows**: 332 | **Columns**: 10 | **Unique Gateways**: 332 (Primary Key is unique).
- **Encoding Quirk**: Encoded in `latin1`/`cp1252` containing German characters (e.g. `Gebäude`, `Außenmast`). Standard UTF-8 parsing fails on byte `0xdf` (`ß`).
- **Gateway Identifier Formats**:
  - 100% of rows in `gateway_master.csv` use colon-delimited MAC format: `^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$` (e.g. `02:14:06:F5:63:96`).
  - No bare hex IDs present in this master file.
- **Attributes & Categorical Distributions**:
  - `tenant`: `tenant_a` (193, 58.1%), `tenant_b` (73, 22.0%), `tenant_c` (42, 12.7%), `tenant_d` (24, 7.2%).
  - `site_type`: `Gebäude` (Building, 151), `Heizraum` (Boiler room, 61), `Außenmast` (Outdoor mast, 53), `Schaltschrank` (Control cabinet, 45), `Kellerraum` (Basement, 22).
  - `region`: `Bayern` (69), `Nordrhein-Westfalen` (64), `Baden-Württemberg` (62), `Hessen` (56), `Niedersachsen` (46), `Sachsen` (35).
  - `hw_model`: `GW-2100` (182), `GW-2100L` (101), `GW-3400` (48), `GW-8800X` (1 — rare outlier unit).
  - `antenna_type`: `Omni 3dBi` (131), `Omni 5dBi` (107), `Panel 7dBi` (58), `Yagi 9dBi` (36).
  - `fw_version`: `3.2.0` (124), `2.15.1` (86), `3.3.1` (68), `2.14.3` (54).
  - `n_meters_installed`: Range [40, 822], Median = 156, Mean = 189.0, Std = 118.3. Total connected meters = 62,748.
- **Critical Lifecycle Dates & Anomalies**:
  - `installed_on`: Range `2019-03-04` to `2026-07-14`.
    - **Anomaly / Future Dates**: 39 gateways have `installed_on` dates after `2025-08-01`. 12 gateways have installation dates in mid-2026 (e.g. May, June, July 2026).
  - `decommissioned_on`: 12 gateways are decommissioned between `2025-09-22` and `2026-02-25` (320 gateways remain active at start).
  - `fw_updated_on`: 53 gateways had firmware updates in November 2025 (`2025-11-03` to `2025-11-30`); remaining 279 are blank (never updated).

### 2. `field_visits.csv` (Historical Maintenance Work Orders)
- **Rows**: 642 | **Columns**: 8 | **Unique Work Orders**: 642 | **Unique Gateways**: 215.
- **Date Horizons**:
  - `requested_on`: `2025-02-03` to `2026-01-30` (All work orders requested prior to scoring window).
  - `visited_on`: `2025-02-05` to `2026-02-14` (13 visits completed during the first two weeks of February 2026).
- **Reported Reasons (`reason_reported`)**:
  - `Haeufige Neustarts` (Frequent reboots): 110 (17.1%)
  - `Kunde meldet Ausfall` (Customer reported failure): 101 (15.7%)
  - `Keine Verbindung` (No connection): 100 (15.6%)
  - `Auffaellige Statistik` (Suspicious statistics): 87 (13.6%)
  - `Zaehler nicht gelesen` (Meters not read): 86 (13.4%)
  - `Signal schwach` (Weak signal): 79 (12.3%)
  - `Routinepruefung` (Routine check): 79 (12.3%)
- **Technician Outcomes (`outcome`) — Operational Reality**:
  - `Kein Fehler gefunden` (No fault found / False alarm): **390 visits (60.7%)** — Direct empirical validation of the €380 wasted dispatch problem!
  - `Fehler behoben` (Fault resolved): **223 visits (34.7%)**.
  - `Kein Zugang` (No site access): **29 visits (4.5%)**.
- **Parts Replaced (`parts_replaced`)**:
  - None / No part replaced: 476 (74.1%)
  - `Netzteil` (Power supply unit): 39 (6.1%)
  - `Antenne` (Antenna): 37 (5.8%)
  - `Kabel` (Cabling): 35 (5.5%)
  - `Gateway getauscht` (Complete gateway swapped): 30 (4.7%)
  - `SIM-Karte` (Cellular SIM): 25 (3.9%)
- **Technician Hours (`technician_hours`)**:
  - Range [0.5, 3.8] hours, Mean = 1.67 hours, Median = 1.55 hours.

### 3. `meter_read_success.csv` (Weekly Business Meter Reads)
- **Rows**: 7,226 | **Columns**: 4 | **Unique Gateways**: 280.
- **Reporting Horizon**: 26 consecutive weeks, from `2025-08-04` to `2026-01-26`.
- **CRITICAL TEMPORAL STRUCTURAL FINDING**:
  - `meter_read_success.csv` contains zero records for February and March 2026 (the scoring period `2026-02-02` to `2026-03-23`).
  - This is intentional: during live deployment, meter reading failures are a lagging metric discovered weeks after gateway degradation. Candidates cannot use future meter read success during the scoring window.
- **Reading Distribution**:
  - `meters_expected`: Range [40, 822], Mean = 191.9, Median = 158.
  - `meters_read`: Range [0, 822], Mean = 176.6, Median = 154.
  - **Zero Read Events (`meters_read == 0`)**: 371 gateway-weeks (5.14%) — Complete gateway blackouts.
  - **Partial Reads (`0 < meters_read < expected`)**: 1,228 gateway-weeks (16.99%) — Degraded RF reception or intermittent backhaul.
  - **Perfect Reads (`meters_read == expected`)**: 5,627 gateway-weeks (77.87%).
  - **Impossible Reads (`meters_read > expected`)**: 0 (Clean data integrity).

### 4. `engineer_review_2026-02.xlsx` (Expert Assessment Snapshot)
- **Rows**: 120 | **Columns**: 5 | **Unique Gateways**: 120.
- **Review Date**: Exactly one calendar date: `2026-02-15` (Sunday before Week 3 scoring Monday `2026-02-16`).
- **Reviewer**: Single expert engineer: `M. Hoffmann`.
- **Label Distribution (`Kategorie`)**:
  - Exactly **60 `Normal` (50.0%)** and **60 `Schlecht` (50.0%)**.
  - Perfectly balanced synthetic validation set.
- **Free-Text Engineering Notes (`Bemerkung`)**:
  - 37 non-null notes, e.g., `"haeufige Ausfaelle, Standort pruefen"`, `"nach Tausch stabil"`, `"Hardware vermutlich defekt"`, `"wiederholt neu gestartet"`.

---

## Section 3: Telemetry Partition Deep Forensics (Phase 4)

### Partition Summary Table

| Partition Month | Parquet Rows | Gateways Present | UTC Date Range | Local Date Range (`DateDt`) | Hours per Gateway (Min / Med / Max) | Theoretical Expected Hours |
|---|---|---|---|---|---|---|
| `month=2025-08` | 181,484 | 280 | 2025-08-01 00:00 to 2025-08-31 23:00 | 2025-08-01 to 2025-09-01 | 130 / 689 / 731 | 744 (31 d × 24 h) |
| `month=2025-09` | 177,308 | 280 | 2025-09-01 00:00 to 2025-09-30 23:00 | 2025-09-01 to 2025-10-01 | 97 / 672 / 724 | 720 (30 d × 24 h) |
| `month=2025-10` | 178,698 | 279 | 2025-10-01 00:00 to 2025-10-31 23:00 | 2025-10-01 to 2025-11-01 | 44 / 686 / 735 | 744 (31 d × 24 h) |
| `month=2025-11` | 172,421 | 276 | 2025-11-01 00:00 to 2025-11-30 23:00 | 2025-11-01 to 2025-12-01 | 194 / 673.5 / 722 | 720 (30 d × 24 h) |
| `month=2025-12` | 175,850 | 274 | 2025-12-01 00:00 to 2025-12-31 23:00 | 2025-12-01 to 2026-01-01 | 178 / 683 / 734 | 744 (31 d × 24 h) |
| `month=2026-01` | 181,470 | 288 | 2026-01-01 00:00 to 2026-01-31 23:00 | 2026-01-01 to 2026-02-01 | 17 / 691 / 746 | 744 (31 d × 24 h) |
| `month=2026-02` | 170,151 | 302 | 2026-02-01 00:00 to 2026-02-28 23:00 | 2026-02-01 to 2026-03-01 | 22 / 619 / 661 | 672 (28 d × 24 h) |
| `month=2026-03` | 196,005 | 308 | 2026-03-01 00:00 to 2026-03-31 23:00 | 2026-03-01 to 2026-04-01 | 158 / 687 / 733 | 744 (31 d × 24 h) |
| **Total** | **1,433,387** | **321 Unique** | **2025-08-01 to 2026-03-31** | **2025-08-01 to 2026-04-01** | — | **5,832 h** |

### Telemetry Forensic Findings:
1. **Gateway Churn & Expansion**:
   - The network starts with 280 active reporting gateways in August 2025.
   - It dips to 274 in December 2025 (due to decommissioning of faulty gateways).
   - In January–March 2026, newly commissioned gateways join the network, bringing the active count to 308 in March 2026. Across the entire 8 months, exactly 321 distinct gateway IDs appear in telemetry.
2. **Missing Hourly Records**:
   - Median monthly hours per gateway is ~672–691 hours (representing ~92–95% uptime).
   - Minimum hours for some failing or newly added gateways is as low as 17 hours in a month.
   - When a gateway is offline or power-cycled for a full hour, no record is generated, resulting in timestamp gaps.
3. **Duplicate Check**:
   - `(gateway_id, ts_utc)` pairs have **0 duplicates** across all 1.43M rows. Primary grain key is clean.
4. **Timezone & Daylight Saving Time (DST) Forensics**:
   - `ts_utc` is continuous ISO-8859 UTC without gaps or jumps.
   - `DateDt` and `hour` are in local German time (`Europe/Berlin`).
   - On the final day of each UTC month, the last 1–2 hours (22:00 and 23:00 UTC) roll into `00:00` and `01:00` of the 1st of the next month in `DateDt` (UTC+1 / UTC+2).
   - **DST Transitions**:
     - October 26, 2025 (CEST -> CET, UTC+2 to UTC+1): Local clock falls back.
     - March 29, 2026 (CET -> CEST, UTC+1 to UTC+2): Local clock springs forward.
   - **Recommendation**: Always filter and join on `ts_utc` (or convert `ts_utc` to UTC timestamp) to prevent timezone boundary bugs.

---

## Section 4: Telemetry Feature Group Forensic Analysis

### 1. Network & RF Traffic (`rx_*`, `tx_*`)
- `rx_nr_pkts` (Packets received): Mean = 285.86, Median = 30, Range [6, 140,852].
- `rx_crc_bad` (Bad CRC packets): Mean = 285.57, Median = 30, Range [5, 147,366].
  - **Observation**: Over 99% of raw received RF bursts fail CRC checks across the network, reflecting high RF background noise. A sudden spike in `rx_crc_bad` relative to `rx_nr_pkts` indicates localized RF interference.
- `tx_success` (Downlink successes): Mean = 0.47, Median = 0, Range [0, 200]. 89.5% of hourly records are 0.
- `tx_busy` & `tx_override`: Capture radio channel collisions when the transmitter is occupied.

### 2. System Health & Operating Metrics
- `avg_idletime`: Mean CPU idle time.
- `avg_load1`: Mean 1-min load average. Mean = 0.69, Median = 0.44, Max = 202.0. Severe load spikes (> 2.0) correlate with process contention and memory thrashing.
- `load1_bigger1` & `load1_bigger2`: Count of sampling points within the hour exceeding load thresholds 1.0 and 2.0.
- `avg_memfree`: Mean free RAM. Range [29,459, 114,706], Mean = 64,030. Drop in free memory below 35,000 indicates memory leaks preceding crashes.
- `avg_uptime`: Counter tracking firmware uptime. Note: Values range up to 1.5×10^9 due to 32-bit counter roll/firmware representation. Sudden drops in `avg_uptime` confirm unlogged gateway reboots.

### 3. Reboots & Restarts
- `reboot_cnt`: Hourly reboot counter. Mean = 0.041, Median = 0, Max = 32. 98.4% of normal operating hours have 0 reboots.
- `reboot_duration_sec`: Time spent in reboot sequence during the hour (seconds).
- Reboot attribution breakdown:
  - `r_cnt_power_cycle` & `r_dur_power_cycle`: Hard electrical power cuts.
  - `r_cnt_reboot` & `r_dur_reboot`: Software-initiated restarts (watchdog or crash).
  - `r_cnt_unknown` & `r_dur_unknown`: Unclassified reboot causes.
- `reboot_importance`: Proprietary severity score assigned by firmware/monitoring.

### 4. Backhaul Connectivity
- `disconnection_cnt`: Backhaul dropouts during the hour. Mean = 0.78, Median = 0, Max = 55.
- `offline_duration_sec`: Total offline time. Max = 726,642 seconds (~201 hours).
  - **Firmware Accumulator Quirk**: The data dictionary confirms `offline_duration_sec` is an unreset cumulative firmware counter on certain versions rather than an hourly bounded 0–3600 second sum.
- `online_duration_mins`: Minutes online during the hour.
- `no_conn_importance`: Severity score for backhaul disconnection events.

### 5. Cellular Technology & Operators
- `network_2g`, `network_3g`, `network_4g`, `network_unknown`: Reading counts on each radio technology.
- **Operator Columns — Zero-Variance Finding**:
  - The following 7 operator columns are **100% ZERO** across all 1.43M rows:
    - `operator_3AT == 0`
    - `operator_A1 == 0`
    - `operator_Eplus == 0`
    - `operator_OrangeLU == 0`
    - `operator_Salt == 0`
    - `operator_Swisscom == 0`
    - `operator_TmobileA == 0`
  - Active cellular providers in the data: `operator_TelekomDE`, `operator_VodafoneDE`, `operator_O2DE`, and `operator_unknown`.
  - Non-German / Austrian / Swiss roaming columns are unpopulated schema placeholders.

### 6. Signal Quality Indicators
- `rssi_good`, `rssi_normal`, `rssi_bad`: Distribution of Received Signal Strength Indication across good/normal/bad bins.
- `rscp_rsrp_good`, `rscp_rsrp_normal`, `rscp_rsrp_bad`: 3G RSCP / 4G RSRP signal power quality bins.
- `ecio_rsrq_good`, `ecio_rsrq_normal`, `ecio_rsrq_bad`: Signal-to-interference ratio bins.
