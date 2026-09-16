# Project Feature Registry
**LPDG Innovation Hub Selection Challenge 2026**  
*The Authoritative Engineered Feature Catalog, Family Groupings, Lineage Tracking, and Leakage Firewall*

---

## 1. Governance & Master Status

> [!NOTE]
> **Feature Matrix Status**: **STAGES 4–9 AUDITED, CORRECTED & REVALIDATED**  
> All 31 engineered features are constructed strictly backward-looking ($t < T = \text{Monday 00:00:00 UTC}$) with programmatic leakage verification via [`validate_target_leakage_firewall`](file:///m:/LPDGE/src/models/target.py).  
> Code implementation: [`src/features/builder.py`](file:///m:/LPDGE/src/features/builder.py).  
> Unit tests: [`tests/test_stage5.py`](file:///m:/LPDGE/tests/test_stage5.py) (8/8 passing).

---

## 2. Audited Engineered Feature Catalog (All 31 Features)

Features are cataloged across 4 operational domain families as defined by `get_feature_family_columns()` in [`src/features/builder.py`](file:///m:/LPDGE/src/features/builder.py):

### Family 1: Availability & Silence (`availability`, 10 Features)
| Feature Name | Raw Source | Math Definition | Window | Expected Range | Observed Range | Missing Handling | Leakage Risk | Status |
|---|---|---|---|---|---|---|---|---|
| `feat_observed_hours` | `ts_utc` (distinct) | $\min(168, \|\text{unique hourly buckets}\|)$ | Trailing 7d | $[0, 168]$ | $[0, 168]$ | 0 on silence | None ($t < T$) | **AUDITED & BOUNDED** |
| `feat_missing_hours` | `ts_utc` (grid) | $168 - \text{observed\_hours}$ | Trailing 7d | $[0, 168]$ | $[0, 168]$ | 168 on silence | None ($t < T$) | **AUDITED & BOUNDED** |
| `feat_missing_ratio` | Derived | $\text{missing\_hours} / 168.0$ | Trailing 7d | $[0.0, 1.0]$ | $[0.0, 1.0]$ | 1.0 on silence | None ($t < T$) | **AUDITED & BOUNDED** |
| `feat_max_silence_streak`| Telemetry grid | $\max(\text{consecutive missing hours})$ | Trailing 7d | $[0, 168]$ | $[0, 168]$ | 168 on silence | None ($t < T$) | **AUDITED & BOUNDED** |
| `feat_tail_silence` | Telemetry grid | Missing hours adjacent to cutoff $T$ | Trailing 7d | $[0, 168]$ | $[0, 168]$ | 168 on silence | None ($t < T$) | **AUDITED & BOUNDED** |
| `feat_silence_spell_count`| Telemetry grid | Count of contiguous silence spells | Trailing 7d | $[0, 84]$ | $[0, 51]$ | 1 on silence | None ($t < T$) | **AUDITED & BOUNDED** |
| `feat_sum_offline_sec` | `offline_duration_sec`| Peak event duration: $\min(604800, \max(\text{sec}))$ | Trailing 7d | $[0, 604800]$ | $[0, 604800]$ | 0 on silence | None ($t < T$) | **AUDITED & BOUNDED** |
| `feat_offline_hours` | `offline_duration_sec`| Peak event hours: $\min(168.0, \max(\text{sec})/3600)$ | Trailing 7d | $[0.0, 168.0]$ | $[0.0, 168.0]$ | 0 on silence | None ($t < T$) | **AUDITED & BOUNDED** |
| `feat_offline_ge_24h` | Derived | $\mathbb{I}(\text{offline\_hours} \ge 24.0)$ | Trailing 7d | $\{0, 1\}$ | $\{0, 1\}$ | 0 on silence | None ($t < T$) | **AUDITED & BOUNDED** |
| `feat_sum_disconnections`| `disconnection_cnt` | Peak disconnection count: $\max(\text{disconn})$ | Trailing 7d | $[0, 200]$ | $[0, 55]$ | 0 on silence | None ($t < T$) | **AUDITED & BOUNDED** |

### Family 2: Stability & Reboots (`stability`, 6 Features)
| Feature Name | Raw Source | Math Definition | Window | Expected Range | Observed Range | Missing Handling | Leakage Risk | Status |
|---|---|---|---|---|---|---|---|---|
| `feat_reboot_cnt_total` | `reboot_cnt` | $\sum \text{reboot\_cnt}$ | Trailing 7d | $[0, 5000]$ | $[0, 1907]$ | 0 on silence | None ($t < T$) | **AUDITED** |
| `feat_power_cycle_cnt` | `r_cnt_power_cycle` | $\sum r\_\text{cnt\_power\_cycle}$ | Trailing 7d | $[0, 5000]$ | $[0, 1701]$ | 0 on silence | None ($t < T$) | **AUDITED** |
| `feat_sw_reboot_cnt` | `r_cnt_reboot` | $\sum r\_\text{cnt\_reboot}$ | Trailing 7d | $[0, 1000]$ | $[0, 123]$ | 0 on silence | None ($t < T$) | **AUDITED** |
| `feat_unknown_reboot_cnt`| `r_cnt_unknown` | $\sum r\_\text{cnt\_unknown}$ | Trailing 7d | $[0, 1000]$ | $[0, 309]$ | 0 on silence | None ($t < T$) | **AUDITED** |
| `feat_max_reboot_1h` | `reboot_cnt` | $\max_h(\text{reboot\_cnt}_h)$ | Trailing 7d | $[0, 100]$ | $[0, 32]$ | 0 on silence | None ($t < T$) | **AUDITED** |
| `feat_power_cycle_recent_24h`| `r_cnt_power_cycle`| $\sum_{t \in [T-24\text{h}, T)} r\_\text{cnt\_power\_cycle}$ | Trailing 24h | $[0, 500]$ | $[0, 288]$ | 0 on silence | None ($t < T$) | **AUDITED** |

### Family 3: Radio & Operating System (`radio`, 4 Features)
| Feature Name | Raw Source | Math Definition | Window | Expected Range | Observed Range | Missing Handling | Leakage Risk | Status |
|---|---|---|---|---|---|---|---|---|
| `feat_mean_rssi_bad` | `rssi_bad` | $\text{mean}(\text{rssi\_bad})$ | Trailing 7d | $[0, 50]$ | $[0.0, 13.0]$ | 0.0 on silence | None ($t < T$) | **AUDITED** |
| `feat_tot_tx_success` | `tx_success` | $\sum \text{tx\_success}$ | Trailing 7d | $[0, 1000]$ | $[0, 453]$ | 0 on silence | None ($t < T$) | **AUDITED** |
| `feat_mean_load1` | `avg_load1` | $\text{mean}(\text{avg\_load1})$ | Trailing 7d | $[0.0, 20.0]$ | $[0.0, 5.60]$ | 0.0 on silence | None ($t < T$) | **AUDITED** |
| `feat_min_memfree` | `avg_memfree` | $\min(\text{avg\_memfree})$ (kB) | Trailing 7d | $[0, 120000]$ | $[0.0, 92945]$ | 0.0 on silence | None ($t < T$) | **AUDITED** |

### Family 4: Static Metadata & Context (`static`, 11 Features)
| Feature Name | Raw Source | Math Definition | Window | Expected Range | Observed Range | Missing Handling | Leakage Risk | Status |
|---|---|---|---|---|---|---|---|---|
| `feat_n_meters_installed` | `gateway_master.csv` | $N_{\text{meters}}$ from master | Static | $[40, 850]$ | $[40, 769]$ | Imputed (180) | None | **AUDITED** |
| `feat_installation_age_days`| `gateway_master.csv` | $(T - \text{installed\_on}).\text{days}$ | Static | $[0, 3000]$ | $[1, 2520]$ | Imputed (365) | None | **AUDITED** |
| `feat_antenna_Omni_3dBi` | `antenna_type` | One-hot indicator | Static | $\{0, 1\}$ | $\{0, 1\}$ | Default Omni 3dBi | None | **AUDITED** |
| `feat_antenna_Omni_5dBi` | `antenna_type` | One-hot indicator | Static | $\{0, 1\}$ | $\{0, 1\}$ | 0 | None | **AUDITED** |
| `feat_antenna_Panel_7dBi`| `antenna_type` | One-hot indicator | Static | $\{0, 1\}$ | $\{0, 1\}$ | 0 | None | **AUDITED** |
| `feat_antenna_Yagi_9dBi` | `antenna_type` | One-hot indicator | Static | $\{0, 1\}$ | $\{0, 1\}$ | 0 | None | **AUDITED** |
| `feat_site_Indoor` | `site_type` | German map: Gebäude/Heizraum/Keller | Static | $\{0, 1\}$ | $\{0, 1\}$ | 0 | None | **AUDITED & FIXED** |
| `feat_site_Outdoor` | `site_type` | German map: Außenmast/Schaltschrank | Static | $\{0, 1\}$ | $\{0, 1\}$ | 1 (Default) | None | **AUDITED & FIXED** |
| `feat_site_Pole` | `site_type` | German map: Außenmast | Static | $\{0, 1\}$ | $\{0, 1\}$ | 0 | None | **AUDITED & FIXED** |
| `feat_site_Rooftop` | `site_type` | German map: Dach / Rooftop | Static | $\{0, 1\}$ | $\{0\}$ | 0 | None | **AUDITED (0 in fleet)** |
| `feat_engineer_priority_score`| `engineer_review` | Review score (gated $\ge \text{2026-02-15}$) | External | $[0.0, 1.0]$ | $[0.0, 0.0]^*$ | 0.0 pre-release | Temporal Gated | **AUDITED (0.0 historical)** |

*\*Note: `feat_engineer_priority_score` is strictly 0.0 across all historical training decision boundaries prior to February 15, 2026 to prevent lookahead leakage.*

---

## 3. Physical Invariants & Integrity Laws Enforced

1. **Hourly Conservation Law**:
   $$\text{feat\_observed\_hours} + \text{feat\_missing\_hours} = 168$$
   Every single hour in the 7-day lookback window $[T - 168\text{h}, T)$ is strictly classified as either observed (telemetry packet received) or missing. Verified by regression test in `tests/test_stage5.py`.

2. **Physical Wall-Clock Bounding**:
   $$\text{feat\_offline\_hours} \le 168.0 \quad \text{and} \quad \text{feat\_sum\_offline\_sec} \le 604,800.0$$
   Eliminates impossible historical artifacts caused by frozen/retransmitted firmware registers.

3. **Strict Pre-Decision Temporal Boundary**:
   $$\text{observation\_cutoff\_utc} = T - 1\text{ second} < T$$
   Guaranteed by `validate_target_leakage_firewall`.

---

## 4. Candidate Innovation Feature Families (Innovations 1–5)

### Family 5: Failure Progression & Deterioration (`deterioration`, 12 Features)
*Source implementation*: [`src/features/deterioration.py`](file:///m:/LPDGE/src/features/deterioration.py)  
*Temporal window*: $[T - 7\text{d}, T)$ recent vs $[T - 28\text{d}, T - 7\text{d})$ historical baseline. Strictly $t < T$.

| Feature Name | Math Definition | Window | Expected Range | Missing / Cold-Start Handling | Leakage Risk | Status |
|---|---|---|---|---|---|---|
| `feat_det_has_history` | $\mathbb{I}(\text{prior observations} \ge 72\text{h})$ | Prior 21d | $\{0, 1\}$ | 0 if new install | None ($t < T$) | **TESTED** |
| `feat_det_missing_hours_delta` | $\text{missing}_{\text{rec}} - \text{missing}_{\text{prior}}/3.0$ | 7d vs 21d | $[-168.0, 168.0]$ | 0.0 if no history | None ($t < T$) | **TESTED** |
| `feat_det_offline_hours_delta` | $\text{offline}_{\text{rec}} - \text{offline}_{\text{prior}}/3.0$ | 7d vs 21d | $[-168.0, 168.0]$ | 0.0 if no history | None ($t < T$) | **TESTED** |
| `feat_det_disconns_delta` | $\text{disconns}_{\text{rec}} - \text{disconns}_{\text{prior}}/3.0$ | 7d vs 21d | $[-100.0, 100.0]$ | 0.0 if no history | None ($t < T$) | **TESTED** |
| `feat_det_reboots_delta` | $\text{reboots}_{\text{rec}} - \text{reboots}_{\text{prior}}/3.0$ | 7d vs 21d | $[-1000.0, 1000.0]$ | 0.0 if no history | None ($t < T$) | **TESTED** |
| `feat_det_power_cycles_delta` | $\text{pcycle}_{\text{rec}} - \text{pcycle}_{\text{prior}}/3.0$ | 7d vs 21d | $[-1000.0, 1000.0]$ | 0.0 if no history | None ($t < T$) | **TESTED** |
| `feat_det_rssi_bad_delta` | $\text{rssi\_bad}_{\text{rec}} - \text{rssi\_bad}_{\text{prior}}$ | 7d vs 21d | $[-50.0, 50.0]$ | 0.0 if no history | None ($t < T$) | **TESTED** |
| `feat_det_load1_delta` | $\text{load1}_{\text{rec}} - \text{load1}_{\text{prior}}$ | 7d vs 21d | $[-10.0, 10.0]$ | 0.0 if no history | None ($t < T$) | **TESTED** |
| `feat_det_norm_missing_surge` | Normalized surge ratio | 7d vs 21d | $[0.0, 100.0]$ | 0.0 if no history | None ($t < T$) | **TESTED** |
| `feat_det_norm_offline_surge` | Normalized surge ratio | 7d vs 21d | $[0.0, 100.0]$ | 0.0 if no history | None ($t < T$) | **TESTED** |
| `feat_det_norm_reboot_surge` | Normalized surge ratio | 7d vs 21d | $[0.0, 100.0]$ | 0.0 if no history | None ($t < T$) | **TESTED** |
| `feat_deterioration_score` | Bounded composite score | 7d vs 21d | $[0.0, 1.0]$ | 0.0 if no history | None ($t < T$) | **TESTED & BOUNDED** |

### Family 6: Operational Failure Signatures (`signatures`, 7 Features)
*Source implementation*: [`src/intelligence/failure_signatures.py`](file:///m:/LPDGE/src/intelligence/failure_signatures.py)  
*Temporal window*: Trailing 7 days $[T - 7\text{d}, T)$. Strictly $t < T$.

| Feature Name | Signature Condition | Target Deficit Association | Expected Range | Leakage Risk | Status |
|---|---|---|---|---|---|
| `sig_01_connectivity_collapse` | Disconns $\ge 10 \land$ Offline $\ge 24\text{h} \land$ Missing $\ge 12\text{h}$ | High Relative Risk | $\{0, 1\}$ | None ($t < T$) | **TESTED** |
| `sig_02_hardware_power_cycle_surge` | Power cycles $\ge 2$ | 13.4x in repairs | $\{0, 1\}$ | None ($t < T$) | **TESTED** |
| `sig_03_persistent_silence_blackout`| Tail silence $\ge 24\text{h} \land$ Missing ratio $\ge 0.50$ | Severe deficit indicator | $\{0, 1\}$ | None ($t < T$) | **TESTED** |
| `sig_04_radio_downlink_degradation` | Bad RSSI $\ge 2.0 \land$ Load1 $\ge 1.5 \land$ TX success $< 50$ | RF front-end failure | $\{0, 1\}$ | None ($t < T$) | **TESTED** |
| `sig_05_multi_domain_crisis` | $\ge 3$ active domains simultaneously | Compound crisis | $\{0, 1\}$ | None ($t < T$) | **TESTED** |
| `sig_active_count` | Sum of active signatures [0..5] | Multi-domain burden | $[0, 5]$ | None ($t < T$) | **TESTED** |
| `feat_signature_score` | Weighted composite score | Domain failure burden | $[0.0, 1.0]$ | None ($t < T$) | **TESTED & BOUNDED** |

### Family 7: Gateway-Specific Historical Baseline (`gateway_baseline`, 7 Features)
*Source implementation*: [`src/features/gateway_baseline.py`](file:///m:/LPDGE/src/features/gateway_baseline.py)  
*Temporal window*: $[T - 28\text{d}, T - 7\text{d})$ historical self-baseline. Strictly $t < T$.

| Feature Name | Math Definition | Fallback / Cold Start | Expected Range | Leakage Risk | Status |
|---|---|---|---|---|---|
| `feat_gw_has_adequate_history` | $\mathbb{I}(\text{historical observed hours} \ge 72\text{h})$ | 0 if $< 72\text{h}$ | $\{0, 1\}$ | None ($t < T$) | **TESTED** |
| `feat_gw_hist_obs_hours` | Total observed hours in prior 21d | Raw count | $[0, 504]$ | None ($t < T$) | **TESTED** |
| `feat_gw_z_offline` | $(x_{\text{rec}} - \mu_{\text{gw}}) / (\sigma_{\text{gw}} + 1.0)$ | Fleet $\mu_{\text{fleet}}, \sigma_{\text{fleet}}$ | $[-5.0, 20.0]$ | None ($t < T$) | **TESTED** |
| `feat_gw_z_disconns` | $(x_{\text{rec}} - \mu_{\text{gw}}) / (\sigma_{\text{gw}} + 1.0)$ | Fleet $\mu_{\text{fleet}}, \sigma_{\text{fleet}}$ | $[-5.0, 20.0]$ | None ($t < T$) | **TESTED** |
| `feat_gw_z_reboots` | $(x_{\text{rec}} - \mu_{\text{gw}}) / (\sigma_{\text{gw}} + 1.0)$ | Fleet $\mu_{\text{fleet}}, \sigma_{\text{fleet}}$ | $[-5.0, 20.0]$ | None ($t < T$) | **TESTED** |
| `feat_gw_z_missing` | $(x_{\text{rec}} - \mu_{\text{gw}}) / (\sigma_{\text{gw}} + 1.0)$ | Fleet $\mu_{\text{fleet}}, \sigma_{\text{fleet}}$ | $[-5.0, 20.0]$ | None ($t < T$) | **TESTED** |
| `feat_gw_relative_anomaly_score` | Logistic mapping of $\sum \max(0, Z)$ | Centered at $2.0\sigma$ | $[0.0, 1.0]$ | None ($t < T$) | **TESTED & BOUNDED** |

### Family 8: Unsupervised Fleet Novelty (`novelty`, 2 Features)
*Source implementation*: [`src/intelligence/novelty.py`](file:///m:/LPDGE/src/intelligence/novelty.py)  
*Temporal window*: Fitted strictly on pre-decision training weeks ($t < T$).

| Feature Name | Model Definition | Threshold | Expected Range | Leakage Risk | Status |
|---|---|---|---|---|---|
| `feat_novelty_score` | IsolationForest anomaly score | Higher = more anomalous | $[0.0, 1.0]$ | None ($t < T$) | **TESTED & BOUNDED** |
| `is_novel_anomaly` | $\mathbb{I}(\text{feat\_novelty\_score} > \text{95th percentile})$ | Top 5% anomaly cutoff | $\{0, 1\}$ | None ($t < T$) | **TESTED** |

