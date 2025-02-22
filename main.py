import uvicorn
import configparser
import fastapi
import models
import agent

config = configparser.ConfigParser()
config.read("config.ini")
model = agent.Agent(openai_token=config["OPENAI"]["API_TOKEN"], 
                    openai_project=config['OPENAI']['PROJECT'], 
                    anthropic_token=config['ANTHROPIC']['API_TOKEN'])

app = fastapi.FastAPI()

@app.get("/chat")
async def chat(message: str):
  await model.chat(message=message)

  print(model.math_lesson)
  print(model.animation_specification)
  print(model.animation_code)


# 1) /new_animation (topic: str)
# 2) /technical_query (query: str)
# 3) /conceptual_query (query: str)
# 4) /modify_animation (modification: str)

if __name__ == '__main__':
  uvicorn.run("main:app", reload=True)