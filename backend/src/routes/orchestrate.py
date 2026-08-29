from fastapi import APIRouter, HTTPException
from app.schemas.contracts import OrchestrationRequest
from app.services.pipeline import DataAnalystPipeline
from app.services.gemini_agent import EchoHeatGeminiAgent, SystemExecutionDispatcher

router = APIRouter()
pipeline = DataAnalystPipeline()
agent = EchoHeatGeminiAgent(model="gemini-3.6-flash")
dispatcher = SystemExecutionDispatcher()

@router.post("/orchestrate")
async def orchestrate_thermal_event(req: OrchestrationRequest):
    try:
        # 1. Ingest FortyGuard 2m + Open-Meteo & Run Kinetics
        telemetry_payload = pipeline.process_asset(
            asset_id=req.asset_id,
            vertical=req.vertical,
            lat=req.lat,
            lon=req.lon,
            telemetry_kwargs=req.telemetry
        )

        # 2. Run Gemini 3.6 Flash Agent Decision
        decision = agent.evaluate_telemetry(telemetry_payload)

        # 3. Trigger 2-Way System Writeback
        writeback = dispatcher.execute(decision)

        return {
            "success": True,
            "telemetry": telemetry_payload,
            "decision": decision.model_dump(),
            "writeback": writeback
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
