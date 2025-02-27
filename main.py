import uvicorn
import configparser
import fastapi
from fastapi.responses import FileResponse
from fastapi import BackgroundTasks
import agent
import anim
import os

config = configparser.ConfigParser()
config.read("config.ini")
model = agent.Agent(anthropic_token=config['ANTHROPIC']['API_TOKEN'])

app = fastapi.FastAPI()

@app.get("/new_animation_status")
async def new_animation_status(path: str):
  if os.path.exists(path):
    return FileResponse(path)
  else:
    return {"status": "pending"}

@app.post("/new_animation")
async def new_animation(query: str, background_tasks: BackgroundTasks):
  generator = model.new_animation(query, background_tasks)
  async for result in generator:
    return {"path": f"{result}"}

@app.get("/technical_query") 
async def technical_query(query: str):
  await model.technical_query(message=query)
  
  print(model.math_lesson)
  print(model.animation_specification)
  
  return {"status": "Technical query processed"}

@app.get("/conceptual_query")
async def conceptual_query(query: str):
  await model.conceptual_query(message=query)
  
  print(model.math_lesson)
  print(model.animation_specification)
  
  return {"status": "Conceptual query processed"}

@app.get("/modify_animation")
async def modify_animation(modification: str):
  await model.modify_animation(message=modification)
  
  print(model.math_lesson)
  print(model.animation_specification)
  
  return {"status": "Animation modified"}

# 1) /new_animation (topic: str)
# 2) /technical_query (query: str)
# 3) /conceptual_query (query: str)
# 4) /modify_animation (modification: str)

if __name__ == '__main__':
  uvicorn.run("main:app", reload=True)