from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from supabase import create_client, Client
from datetime import datetime, timezone
from typing import Optional
import os

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="MLB Teams API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()

class MLBTeam(BaseModel):
    team_name: str
    city: str
    league: str
    world_series_wins: Optional[int] = 0
    founded: Optional[int] = None

class MLBTeamUpdate(BaseModel):
    team_name: Optional[str] = None
    city: Optional[str] = None
    league: Optional[str] = None
    world_series_wins: Optional[int] = None
    founded: Optional[int] = None

@app.get("/")
def root():
    return {"message": "MLB Teams API is running"}

@app.get("/teams")
def get_teams():
    return supabase.table("mlb_teams").select("*").order("id").execute().data

@app.get("/teams/{team_id}")
def get_team(team_id: int):
    r = supabase.table("mlb_teams").select("*").eq("id", team_id).execute()
    if not r.data:
        raise HTTPException(status_code=404, detail="Team not found")
    return r.data[0]

@app.post("/teams", status_code=201)
def create_team(team: MLBTeam):
    payload = team.dict()
    payload["updated_at"] = utc_now_iso()
    r = supabase.table("mlb_teams").insert(payload).execute()
    if not r.data:
        raise HTTPException(status_code=400, detail="Failed to create team")
    return r.data[0]

@app.put("/teams/{team_id}")
def replace_team(team_id: int, team: MLBTeam):
    payload = team.dict()
    payload["updated_at"] = utc_now_iso()
    r = supabase.table("mlb_teams").update(payload).eq("id", team_id).execute()
    if not r.data:
        raise HTTPException(status_code=404, detail="Team not found")
    return r.data[0]

@app.patch("/teams/{team_id}")
def update_team(team_id: int, team: MLBTeamUpdate):
    payload = {k: v for k, v in team.dict().items() if v is not None}
    if not payload:
        raise HTTPException(status_code=400, detail="No fields provided")
    payload["updated_at"] = utc_now_iso()
    r = supabase.table("mlb_teams").update(payload).eq("id", team_id).execute()
    if not r.data:
        raise HTTPException(status_code=404, detail="Team not found")
    return r.data[0]

@app.delete("/teams/{team_id}")
def delete_team(team_id: int):
    r = supabase.table("mlb_teams").delete().eq("id", team_id).execute()
    if not r.data:
        raise HTTPException(status_code=404, detail="Team not found")
    return {"message": "Team deleted successfully"}
