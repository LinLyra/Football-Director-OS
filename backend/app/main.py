import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .data import demo_events
from .engine import replay
from .evaluation import run_benchmark
from .models import (CompileRequest, CompileResponse, ProgramCreateRequest,
                     ProgramStatusRequest, ReplayRequest, ReplayResponse)
from .providers import configured_provider
from .repository import ProgramRepository


app = FastAPI(
    title="Football Director OS API",
    description="Deterministic, evidence-backed football intent execution.",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
provider = configured_provider()
repository = ProgramRepository(os.getenv("DATABASE_PATH", "data/football_director.db"))


@app.get("/api/health")
def health():
    return {"status": "ok", "engine": "deterministic", "dsl_version": "1.0", "intent_provider": provider.name}


@app.get("/api/matches/match_demo_01/events")
def events():
    return demo_events()


@app.post("/api/director/compile", response_model=CompileResponse)
async def compile_program(request: CompileRequest):
    return await provider.compile(request.instruction)


@app.post("/api/director/programs", status_code=201)
def create_program(request: ProgramCreateRequest):
    return repository.create(request.original_instruction, request.program)


@app.get("/api/director/programs")
def list_programs():
    return repository.list()


@app.patch("/api/director/programs/{program_id}")
def set_program_status(program_id: str, request: ProgramStatusRequest):
    record = repository.set_status(program_id, request.status)
    if not record:
        raise HTTPException(status_code=404, detail="Program not found")
    return record


@app.post("/api/evaluation/replay", response_model=ReplayResponse)
def evaluate_replay(request: ReplayRequest):
    insights = replay(request.program, request.events)
    return ReplayResponse(insights=insights, processed_events=len(request.events))


@app.get("/api/evaluation/benchmark")
def benchmark():
    return run_benchmark()
