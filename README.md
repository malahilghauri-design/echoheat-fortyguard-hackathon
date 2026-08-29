# =====================================================================
# ECHOHEAT DATA ANALYST & KINETICS SERVICE
# File: backend/app/services/pipeline.py
# =====================================================================

import os
import math
import requests
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
from dataclasses import dataclass
from scipy import stats

# ---------------------------------------------------------------------
# DATA SCHEMAS
# ---------------------------------------------------------------------
@dataclass
class MicroclimatePoint:
    lat: float
    lon: float
    timestamp: str
    fortyguard_2m_temp_c: float
    ambient_macro_temp_c: float
    relative_humidity: float
    solar_radiation_w_m2: float
    wind_speed_m_s: float


# ---------------------------------------------------------------------
# 1. FORTYGUARD 2M INGESTION CLIENT
# ---------------------------------------------------------------------
class FortyGuardDataClient:
    """Ingests live 2m street-level thermal data from FortyGuard REST API."""
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.fortyguard.com/v1"):
        self.api_key = api_key or os.getenv("FORTYGUARD_API_KEY")
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"} if self.api_key else {}

    def get_hyperlocal_temperature(self, lat: float, lon: float) -> float:
        if self.api_key:
            endpoint = f"{self.base_url}/temperature/2m"
            params = {"lat": lat, "lon": lon}
            try:
                response = requests.get(endpoint, headers=self.headers, params=params, timeout=3.0)
                if response.status_code == 200:
                    data = response.json()
                    return float(data.get("temp_2m_c", data.get("temperature", 44.5)))
            except Exception:
                pass
        return self._generate_synthetic_heat_island(lat, lon)

    def _generate_synthetic_heat_island(self, lat: float, lon: float) -> float:
        base_ambient = 37.0
        spatial_noise = np.sin(lat * 100) * np.cos(lon * 100) * 3.5
        heat_island_spike = 5.2 + abs(spatial_noise)
        return round(base_ambient + heat_island_spike, 2)


# ---------------------------------------------------------------------
# 2. ENVIRONMENTAL DATA FUSION
# ---------------------------------------------------------------------
class EnvironmentalDataFusion:
    """Fuses FortyGuard 2m data with Open-Meteo atmospheric variables."""
    def __init__(self, fortyguard_client: FortyGuardDataClient):
        self.fg_client = fortyguard_client

    def fetch_fused_microclimate(self, lat: float, lon: float) -> MicroclimatePoint:
        fg_temp = self.fg_client.get_hyperlocal_temperature(lat, lon)

        open_meteo_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,"
            f"direct_normal_irradiance,wind_speed_10m"
        )
        try:
            res = requests.get(open_meteo_url, timeout=3.0).json()
            current = res.get("current", {})
            macro_temp = float(current.get("temperature_2m", 37.0))
            humidity = float(current.get("relative_humidity_2m", 45.0))
            solar_rad = float(current.get("direct_normal_irradiance", 850.0))
            wind_speed = float(current.get("wind_speed_10m", 2.1))
        except Exception:
            macro_temp = 37.0
            humidity = 48.0
            solar_rad = 880.0
            wind_speed = 1.8

        return MicroclimatePoint(
            lat=lat,
            lon=lon,
            timestamp=pd.Timestamp.utcnow().isoformat(),
            fortyguard_2m_temp_c=fg_temp,
            ambient_macro_temp_c=macro_temp,
            relative_humidity=humidity,
            solar_radiation_w_m2=solar_rad,
            wind_speed_m_s=wind_speed
        )


# ---------------------------------------------------------------------
# 3. CORE THERMAL KINETICS & PHYSICS ENGINE
# ---------------------------------------------------------------------
class ThermalKineticsEngine:
    """Computes physics kinetics: WBGT, thermal lag, Q10 spoilage, and reefer excursions."""

    @staticmethod
    def calculate_micro_wbgt(temp_db: float, rh: float, solar_rad: float, wind_speed: float) -> float:
        t = temp_db
        t_nw = (t * math.atan(0.151977 * math.sqrt(rh + 8.313659)) +
                math.atan(t + rh) - math.atan(rh - 1.676331) +
                0.00391838 * (rh ** 1.5) * math.atan(0.023101 * rh) - 4.686035)

        t_g = temp_db + (0.014 * solar_rad) - (0.5 * max(wind_speed, 0.5))
        wbgt = (0.7 * t_nw) + (0.2 * t_g) + (0.1 * temp_db)
        return round(wbgt, 2)

    @staticmethod
    def calculate_structural_thermal_lag(thickness_m: float, thermal_diffusivity: float, period_hours: float = 24.0) -> float:
        period_seconds = period_hours * 3600.0
        lag_seconds = (thickness_m / 2.0) * math.sqrt(period_seconds / (math.pi * thermal_diffusivity))
        return round(lag_seconds / 60.0, 1)

    @staticmethod
    def calculate_q10_spoilage_rate(current_temp: float, target_temp: float, q10_coefficient: float = 2.2) -> float:
        delta_t = max(0.0, current_temp - target_temp)
        decay_multiplier = math.pow(q10_coefficient, (delta_t / 10.0))
        return round(decay_multiplier, 2)

    @classmethod
    def estimate_reefer_excursion(cls, fortyguard_temp: float, door_open_minutes: int, insulation_u_val: float = 0.35) -> float:
        temp_gradient = max(0.0, fortyguard_temp - (-18.0))
        temp_rise = (temp_gradient * insulation_u_val * (door_open_minutes / 10.0))
        return round(temp_rise, 2)


# ---------------------------------------------------------------------
# 4. MASTER DATA ANALYST PIPELINE ORCHESTRATOR
# ---------------------------------------------------------------------
class DataAnalystPipeline:
    """Master pipeline orchestrating 2m data ingestion, physics, and telemetry packaging."""
    def __init__(self, fg_api_key: Optional[str] = None):
        self.fg_client = FortyGuardDataClient(api_key=fg_api_key)
        self.fusion = EnvironmentalDataFusion(self.fg_client)
        self.kinetics = ThermalKineticsEngine()

    def process_asset(self, asset_id: str, vertical: str, lat: float, lon: float, telemetry_kwargs: Dict[str, Any]) -> Dict[str, Any]:
        env = self.fusion.fetch_fused_microclimate(lat, lon)
        wbgt = self.kinetics.calculate_micro_wbgt(
            env.fortyguard_2m_temp_c, env.relative_humidity, env.solar_radiation_w_m2, env.wind_speed_m_s
        )
        temp_delta = round(env.fortyguard_2m_temp_c - env.ambient_macro_temp_c, 2)

        if vertical == "cold_chain":
            curr_reefer = telemetry_kwargs.get("current_reefer_temp_c", -14.2)
            target_cargo = telemetry_kwargs.get("target_cargo_temp_c", -18.0)
            mins_to_stop = telemetry_kwargs.get("minutes_to_next_stop", 35)

            t_lag = self.kinetics.calculate_structural_thermal_lag(thickness_m=0.10, thermal_diffusivity=1.2e-7)
            q10 = self.kinetics.calculate_q10_spoilage_rate(curr_reefer, target_cargo)
            excursion = self.kinetics.estimate_reefer_excursion(env.fortyguard_2m_temp_c, door_open_minutes=15)

            return {
                "site_or_asset_id": asset_id,
                "vertical": vertical,
                "location": {"lat": lat, "lon": lon},
                "metrics": {
                    "fortyguard_2m_temp_c": env.fortyguard_2m_temp_c,
                    "macro_temp_c": env.ambient_macro_temp_c,
                    "temp_delta_c": temp_delta,
                    "wbgt_c": wbgt,
                    "relative_humidity": env.relative_humidity,
                    "solar_radiation_w_m2": env.solar_radiation_w_m2,
                    "thermal_lag_minutes": t_lag,
                    "q10_decay_multiplier": q10,
                    "projected_door_open_excursion_c": excursion,
                    "current_reefer_temp_c": curr_reefer,
                    "target_cargo_temp_c": target_cargo,
                    "minutes_to_next_stop": mins_to_stop
                }
            }

        elif vertical == "workforce_safety":
            osha_risk = "Low"
            if wbgt >= 32.2:
                osha_risk = "Extreme"
            elif wbgt >= 30.0:
                osha_risk = "High"
            elif wbgt >= 26.0:
                osha_risk = "Moderate"

            return {
                "site_or_asset_id": asset_id,
                "vertical": vertical,
                "location": {"lat": lat, "lon": lon},
                "metrics": {
                    "fortyguard_2m_temp_c": env.fortyguard_2m_temp_c,
                    "macro_temp_c": env.ambient_macro_temp_c,
                    "temp_delta_c": temp_delta,
                    "wbgt_c": wbgt,
                    "relative_humidity": env.relative_humidity,
                    "solar_flux_w_m2": env.solar_radiation_w_m2,
                    "osha_heat_risk_level": osha_risk,
                    "shift_elapsed_hours": telemetry_kwargs.get("shift_elapsed_hours", 4.5)
                }
            }

        elif vertical == "commercial_facility":
            t_lag = self.kinetics.calculate_structural_thermal_lag(thickness_m=0.30, thermal_diffusivity=8.0e-7)
            load_spike = 57.5 if env.fortyguard_2m_temp_c > 44.5 else 12.0

            return {
                "site_or_asset_id": asset_id,
                "vertical": vertical,
                "location": {"lat": lat, "lon": lon},
                "metrics": {
                    "fortyguard_2m_temp_c": env.fortyguard_2m_temp_c,
                    "macro_temp_c": env.ambient_macro_temp_c,
                    "temp_delta_c": temp_delta,
                    "thermal_lag_minutes": t_lag,
                    "projected_hvac_load_spike_mw": load_spike,
                    "current_chiller_setpoint_c": telemetry_kwargs.get("chiller_setpoint_c", 6.5),
                    "peak_tariff_window_starts_in_hrs": telemetry_kwargs.get("peak_starts_in_hrs", 2.0)
                }
            }
        else:
            raise ValueError(f"Unknown vertical: {vertical}")
