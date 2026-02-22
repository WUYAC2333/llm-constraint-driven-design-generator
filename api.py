from fastapi import FastAPI
from pydantic import BaseModel
from main import run_design_pipeline

app = FastAPI(title="Spatial Design Generator API")

class DesignRequest(BaseModel):
    user_input: str

class DesignResponse(BaseModel):
    llm_raw_output: str
    parsed_design: dict
    validation_passed: bool
    validation_result: str

@app.post("/generate", response_model=DesignResponse)
def generate_design(request: DesignRequest):
    result = run_design_pipeline(request.user_input)
    return result