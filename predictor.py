
from typing import List, Dict, Optional


def predict_direction(matches: List[Dict], n_max: int = 5, k_min: int = 2):
    if not matches:
        return {"prediction": "NO_PREDICTION", "k": 0, "confidence": None}

    usable = matches[:n_max]
    k = len(usable)

    if k < k_min:
        return {"prediction": "NO_PREDICTION", "k": k, "confidence": None}

    up = down = neutral = 0.0

    for m in usable:
        sim = m["similarity"]
        ret = m["outcome"]["final_return_pct"]
        if ret > 0:
            up += sim
        elif ret < 0:
            down += sim
        else:
            neutral += sim

    total = up + down + neutral
    if total == 0:
        return {"prediction": "NO_PREDICTION", "k": k, "confidence": None}

    scores = {"UP": up, "DOWN": down, "NEUTRAL": neutral}
    pred = max(scores, key=scores.get)
    return {"prediction": pred, "k": k, "confidence": scores[pred] / total}
