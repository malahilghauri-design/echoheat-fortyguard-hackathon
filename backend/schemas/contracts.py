from typing import Dict, Any, Literal
from pydantic import BaseModel, Field

class AgentDecisionOutput(BaseModel):
    decision_id: str
    action_type: Literal[
        "TRIGGER_REEFER_PRECOOL",
        "RESCHEDULE_ROUTE_STOP",
        "DISPATCH_OSHA_BREAK",
        "ADJUST_HVAC_PRECOOL_SETPOINT",
        "NO_ACTION_REQUIRED"
    ]
    status: Literal["READY_FOR_EXECUTION", "AUTO_EXECUTED", "FLAGGED_FOR_REVIEW"]
    system_target: Literal["SAMSARA_API_V1", "PROCORE_SAFETY_API", "BACNET_BMS_GATEWAY", "LOCAL_STAGING"]
    tool_payload: Dict[str, Any]
    executive_brief: str
    estimated_loss_prevented_usd: float

class OrchestrationRequest(BaseModel):
    asset_id: str
    vertical: Literal["cold_chain", "workforce_safety", "commercial_facility"]
    lat: float
    lon: float
    telemetry: Dict[str, Any] = {}
