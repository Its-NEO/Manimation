from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import anthropic
import os
import subprocess
import uuid
from pathlib import Path
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the FastAPI app
app = FastAPI(title="Math Visualization API")

# Create videos directory if it doesn't exist
Path("videos").mkdir(exist_ok=True)

# IMPORTANT: Set your Anthropic API key here or in environment variables
ANTHROPIC_API_KEY = os.environ.get(
    "ANTHROPIC_API_KEY",
    "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",
)

# Configure Anthropic client with explicit API key
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class MathVisualizationRequest(BaseModel):
    topic: str


class VisualizationStatus(BaseModel):
    job_id: str
    status: str
    video_path: str = None
    error: str = None


# In-memory job store
# In production, use a database instead
job_store = {}

# The Claude prompt template
CLAUDE_PROMPT = """You are a math visualizer and you need to explain {topic} by generating manim video code with no jargon only absolute code and also the video should be generated in single take and contain multiple constructors. Return ONLY the Python code for Manim with no explanations, comments or anything else."""


async def generate_manim_code(topic: str):
    """Generate Manim code using Claude 3.5 for the given math topic."""
    try:
        logger.info(f"Requesting Manim code for topic: {topic}")

        # Check if API key is properly set
        if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY == "your_api_key_here":
            raise Exception(
                "ANTHROPIC_API_KEY not properly configured. Please set it in the code or environment variables."
            )

        message = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=10000,
            temperature=0.2,
            system="You are a math visualization expert who creates Manim code. Only respond with complete, working Python code for Manim, no explanations. please try to explain concept properly",
            messages=[{"role": "user", "content": CLAUDE_PROMPT.format(topic=topic)}],
        )

        code = message.content[0].text

        # Check if the response contains jargon or explanations instead of just code
        if "```python" in code:
            # Extract code between python code blocks
            import re

            code_blocks = re.findall(r"```python\n(.*?)```", code, re.DOTALL)
            if code_blocks:
                code = code_blocks[0]

        # If the response still seems to contain explanations, try again
        if len(code.splitlines()) < 10 or "Here's" in code or "I'll" in code:
            logger.info(
                "Response contains explanations instead of pure code. Trying again..."
            )

            message = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=4000,
                temperature=0.1,
                system="You MUST ONLY output complete Python code for Manim. NO explanations, NO comments, NO conversation.",
                messages=[
                    {
                        "role": "user",
                        "content": f"Generate ONLY the complete Python Manim code to visualize {topic}. DO NOT include any explanations, just the full working code.",
                    }
                ],
            )

            code = message.content[0].text

            # Extract code again if needed
            if "```python" in code:
                code_blocks = re.findall(r"```python\n(.*?)```", code, re.DOTALL)
                if code_blocks:
                    code = code_blocks[0]

        return code
    except Exception as e:
        logger.error(f"Error generating Manim code: {str(e)}")
        raise Exception(f"Failed to generate Manim code: {str(e)}")


async def generate_visualization(job_id: str, topic: str):
    """Background task to generate the visualization and handle the entire process."""
    try:
        # Update job status
        job_store[job_id]["status"] = "generating_code"

        # Step 1: Generate Manim code using Claude
        code = await generate_manim_code(topic)

        # Step 2: Save the code to a file
        file_path = f"manim_code_{job_id}.py"
        with open(file_path, "w") as f:
            f.write(code)

        # Update job status
        job_store[job_id]["status"] = "rendering_video"

        # Step 3: Run Manim to generate the video
        output_path = f"videos/{job_id}"
        os.makedirs(output_path, exist_ok=True)

        # Execute Manim command
        try:
            # The -pql flag creates a low quality, faster render
            # Change to -pqh for higher quality
            cmd = f"manim -pql {file_path} -o {job_id}"
            logger.info(f"Running command: {cmd}")

            process = subprocess.run(
                cmd, shell=True, check=True, capture_output=True, text=True
            )

            logger.info(f"Manim output: {process.stdout}")

            # Find the output video file
            video_files = list(Path("media/videos").glob(f"*/{job_id}.mp4"))

            if not video_files:
                raise Exception("Video file not found after rendering")

            # Move the video to our videos directory
            source_video = str(video_files[0])
            dest_video = f"videos/{job_id}.mp4"
            os.rename(source_video, dest_video)

            # Update job status to completed
            job_store[job_id]["status"] = "completed"
            job_store[job_id]["video_path"] = dest_video

        except subprocess.CalledProcessError as e:
            logger.error(f"Manim rendering error: {e.stderr}")
            job_store[job_id]["status"] = "failed"
            job_store[job_id]["error"] = f"Manim rendering failed: {e.stderr}"

        # Clean up temp file
        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        logger.error(f"Error in generate_visualization: {str(e)}")
        job_store[job_id]["status"] = "failed"
        job_store[job_id]["error"] = str(e)


@app.post("/generate", response_model=VisualizationStatus)
async def generate_endpoint(
    request: MathVisualizationRequest, background_tasks: BackgroundTasks
):
    """Endpoint to request a math visualization."""
    job_id = str(uuid.uuid4())

    # Initialize job in the store
    job_store[job_id] = {
        "status": "queued",
        "topic": request.topic,
        "created_at": time.time(),
    }

    # Start the background task
    background_tasks.add_task(generate_visualization, job_id, request.topic)

    return JSONResponse(
        {
            "job_id": job_id,
            "status": "queued",
            "message": "Visualization generation started in the background. Use the /status endpoint to check progress.",
        }
    )


@app.get("/status/{job_id}", response_model=VisualizationStatus)
async def status_endpoint(job_id: str):
    """Check the status of a visualization job."""
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job not found")

    job = job_store[job_id]

    return {
        "job_id": job_id,
        "status": job["status"],
        "video_path": job.get("video_path"),
        "error": job.get("error"),
    }


@app.get("/list-jobs")
async def list_jobs():
    """List all jobs and their statuses."""
    return {
        "jobs": [
            {
                "job_id": job_id,
                "status": details["status"],
                "topic": details["topic"],
                "created_at": details["created_at"],
            }
            for job_id, details in job_store.items()
        ]
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
