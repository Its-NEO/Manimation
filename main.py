import uvicorn
import configparser
import fastapi
import agent
import anim

config = configparser.ConfigParser()
config.read("config.ini")
model = agent.Agent(anthropic_token=config['ANTHROPIC']['API_TOKEN'])

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
  await model.technical_query(message=query)
  
  print(model.math_lesson)
  print(model.animation_specification)
  print(model.animation_code)
  
  return {"status": "Technical query processed"}

@app.get("/conceptual_query")
async def conceptual_query(query: str):
  await model.conceptual_query(message=query)
  
  print(model.math_lesson)
  print(model.animation_specification)
  print(model.animation_code)
  
  return {"status": "Conceptual query processed"}

@app.get("/modify_animation")
async def modify_animation(modification: str):
  await model.modify_animation(message=modification)
  
  print(model.math_lesson)
  print(model.animation_specification)
  print(model.animation_code)
  
  return {"status": "Animation modified"}

# 1) /new_animation (topic: str)
# 2) /technical_query (query: str)
# 3) /conceptual_query (query: str)
# 4) /modify_animation (modification: str)

if __name__ == '__main__':
  print(anim.generate_animation_video('{"code": "from manim import *\\nclass CreateCircle(Scene):\\n    def construct(self):\\n        circle = Circle()  # create a circle\\n        circle.set_fill(PINK, opacity=0.5)  # set the color and transparency\\n        self.play(Create(circle))  # show the circle on screen", "scenes": ["CreateCircle"], "title": "Circle"}'))