# Empirical Experiment Backlog
**LPDG Innovation Hub Selection Challenge 2026**  
*Structured Scientific Protocols for Data Validation, Feature Engineering, and Cost Optimization*

---

## Executive Overview

In Section 8 of *FAQ — Round Two, and final*, LPDG explicitly instructed candidates:
> *“These are the findings the exercise exists to produce. Every one of them is measurable in the data you already have, in under an hour... Go and measure it. Then tell us what you found, how confident you are, and what would change your mind.”*

This backlog outlines the **14 prioritized empirical experiments** designed to test operational hypotheses, validate data behavior, and calibrate decision policies before finalizing our production pipeline.

---

## Experiment E-01: Offline Duration vs. Meter-Read Success Collapse
- **HYPOTHESIS**: Gateway offline duration does not cause linear data loss due to local edge buffering; only when cumulative offline duration exceeds a critical threshold ($	heta_{	ext{buffer}} pprox 12	ext{ hours/week}$) does meter read success collapse.
- **DATA REQUIRED**: `data/telemetry` (Aug 2025 – Jan 2026) and `meter_read_success.csv`.
- **FEATURES**: Weekly cumulative `offline_duration_sec`, weekly `disconnection_cnt`, `n_meters_installed`.
- **TARGET**: Weekly `read_success_rate = meters_read / meters_expected`.
- **METHOD**:
  1. Aggregate hourly telemetry to calendar weeks aligned with `meter_read_success.csv` (`week_start`).
  2. Compute non-linear piecewise regression and Spearman rank correlation between offline time and read success.
  3. Identify structural inflection points where $rac{d(	ext{read\_rate})}{d(	ext{offline\_time})}$ drops sharply.
- **EXPECTED OUTPUT**: Scatter plot with piecewise fitted spline showing buffer capacity and threshold $	heta_{	ext{buffer}}$.
- **DECISION CRITERIA**: If $r < 0.2$ below 12 hours, treat transient offline duration as buffered; trigger alarms only above $	heta_{	ext{buffer}}$.
- **LIMITATIONS**: Meter read success is weekly aggregate; cannot observe intraday buffer flushes.
- **POTENTIAL PROJECT IMPACT**: Eliminates false-positive dispatches on gateways with healthy edge recovery (€380 savings).

---

## Experiment E-02: Reboot Frequency & Thrashing vs. Work Order Repairs
- **HYPOTHESIS**: High reboot counts alone are uninformative (often scheduled maintenance); true hardware failure requires reboots combined with memory exhaustion (`avg_memfree < 35,000`) and high load averages (`avg_load1 > 2.0`).
- **DATA REQUIRED**: `field_visits.csv` and `data/telemetry`.
- **FEATURES**: Trailing 7-day `reboot_cnt`, `r_cnt_power_cycle`, `r_cnt_reboot`, `avg_memfree`, `avg_load1`, `avg_uptime`.
- **TARGET**: Work order outcome binary label: `1` if `outcome == 'Fehler behoben'` (fault fixed), `0` if `outcome == 'Kein Fehler gefunden'` (false alarm).
- **METHOD**:
  1. Extract telemetry windows for the 7 days preceding each work order `visited_on` in `field_visits.csv`.
  2. Train a decision tree / logistic regression to separate verified faults from false alarms.
  3. Measure feature interaction between reboot count and memory/load metrics.
- **EXPECTED OUTPUT**: ROC curve, interaction contours, and feature importance table.
- **DECISION CRITERIA**: If interaction term (`reboots * load`) has odds ratio $> 3.0$ while raw reboots has odds ratio $pprox 1.0$, require memory/load confirmation before flagging reboot anomalies.
- **LIMITATIONS**: `field_visits.csv` has technician label noise and non-random selection bias.
- **POTENTIAL PROJECT IMPACT**: Directly fulfills LPDG FAQ §4.8 guidance and reduces false alarms by up to 40%.

---

## Experiment E-03: Weak Signal vs. Active Failure (Nuisance vs. Fault)
- **HYPOTHESIS**: Poor RF signal quality (`rssi_bad`, `rscp_rsrp_bad`) without concurrent LoRa CRC errors or backhaul drops is an operational nuisance, not an actionable failure requiring a €380 visit.
- **DATA REQUIRED**: `data/telemetry` and `meter_read_success.csv`.
- **FEATURES**: Ratio of `rssi_bad / (rssi_good + rssi_normal + rssi_bad)`, `rx_crc_bad / rx_nr_pkts`.
- **TARGET**: Subsequent 4-week meter reading deficit: `read_success_rate < 0.8`.
- **METHOD**:
  1. Identify cohort of gateways with $>50\%$ weak signal but $100\%$ meter reads in month $M$.
  2. Perform survival analysis (Kaplan-Meier estimator) tracking weeks until meter read collapse.
  3. Compare hazard rate against normal-signal cohort.
- **EXPECTED OUTPUT**: Kaplan-Meier survival curves comparing weak-signal vs. normal-signal cohorts.
- **DECISION CRITERIA**: If hazard ratio $< 1.2$, exclude pure RF signal degradation from the primary ranking score.
- **LIMITATIONS**: Weather-induced RF attenuation cannot be separated from hardware antenna corrosion without long observation windows.
- **POTENTIAL PROJECT IMPACT**: Prevents burning top-15 slots on gateways whose meters are functioning perfectly.

---

## Experiment E-04: Candidate Definitions of "Needs a Visit"
- **HYPOTHESIS**: A multi-signal composite failure definition (combining severe packet loss, persistent disconnects, and terminal silence) correlates more strongly with verified historical repairs than any single-metric definition.
- **DATA REQUIRED**: `data/telemetry`, `meter_read_success.csv`, `field_visits.csv`.
- **FEATURES**: Full suite of connectivity, system, and RF features.
- **TARGET**: Candidate Targets:
  - Target A: Meter Deficit ($<50\%$ read success for 2 consecutive weeks).
  - Target B: Terminal Hardware Blackout ($>48$ hours telemetry silence).
  - Target C: Composite Operational Failure Index.
- **METHOD**:
  1. Formulate mathematical definitions for Targets A, B, and C.
  2. Evaluate overlap, precision, and recall against historical work orders with replaced parts (`Gateway getauscht`, `Netzteil`, `Antenne`).
  3. Simulate resulting operational dispatch costs under each target.
- **EXPECTED OUTPUT**: Venn diagram of identified gateways, confusion matrices, and total simulated euro cost.
- **DECISION CRITERIA**: Select target definition that achieves the lowest total simulated cost in historical backtests.
- **LIMITATIONS**: LPDG hidden ground truth cannot be observed directly.
- **POTENTIAL PROJECT IMPACT**: Solves the central 25% Judgement deliverable and defines the objective function.

---

## Experiment E-05: Missing-Data Handling & Imputation Sensitivity
- **HYPOTHESIS**: Treating absent telemetry hours as explicit failure evidence rather than missing data significantly alters the composition of the weekly top 15 and reduces missed blackout penalties.
- **DATA REQUIRED**: `data/telemetry` (Aug 2025 – Jan 2026).
- **FEATURES**: Aggregated features computed with:
  - Policy 1: Complete-case analysis (ignoring missing rows).
  - Policy 2: Global `fillna(0)`.
  - Policy 3: Time-grid reindexing with explicit missing-hour counting.
- **TARGET**: Top 15 ranked gateway set per week.
- **METHOD**:
  1. Implement all three imputation/missingness policies.
  2. Generate weekly rankings for all 26 historical weeks under each policy.
  3. Compute Jaccard similarity $J(S_1, S_2) = rac{|S_1 \cap S_2|}{|S_1 \cup S_2|}$ across weekly Top-15 sets.
- **EXPECTED OUTPUT**: Jaccard similarity matrix across weeks and rank turnover percentage.
- **DECISION CRITERIA**: If turnover $> 30\%$, missingness handling is load-bearing; adopt Policy 3 and document in `DECISIONS.md`.
- **LIMITATIONS**: Cannot verify ground truth of absent rows without physical technician inspection.
- **POTENTIAL PROJECT IMPACT**: Directly answers FAQ §3.3 recommendation (*"run your ranking with and without your handling of absent data"*).

---

## Experiment E-06: Lead-Time & Early Detection Horizon Analysis
- **HYPOTHESIS**: Gateway failures exhibit detectable pre-failure degradation 5 to 10 days prior to terminal breakdown; detecting failures at $T-7$ days captures $>80\%$ of recurring €600 savings compared to $T-1$ day reactive alerting.
- **DATA REQUIRED**: `data/telemetry` and `field_visits.csv`.
- **FEATURES**: Rolling aggregators over $T-24	ext{h}$, $T-48	ext{h}$, $T-7	ext{d}$, and $T-14	ext{d}$.
- **TARGET**: Confirmed failure onset date.
- **METHOD**:
  1. Profile metric trajectories (load, reboot, CRC error rate) backwards from failure onset.
  2. Compute divergence from 28-day baseline at daily steps from $T-14$ to $T-1$.
  3. Measure cumulative cost savings of early dispatch.
- **EXPECTED OUTPUT**: Lead-time trajectory plots and cost savings curve vs. warning lead time.
- **DECISION CRITERIA**: Optimal feature window is the point maximizing early capture while maintaining false alarm probability $<0.2$.
- **LIMITATIONS**: Instantaneous power cuts have zero lead time.
- **POTENTIAL PROJECT IMPACT**: Maximizes the high-value €600 counterfactual savings described in FAQ §5.2.

---

## Experiment E-07: Telemetry Silence Profiling (Observability vs. Failure)
- **HYPOTHESIS**: Short timestamp gaps ($<24	ext{ hours}$) are cellular network dropouts; prolonged silence ($>48	ext{ hours}$) in active gateways represents terminal power supply or hardware failure requiring dispatch.
- **DATA REQUIRED**: `data/telemetry` and `gateway_master.csv`.
- **FEATURES**: Maximum consecutive missing hours per gateway, distribution of gap lengths.
- **TARGET**: Eventual gateway reactivation vs. decommissioning / replacement.
- **METHOD**:
  1. Build a full hourly timestamp grid for all 332 gateways.
  2. Extract all continuous silence intervals; fit empirical survival distribution.
  3. Correlate silence intervals with subsequent `field_visits.csv` power supply replacements (`Netzteil`).
- **EXPECTED OUTPUT**: Histogram of gap lengths and conditional probability of permanent failure given $K$ hours of silence.
- **DECISION CRITERIA**: If probability of recovery drops below 10% after 48 hours, classify $\ge 48	ext{h}$ silence as confirmed failure.
- **LIMITATIONS**: Unmonitored or uninstalled gateways must be filtered using `installed_on` and `decommissioned_on`.
- **POTENTIAL PROJECT IMPACT**: Resolves Candidate Question 2 and provides a silence detector that catches baseline blind spots.

---

## Experiment E-08: Feature Attribution, Collinearity, and Pruning
- **HYPOTHESIS**: Removing the 7 zero-variance operator columns and highly collinear signal pairs (e.g. `rx_nr_pkts` and `rx_crc_bad`) improves tree model stability without loss of predictive cost reduction.
- **DATA REQUIRED**: `data/telemetry`.
- **FEATURES**: All 57 telemetry columns + derived rolling statistics.
- **TARGET**: Candidate composite failure target.
- **METHOD**:
  1. Compute Pearson correlation and Variance Inflation Factors (VIF).
  2. Train LightGBM model on full feature set vs. pruned feature set.
  3. Compute SHAP values and compare test set cost savings.
- **EXPECTED OUTPUT**: SHAP summary plot, correlation heatmap, and cost delta.
- **DECISION CRITERIA**: Retain pruned feature set if cost performance is equal or improved ($\Delta 	ext{Cost} \le 0$) while reducing model surface area.
- **LIMITATIONS**: Tree models naturally handle collinearity, but explainability is impaired.
- **POTENTIAL PROJECT IMPACT**: Produces clean, defensible feature documentation for `DECISIONS.md` and live session inspection.

---

## Experiment E-09: Decision Threshold vs. Operational Cost Curve
- **HYPOTHESIS**: The optimal decision threshold $	au^*$ that minimizes total operational cost is lower than the standard balanced accuracy cutoff ($	au = 0.5$) due to the asymmetric penalty ratio ($380 / 600 = 0.633$).
- **DATA REQUIRED**: Historical validation predictions from candidate models.
- **FEATURES**: Continuous model risk scores / predicted failure probabilities.
- **TARGET**: Simulated operational cost.
- **METHOD**:
  1. Sweep decision threshold $	au$ from $0.05$ to $0.95$ in increments of $0.01$.
  2. Calculate dispatched visits ($N_{	ext{visits}} 	imes €380$) and unresolved failure weeks ($N_{	ext{failures}} 	imes €600$).
  3. Plot total cost vs. threshold and find global minimum $	au^*$.
- **EXPECTED OUTPUT**: U-shaped cost curve showing minimum at $	au^*$ and marginal derivative curve.
- **DECISION CRITERIA**: Select $	au^*$ minimizing total cost; document the economic cost of moving threshold $\pm 0.1$.
- **LIMITATIONS**: Assumes simulated failure duration reflects future distribution.
- **POTENTIAL PROJECT IMPACT**: Fulfills Data Science core deliverable #4 and pre-calculates the exact live-session modification answer.

---

## Experiment E-10: Stateful Re-visit Cooldown Policy Simulation
- **HYPOTHESIS**: Applying a 2- to 3-week suppression filter on previously dispatched gateways saves $>€3,000$ over 8 weeks by preventing wasted €380 re-picks within the same counterfactual fault episode.
- **DATA REQUIRED**: Simulated 8-week predictions across historical validation periods.
- **FEATURES**: Weekly candidate rankings under:
  - Policy A: Stateless dispatch (no memory of previous visits).
  - Policy B: 1-week cooldown.
  - Policy C: 2-week cooldown.
  - Policy D: 3-week cooldown.
- **TARGET**: Total operational cost under FAQ §4.1 episode accounting.
- **METHOD**:
  1. Run the 8-week simulation under Policies A, B, C, and D.
  2. Calculate total cost, wasted re-picks, and missed new episodes.
- **EXPECTED OUTPUT**: Comparative cost table showing exact euro savings per policy.
- **DECISION CRITERIA**: Select the cooldown duration that maximizes net savings while allowing genuine re-emergence capture.
- **LIMITATIONS**: If an actual second episode occurs within the cooldown window, it is missed.
- **POTENTIAL PROJECT IMPACT**: Directly solves our Round 2 Question 1 insight and prevents the most expensive recurring error in the challenge.

---

## Experiment E-11: Model Benchmark vs. 3-Sigma Baseline on Total Cost
- **HYPOTHESIS**: A machine learning model incorporating silence detection, load thrashing, and RF error rates beats `baseline_3sigma.py` by at least €5,000 in total operational cost on out-of-time data.
- **DATA REQUIRED**: Complete historical dataset.
- **FEATURES**: Full engineered feature set vs. baseline 3 metrics.
- **TARGET**: Evaluated under the official cost matrix (€380 dispatch + €600 unaddressed fault).
- **METHOD**:
  1. Generate predictions using `baseline_3sigma.py`.
  2. Generate predictions using candidate ML models (LightGBM, Survival Model).
  3. Evaluate both through `CostEvaluator` on held-out January 2026 data.
- **EXPECTED OUTPUT**: Head-to-head comparison table: Total Cost, Precision@15, Recall, Avoided Failures, Wasted Visits.
- **DECISION CRITERIA**: Candidate model must strictly achieve $	ext{Cost}_{	ext{ML}} < 	ext{Cost}_{	ext{Baseline}}$.
- **LIMITATIONS**: Evaluated against proxy ground truth rather than official hidden answer key.
- **POTENTIAL PROJECT IMPACT**: Fulfills the mandatory Track E (Machine Learning) requirement.

---

## Experiment E-12: Grouped (Device-Disjoint) Generalization Assessment
- **HYPOTHESIS**: Evaluating models on unseen gateways reveals a measurable performance drop ($10	ext{–}20\%$) compared to random splitting, confirming that device-disjoint validation is essential to prevent over-optimistic scoring.
- **DATA REQUIRED**: Historical telemetry and labels.
- **FEATURES**: Candidate feature store.
- **TARGET**: Failure outcome.
- **METHOD**:
  1. Evaluate model under 5-Fold Random Stratified K-Fold.
  2. Evaluate model under 5-Fold GroupKFold (grouped by `gateway_id`).
  3. Compare cost, precision@15, and feature importance rank stability across both setups.
- **EXPECTED OUTPUT**: Paired bar charts showing metric degradation under device-disjoint splitting.
- **DECISION CRITERIA**: Adopt GroupKFold as the authoritative validation split; report both numbers to demonstrate honesty.
- **LIMITATIONS**: Fleet size is small (~320 gateways); fold variance will be noticeable.
- **POTENTIAL PROJECT IMPACT**: Validates Clue 14 and establishes the 25% Judgement credibility required by FAQ §5.2.

---

## Experiment E-13: Forward-in-Time Temporal Validation Walk
- **HYPOTHESIS**: Model performance degrades when predicting across temporal distance due to seasonal shifts and firmware updates; expanding walk-forward validation provides the only honest estimate of February/March 2026 performance.
- **DATA REQUIRED**: Telemetry from August 2025 through January 2026.
- **FEATURES**: Bounded historical features ($t < T$).
- **TARGET**: Weekly failure predictions.
- **METHOD**:
  1. Train on Month 1..$k$, evaluate on Month $k+1$ for $k \in \{4, 5\}$.
  2. Measure performance drift, calibration drift, and cost stability.
- **EXPECTED OUTPUT**: Month-over-month cost trajectory and drift diagnostic charts.
- **DECISION CRITERIA**: If drift $> 15\%$, incorporate recency normalization in feature engineering.
- **LIMITATIONS**: Only 6 historical months available prior to February 2026.
- **POTENTIAL PROJECT IMPACT**: Completely eliminates forward-looking temporal leakage and proves temporal robustness.

---

## Experiment E-14: Validation Spread & Cohort Stability Quantification
- **HYPOTHESIS**: Quoting a single validation point estimate misrepresents uncertainty; reporting 5-fold Min–Max cost ranges demonstrates statistical integrity and guards against live-session evaluation variance.
- **DATA REQUIRED**: Output of Experiment E-12 and E-13.
- **FEATURES**: Model predictions across all folds.
- **TARGET**: Fold-level simulated operational cost.
- **METHOD**:
  1. Compute cost, precision@15, and recall for each individual fold.
  2. Calculate Mean, Standard Deviation, Min, Median, and Max across folds.
  3. Segment stability by site type (`Heizraum`, `Außenmast`, `Gebäude`) and tenant.
- **EXPECTED OUTPUT**: Box plots and summary tables displaying performance ranges across cohorts.
- **DECISION CRITERIA**: Include full range in `DECISIONS.md` and report write-up; explicitly explain why the range is wide.
- **LIMITATIONS**: Small sample size per fold ($~64$ gateways).
- **POTENTIAL PROJECT IMPACT**: Fulfills Data Science deliverable #3 and directly avoids the common penalty noted in FAQ §5.2.
