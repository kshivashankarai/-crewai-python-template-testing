#!/usr/bin/env python
import os

import sys
import warnings
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from datetime import datetime

from latest_ai_development.crew import LatestAiDevelopment

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

# init Fast api
app = FastAPI(root_path=f"/{os.getenv('CONTEXT', 'crewai-agent')}")


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker health checks"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}



class TopicRequest(BaseModel):
    topic: str

class TopicResponse(BaseModel):
    result: str


def run():
    """
    Run the crew.
    """
    inputs = {
        'topic': 'Clawdbot',
        'current_year': str(datetime.now().year)
    }

    try:
        LatestAiDevelopment().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "topic": "Clawdbot",
        'current_year': str(datetime.now().year)
    }
    try:
        LatestAiDevelopment().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        LatestAiDevelopment().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "topic": "AI LLMs",
        "current_year": str(datetime.now().year)
    }

    try:
        LatestAiDevelopment().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

def run_with_trigger():
    """
    Run the crew with trigger payload.
    """
    import json

    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    inputs = {
        "crewai_trigger_payload": trigger_payload,
        "topic": "",
        "current_year": ""
    }

    try:
        result = LatestAiDevelopment().crew().kickoff(inputs=inputs)
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew with trigger: {e}")


@app.post("/ask")
async def ask(request: TopicRequest):
    inputs = {
        "topic": request.topic,
        "current_year": str(datetime.now().year)
    }

    try:
        result = LatestAiDevelopment().crew().kickoff(inputs=inputs)
        return {"result": result}
    except Exception as e:
        return {"error": f"An error occurred while running the crew: {e}"}

if __name__ == "__main__":
    uvicorn.run("latest_ai_development.main:app", host="0.0.0.0", port=int(os.getenv("PORT",8080)))
