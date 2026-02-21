# ps2/core/fusion.py
import numpy as np

def classify_frame(i, flows, ssims, blurs, window=20):
    n = len(flows)

    # global stats
    mean_flow = np.mean(flows)
    std_flow = np.std(flows) + 1e-6

    # relative jump
    if i > 0:
        jump = flows[i] - flows[i-1]
    else:
        jump = 0

    # ----- DROP DETECTION -----
    if (
        flows[i] > mean_flow + 1.5 * std_flow and
        ssims[i] < 0.85 and
        jump > std_flow * 0.5
    ):
        confidence = min(1.0, (flows[i] - mean_flow) / (3 * std_flow))
        return "DROP", float(confidence)

    # ----- MERGE DETECTION -----
    if (
        flows[i] < mean_flow * 0.3 and
        ssims[i] > 0.99
    ):
        return "MERGE", 0.9

    return "NORMAL", 0.0