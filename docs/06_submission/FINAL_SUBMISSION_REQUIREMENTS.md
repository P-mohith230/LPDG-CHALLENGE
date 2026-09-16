# Master Submission Requirements & Discrepancy Reconciliation
**NEXORA 2026 / LPDG Innovation Hub Selection Challenge**  
*Comprehensive Checklists, Channel Protocols, and Institutional Rules*

---

## 1. Source Conflict & Reconciliation Table

A critical discrepancy exists between the institutional submission email from RGMCET CSEDS Department and the official LPDG Challenge Brief/FAQ regarding deadlines and submission channels:

| Dimension | Source A: Institutional Submission Email (NEXORA 2026) | Source B: LPDG Challenge Brief & FAQ (Tarun Gupta) | Nature of Discrepancy | Practical Safe Interpretation |
|---|---|---|---|---|
| **Submission Deadline** | **Wednesday, 16th September 2026, 20:00 IST (Night 8:00 IST)** | **Wednesday, 16th September 2026, 23:59 IST** | Institutional deadline is **almost 4 hours earlier** than LPDG deadline. | **CRITICAL: Freeze all work and submit before 20:00 IST on 16 September 2026.** Submitting at 21:00 IST satisfies LPDG but will be marked late/rejected by the RGMCET Google Form. |
| **Submission Method / Portal** | Google Form: `https://forms.gle/qHZqsRRPGWf8ja5S6` | Email reply to the original invitation email | Different submission channels. | **Dual Submission**: Submit the Google Form first before 20:00 IST, and reply to the official LPDG invitation email with the public GitHub repo link. |
| **Email Account Allowed** | Strictly official email: `xxxxxx@rgmcet.edu.in` (`23091a3286@rgmcet.edu.in`). Personal emails forbidden. | "On your own account... reply to the invitation email" | Institutional form requires RGMCET institutional GSuite authentication. | Use `23091a3286@rgmcet.edu.in` for the Google Form submission and all official correspondence. |
| **Duplicate Submissions** | "First submission will only be considered. Remaining will be summarily rejected." | Brief commits to nothing regarding revisions before 23:59. | Institutional portal penalizes resubmission. | **Zero-Defect Single Submit**: Rehearse everything locally before making the single official Google Form submission. |
| **Evaluation Venue** | In-person at RGMCET campus on **18th September 2026, 9:00 AM onwards**. | "If we invite you to a live session... format and time come by email." | Offline physical presentation on campus. | Prepare the submission to run fully offline on the personal laptop for the in-person panel. |

---

## 2. Exhaustive Submission Requirements Checklist

### A. Repository Configuration & Git Hygiene
- [ ] **Public Visibility**: The repository must be flipped from PRIVATE to PUBLIC before 20:00 IST on 16 September 2026. Inaccessible links will not be scored.
- [ ] **No Challenge Data in Git**: Verify that `data/` is strictly excluded in `.gitignore`. The 104 MB dataset must not appear in commit history.
- [ ] **No Secret Tokens in History**: Check git history for API keys, passwords, or personal credentials.
- [ ] **Granular Commit History**: Verify normal, iterative chronological commits (no single monolithic commit).

### B. Mandatory File Deliverables in Repository
1. `predictions.csv`:
   - [ ] Exactly 120 rows (15 rows for each of the 8 scored weeks).
   - [ ] Verified with `python validate_submission.py predictions.csv` (exit code 0).
   - [ ] Columns: `week_start`, `rank`, `gateway_id`, `score`, `reason`.
   - [ ] Deterministic ranking order.
2. `README.md`:
   - [ ] Setup and execution instructions clear enough for a stranger to run without asking.
   - [ ] Link to the 6 to 8-minute screen recording.
   - [ ] Documentation of visualization plots with proper descriptions (institutional requirement).
   - [ ] Description of project architecture, data flow, and operational decisions.
3. `DECISIONS.md`:
   - [ ] Five explicit choices, each documenting: what was chosen, what alternative was considered, and why it was rejected.
   - [ ] Exactly one choice stating and justifying the chosen Part 2 area (e.g. Data Science vs. Machine Learning).
   - [ ] Limitations section ("What it cannot do") describing 3 real, costed weaknesses and what another two weeks would fix.
4. `AI-USAGE.md`:
   - [ ] Disclosure of what AI coding assistants were used for.
   - [ ] At least one concrete error the AI made that the candidate caught and corrected (e.g. silent ID merge failure or encoding crash).
5. `<Registration_Id.pdf>` (Candidate Resume):
   - [ ] Candidate resume placed directly in the home/root directory named `23091a3286.pdf` (exact naming convention from submission instructions).
6. Model Artifacts (`.pkl` / `.joblib`):
   - [ ] Serialized model weights and companion parameter JSON included in the repository under `models/`. File size $<2	ext{ MB}$.

---

## 3. Execution & Verification Commands

### Final Smoke-Test Protocol (Run on a Clean Machine / Directory):
```bash
# 1. Clone your public repository
git clone https://github.com/P-mohith230/LPDG-CHALLENGE.git test_submission
cd test_submission

# 2. Drop challenge data folder
cp -r /path/to/data ./data

# 3. Execute the single command
./run.sh   # or: docker compose up

# 4. Verify output validity
python validate_submission.py predictions.csv
```

---

## 4. Institutional Google Form Submission Details
- **Form URL**: `https://forms.gle/qHZqsRRPGWf8ja5S6`
- **Authenticated Account**: `23091a3286@rgmcet.edu.in`
- **Submission Target Time**: Wednesday 16 September 2026, 18:00 IST (2 hours ahead of the 20:00 IST hard cutoff).
