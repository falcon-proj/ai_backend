from common_imports import *


"""
JSON_Engine is a wrapper over LlamaIndex JSON Query Engine
It takes a JSON prompt and a pydanctic class name as input in the constructor
It uses OpenAI API to generate the output

run method processes the prompt and returns the output in the form of pydantic class object
"""
class JSON_Engine(BaseTool):
    def __init__(self, prompt, class_name, model: str = "gpt-3.5-turbo",temperature=0.1, api_key_name = "OPENAI_API_KEY"):
        self.output_parser = PydanticOutputParser(class_name)
        self.llm = OpenAI(model=model,temperature=temperature,api_key=os.getenv(api_key_name))
        self.json_prompt_str = prompt
        self.class_name = class_name
        self.json_prompt_str = self.output_parser.format(self.json_prompt_str)
        self.json_prompt_tmpl = PromptTemplate(self.json_prompt_str)
        self.p = QueryPipeline(chain=[self.json_prompt_tmpl, self.llm, self.output_parser], verbose=False)
    
    def run(self, **kwargs):
        response = self.p.run(**kwargs)
        return response

    def __call__(self, input: Any) -> ToolOutput:
        return None
    
    def metadata(self):
        pass


class FalconLLM:
  def __init__(self, model_name: str = "tiiuae/falcon-180b-chat", api_key_name = "AI71_API_KEY"):
    AI71_API_KEY = os.getenv(api_key_name)
    self.obj = lambda user_msg:AI71(AI71_API_KEY).chat.completions.create(
                      model=model_name,
                      messages=[
                          {"role": "system", "content": "You are a helpful assistant."},
                          {"role": "user", "content": user_msg},
                      ], stream=True)

  def complete(self, user_msg):
    ans = ""
    for chunk in self.obj(user_msg):
      if chunk.choices[0].delta.content:
        ans += chunk.choices[0].delta.content
    return ans

"""
JSON_Engine is a wrapper over LlamaIndex JSON Query Engine Powered by flacon model. 
It takes a JSON prompt and a pydanctic class name as input in the constructor
It uses OpenAI API to generate the output

run method processes the prompt and returns the output in the form of pydantic class object
"""
class Falcon_JSON_Engine(BaseTool):
    def __init__(self, prompt, class_name):
        self.output_parser = PydanticOutputParser(class_name)
        self.llm = FalconLLM()
        self.json_prompt_str = prompt
        self.class_name = class_name
        self.json_prompt_str = self.output_parser.format(self.json_prompt_str)
        self.json_prompt_tmpl = PromptTemplate(self.json_prompt_str)
        self.p = QueryPipeline(chain=[self.json_prompt_tmpl, self.llm, self.output_parser], verbose=False)
    
    def run(self, **kwargs):
        response = self.p.run(**kwargs)
        return response

    def __call__(self, input: Any) -> ToolOutput:
        return None
    
    def metadata(self):
        pass

        
