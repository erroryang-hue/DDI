from typing import Any, List

from pydantic import BaseModel, Field


class DDIRequest(BaseModel):
    drug1: str
    drug2: str

    # Patient context
    age: int = Field(..., ge=0, le=120)
    weight: float = Field(..., gt=0)
    dose1: float = Field(..., gt=0)
    dose2: float = Field(..., gt=0)

    # Temporal parameters
    start1: float
    start2: float
    interval1: float = Field(..., gt=0)
    interval2: float = Field(..., gt=0)

    # Pharmacokinetics (optional; server will lookup from dataset if omitted)
    half_life1: float | None = None
    half_life2: float | None = None

    # Genetics (simple flag)
    poor_metabolizer: bool = False


class AnalysisReport(BaseModel):
    drug1: str
    drug2: str
    risk_score: float
    severity: str
    mechanisms: List[str] = Field(default_factory=list)
    graph_paths: List[Any] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
