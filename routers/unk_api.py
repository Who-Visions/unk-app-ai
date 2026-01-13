from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from services.llm.unk_agent import UnkAiAgent

router = APIRouter()
unk_agent = UnkAiAgent()


class TrendPayload(BaseModel):
    title: str
    platform: str
    raw_text: str
    sound_name: str | None = None
    creator_handle: str | None = None
    example_use_cases: List[str] | None = None


class UserProfile(BaseModel):
    age_range: str
    culture_lanes: List[str] = []
    platforms: List[str] = []
    is_creator: bool = False
    posting_frequency: str | None = None


class ExplainLinkRequest(BaseModel):
    url: str
    user_profile: UserProfile


@router.post("/unk/trend/analyze")
async def analyze_trend(payload: TrendPayload):
    summary = unk_agent.summarise_trend(payload.model_dump())
    return {"status": "success", "summary": summary}


@router.post("/unk/link/explain")
async def explain_link(body: ExplainLinkRequest):
    result = unk_agent.explain_link_for_unk(
        url=body.url,
        user_profile=body.user_profile.model_dump()
    )
    return {"status": "success", "explanation": result}


@router.post("/unk/trend/score")
async def score_trend(body: Dict[str, Any]):
    trend_summary = body.get("trend_summary")
    user_profile = body.get("user_profile")
    if not trend_summary or not user_profile:
        raise HTTPException(status_code=400, detail="Missing trend_summary or user_profile")

    result = unk_agent.score_should_i_hop(
        trend_summary=trend_summary,
        user_profile=user_profile
    )
    return {"status": "success", "decision": result}
