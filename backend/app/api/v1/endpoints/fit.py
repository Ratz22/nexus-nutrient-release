"""POST /fit - fit a user's own release curve to 4 standard kinetic models."""
from typing import List

import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.ml.kinetics import fit_release, predict, time_to_release

router = APIRouter()

DISCLAIMER = ("Research guidance only. Not agronomic, regulatory or safety advice. "
              "Validate in your own conditions.")


class FitRequest(BaseModel):
    time_days: List[float] = Field(..., min_length=4)
    release_pct: List[float] = Field(..., min_length=4)


@router.post("/fit")
def fit(req: FitRequest):
    if len(req.time_days) != len(req.release_pct):
        raise HTTPException(422, "time_days and release_pct must be the same length")
    try:
        res = fit_release(req.time_days, req.release_pct)
    except ValueError as e:
        raise HTTPException(422, str(e))
    best = res["best_model"]
    if best:
        res["t80_days"] = time_to_release(best, res["fits"][best]["params"], 80)
    grid = np.linspace(0.01, max(req.time_days) * 1.3, 100)
    res["curves"] = {name: {"t": grid.tolist(), "y": predict(name, r["params"], grid).tolist()}
                     for name, r in res["fits"].items() if "params" in r}
    res["disclaimer"] = DISCLAIMER
    return res