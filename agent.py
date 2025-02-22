import anthropic
import models

class Agent:
  def __init__(self, anthropic_token: str):
    self.MAX_TOKENS = 3000

    self.__anthropic = anthropic.AsyncClient(api_key=anthropic_token)
    
    self.topic = None
    self.math_lesson = None
    self.animation_specification = None
    self.animation_code = None

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

  # Use for Technical Help
  @property
  def __technical_details_context(self):
    return [{
      "role": "system",
      "content": "You are a math visualization and manim coding expert specializing in creating clear, detailed animation specifications and their code.\n\n\n "
        f"Current specification for {self.topic}:\n\n{self.animation_specification}\n\n\n"
        f"Current implementation for {self.topic}:\n\n{self.animation_code}"
    }]

  # Use for concept help
  @property
  def __concept_details_context(self):
    return [{
      "role": "system",
      "content": "You are a math teacher."
        f"Current math lesson for {self.topic}:\n\n{self.math_lesson}"
    }]

  async def _generate_math_lesson(self):
    system = self._get_math_lesson_system_prompt()
    messages = [
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": f"Math Lesson on Topic \"{self.topic}\""
          }
        ]
      }
    ]
    result = await self.__anthropic.messages.create(model="claude-3-5-sonnet-latest", system=system, messages=messages, max_tokens=self.MAX_TOKENS)
    self.math_lesson = result.content

  async def _generate_animation_spec(self):
    system = self._get_animation_spec_system_prompt()
    messages = [
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": f"Animation specification on \"{self.math_lesson}\""
          }
        ]
      }
    ]
    result = await self.__anthropic.messages.create(model="claude-3-5-sonnet-latest", system=system, messages=messages ,max_tokens=self.MAX_TOKENS)
    self.animation_specification = result.content

  async def _generate_animation_code(self):
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
    self.animation_code = result.content

  async def new_animation(self):
    await self._generate_math_lesson()
    await self._generate_animation_spec()
    await self._generate_animation_code()

  async def modify_animation(self):
    ...

  async def categorize(self, message: str) -> str:
    ...
  
  async def chat(self, message: str):
    response = await self.categorize(message)
    category: models.CategorizeQuery = models.CategorizeQuery.model_validate_json(response)
    print(category)
    
    match category.type_:
      case models.QueryType.NEW_ANIMATION:
        await self.new_animation()
      case models.QueryType.MODIFY_ANIMATION:
        ...
      case models.QueryType.TECHNICAL_HELP:
        ...
      case models.QueryType.CONCEPT_HELP:
        ...

if __name__ == '__main__':
  import configparser
  import asyncio

  config = configparser.ConfigParser()
  config.read("config.ini")

  model = Agent(config["ANTHROPIC"]["API_TOKEN"])
  # model.topic = "Calculus"

  # asyncio.run(model.new_animation())
  
  # print(model.topic)
  # print(model.math_lesson)
  # print(model.animation_specification)
  # print(model.animation_code)

  user = [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Visualize integration beautifully with manim code. One scene."
        }
      ]
    }
  ]



  # TODO: FIX THE PROMPTS
  # TODO: 