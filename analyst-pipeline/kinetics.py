import pandas as pd
import numpy as np

def thermal_lag(u_value, thermal_mass, delta_t_outside):
    return round((thermal_mass / u_value) * 0.1 * delta_t_outside, 2)

def q10_decay(initial_temp, ambient_temp, door_open_minutes, q10=2.0):
    k = 0.05 * q10
    recovery_temp = ambient_temp - (ambient_temp - initial_temp) * np.exp(-k * door_open_minutes)
    return np.round(recovery_temp, 2)

if __name__ == "__main__":
    df = pd.read_csv("data/processed/wbgt_processed.csv")
    
    df["q10_recovery_temp"] = q10_decay(
        df["reefer_internal_temp"], df["ambient_temp_c"], df["door_open_minutes"]
    )
    
    df["thermal_lag_hours"] = df["ambient_temp_c"].apply(
        lambda t: thermal_lag(u_value=0.35, thermal_mass=150, delta_t_outside=max(t - 30, 0))
    )
    
    df.to_csv("data/processed/kinetics_processed.csv", index=False)
    print("Kinetics calculated. Sample:")
    print(df[["timestamp", "q10_recovery_temp", "thermal_lag_hours"]].head())