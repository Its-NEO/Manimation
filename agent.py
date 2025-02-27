import anthropic
import json
import typing
import anim

class Agent:
  def __init__(self, anthropic_token: str):
    self.MAX_TOKENS = 5000
    self.CONTEXT_LIMIT = 5

    self.__anthropic = anthropic.AsyncClient(api_key=anthropic_token)
    
    self.topic = None
    self.math_lesson = None
    self.animation_specification = None
    self.animation_json = None

    self.technical_chat_history = []
    self.conceptual_chat_history = []

  @property
  def video_path(self):
    title = self.topic
    filename = title.lower()
    output = f"output/{title}"
    output_path = f"{output}/media/videos/{filename}/1080p/video"
    return f"{output_path}[r].mp4"

  def _get_math_lesson_system_prompt(self) -> str:
    return Agent.read_file("prompts/math-lesson-system-prompt.txt")

  def _get_animation_spec_system_prompt(self) -> str:
    return Agent.read_file("prompts/animation-spec-system-prompt.txt")

  def _get_animation_code_system_prompt(self) -> str:
    return Agent.read_file("prompts/animation-code-system-prompt.txt")

  def read_file(filename: str) -> str:
    with open(filename,'r') as file:
      content = file.read()
    return content
  
  def append_technical_chat_message(self, message: dict[str, typing.Any]):
    while len(self.technical_chat_history) >= self.CONTEXT_LIMIT:
      self.technical_chat_history.pop(0)

    self.technical_chat_history.append(message)

  def append_conceptual_chat_message(self, message: dict[str, typing.Any]):
    while len(self.conceptual_chat_history) >= self.CONTEXT_LIMIT:
      self.conceptual_chat_history.pop(0)

    self.conceptual_chat_history.append(message)

  # Use for Technical Help
  @property
  def __technical_details_context(self):
    return f"You are a math visualization and manim coding expert specializing in creating clear, detailed animation specifications and their code. You have already created some work for a given topic, your job is to assist the user with any queries or doubts regarding your implementation.\nCurrent implementation for {self.topic}:\n\n{self.animation_json}"

  # Use for concept help
  @property
  def __concept_details_context(self):
    return f"You are a math teacher. Assist the user in explaining any conceptual details about the topic {self.topic}."

  async def _generate_math_lesson(self):
    system = self._get_math_lesson_system_prompt()
    messages = [
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": f"Provide me with a math lesson on the topic \"{self.topic}\""
          }
        ]
      }
    ]
    result = await self.__anthropic.messages.create(model="claude-3-5-sonnet-latest", system=system, messages=messages, max_tokens=self.MAX_TOKENS)
    self.math_lesson = result.content[0].text

  async def _generate_animation_spec(self):
    system = self._get_animation_spec_system_prompt()
    messages = [
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": f"Generate an animation specification on the lesson below: \n\n{self.math_lesson}"
          }
        ]
      }
    ]
    result = await self.__anthropic.messages.create(model="claude-3-5-sonnet-latest", system=system, messages=messages, max_tokens=self.MAX_TOKENS)
    self.animation_specification = result.content[0].text

  async def generate_animation_json(self):
    system = self._get_animation_code_system_prompt()
    messages = [
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": f"Animation Code on \"{self.animation_specification}\""
          }
        ]
      }
    ]
    result = await self.__anthropic.messages.create(model="claude-3-5-haiku-latest", system=system, messages=messages, max_tokens=self.MAX_TOKENS)
    self.animation_json = result.content[0].text

  async def _extract_topic(self, description: str):
    topic_extraction_prompt: str = Agent.read_file("prompts/topic-extraction-prompt.txt")
    prompt = topic_extraction_prompt.replace("<TOPIC>", description)

    messages = [
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": prompt
          }
        ]
      }
    ]

    completion = await self.__anthropic.messages.create(messages=messages, model="claude-3-5-haiku-latest", max_tokens=100)
    print(completion.content[0].text)
    topic = json.loads(completion.content[0].text)["topic"]

    self.topic = topic

  async def _continue_video_generation(self):
    print("Running bg tasks")
    await self._generate_math_lesson()
    print(f"Math Lesson:{self.math_lesson}")
    await self._generate_animation_spec()
    print(f"Animation Spec:{self.animation_specification}")
    await self.generate_animation_json()
    print(f"Animation JSON:{self.animation_json}")
    
    # This is blocking so it is a bad practice
    anim.generate_animation_video(self.topic, self.animation_json)

  import fastapi 
  async def new_animation(self, query: str, background_tasks: fastapi.BackgroundTasks):
    await self._extract_topic(query)
    background_tasks.add_task(self._continue_video_generation)
    
    yield self.video_path

  def create_user_message(query: str) -> dict[str, typing.Any]:
    return {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": query
        }
      ]
    }
  
  async def modify_animation(self, query: str):
    ...

  async def technical_query(self, query: str):
    self.append_technical_chat_message(self.create_user_message(query))
    completion = await self.__anthropic.messages.create(system=self.__technical_details_context, messages=self.technical_chat_history)

  async def conceptual_query(self, query: str):
    self.append_conceptual_chat_message(self.create_user_message(query))
    completion = await self.__anthropic.messages.create(system= self.__concept_details_context,messages=self.conceptual_chat_history)

async def test():
  import configparser
  import asyncio

  config = configparser.ConfigParser()
  config.read("config.ini")

  model = Agent(config["ANTHROPIC"]["API_TOKEN"])
  async for result in model.new_animation("Something"):
    print(result)


if __name__ == '__main__':
  import asyncio
  asyncio.run(test())