# Selected Final Round 1 Clarification Questions
**LPDG Innovation Hub Selection Challenge 2026**  
*Evaluation Rubric, Multi-Factor Scoring, and Structured Question Cards (Phase 13)*

---

## Section 1: Multi-Factor Evaluation Rubric & Scoring

Every candidate question was evaluated against the formal four-pillar weighting system:
1. **Importance to Correctness (40%)**: Does the ambiguity prevent building a fundamentally correct system?
2. **Impact on Evaluation Fairness (25%)**: Does the lack of clarity create asymmetric scoring disadvantages between candidates?
3. **Ambiguity in Official Materials (20%)**: Is the question genuinely unaddressed or contradicted across the Brief, Data Dictionary, and Validator?
4. **Likelihood of Concrete Response (15%)**: Is the question practical and objective rather than asking LPDG for modeling advice?

### Candidate Scoring Matrix

| Question Candidate | Correctness (40%) | Fairness (25%) | Ambiguity (20%) | Answerability (15%) | Total Weighted Score (/100) | Selection Status |
|---|---|---|---|---|---|---|
| **Q1: 15-Visit Cap vs Fixed 120-Row Validator Contract** | 38.0 / 40 | 23.5 / 25 | 19.5 / 20 | 14.5 / 15 | **95.5** | **SELECTED (Question 1)** |
| **Q2: Operational Cost Mechanics & Repair Simulation** | 38.0 / 40 | 24.0 / 25 | 18.5 / 20 | 14.0 / 15 | **94.5** | **SELECTED (Question 2)** |
| **Q3: Temporal Cutoff of `engineer_review`** | 34.0 / 40 | 21.0 / 25 | 17.5 / 20 | 13.5 / 15 | **86.0** | Alternate Pool |
| **Q4: Decommissioned Gateway Filtering Rule** | 30.0 / 40 | 18.0 / 25 | 14.0 / 20 | 14.5 / 15 | **76.5** | Alternate Pool |
| **Q5: Intra-Week Rank Order vs Set Evaluation** | 28.0 / 40 | 20.0 / 25 | 15.0 / 20 | 13.0 / 15 | **76.0** | Alternate Pool |

---

## Section 2: Structured Question Cards for Round 1 Submission

---

### Question 1: Submission Row Count vs Sub-15 Operational Visit Cap

#### QUESTION:
> *The Challenge Brief states that "Fifteen visits is a hard limit. Not a goal, not a minimum," indicating that sending fewer than 15 visits is economically preferable if fewer gateways are faulty. However, `validate_submission.py` strictly requires exactly 120 rows (15 rows for every week) and fails on submissions with fewer rows. Should candidates always output exactly 15 ranked rows per week in `predictions.csv` (with score thresholds applied internally by your scoring script), or does the official evaluation pipeline accept submissions with fewer than 15 rows per week when an algorithm determines fewer visits are warranted?*

#### WHY WE SHOULD ASK:
This resolves a direct, high-stakes contradiction between the business logic of the problem and the programmatic validator shipped with the challenge. In real operations, dispatching a technician costs €380, so sending 15 visits when only 7 are broken wastes €3,040 ($8 \times €380$). If candidates must pad `predictions.csv` to 15 rows to satisfy `validate_submission.py`, we need to know whether the scoring script penalizes rows 8–15 as false alarms (€380 wasted each) or uses candidate `score` values / internal cutoffs.

#### WHAT IN THE DOCUMENTS CAUSED THE QUESTION:
- **Challenge Brief p. 3**: *"Fifteen visits is a hard limit. Not a goal, not a minimum."*
- **Challenge Brief p. 2–3**: *"They get there and nothing is wrong: €380, wasted."*
- **`validate_submission.py` Lines 58–63 & 99–102**:
  ```python
  expected_rows = VISITS_PER_WEEK * len(SCORED_WEEKS)
  if len(frame) != expected_rows:
      problems.append(f"expected {expected_rows} rows ({VISITS_PER_WEEK} per week x {len(SCORED_WEEKS)} weeks), found {len(frame)}")
  ```
- **`baseline_3sigma.py` Lines 81–85**:
  ```python
  # If fewer than fifteen gateways flag anything, fill the rest with the gateways that
  # were quietest about it — the cap has to be used in full either way.
  ```

#### WHAT WE SHOULD NOT ASSUME:
- We should **not assume** that padding the list to 15 rows with low-score gateways is cost-free (it could trigger €380 wasted visit penalties).
- We should **not assume** that the validator can be bypassed or that the evaluation script is more permissive than `validate_submission.py`.

#### EXPECTED ANSWER TYPE:
LPDG will clarify whether:
1. `predictions.csv` must always contain 120 rows, but the scoring script uses the `score` column or a top-$k$ cutoff to decide how many visits to actually execute; or
2. The validator enforces 120 rows because the evaluation script simulates sending all 15 technicians every week (as in `baseline_3sigma.py`).

---

### Question 2: Multi-Week Failure Resolution & Evaluation Cost Dynamics

#### QUESTION:
> *Regarding the total operational cost evaluation (€380 per visit, €600 per week for an unaddressed broken gateway): In the evaluation scoring script, when a truly broken gateway is included in a weekly dispatch (rank 1–15), is it modeled as repaired and returned to a healthy state for subsequent weeks (incurring €380 in that week and €0 failure penalty in subsequent weeks), or do multi-week persistent failures require continued re-inspection?*

#### WHY WE SHOULD ASK:
In an 8-week dynamic simulation, a failure in Week 1 left unvisited accumulates $8 \times €600 = €4,800$ in penalties. If visiting the gateway in Week 1 cures the failure for Weeks 2–8, the return on investment of early detection is enormous. Conversely, if the simulation evaluates each week independently without stateful repair feedback, recurring multi-week penalties do not compound dynamically. This distinction fundamentally changes the loss function and optimal decision policy for Data Science and Machine Learning models.

#### WHAT IN THE DOCUMENTS CAUSED THE QUESTION:
- **Challenge Brief p. 3**:
  *"What happens / Cost:*
  *You send someone out: €380*
  *They get there and nothing is wrong: €380, wasted*
  *A broken gateway is left alone for a week: €600*
  *The €600 happens again every week the gateway stays broken. The €380 happens once."*
- **Challenge Brief p. 4 (Track E — ML)**:
  *"A model that beats `baseline_3sigma.py` on total cost. Not on accuracy."*

#### WHAT WE SHOULD NOT ASSUME:
- We should **not assume** the scoring script is a static weekly snapshot rather than a stateful multi-week simulation.
- We should **not assume** that visiting a gateway removes it from future failure queues without knowing how the evaluation environment models repair dynamics.

#### EXPECTED ANSWER TYPE:
LPDG will provide a clear operational statement explaining how the evaluation script handles post-visit state transitions (e.g., whether visited gateways are treated as resolved/repaired in subsequent simulation steps or evaluated against fixed weekly ground truth).
