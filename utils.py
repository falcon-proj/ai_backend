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