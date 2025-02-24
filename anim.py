import json
import asyncio
import os
import subprocess


def generate_animation_video(animation_json: str):
    animation = json.loads(animation_json)
    code = animation["code"]
    scenes = animation["scenes"]
    title = animation["title"]

    output = f"output/{title}"
    filename = title.lower()
    filepath = f"{output}/{filename}.py"

    if not os.path.exists(output):
        os.makedirs(output)

    with open(filepath, "w") as file:
        file.write(code)

    for scene in scenes:
        command = ["manim", f"{filename}.py", scene, "-ql", "-o", "video"]

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

    return f"{output}/media/videos/{filename}/1080p60/video.mp4"
