# Innovation 4: Risk × Deterioration Priority Dispatch Engine & Lead-Time Analysis

## Problem Statement
Standard machine learning dispatch policies rank candidates exclusively by their predicted static risk probability $P(\text{deficit} \mid X)$. This creates a fundamental operational blind spot:
- **Chronic High-Risk Assets**: Gateways that persistently hover at $P \approx 0.75$ with constant, unchanging telemetry. Even if visited, their environment may prevent further improvement, resulting in repeat or wasted visits.
- **Acute Emerging Assets**: Gateways currently at moderate risk ($P \approx 0.45$), but exhibiting steep, accelerating deterioration trajectories ($D \approx 0.90$). Under a strict top-15 risk cutoff, these emerging failures are deferred until the following week, when they have fully collapsed into an unaddressed deficit episode incurring €600/week in SLA penalties.

Decoupling **current state risk** from **temporal deterioration progression** allows operations to prioritize assets before catastrophic failure occurs.

## Empirical Hypothesis
Decoupling and subsequently recombining static ML risk ($P$) with dynamic progression ($D$) into a unified **Dispatch Priority Score** ($S_{\text{priority}}$):
1. Elevates rapidly deteriorating gateways into the weekly top-15 quota before complete collection blackout.
2. Increases detection lead-time (evaluating signal trajectory at Weeks -4, -3, -2, -1 before onset).
3. Reduces repeat visits and penalty accumulation under the 2-week cooldown policy.

## Operational Priority Formulations
For each candidate gateway at decision time $T$, we evaluate:
- $P \in [0.0, 1.0]$: Supervised HistGradientBoosting probability.
- $D \in [0.0, 1.0]$: Bounded Deterioration Progression Score.

### 1. Multiplicative Interaction Engine
Amplifies baseline risk proportionally to the rate of deterioration:
$$S_{\text{priority}} = \frac{P \cdot (1.0 + \beta \cdot D)}{1.0 + \beta}$$
where $\beta = 0.50$ provides up to a $1.5\times$ amplification for accelerating degradation.

### 2. Weighted Additive Linear Combination
Direct linear blend of probability and deterioration:
$$S_{\text{priority}} = \alpha \cdot P + (1.0 - \alpha) \cdot D$$
where $\alpha = 0.70$ anchors priority primarily on validated ML risk.

### 3. Rank-Based Borda Count
Combines the relative fleet percentiles of risk and deterioration, providing robustness against probability calibration shifts:
$$\text{pct}_P = \frac{\text{rank}(P)}{N}, \quad \text{pct}_D = \frac{\text{rank}(D)}{N}$$
$$S_{\text{priority}} = \alpha \cdot \text{pct}_P + (1.0 - \alpha) \cdot \text{pct}_D$$

### 4. Quadrant Classification & Boost Engine
Assets are partitioned into operational quadrants:
- **Quadrant 1 (Critical Accelerating)**: $P \ge 0.50 \land D \ge 0.40 \implies \text{Priority Boost} +0.20$
- **Quadrant 2 (Chronic Persistent)**: $P \ge 0.50 \land D < 0.40 \implies \text{Standard Risk}$
- **Quadrant 3 (Early-Warning Emerging)**: $P < 0.50 \land D \ge 0.60 \implies \text{Priority Boost} +0.15$
- **Quadrant 4 (Stable Healthy)**: $P < 0.50 \land D < 0.40 \implies \text{Deprioritized}$

## Lead-Time Early-Warning Protocol (Weeks -4 to 0)
To determine how many weeks *before* severe collection deficit onset the signal becomes detectable, we trace historical trajectories for gateways that experience deficit episodes ($\text{read\_ratio} < 0.50$):
- **Week -4**: 4 weeks prior to onset.
- **Week -3**: 3 weeks prior to onset.
- **Week -2**: 2 weeks prior to onset.
- **Week -1**: 1 week prior to onset.
- **Week 0**: Exact week of deficit onset.

We evaluate the progression of deterioration score, offline duration, missing hours, and reboot activity.

## Results & Findings

### Priority Formulation Head-to-Head Benchmark (Unified 16-Week Window)

| Priority Formulation Method | Formula / Logic | 16-Wk Cost (€) | Penalty Cost (€) | Precision@15 | Recall | Intercepted Faults | Unaddressed Faults | Repeat Visits |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`risk_only`** (Baseline V1) | $S = P$ | €128,400 | €37,200 | 30.83% | 83.33% | 310 | 62 | 52 |
| **`multiplicative`** | $S = P \cdot (1 + 0.5D) / 1.5$ | €126,600 | €35,400 | 30.83% | 84.14% | 313 | 59 | 53 |
| **`additive`** | $S = 0.7P + 0.3D$ | €124,200 | €33,000 | 30.83% | 85.22% | 317 | 55 | 54 |
| **`rank_borda`** | $0.7 \cdot \text{pct}(P) + 0.3 \cdot \text{pct}(D)$ | **€121,200** | **€30,000** | **31.25%** | **86.56%** | **322** | **50** | **50** |
| **`quadrant_boost`** | Multiplicative + Quadrant Bonus | €122,400 | €31,200 | 30.83% | 86.02% | 320 | 52 | 54 |

### Lead-Time Early-Warning Trajectory Analysis (Weeks -4 to 0)

Tracing historical telemetry trajectories across $N=111$ severe collection deficit episodes reveals clear precursor degradation prior to failure onset:

| Observation Horizon | Lead Time | Mean Deterioration Score | Mean Offline Hours | Mean Missing Hours | Mean Reboot Count | Sample Size |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Week -4** | 4 Weeks Prior | 0.1971 | 4.37h | 24.12h | 2.41 | 96 |
| **Week -3** | 3 Weeks Prior | 0.2018 | 3.63h | 23.95h | 2.24 | 100 |
| **Week -2** | 2 Weeks Prior | 0.2043 | 3.73h | 24.50h | 3.58 | 104 |
| **Week -1** | 1 Week Prior | **0.2331** | **5.36h** | **29.66h** | **4.58** | 111 |
| **Week 0** | Deficit Onset Week | **0.3753** | **21.61h** | **45.21h** | **11.59** | 111 |

## Interpretation & Operational Insights
1. **Measurable Lead-Time Progression**: Deterioration signals begin rising at **Week -1** (Deterioration Score $+18\%$, missing hours $+23\%$, reboots $+28\%$) before exploding at **Week 0** (Deterioration Score jumps $+61\%$, offline hours jump $4.0\times$ from 5.36h to 21.61h, reboots jump $2.5\times$ to 11.59).
2. **Economic Efficacy of Rank Borda & Quadrant Prioritization**: Decoupling risk from deterioration via Rank Borda or Quadrant Boost cuts operational cost by **€7,200** to **€6,000**, reducing unaddressed fault episodes from 62 down to 50–52. Rank Borda also achieved the lowest repeat visits (50 vs 52).
3. **Synergy with Cooldown**: Cooldown prevents re-visiting recently serviced assets, enabling the priority engine to reach deeper into the fleet and intercept developing Quadrant 3 ("Early-Warning Emerging") failures.

## Limitations
1. **Calibration Sensitivity**: Blending rank percentiles alters raw probability calibration, requiring raw risk probabilities to be preserved alongside priority scores for auditing.
2. **Transient Glitches**: Single-day backhaul spikes can temporarily elevate deterioration without causing persistent meter-read collection collapse.

## Decision
**PROMOTED TO DISPATCH RANKING LAYER**. The Risk $\times$ Deterioration Priority Engine (Rank Borda / Quadrant Boost) demonstrates measurable early-warning interception, reduces operational cost by up to €7,200, and reduces unaddressed penalty episodes.
