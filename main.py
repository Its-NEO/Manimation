import uvicorn
import configparser
import fastapi
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.exceptions import HTTPException
from fastapi import BackgroundTasks
import os
import sys
from pydantic import BaseModel
from anthropic import AsyncClient
import subprocess
import logging
import time
from pathlib import Path
import uuid
import shutil
import re
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict
import asyncio
import io

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

config = configparser.ConfigParser()
config.read("config.ini")
__anthropic = AsyncClient(api_key=config["ANTHROPIC"]["API_TOKEN"])

app = fastapi.FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
job_store = {}
MAX_TOKENS = 3000
CONTEXT_LIMIT = 5
MAX_RETRIES = 3  # Maximum number of retries for code generation
chat_context = []

# Basic prompt for Manim code generation
BASE_PROMPT = """You are a math visualizer and you need to explain {topic} by generating manim video code. Return ONLY the Python code for Manim with no explanations, comments or anything else.

IMPORTANT REQUIREMENTS:
1. If your visualization needs 3D capabilities, make sure the scene class inherits from ThreeDScene.
2. If using 3D, include 'from manim import *' and use the appropriate 3D methods like set_camera_orientation instead of move_camera.
3. Make sure all LaTeX expressions are properly escaped.
4. Remove text timely to make space for new illustrations.
5. Keep the video under 1 minute in length.
6. Make the visualization visually clean and educational.
7. Do not use special Unicode characters, use ASCII alternatives instead.

Example 3D scene structure:
```python
from manim import *

class YourVisualizationName(ThreeDScene):
    def construct(self):
        # Your code here
        self.set_camera_orientation(phi=75 * DEGREES, theta=30 * DEGREES)
        # More code
```
"""

# Error correction prompt
ERROR_CORRECTION_PROMPT = """The Manim code you provided resulted in the following error:

```
{error}
```

Please fix the code to address this specific error. Common issues include:
1. Using move_camera instead of set_camera_orientation in ThreeDScene
2. Incorrect inheritance (2D vs 3D scene)
3. Syntax errors in LaTeX expressions
4. References to undefined variables or objects

Provide ONLY the complete, corrected code with no explanations:
"""


class VisualizationStatus(BaseModel):
    job_id: str
    status: str
    video_path: Optional[str] = None
    error: Optional[str] = None


class MathVisualizationRequest(BaseModel):
    topic: str


class ChatMessage(BaseModel):
    message: str


def append_chat(role: str, message: str):
    while len(chat_context) >= CONTEXT_LIMIT:
        chat_context.pop(0)

    chat_context.append({"role": role, "content": [{"type": "text", "text": message}]})


async def generate_manim_code(
    topic: str, error_message: str = None, retry_count: int = 0
):
    """Generate Manim code using Claude 3.5 for the given math topic.
    If error_message is provided, it will be used to correct previous code."""
    try:
        logger.info(f"Requesting Manim code for topic: {topic} (Retry: {retry_count})")

        if error_message:
            # We're in correction mode
            prompt = ERROR_CORRECTION_PROMPT.format(error=error_message)
            logger.info("Using error correction prompt")
        else:
            # First attempt
            prompt = BASE_PROMPT.format(topic=topic)

        message = await __anthropic.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=MAX_TOKENS,
            temperature=0.2,
            system="You are a math visualization expert who creates flawless Manim code. Only respond with complete, working Python code for Manim, no explanations. Your code should NOT use special Unicode characters, use ASCII alternatives instead.",
            messages=[{"role": "user", "content": prompt}],
        )

        code = message.content[0].text

        # Check if the response contains code blocks
        if "```python" in code:
            # Extract code between python code blocks
            code_blocks = re.findall(r"```python\n(.*?)```", code, re.DOTALL)
            if code_blocks:
                code = code_blocks[0]
        elif "```" in code:
            # Extract code between any code blocks
            code_blocks = re.findall(r"```\n(.*?)```", code, re.DOTALL)
            if code_blocks:
                code = code_blocks[0]

        # If the response still seems to contain explanations, try again
        if len(code.splitlines()) < 10 or "Here's" in code or "I'll" in code:
            logger.info(
                "Response contains explanations instead of pure code. Trying again..."
            )

            message = await __anthropic.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=MAX_TOKENS,
                temperature=0.1,
                system="You MUST ONLY output complete Python code for Manim. NO explanations, NO comments, NO conversation. Do NOT use special Unicode characters, use ASCII alternatives instead.",
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
            elif "```" in code:
                code_blocks = re.findall(r"```\n(.*?)```", code, re.DOTALL)
                if code_blocks:
                    code = code_blocks[0]

        # Make sure 3D scenes use set_camera_orientation instead of move_camera
        if "ThreeDScene" in code and "move_camera" in code:
            code = code.replace("move_camera", "set_camera_orientation")

        # Make sure we import * from manim
        if "from manim import" not in code and "import manim" not in code:
            code = "from manim import *\n" + code

        append_chat("user", prompt)
        append_chat("assistant", code)
        return code
    except Exception as e:
        logger.error(f"Error generating Manim code: {str(e)}")
        raise Exception(f"Failed to generate Manim code: {str(e)}")


# Add a timeout parameter to run_manim_command
async def run_manim_command(file_path: str, job_id: str, timeout: int = 300):
    """Run the Manim command with a timeout and return success status and error message if any."""
    try:
        # The -pql flag creates a low quality, faster render
        python_exe = sys.executable
        output_dir = f"media/videos/{job_id}"
        os.makedirs(output_dir, exist_ok=True)

        cmd = f'"{python_exe}" -m manim -pql {file_path} --media_dir -o  {job_id}'
        logger.info(f"Running command: {cmd}")

        # Use asyncio to run the subprocess with a timeout
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
            stdout = stdout.decode("utf-8")
            stderr = stderr.decode("utf-8")

            # Update job status in the store to reflect progress
            if job_id in job_store:
                job_store[job_id]["status"] = "processing_video"

            if process.returncode != 0:
                logger.error(f"Manim error: {stderr}")
                return False, stderr

            logger.info(f"Manim output: {stdout}")
            return True, None

        except asyncio.TimeoutError:
            # Kill the process if it times out
            process.kill()
            error_msg = f"Manim rendering timed out after {timeout} seconds"
            logger.error(error_msg)
            return False, error_msg

    except Exception as e:
        logger.error(f"Error running Manim: {str(e)}")
        return False, str(e)


async def find_and_move_video(job_id: str):
    """Find the generated video file and move it to the videos directory.
    Returns (success, error_message)."""
    try:
        # Look for videos in the job-specific output directory
        job_output_dir = Path(f"media/videos/{job_id}")

        # Wait a moment for file system to update
        await asyncio.sleep(1)

        # List all MP4 files in that directory
        if job_output_dir.exists():
            video_files = list(job_output_dir.glob("*.mp4"))
            logger.info(f"Found {len(video_files)} videos in {job_output_dir}")
        else:
            video_files = []
            logger.warning(f"Directory not found: {job_output_dir}")

        # If not found in the expected location, search more broadly
        if not video_files:
            # Search for any file containing the job_id in its name
            for root, dirs, files in os.walk("media/videos"):
                for file in files:
                    if file.endswith(".mp4"):
                        filepath = os.path.join(root, file)
                        logger.info(f"Found MP4: {filepath}")
                        video_files.append(Path(filepath))

            # If still not found, do a deep search
            if not video_files:
                video_files = list(Path(".").glob(f"**/*.mp4"))
                logger.info(f"Deep search found {len(video_files)} MP4 files")

        if not video_files:
            return False, f"Video file not found for job_id: {job_id}"

        # Sort by creation time to get the newest video if multiple are found
        if len(video_files) > 1:
            video_files.sort(key=lambda x: os.path.getctime(str(x)), reverse=True)
            logger.info(
                f"Multiple videos found, using the newest one: {video_files[0]}"
            )

        # Move the video to our videos directory
        source_video = str(video_files[0])
        dest_video = f"videos/{job_id}.mp4"

        # Use shutil.copy2 instead of os.rename to avoid cross-device link errors
        shutil.copy2(source_video, dest_video)
        logger.info(f"Video copied from {source_video} to {dest_video}")

        return True, dest_video
    except Exception as e:
        logger.error(f"Error finding/moving video for job_id {job_id}: {str(e)}")
        return False, str(e)


async def generate_visualization(job_id: str, topic: str):
    """Background task to generate the visualization with improved status reporting."""
    file_path = f"manim_code_{job_id}.py"

    try:
        # Update job status
        job_store[job_id]["status"] = "generating_code"
        job_store[job_id]["progress_details"] = "Requesting code from Claude"

        retry_count = 0
        last_error = None
        success = False

        while retry_count <= MAX_RETRIES and not success:
            try:
                # Clear the previous error message when we start a new retry
                if retry_count > 0:
                    job_store[job_id][
                        "status"
                    ] = f"retry_{retry_count}_of_{MAX_RETRIES}"
                    job_store[job_id][
                        "progress_details"
                    ] = f"Attempting code generation (attempt {retry_count+1})"

                # Step 1: Generate Manim code using Claude
                code = await generate_manim_code(topic, last_error, retry_count)

                # Step 2: Save the code to a file
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(code)

                # Update job status before rendering
                job_store[job_id]["status"] = "rendering_video"
                job_store[job_id][
                    "progress_details"
                ] = "Executing Manim to render visualization"

                # Step 3: Run Manim with timeout
                success, error_message = await run_manim_command(
                    file_path, job_id, timeout=300
                )

                if not success:
                    retry_count += 1
                    last_error = error_message
                    job_store[job_id]["error"] = f"Rendering failed: {error_message}"
                    job_store[job_id][
                        "progress_details"
                    ] = f"Rendering failed on attempt {retry_count}"
                    logger.warning(
                        f"Manim rendering failed on attempt {retry_count}. Error: {error_message}"
                    )

                    if retry_count > MAX_RETRIES:
                        job_store[job_id]["status"] = "failed"
                        break
                    else:
                        # Wait a short time before retry to avoid rapid cycling
                        await asyncio.sleep(2)
                        continue

                # Update status for video processing
                job_store[job_id]["status"] = "processing_video"
                job_store[job_id]["progress_details"] = "Finding and moving video file"

                # Find and move the video file
                video_success, video_result = await find_and_move_video(job_id)

                if not video_success:
                    retry_count += 1
                    last_error = video_result
                    job_store[job_id][
                        "error"
                    ] = f"Video processing failed: {video_result}"
                    job_store[job_id][
                        "progress_details"
                    ] = f"Video processing failed on attempt {retry_count}"
                    logger.warning(
                        f"Video file handling failed on attempt {retry_count}. Error: {video_result}"
                    )

                    if retry_count > MAX_RETRIES:
                        job_store[job_id]["status"] = "failed"
                        break
                    else:
                        await asyncio.sleep(2)
                        continue

                # Everything succeeded
                job_store[job_id]["status"] = "completed"
                job_store[job_id]["video_path"] = video_result
                job_store[job_id][
                    "progress_details"
                ] = "Visualization successfully completed"
                job_store[job_id]["error"] = None
                success = True

            except Exception as e:
                retry_count += 1
                last_error = str(e)
                job_store[job_id]["error"] = f"Error: {last_error}"
                job_store[job_id][
                    "progress_details"
                ] = f"Error on attempt {retry_count}: {last_error}"
                logger.error(
                    f"Error in visualization attempt {retry_count}: {last_error}"
                )

                if retry_count <= MAX_RETRIES:
                    await asyncio.sleep(2)
                else:
                    job_store[job_id]["status"] = "failed"
                    job_store[job_id][
                        "progress_details"
                    ] = f"Failed after {MAX_RETRIES} attempts"

        # Clean up temp file
        if os.path.exists(file_path):
            os.remove(file_path)

        # Final check if we succeeded or failed
        if not success and job_store[job_id]["status"] != "failed":
            job_store[job_id]["status"] = "failed"
            job_store[job_id][
                "progress_details"
            ] = f"Failed after {MAX_RETRIES} attempts"
            job_store[job_id]["error"] = f"Last error: {last_error}"

    except Exception as e:
        logger.error(f"Fatal error in generate_visualization: {str(e)}")
        job_store[job_id]["status"] = "failed"
        job_store[job_id]["error"] = str(e)
        job_store[job_id]["progress_details"] = "Unexpected error in generation process"

        # Clean up temp file
        if os.path.exists(file_path):
            os.remove(file_path)


# New function to stream video using ffmpeg
async def stream_video(video_path: str):
    """Stream a video file using ffmpeg."""
    try:
        # Check if the video file exists
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Set up process to stream video using ffmpeg
        process = subprocess.Popen(
            [
                "ffmpeg",
                "-i",
                video_path,
                "-f",
                "mp4",
                "-movflags",
                "frag_keyframe+empty_moov",
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                "-",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Define the generator function to yield video data
        async def generate():
            while True:
                # Read data from stdout
                data = process.stdout.read(1024 * 1024)  # Read 1MB at a time
                if not data:
                    break
                yield data

            # Ensure process is terminated
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

        return generate()

    except Exception as e:
        logger.error(f"Error in stream_video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Video streaming error: {str(e)}")


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
        "error": None,
        "video_path": None,
    }

    # Start the background task
    background_tasks.add_task(generate_visualization, job_id, request.topic)

    return JSONResponse(
        {
            "job_id": job_id,
            "status": "queued",
            "video_path": "",
            "error": "",
            "message": "Visualization generation started in the background. Use the /status endpoint to check progress.",
        }
    )


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Math Visualization API",
        "endpoints": [
            {
                "path": "/generate",
                "method": "POST",
                "description": "Generate a math visualization video",
            },
            {
                "path": "/status/{job_id}",
                "method": "GET",
                "description": "Check status of a job",
            },
            {"path": "/list-jobs", "method": "GET", "description": "List all jobs"},
            {
                "path": "/video/{job_id}",
                "method": "GET",
                "description": "Stream video file",
            },
            {"path": "/chat", "method": "POST", "description": "Chat about Manim code"},
        ],
        "usage": "Send a POST request to /generate with a JSON body containing 'topic'",
    }


@app.get("/status/{job_id}")
async def status_endpoint(job_id: str):
    """Check the status of a visualization job."""
    try:
        logger.info(f"Status check requested for job: {job_id}")

        if job_id not in job_store:
            logger.warning(f"Job not found: {job_id}")
            raise HTTPException(status_code=404, detail="Job not found")

        job = job_store[job_id]
        logger.info(f"Job data: {job}")

        # Ensure values are of the right type
        return {
            "job_id": job_id,
            "status": job["status"],
            "video_path": job.get("video_path") or "",  # Convert None to empty string
            "error": job.get("error") or "",  # Convert None to empty string
        }
    except Exception as e:
        logger.error(f"Error in status endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


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


@app.post("/chat")
async def chat(chat: ChatMessage):
    append_chat(role="user", message=chat.message)
    message = await __anthropic.messages.create(
        model="claude-3-5-haiku-latest",
        max_tokens=MAX_TOKENS,
        temperature=0.1,
        system="You are an expert at manim code. Your job is to assist the user in their queries.",
        messages=chat_context,
    )

    response = message.content[0].text
    append_chat(role="assistant", message=response)
    return {"response": response}


@app.get("/video/{job_id}")
async def get_video(job_id: str):
    """Stream a video for a completed job using ffmpeg."""
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job not found")

    job = job_store[job_id]
    if job.get("video_path") is None or job.get("video_path") == "":
        raise HTTPException(status_code=404, detail="Video not yet available")

    video_path = job["video_path"]
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video file not found")

    # Check if ffmpeg is available
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, capture_output=True)
    except (subprocess.SubprocessError, FileNotFoundError):
        logger.warning("FFmpeg not found, falling back to direct file response")
        return FileResponse(
            video_path, media_type="video/mp4", headers={"Accept-Ranges": "bytes"}
        )

    # Stream the video using ffmpeg
    generator = await stream_video(video_path)

    return StreamingResponse(
        generator,
        media_type="video/mp4",
        headers={
            "Accept-Ranges": "bytes",
            "Content-Disposition": f"inline; filename={job_id}.mp4",
        },
    )


@app.get("/check-manim")
async def check_manim():
    """Endpoint to check if manim is properly installed."""
    try:
        python_exe = sys.executable
        cmd = f'"{python_exe}" -m pip list'

        # Check platform to use the appropriate grep command
        if sys.platform == "win32":
            cmd += " | findstr manim"
        else:
            cmd += " | grep manim"

        result = subprocess.run(
            cmd,
            shell=True,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        if result.stdout:
            return {"status": "installed", "details": result.stdout}
        else:
            return {"status": "not found", "details": "Manim not found in pip list"}
    except Exception as e:
        return {"status": "error", "details": str(e)}


@app.get("/check-ffmpeg")
async def check_ffmpeg():
    """Endpoint to check if ffmpeg is properly installed."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            shell=False,
            check=False,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            # Extract the first line of the version information
            version_info = (
                result.stdout.splitlines()[0] if result.stdout else "Unknown version"
            )
            return {"status": "installed", "details": version_info}
        else:
            return {
                "status": "not found",
                "details": "FFmpeg not found or not working properly",
            }
    except Exception as e:
        return {"status": "error", "details": str(e)}


@app.get("/logs/{job_id}")
async def get_job_logs(job_id: str):
    """Get detailed logs for a specific job."""
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job not found")

    job = job_store[job_id]

    # Construct log information
    logs = {
        "job_id": job_id,
        "topic": job["topic"],
        "status": job["status"],
        "created_at": job["created_at"],
        "error": job.get("error") or "",
        "video_path": job.get("video_path") or "",
    }

    return logs


if __name__ == "__main__":
    # Create videos directory if it doesn't exist
    os.makedirs("videos", exist_ok=True)
    uvicorn.run("main:app", reload=True)
