from typing import Dict, List, Optional


def classify_return(final_return_pct: float, theta_pct: float = 0.0) -> str:
    if final_return_pct >= theta_pct:
        return "UP"
    if final_return_pct <= -theta_pct:
        return "DOWN"
    return "NEUTRAL"


def predict_direction(
    matches: List[Dict],
    n_max: int = 5,
    k_min: int = 2,
    theta_pct: float = 0.0,
) -> Dict[str, Optional[float]]:
    if not matches:
        return {
            "prediction": "NO_PREDICTION",
            "k": 0,
            "confidence": None,
            "dominance_ratio": None,
            "total_weight": 0.0,
        }

    usable = matches[:n_max]
    k = len(usable)

    if k < k_min:
        return {
            "prediction": "NO_PREDICTION",
            "k": k,
            "confidence": None,
            "dominance_ratio": None,
            "total_weight": 0.0,
        }

    scores = {"UP": 0.0, "DOWN": 0.0, "NEUTRAL": 0.0}

    for match in usable:
        sim = float(match["similarity"])
        ret = float(match["outcome"]["final_return_pct"])
        label = classify_return(ret, theta_pct=theta_pct)
        scores[label] += sim

    total_weight = sum(scores.values())
    if total_weight <= 0:
        return {
            "prediction": "NO_PREDICTION",
            "k": k,
            "confidence": None,
            "dominance_ratio": None,
            "total_weight": 0.0,
        }

    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    pred, top_score = ordered[0]
    second_score = ordered[1][1]

    confidence = top_score / total_weight
    dominance_ratio = top_score / (second_score + 1e-12)

    return {
        "prediction": pred,
        "k": k,
        "confidence": confidence,
        "dominance_ratio": dominance_ratio,
        "total_weight": total_weight,
    }
