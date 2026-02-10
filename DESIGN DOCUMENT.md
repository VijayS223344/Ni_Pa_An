📘 DESIGN DOCUMENT
NIFTY Pattern-Based Directional Prediction Engine

Project Type: Research & Evaluation Framework
Primary Use Case: Directional bias for swing trading (option selling)
Status: Working Design (Iterative / Trial-and-Error)
Version: v0.2 (updated for active experimentation)

1. Objective

Build a system that, at any time T, predicts directional bias of the NIFTY index over a fixed forward window using historical pattern similarity, and evaluates multiple model variants using walk-forward validation.

Primary goal is to minimize wrong-direction predictions, while balancing coverage and conditional accuracy.

Important project stance:
- This project is currently exploratory.
- Parameters and logic are not frozen yet.
- The workflow is trial-and-error driven until robust model behavior is established.

2. Trading & Evaluation Horizon (Current Experiment)

Trading style: Swing (days to weeks)

Lookback window (pattern length): 15 bars (default; tunable)

Forward evaluation window: 30 bars (current active setting)
(Used for both historical match outcomes and future validation)

3. Prediction States (Explicit & Non-Overlapping)

Each model at time T must output exactly one of:

UP – positive directional bias

DOWN – negative directional bias

NEUTRAL – sideways / no strong directional bias

NO_PREDICTION – insufficient comparable historical data / low confidence

Important distinctions:

NEUTRAL is a prediction

NO_PREDICTION is abstention

Abstention is acceptable and should be evaluated via coverage metrics, not treated as automatic failure.

4. Direction Definition (Current Default)

Let R be net return over the forward window.

UP if R ≥ +θ

DOWN if R ≤ −θ

NEUTRAL if −θ < R < +θ

Current default:

θ = 0% (baseline default; tunable in experiments)

This definition should apply uniformly to:

historical match outcomes

actual future outcomes during evaluation

5. Similarity Engine (Current)

Input features: Normalized OHLC values

Similarity method: Dynamic Time Warping (DTW)

Normalization: All prices expressed as % change from first bar in each pattern window

Distance → similarity mapping:

similarity = 1 / (1 + distance)

Lower distance = higher similarity.

6. Match Selection Parameters (Experiment Defaults)

N_max = 5
Maximum number of historical matches considered

k_min = 2
Minimum number of valid matches required to make a prediction

Similarity threshold:
- Optional and tunable.
- If enabled, retain only matches with similarity ≥ threshold.
- Threshold is not frozen yet.

7. Model Variants (Ablation Study)

All models share identical logic and core parameters except filters.

Model A: Price action only

Model B: Price action + ATR filter

Model C: Price action + Regime filter

Model D: Price action + ATR + Regime filter

Model-specific tuning is allowed during experimentation, but all changes must be logged.

8. Volatility Filter (ATR) — Baseline Proposal

Metric: ATR expressed as % of price (ATR%)

Baseline ATR window: 14 or 20 bars (quant standard baseline; tunable)

For each pattern window:

Compute average ATR% over lookback

Baseline filter rule:

|ATR_hist − ATR_current| / ATR_current ≤ ATR_threshold

Baseline threshold suggestion for initial testing:
- ATR_threshold in the 15%–30% range (start at 20%).

ATR is used only as a filter, never as a directional signal.

9. Regime Filter — Baseline Proposal

Each bar is assigned a regime label.

Baseline regime dimensions:

Trend state: up / down / flat
(Example baseline: sign and magnitude band of rolling slope / moving-average drift)

Volatility state: low / normal / high
(Example baseline: ATR% or realized-vol percentile buckets)

Filter rule:

Historical match is eligible only if regime matches current regime

Regime definitions are tunable during experimentation and should be versioned in logs.

10. Match Selection Logic (Per Model, Per Time T)

Use only data ≤ T

Generate all historical candidate windows

Apply model-specific filters (ATR, regime, both, or none)

Rank remaining candidates by similarity

Optionally apply similarity threshold

Retain up to N_max matches

Let k = number of retained matches

Decision:

If k < k_min → NO_PREDICTION

Else → proceed to direction inference

11. Direction Inference Logic

For k ≥ k_min:

Assign each match a weight based on similarity

Compute weighted scores:

score_UP

score_DOWN

score_NEUTRAL

Predicted direction = argmax(score)

Optional diagnostics (logged):

k

total weight

dominance ratio (confidence proxy)

12. Walk-Forward Evaluation Framework

Evaluation method:

Walk-forward / rolling-origin validation

Strictly time-respecting (no future leakage)

At each evaluation date T, for each model:

Freeze data ≤ T

Generate prediction

Observe actual outcome over forward window

Log:

prediction

actual outcome

correctness

wrong-way flag

k value

confidence

13. Model Evaluation Metrics (Priority Order)

Models are compared using:

Wrong-way rate
(Predicted UP → actual DOWN, or vice versa)

Conditional accuracy
Accuracy when model makes a prediction

Coverage
Fraction of times model predicts (not NO_PREDICTION)

Diagnostic analysis:

performance vs k

performance vs confidence

stability across time slices

Raw hit rate alone is insufficient.

14. Interpretation Rules (Current)

Abstention is not failure

Lower wrong-way calls are prioritized over higher trade frequency

Models should be judged after sufficiently broad walk-forward runs, not isolated periods

No ad-hoc undocumented parameter changes mid-run
(Changes are allowed if intentionally versioned as a new experiment config)

15. Explicitly Out of Scope (For This Project)

Option strike selection

Position sizing

Expiry selection

Capital allocation

Execution / slippage modeling

These remain intentionally excluded to keep research clean.

16. Data Source (Current)

Primary dataset file for local runs:

nifty_data_recent.csv

Legacy datasets may be retained for archival comparison but should not be the default input.

17. Execution Checklist (Living Section)

[ ] Finalize baseline parameter ranges for sweep runs
[ ] Implement ATR filter module
[ ] Implement regime filter module
[ ] Add configurable similarity threshold switch
[ ] Ensure predictor uses consistent θ logic
[ ] Run full walk-forward evaluation across all model variants
[ ] Compare variants on wrong-way rate, conditional accuracy, and coverage
[ ] Select top candidates for live shadow testing
[ ] Freeze v1 experiment spec once robust behavior is observed

18. Change Control Rule (Iterative Phase)

During the current exploratory phase:
- Changes to definitions, parameters, logic, or evaluation rules are allowed.
- Every such change must be logged with an experiment version tag.

Once v1 is frozen:
- Any further change requires a new experiment version and document update.

End of Working Design Document

Program Design
┌────────────────────────┐
│    Historical Data     │
│      (OHLC)            │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│ Walk Forward Evaluator │
│   (owns time T)        │
│                        │
│ - choose T             │
│ - slice data ≤ T       │
│ - extract current bars │
└───────────┬────────────┘
            │
            ▼
┌──────────────────────────────────────────┐
│        Price Action Matcher              │
│            (matcher.py)                  │
│                                          │
│  Same logic, different model configs     │
│                                          │
│  Model A: No Filter                      │
│  Model B: ATR Filter                     │
│  Model C: Regime Filter                  │
│  Model D: ATR + Regime Filter            │
│                                          │
│  For each model:                         │
│   - scan historical windows              │
│   - apply filters (if enabled)           │
│   - compute DTW similarity               │
│   - attach future outcome                │
│   - rank matches                         │
└───────────┬───────────────┬──────────────┘
            │               │
            │ (per model)   │
            ▼               ▼
   ┌────────────────┐   ┌─────────────────┐
   │  Matches (A)   │   │  Matches (B,C,D)│
   │  No Filter     │   │  Filtered       │
   └────────┬───────┘   └────────┬────────┘
            │                    │
            └──────────┬─────────┘
                       ▼
               ┌─────────────────┐
               │   Predictor     │
               │ (predictor.py)  │
               │                 │
               │ - take top N    │
               │ - enforce k_min │
               │ - weight votes  │
               │ - decide bias   │
               └────────┬────────┘
                        ▼
        ┌────────────────────────────────┐
        │ UP / DOWN / NEUTRAL /          │
        │ NO_PREDICTION                  │
        │ + confidence + k               │
        └────────────────────────────────┘
