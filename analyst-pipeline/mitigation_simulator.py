import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta

def simulate_actions(df):
    actions = []
    high_risk = df[df["wbgt"] > 41.5].copy()
    
    action_templates = [
        ("pre-cooling initiated, target 22°C", "completed"),
        ("re-routed via thermal corridor", "in progress"),
        ("backup unit dispatched", "completed"),
        ("WBGT threshold exceeded, rest interval triggered", "completed"),
        ("pre-cooling cycle complete", "completed"),
        ("fleet reroute: units shifted to safe corridor", "completed"),
    ]
    
    sample = high_risk.sample(min(15, len(high_risk)), random_state=1) if len(high_risk) > 0 else df.sample(15, random_state=1)
    
    for i, (_, row) in enumerate(sample.iterrows()):
        template, status = action_templates[i % len(action_templates)]
        actions.append({
            "unit_id": row["vehicle_id"],
            "action": f"{row['vehicle_id']} {template}",
            "status": status,
            "wbgt_at_trigger": row["wbgt"],
            "timestamp": str(row["timestamp"])
        })
    
    return actions

if __name__ == "__main__":
    df = pd.read_csv("data/processed/kinetics_processed.csv")
    actions = simulate_actions(df)
    with open("data/processed/action_feed.json", "w") as f:
        json.dump(actions, f, indent=2)
    print(f"Generated {len(actions)} simulated writeback actions")
    print(json.dumps(actions[0], indent=2))