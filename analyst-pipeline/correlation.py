import pandas as pd
import numpy as np
from scipy import stats

def find_threshold(df, temp_col, metric_col, step=0.5):
    thresholds = np.arange(df[temp_col].min(), df[temp_col].max(), step)
    best_r, best_p, best_t = 0, 1, None
    
    for t in thresholds:
        subset = df[df[temp_col] > t]
        if len(subset) > 10 and subset[metric_col].std() > 0:
            r, p = stats.pearsonr(subset[temp_col], subset[metric_col])
            if abs(r) > abs(best_r):
                best_r, best_p, best_t = r, p, t
    return best_t, best_r, best_p

if __name__ == "__main__":
    df = pd.read_csv("data/processed/kinetics_processed.csv")
    
    results = {}
    for metric in ["cooling_load_mw", "delivery_delay_min", "worker_incident_flag"]:
        t, r, p = find_threshold(df, "ambient_temp_c", metric)
        results[metric] = {"threshold_c": t, "r": round(r, 3), "p_value": round(p, 5)}
        print(f"{metric}: threshold={t}°C, r={round(r,3)}, p={round(p,5)}")
    
    pd.DataFrame(results).T.to_csv("data/processed/correlation_results.csv")
    print("\nSaved to data/processed/correlation_results.csv")