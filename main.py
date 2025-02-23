import uvicorn
import configparser
import fastapi
import agent

config = configparser.ConfigParser()
config.read("config.ini")
model = agent.Agent(openai_token=config["OPENAI"]["API_TOKEN"], 
                    openai_project=config['OPENAI']['PROJECT'], 
                    anthropic_token=config['ANTHROPIC']['API_TOKEN'])

app = fastapi.FastAPI()

@app.get("/new_animation")
async def new_animation(topic: str):
  await model.new_animation(message=topic)
  
  print(model.math_lesson)
  print(model.animation_specification)
  print(model.animation_code)
  
  return {"status": "Animation created"}

@app.get("/technical_query") 
async def technical_query(query: str):
  await model.chat(message=query)
  
  print(model.math_lesson)
  print(model.animation_specification)
  print(model.animation_code)
  
  return {"status": "Technical query processed"}

@app.get("/conceptual_query")
async def conceptual_query(query: str):
  await model.chat(message=query)
  
  print(model.math_lesson)
  print(model.animation_specification)
  print(model.animation_code)
  
  return {"status": "Conceptual query processed"}

@app.get("/modify_animation")
async def modify_animation(modification: str):
  await model.chat(message=modification)
  
  print(model.math_lesson)
  print(model.animation_specification)
  print(model.animation_code)
  
  return {"status": "Animation modified"}

# 1) /new_animation (topic: str)
# 2) /technical_query (query: str)
# 3) /conceptual_query (query: str)
# 4) /modify_animation (modification: str)

if __name__ == '__main__':
  uvicorn.run("main:app", reload=True)