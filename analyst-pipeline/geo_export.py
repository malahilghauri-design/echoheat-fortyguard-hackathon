import pandas as pd
import json

def to_geojson(df):
    features = []
    for _, row in df.iterrows():
        risk = "high" if row["wbgt"] > 41.5 else ("moderate" if row["wbgt"] > 35 else "low")
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [row["site_lon"], row["site_lat"]]
            },
            "properties": {
                "timestamp": str(row["timestamp"]),
                "wbgt": row["wbgt"],
                "risk_level": risk
            }
        })
    return {"type": "FeatureCollection", "features": features}

if __name__ == "__main__":
    df = pd.read_csv("data/processed/kinetics_processed.csv")
    geojson = to_geojson(df)
    with open("data/processed/risk_map.geojson", "w") as f:
        json.dump(geojson, f, indent=2)
    print("GeoJSON exported:", len(geojson["features"]), "points")