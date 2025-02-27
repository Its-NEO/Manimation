import json
import asyncio
import os
import subprocess
import pathlib

def generate_animation_video(topic: str, animation_json: str) -> pathlib.Path:
    animation = json.loads(animation_json)
    code = animation["code"]
    scene = animation["scene"]
    title = topic

    output = f"output/{title}"
    filename = title.lower()
    filepath = f"{output}/{filename}.py"

    if not os.path.exists(output):
        os.makedirs(output)

    with open(filepath, "w") as file:
        file.write(code)
        
    command = ["manim", f"{filename}.py", scene, "-qh", "-o", "video[n]"]

    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            text=True,
            cwd=output,
        )
        if result.stderr:
            print(f"[{filepath}:{scene}]: result.stderr")
    except Exception:
        print("Error running manim")

    output_path = f"{output}/media/videos/{filename}/1080p60/video"
    os.rename(f"{output_path}[n].mp4", output_path.replace("[n]", "[r]"))

import pathlib
def trash_animation_video(path: str):
    os.remove(path)