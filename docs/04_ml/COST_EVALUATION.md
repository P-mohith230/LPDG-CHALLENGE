# Operational Cost Evaluation & Economic Modeling Specification
**LPDG Innovation Hub Selection Challenge 2026**  
*The Authoritative Financial Accounting Engine, Episode Mechanics, and Asymmetric Utility Economics*

---

## 1. Executive Cost Principles

The core objective of the LPDG challenge is to minimize the total operational cost incurred by the smart utility network over the 8-week evaluation window (February–March 2026).

> [!IMPORTANT]
> **Total Operational Cost Formula**:  
> $$\text{Total Cost} = \text{Dispatch Visit Costs} + \text{Unaddressed Fault Penalty Costs}$$
> $$\text{Total Cost} = \left( N_{\text{visits}} \times €380 \right) + \sum_{e \in \text{Episodes}} \text{Duration}_e \times €600$$
> - **Dispatch Visit Cost**: Fixed at **€380** per physical on-site technician dispatch.
> - **Unaddressed Fault Penalty**: Fixed at **€600** per faulty gateway per week, flat (unweighted by meter count).

---

## 2. Fixed Visit Component Economics

In accordance with FAQ Round 1 §5.1–§5.4 and `validate_submission.py`, every compliant submission must contain exactly 15 recommendations per week across all 8 scored weeks:

$$\text{Fixed Visit Expenditure} = 8\text{ weeks} \times 15\text{ dispatches/week} \times €380 = €45,600$$

### Critical Strategic Insight:
Because the submission contract mandates exactly 120 total visits, **every valid submission incurs an identical €45,600 dispatch cost**.

Therefore, the **only variable component that differentiates candidate solutions is how effectively those 120 visits curtail unaddressed fault penalties (€600/week)**.

---

## 3. Official Fault Episode Accounting Rules (FAQ Round 2 §4.1)

In response to our formal Round 2 question regarding multi-week fault accounting, LPDG clarified the exact mechanics governing fault episodes:

```mermaid
sequenceDiagram
    participant GroundTruth as Hidden Ground Truth
    participant Scorer as Official Scorer
    participant Candidate as Candidate Top-15 Dispatches

    Note over GroundTruth: Episode 1: Weeks 1, 2, 3 (Faulty)
    Candidate->>Scorer: Week 2: Dispatches Visit to Gateway G
    Scorer->>Scorer: Week 1: Incurs €600 (Unaddressed)
    Scorer->>Scorer: Week 2: Visited! Incurs €380 visit cost.
    Scorer->>Scorer: Week 3: Incurs €0 (Halted by Week 2 visit!)
    
    Note over GroundTruth: Week 4: Healthy (Episode 1 Ended)
    Candidate->>Scorer: Week 4: No visit needed.
    
    Note over GroundTruth: Episode 2: Weeks 5, 6 (New Fault!)
    Candidate->>Scorer: Week 5: Misses Gateway G (Incurs €600)
    Candidate->>Scorer: Week 6: Dispatches Visit (Incurs €380 visit; halts Week 6 accrual)
```

### The 6 Binding Episode Rules:
1. **Pre-Calculated Ground Truth**: Fault episodes are determined entirely from hidden ground truth before candidate submissions are evaluated.
2. **Episode Definition**: An episode is a maximal sequence of consecutive faulty weeks for a specific gateway.
3. **Episode Separation**: A single healthy week between faulty periods definitively terminates the previous episode and establishes a new, independent episode.
4. **Earliest Visit Priority**: Only the **earliest visit** occurring during an episode halts the penalty. The episode incurs €600/week from its onset up to and including the week of the first visit.
5. **Zero Benefit for Repeat Visits (The Wasted Dispatch Penalty)**:
   - Selecting the same gateway again in a later week of the **same episode** yields **€0 additional penalty savings**.
   - However, the repeat selection still incurs the **€380 visit cost** and burns 1 of the 15 scarce weekly dispatch slots!
6. **New Episodes Require New Visits**: A subsequent episode (occurring after a healthy week) must be detected and visited independently.
7. **Static Telemetry**: Physical site visits do **NOT** modify historical telemetry records counterfactually; only the financial accounting ledger is updated.

---

## 4. The Economics of Early Detection

The recurring €600 weekly penalty strongly incentivizes detecting degrading gateways at the earliest possible moment:

| Week Detected | Weeks Unaddressed | Accrued Fault Penalty | Visit Cost | Total Episode Cost | Net Savings vs. Unvisited (3-Week Episode) |
|---|---|---|---|---|---|
| **Week 1 (Onset)** | 1 week | €600 | €380 | **€980** | **+€820 saved** (€1,800 - €980) |
| **Week 2** | 2 weeks | €1,200 | €380 | **€1,580** | **+€220 saved** (€1,800 - €1,580) |
| **Week 3** | 3 weeks | €1,800 | €380 | **€2,180** | **-€380 loss** (Visit arrived at terminal week) |
| **Never Visited** | 3 weeks | €1,800 | €0 | **€1,800** | Reference unmitigated loss |

### Key Economic Takeaways:
- Catching an episode in its **first week** yields a massive €820 net saving over the life of a 3-week outage.
- Delaying detection by a single week forfeits €600 in avoidable utility penalties.
- Visiting in the final week of an episode costs €380 to save zero future weeks, generating a net financial loss.

---

## 5. Mathematical Cost Simulator Architecture

To guide model selection and threshold calibration, our local evaluation harness implements a Python cost simulator reflecting the exact ground truth episode logic:

```python
def compute_operational_cost(ground_truth_episodes, candidate_predictions):
    """
    Simulates total operational cost under LPDG Round 2 §4.1 accounting.
    """
    total_visit_cost = len(candidate_predictions) * 380  # Exactly 120 * 380 = 45,600
    total_penalty_cost = 0
    
    # Track visited episodes
    visited_episodes = set()
    
    for episode in ground_truth_episodes:
        # Find earliest candidate visit during this episode
        visits = [v for v in candidate_predictions 
                  if v.gateway_id == episode.gateway_id 
                  and episode.start_week <= v.week <= episode.end_week]
        
        if visits:
            earliest_visit_week = min(v.week for v in visits)
            active_weeks = (earliest_visit_week - episode.start_week) + 1
        else:
            active_weeks = (episode.end_week - episode.start_week) + 1
            
        total_penalty_cost += active_weeks * 600
        
    return total_visit_cost + total_penalty_cost
```

---

## 6. Threshold Optimization & Economic Decision Boundary

In standard ML classification with predicted failure probability $P(\text{fault})$, the expected cost of dispatching a visit versus withholding a visit is:
- $\mathbb{E}[\text{Cost} \mid \text{Dispatch}] = €380 + (1 - P(\text{fault})) \cdot €0 = €380$
- $\mathbb{E}[\text{Cost} \mid \text{No Dispatch}] = P(\text{fault}) \cdot €600 \times L$ (where $L$ is expected episode length in weeks).

For a single-week horizon ($L=1$):
$$P(\text{fault}) \cdot €600 > €380 \implies P^* > \frac{380}{600} \approx 0.633$$

For a multi-week horizon ($L \ge 2$ weeks):
$$P(\text{fault}) \cdot €1,200 > €380 \implies P^* > \frac{380}{1,200} \approx 0.317$$

### Strategic Conclusion:
Under multi-week episode dynamics, the optimal threshold shifts aggressively towards early intervention ($P^* \approx 0.32$), confirming that risk-neutral models that wait for 90% certainty will severely lose to proactive rankers.
