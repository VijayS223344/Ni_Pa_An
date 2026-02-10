📘 DESIGN DOCUMENT
NIFTY Pattern-Based Directional Prediction Engine

Project Type: Research & Evaluation Framework
Primary Use Case: Directional bias for swing trading (option selling)
Status: Governing Design (Initial Version)

1. Objective (Frozen)

Build a system that, at any time T, predicts directional bias of the NIFTY index over a fixed forward window using historical pattern similarity, and evaluates multiple model variants using walk-forward validation.

Primary goal is to minimize wrong-direction predictions, not maximize trade frequency or return magnitude.

2. Trading & Evaluation Horizon (Frozen)

Trading style: Swing (days to weeks)

Lookback window (pattern length): 15 bars

Forward evaluation window: 15 bars
(Used for both historical outcomes and future validation)

3. Prediction States (Explicit & Non-Overlapping)

Each model at time T must output exactly one of:

UP – positive directional bias

DOWN – negative directional bias

NEUTRAL – sideways / no strong directional bias

NO_PREDICTION – insufficient comparable historical data

Important distinctions:

NEUTRAL is a prediction

NO_PREDICTION is abstention

Abstention is acceptable and not penalized by itself

4. Direction Definition (Frozen)

Let R be net return over the forward window.

UP if R ≥ +θ

DOWN if R ≤ −θ

NEUTRAL if −θ < R < +θ

Initial value:

θ = 0% (can be revised only via a new experiment)

This definition applies uniformly to:

historical match outcomes

actual future outcomes during evaluation

5. Similarity Engine (Frozen)

Input features: Normalized OHLC values

Similarity method: Dynamic Time Warping (DTW)

Normalization: All prices expressed as % change from first bar

Distance → similarity mapping:

similarity = 1 / (1 + distance)


Lower distance = higher similarity.

6. Match Selection Parameters (Frozen)

N_max = 5
Maximum number of historical matches considered

k_min = 2
Minimum number of valid matches required to make a prediction

Similarity threshold:
Fixed minimum similarity required for a match to be considered
(Exact value frozen per experiment)

7. Model Variants (Ablation Study)

All models share identical logic and parameters except filters.

Model A: Price action only

Model B: Price action + ATR filter

Model C: Price action + Regime filter

Model D: Price action + ATR + Regime filter

No model-specific tuning is allowed.

8. Volatility Filter (ATR)

Metric: ATR expressed as % of price (ATR%)

ATR window: ≥ lookback (e.g. 20 bars)

For each pattern window:

Compute average ATR% over lookback

Filter rule:

|ATR_hist − ATR_current| / ATR_current ≤ ATR_threshold


ATR is used only as a filter, never as a directional signal.

9. Regime Filter

Each bar is assigned a regime label.

Minimum regime dimensions:

Trend state: up / down / flat

Volatility state: low / normal / high

Filter rule:

Historical match is eligible only if regime matches current regime

(Regime definition is frozen per experiment.)

10. Match Selection Logic (Per Model, Per Time T)

Use only data ≤ T

Generate all historical candidate windows

Apply model-specific filters (ATR, regime, or none)

Rank remaining candidates by similarity

Apply similarity threshold

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

Optional diagnostics (logged, not decision-critical):

k

total weight

dominance ratio (confidence proxy)

12. Walk-Forward Evaluation Framework (Frozen)
Evaluation Method

Walk-forward / rolling-origin validation

Strictly time-respecting (no future leakage)

At Each Evaluation Date T

For each model:

Freeze data ≤ T

Generate prediction

Observe actual outcome over forward window

Log:

prediction

actual outcome

correctness

wrong-way flag

k value

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

14. Interpretation Rules (Frozen)

Abstention is not failure

Predictions with fewer wrong-way calls is preferred

Models are judged only after full walk-forward completion

No mid-run parameter changes allowed

15. Explicitly Out of Scope (For This Project)

Option strike selection

Position sizing

Expiry selection

Capital allocation

Execution / slippage modeling

These are intentionally excluded to keep research clean.

16. Execution Checklist (Living Section)
[x] Freeze similarity threshold
[ ] Finalize ATR threshold
[ ] Finalize regime definition
[ ] Implement filter modules
[ ] Implement predictor logic
[ ] Implement walk-forward engine
[ ] Run full historical evaluation
[ ] Compare model variants
[ ] Select candidates for live shadow testing

17. Change Control Rule (Important)

Any change to:

definitions

parameters

logic

evaluation rules

→ requires a new experiment and an updated design document version.

End of Governing Design Document

Program Desigm
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
