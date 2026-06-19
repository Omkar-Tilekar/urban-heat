import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from app.services.gis_service import GISService
from app.services.ml_service import MLService

app = FastAPI(
    title="ISRO Urban Heat Mitigation Platform API",
    description="Backend API for GIS, Hotspot Clustering, and ML Simulations",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this. For hackathon, allow all.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
gis_service = GISService()
ml_service = MLService(gis_service)

# Request schemas
class SimulationRequest(BaseModel):
    cell_ids: List[int]
    intervention_type: str
    region: str = "india"

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "ISRO UHI Engine"}

@app.get("/api/map/stats")
def get_map_stats(region: str = "india"):
    try:
        stats = gis_service.get_summary_stats(region)
        if not stats:
            raise HTTPException(status_code=404, detail=f"Stats for region '{region}' not found")
            
        model = ml_service.models.get(region, list(ml_service.models.values())[0])
        # Include baseline model details
        stats["model_params"] = {
            "ndvi_weight": round(float(model.coef_[0]), 2),
            "built_up_weight": round(float(model.coef_[1]), 2),
            "intercept": round(float(model.intercept_), 2)
        }
        return stats
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/map/grid")
def get_map_grid(region: str = "india"):
    try:
        return gis_service.get_grid(region)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/map/hotspots")
def get_map_hotspots(region: str = "india", eps: Optional[float] = None, min_samples: int = 4, percentile: float = 85.0):
    try:
        return ml_service.detect_hotspots(region=region, eps_deg=eps, min_samples=min_samples, lst_percentile=percentile)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

import numpy as np
from datetime import datetime
from app.db import get_db

@app.post("/api/simulate")
def run_simulation(req: SimulationRequest):
    try:
        if not req.cell_ids:
            raise HTTPException(status_code=400, detail="cell_ids list cannot be empty")
        
        simulated_cells = ml_service.simulate_intervention(
            cell_ids=req.cell_ids,
            intervention_type=req.intervention_type,
            region=req.region
        )
        
        # Log simulation run to MongoDB if available
        db = get_db()
        if db is not None:
            try:
                db.simulations.insert_one({
                    "region": req.region,
                    "intervention": req.intervention_type,
                    "cells_affected_count": len(simulated_cells),
                    "avg_temp_drop": round(float(np.mean([c["lst_diff"] for c in simulated_cells])), 2) if simulated_cells else 0.0,
                    "timestamp": datetime.utcnow()
                })
                print(f"Logged simulation run for region '{req.region}' to MongoDB.")
            except Exception as e:
                print(f"Could not log simulation to MongoDB: {e}")
        
        # Add regression coefficients to make output scientifically explainable
        model = ml_service.models.get(req.region, list(ml_service.models.values())[0])
        coefs = {
            "ndvi_weight": round(float(model.coef_[0]), 2),
            "built_up_weight": round(float(model.coef_[1]), 2),
            "intercept": round(float(model.intercept_), 2)
        }
        
        return {
            "intervention": req.intervention_type,
            "cells_affected": len(simulated_cells),
            "updated_cells": simulated_cells,
            "coefficients": coefs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Allow running directly for development
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
