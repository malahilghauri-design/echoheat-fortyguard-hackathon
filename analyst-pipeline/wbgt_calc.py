import pandas as pd
import numpy as np

def calc_wbgt(temp_c, rh_percent, solar_wm2, wind_ms):
    e = (rh_percent / 100) * 6.105 * np.exp((17.27 * temp_c) / (237.7 + temp_c))
    wbgt = 0.567 * temp_c + 0.393 * e + 3.94
    wbgt = wbgt + 0.001 * solar_wm2 - 0.05 * wind_ms
    return np.round(wbgt, 2)

def add_operational_metrics(df):
    over_threshold = np.clip(df["ambient_temp_c"] - 44.5, 0, None)
    max_over = max(over_threshold.max(), 0.01)
    
    df["cooling_load_mw"] = np.round(
        57.5 * (over_threshold / max_over) + np.random.normal(0, 5, len(df)), 2
    )
    df["delivery_delay_min"] = np.round(
        20.4 * (over_threshold / max_over) + np.random.normal(0, 3, len(df)), 2
    )
    df["worker_incident_flag"] = (df["ambient_temp_c"] > 41.5).astype(int)
    return df

if __name__ == "__main__":
    df = pd.read_csv("data/raw/mock_telematics.csv")
    df["wbgt"] = calc_wbgt(
        df["ambient_temp_c"], df["relative_humidity"],
        df["solar_radiation_wm2"], df["wind_speed_ms"]
    )
    df = add_operational_metrics(df)
    df.to_csv("data/processed/wbgt_processed.csv", index=False)
    print("WBGT calculated. Sample:")
    print(df[["timestamp", "ambient_temp_c", "wbgt", "cooling_load_mw"]].head())