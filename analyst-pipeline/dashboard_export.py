import pandas as pd
import json

def build_dashboard_json():
    df = pd.read_csv("data/processed/kinetics_processed.csv")
    with open("data/processed/risk_map.geojson") as f:
        risk_map = json.load(f)
    with open("data/processed/action_feed.json") as f:
        action_feed = json.load(f)
    
    high_risk_sites = df[df["wbgt"] > 41.5]["site_lat"].nunique()
    total_assets = df["vehicle_id"].nunique()
    active_risk_score = round(min(100, (df["wbgt"] > 41.5).mean() * 200), 1)
    
    dashboard_data = {
        "active_risk_score": active_risk_score,
        "high_risk_sites": int(high_risk_sites),
        "active_heat_corridors": int(df[df["wbgt"] > 44.5]["site_lat"].round(1).nunique()),
        "assets_exposed": int(total_assets),
        "avg_wbgt": round(df["wbgt"].mean(), 1),
        "pre_cooling_active": int((df["thermal_lag_hours"] > 0).sum() // 60),
        "routes_resequenced_today": int(len(action_feed)),
        "risk_map": risk_map,
        "action_feed": action_feed
    }
    
    with open("data/processed/dashboard_data.json", "w") as f:
        json.dump(dashboard_data, f, indent=2)
    
    print("Dashboard JSON ready: data/processed/dashboard_data.json")
    print(json.dumps({k: v for k, v in dashboard_data.items() if k not in ["risk_map", "action_feed"]}, indent=2))

if __name__ == "__main__":
    build_dashboard_json()