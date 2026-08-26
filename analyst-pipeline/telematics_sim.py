import pandas as pd
import numpy as np

def generate_mock_data(n_hours=720, seed=42):
    np.random.seed(seed)
    
    timestamps = pd.date_range("2026-06-01", periods=n_hours, freq="h")
    hour_of_day = timestamps.hour.values
    
    base_temp = 32 + 12 * np.clip(np.sin((hour_of_day - 6) * np.pi / 12), 0, None)
    noise = np.random.normal(0, 1.5, n_hours)
    ambient_temp = base_temp + noise
    
    df = pd.DataFrame({
        "timestamp": timestamps,
        "vehicle_id": np.random.choice(["V101", "V102", "V103"], n_hours),
        "site_lat": np.random.uniform(33.3, 33.6, n_hours),
        "site_lon": np.random.uniform(-112.2, -111.9, n_hours),
        "ambient_temp_c": np.round(ambient_temp, 2),
        "relative_humidity": np.round(np.random.uniform(15, 45, n_hours), 1),
        "solar_radiation_wm2": np.round(np.random.uniform(200, 950, n_hours), 1),
        "wind_speed_ms": np.round(np.random.uniform(0.5, 6, n_hours), 2),
        "reefer_internal_temp": np.round(np.random.normal(4, 1.5, n_hours), 2),
        "door_open_minutes": np.random.poisson(8, n_hours),
    })
    return df

if __name__ == "__main__":
    df = generate_mock_data()
    df.to_csv("data/raw/mock_telematics.csv", index=False)
    print("Mock data saved:", df.shape)
    print(df.head())