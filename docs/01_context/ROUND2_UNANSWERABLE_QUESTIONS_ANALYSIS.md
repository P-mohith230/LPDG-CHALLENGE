# Forensic Analysis of Unanswerable Questions: FAQ Section 8
**LPDG Innovation Hub Selection Challenge 2026**  
*Turning Official Rejections into Candidate Empirical Hypotheses and Defensible Decisions*

---

## Executive Summary

Section 8 of *FAQ — Round Two, and final* is entitled **“What we are not answering, and why.”** 

Rather than viewing this section as a barrier, a senior engineer recognizes it as LPDG's explicit **assessment syllabus**. In Section 8, LPDG openly reveals what separates an exceptional candidate from a mediocre one:
> *“These are the findings the exercise exists to produce. Every one of them is measurable in the data you already have, in under an hour, and what you find — plus what you did about it — is a large part of what distinguishes one submission from another... Go and measure it. Then tell us what you found, how confident you are, and what would change your mind. A candidate who reports a relationship and the case where it breaks down is telling us far more than one who repeats an answer we gave.”*

Below is an exhaustive, 13-point forensic analysis of every category of question LPDG refused to answer, transforming each into a concrete data-driven experiment, decision boundary, and defensible narrative for our project.

---

## Category 1: Whether Offline Duration Tracks Meter-Read Success

### 1. What Candidates Asked
*Does higher `offline_duration_sec` or prolonged backhaul disconnection correlate with, or cause, drops in weekly meter read success (`meters_read / meters_expected`)?*

### 2. Why LPDG Refused to Answer
LPDG explicitly noted that this relationship is directly measurable using the supplied telemetry and weekly meter read success files. Giving the answer would eliminate the need for candidates to perform empirical exploratory data analysis and evaluate signal validity.

### 3. What LPDG Expects Candidates to Discover
LPDG expects candidates to discover:
- Whether cellular backhaul downtime immediately results in unread meters or whether gateways buffer packets locally in flash storage and offload them upon reconnection.
- The threshold of downtime where local buffering overflows and meter reading deficits permanently accrue.

### 4. Application to Our Project
Directly foundational. If offline duration does not cause meter reading loss (due to buffer recovery), heavily weighting short offline spikes will produce false positive visits (€380 wasted).

### 5. Investigation Using Supplied Data
Perform a time-lagged merge between weekly aggregated `offline_duration_sec` from `data/telemetry` and `meter_read_success.csv` for the 26 historical weeks (August 2025 – January 2026) across all 280 reporting gateways.

### 6. Concrete Experiment
**Experiment E-01**: Compute weekly cumulative offline hours per gateway versus weekly `read_success_rate = meters_read / meters_expected`. Fit non-linear monotonic regression (Spearman rank correlation, piecewise spline) to detect tipping points.

### 7. Evidence Supporting Hypothesis
A sharp non-linear collapse in `read_success_rate` when weekly offline time exceeds a specific threshold (e.g., >12 hours in a week).

### 8. Evidence Rejecting Hypothesis
A weak correlation ($r < 0.15$) where gateways with high offline duration still report 100% of expected meters once reconnected, indicating robust edge buffering.

### 9. Remaining Limitations
`meter_read_success.csv` is aggregated at weekly resolution; intra-week buffering dynamics cannot be measured at sub-hourly fidelity.

### 10. Effect on Final Top-15 Ranking
High. Dictates whether `offline_duration_sec` is treated as an urgent primary alarm or a secondary indicator.

### 11. Effect on Operational Cost
Directly prevents dispatching €380 visits to gateways that experience transient dropouts but successfully backfill readings.

### 12. Strengthening Judgement (25% Component)
Demonstrates that the candidate tested domain physical mechanisms (buffering vs. loss) rather than blindly assuming downtime equals data destruction.

### 13. Inclusion in DECISIONS.md
Yes. Document as Decision #4: *"Why offline duration was thresholded based on empirical meter-read recovery curves rather than linear 3-sigma deviation."*

---

## Category 2: Whether Reboot Frequency Identifies Gateways Worth Visiting

### 1. What Candidates Asked
*Do frequent gateway reboots (`reboot_cnt`, `r_cnt_reboot`, `r_cnt_power_cycle`) reliably indicate hardware failure warranting a physical technician visit?*

### 2. Why LPDG Refused to Answer
Reboots can be scheduled maintenance watchdog cycles, transient grid fluctuations, or fatal kernel crash loops. Answering would give away whether reboots are benign or catastrophic in this network.

### 3. What LPDG Expects Candidates to Discover
- In `field_visits.csv`, `Haeufige Neustarts` (Frequent reboots) is the #1 reported reason (110 visits), yet only 56% resulted in `Fehler behoben` (fault resolved), while 43% resulted in `Kein Fehler gefunden` (false alarm).
- The difference between watchdog reboots (`r_cnt_reboot`) vs. electrical power cycles (`r_cnt_power_cycle`) vs. unclassified crashes (`r_cnt_unknown`).

### 4. Application to Our Project
Critical. `baseline_3sigma.py` weights `reboot_cnt` equally alongside offline duration and disconnections.

### 5. Investigation Using Supplied Data
Analyze `field_visits.csv` work orders initiated for `Haeufige Neustarts` and cross-reference with telemetry reboot counts, load averages (`avg_load1`), and memory exhaustion (`avg_memfree`) in the preceding 7 days.

### 6. Concrete Experiment
**Experiment E-02**: Logistic regression classifying `outcome == 'Fehler behoben'` vs. `'Kein Fehler gefunden'` given pre-visit reboot patterns, load spikes, and uptime resets.

### 7. Evidence Supporting Hypothesis
Gateways where reboots are accompanied by memory exhaustion (`avg_memfree < 35,000`) and high load averages (`avg_load1 > 2.0`) strongly predict real hardware failure (`Gateway getauscht` or `Netzteil`).

### 8. Evidence Rejecting Hypothesis
Reboot count alone shows near-identical distributions between repaired gateways and false-alarm visits.

### 9. Remaining Limitations
Technician diagnosis in `field_visits.csv` carries human error; some "no fault found" outcomes may reflect intermittent faults.

### 10. Effect on Final Top-15 Ranking
Prevents healthy gateways that reboot routinely from crowding out truly broken units in the top 15.

### 11. Effect on Operational Cost
Substantial. Eliminates false-positive dispatch costs (€380).

### 12. Strengthening Judgement (25% Component)
Directly fulfills the quote from FAQ §4.8: *“'reboot count correlated at 0.31' is not a justification, and 'gateways that reboot repeatedly stop delivering reads within two weeks, which is what costs €600' is.”*

### 13. Inclusion in DECISIONS.md
Yes. Document as Decision #5: *"Separation of benign watchdog reboots from thrashing reboot loops."*

---

## Category 3: Whether Bad Signal with Working Meters is a Fault

### 1. What Candidates Asked
*If a gateway exhibits degraded signal quality (`rssi_bad`, `rscp_rsrp_bad`, `ecio_rsrq_bad`) but continues reading 100% of its meters, should it be prioritized for a visit?*

### 2. Why LPDG Refused to Answer
This goes to the very core of defining "needs a visit." Is a visit intended for preventive maintenance or active failure recovery?

### 3. What LPDG Expects Candidates to Discover
- In `field_visits.csv`, 79 visits were dispatched for `Signal schwach` (Weak signal). **Zero resulted in `Fehler behoben`** (73 found no fault, 6 had no access).
- In the cost model, €600 is charged per gateway per week it is left faulty. If meters are being read, does the utility suffer unbilled consumption? No.

### 4. Application to Our Project
High. Prevents allocating scarce 15-visit capacity to cosmetic RF issues that do not disrupt metering.

### 5. Investigation Using Supplied Data
Measure historical field visits for `Signal schwach` and verify whether weak signal gateways suffered subsequent blackout or meter loss in following months.

### 6. Concrete Experiment
**Experiment E-03**: Survival analysis of gateways with high `rssi_bad` fractions: compute time-to-failure (weeks until `read_pct < 0.8`) for weak signal with 100% reads vs. normal signal.

### 7. Evidence Supporting Hypothesis
Weak signal without packet loss has an expected time-to-failure exceeding 16 weeks, meaning immediate dispatch yields negative economic ROI.

### 8. Evidence Rejecting Hypothesis
Weak signal rapidly degrades into unrecoverable backhaul disconnection within 7–14 days.

### 9. Remaining Limitations
Environmental RF noise (weather, urban construction) can fluctuate without hardware degradation.

### 10. Effect on Final Top-15 Ranking
Major. Downweights pure RF signal metrics unless coupled with active packet dropping.

### 11. Effect on Operational Cost
Saves up to €380 per slot by avoiding futile antenna checks.

### 12. Strengthening Judgement (25% Component)
Demonstrates deep operational prioritization: field teams must fix revenue-impacting outages before addressing aesthetic signal fluctuations.

### 13. Inclusion in DECISIONS.md
Yes. Document as Decision #1: *"Why RF signal degradation without packet loss was rejected as a primary dispatch trigger."*

---

## Category 4: Operational Definition of "Needs a Visit"

### 1. What Candidates Asked
*Can LPDG provide a concrete mathematical definition or labeling rule for which gateways need a visit?*

### 2. Why LPDG Refused to Answer
LPDG explicitly refused in Brief p. 3, FAQ Round 1 §4.1, and FAQ Round 2 §8: *“Deciding what 'needs a visit' means is the task. Write your definition down, say what else you considered, say why you rejected it, and say what your definition would get wrong. That is what the 25% is for.”*

### 3. What LPDG Expects Candidates to Discover
Candidates must formulate an objective, defensible standard that balances the €380 visit cost against the €600 recurring penalty under a 15-visit constraint.

### 4. Application to Our Project
Central requirement of the entire project.

### 5. Investigation Using Supplied Data
Correlate operational failure indicators: complete telemetry silence, persistent CRC corruption, continuous load thrashing, and historical work order parts replacements (`Gateway getauscht`, `Netzteil`, `Antenne`).

### 6. Concrete Experiment
**Experiment E-04**: Compare three candidate target definitions:
- Target A: Pure Meter Deficit ($<50\%$ read success for 2 consecutive weeks).
- Target B: Terminal Hardware/Silence Outage ($>48$ hours telemetry blackout or severe reboot thrashing).
- Target C: Combined Operational Risk Index.

### 7. Evidence Supporting Hypothesis
A combined target captures both silent outages and active data loss, yielding the lowest total cost in simulation.

### 8. Evidence Rejecting Hypothesis
Single-signal targets miss large cohorts of broken devices (e.g., meter deficit misses gateways whose meters fail in the upcoming week).

### 9. Remaining Limitations
True ground truth is hidden; candidate definition is an approximation of operational ground truth.

### 10. Effect on Final Top-15 Ranking
Determines the ranking logic for all 120 submission slots.

### 11. Effect on Operational Cost
Dominates the variable €600 cost curve.

### 12. Strengthening Judgement (25% Component)
Directly answers bullet #1 of Data Science marking criteria (FAQ §5.1).

### 13. Inclusion in DECISIONS.md
Yes. Mandatory Decision #1 in `DECISIONS.md`.

---

## Category 5: Decision Threshold and Economic Trade-Off (€380 vs. €600)

### 1. What Candidates Asked
*Where should the classification or risk score threshold be drawn? How many false alarms are acceptable?*

### 2. Why LPDG Refused to Answer
The economic trade-off between a €380 false alarm and a recurring €600 missed outage is the core optimization task. Giving a threshold turns an optimization problem into an arbitrary lookup.

### 3. What LPDG Expects Candidates to Discover
- Every week has a hard 15-visit cap, meaning the threshold must be evaluated relative to capacity.
- The cost ratio is $380 / 600 = 0.633$. If a gateway has a probability $P(	ext{fault}) > 0.633$, dispatching is immediately cost-positive even if the fault lasts only one week. If the fault persists for multiple weeks, the threshold drops much lower: $P(	ext{fault}) > 380 / (600 	imes 	ext{duration})$.

### 4. Application to Our Project
Dictates how ranks 1 to 15 are selected and how sub-15 decisions are documented.

### 5. Investigation Using Supplied Data
Simulate the cost curve across various threshold percentiles using historical data.

### 6. Concrete Experiment
**Experiment E-05**: Cost curve sensitivity analysis: sweep threshold $	au \in [0.1, 0.9]$, compute total simulated cost, and calculate the economic derivative $\Delta 	ext{Cost} / \Delta 	au$.

### 7. Evidence Supporting Hypothesis
Cost curves exhibit a clear convex minimum where marginal dispatch cost equals expected penalty savings.

### 8. Evidence Rejecting Hypothesis
A flat cost curve with no sensitivity to threshold location.

### 9. Remaining Limitations
Depends on assumed distribution of fault duration in unseen months.

### 10. Effect on Final Top-15 Ranking
Determines which marginal candidates occupy ranks 10–15.

### 11. Effect on Operational Cost
Directly minimizes total euro cost.

### 12. Strengthening Judgement (25% Component)
Fulfills Data Science requirement #4: *"The €380 and €600 turned into an actual decision. Where you draw the line, and what moving it costs in each direction."*

### 13. Inclusion in DECISIONS.md
Yes. Document as Decision #2: *"Calibration of the economic dispatch threshold."*

---

## Category 6: How Early is Early Enough (Pre-failure Detection Horizon)

### 1. What Candidates Asked
*How many days or weeks before a catastrophic failure must a gateway be flagged?*

### 2. Why LPDG Refused to Answer
Early detection is governed by economic trade-offs: detecting too early risks false positives on transient issues; detecting too late allows the €600 weekly penalty to compound.

### 3. What LPDG Expects Candidates to Discover
- FAQ §5.2: *"Finding a fault early is worth strictly more than finding it at all, and finding it late is worth almost nothing."*
- Catching a 4-week fault in Week 1 saves €1,800. Catching it in Week 4 saves €0.

### 4. Application to Our Project
Determines the feature aggregation window (trailing 24 hours vs. 7 days vs. 28 days) and lead time of training targets.

### 5. Investigation Using Supplied Data
Examine telemetry degradation profiles in the 1, 2, 3, and 4 weeks preceding confirmed field visit repairs (`Fehler behoben`).

### 6. Concrete Experiment
**Experiment E-06**: Lead-time sensitivity: measure predictive feature divergence at $T-7$, $T-14$, and $T-21$ days before fault onset.

### 7. Evidence Supporting Hypothesis
Measurable degradation (load spikes, bad CRC ratio increase) emerges 5 to 10 days before complete backhaul failure.

### 8. Evidence Rejecting Hypothesis
Failures occur as sudden step-functions with zero pre-failure telemetry warning.

### 9. Remaining Limitations
Power cuts occur instantaneously without predictive degradation.

### 10. Effect on Final Top-15 Ranking
Ranks deteriorating gateways ahead of already-dead gateways that were previously visited.

### 11. Effect on Operational Cost
Maximizes avoided €600 recurring weekly penalties.

### 12. Strengthening Judgement (25% Component)
Shows deep comprehension of counterfactual savings dynamics.

### 13. Inclusion in DECISIONS.md
Yes. Document as Decision #3: *"Lead-time window selection for early fault capture."*

---

## Summary Matrix: Unanswerable Questions as Project Assets

| Section 8 Category | LPDG Refusal Rationale | Our Empirical Action | Target Artifact |
|---|---|---|---|
| **Offline vs. Meter Reads** | Measurable in data in <1 hr | Lagged correlation & spline regression | `EXPERIMENT_BACKLOG.md` (E-01) |
| **Reboot Significance** | Hardware thrashing vs. scheduled watchdog | Correlate reboots + memory with repair outcomes | `EXPERIMENT_BACKLOG.md` (E-02) |
| **Weak Signal vs. Normal Reads** | Candidate must separate cosmetic vs. real fault | Survival analysis on weak signal cohorts | `EXPERIMENT_BACKLOG.md` (E-03) |
| **Needs a Visit Definition** | The central test of candidate judgement | Formalize hybrid operational failure standard | `PROJECT_DECISION_REGISTER.md` (D-01) |
| **Decision Threshold & Economics** | Must price the trade-off, not discuss it | Cost curve sweep and priced sensitivity | `PROJECT_DECISION_REGISTER.md` (D-02) |
| **Early Detection Horizon** | Finding early saves money, finding late saves zero | Lead-time degradation profile analysis | `EXPERIMENT_BACKLOG.md` (E-06) |
