from common_imports import *
from utils import *
from chunking_utils import *
from rule_list_maker import *
from summarizer_utils import *


### Custom Query Component for KeyPointComponent
class KeyPointComponent(CustomQueryComponent):
    json_summarizer_ : JSON_Engine = Field(..., description="The JSON Engine for extracting key points and examples from the text") 

    def _validate_component_inputs(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Validate component inputs during run_component."""
        # NOTE: this is OPTIONAL but we show you here how to do validation as an example
        return input

    @property
    def _input_keys(self) -> set:
        return {"context"}

    @property
    def _output_keys(self) -> set:
        return {"key_points"}
    
    def _run_component(self, **kwargs) -> Dict[str, Any]:
        context = kwargs.get("context")
        key_points = self.json_summarizer_.run(text=context)
        return {"key_points":key_points}
    


### Custom Query Component for SemanticChunkerComponent
class SemanticChunkerComponent(CustomQueryComponent):

    def _validate_component_inputs(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Validate component inputs during run_component."""
        # NOTE: this is OPTIONAL but we show you here how to do validation as an example
        return input
    
    @property
    def _input_keys(self) -> set:
        return {"key_points","context"}
    
    @property
    def _output_keys(self) -> set:
        return {"grouped_sentences","title"}
    
    def _run_component(self, **kwargs) -> Dict[str, Any]:
        key_points = kwargs.get("key_points")
        title = key_points.title
        context = kwargs.get("context")
        grouped_sentences = embed_chunk(key_points, context)
        return {"grouped_sentences":grouped_sentences,"title":title}
    

# Ingestion Pipeline for converting context to rule lists
class ConvertContextToRuleListsIngestionPipeline:
    def __init__(self,api_key_name_workers = ["OPENAI_API_KEY"]):
        self.key_point_comp  = KeyPointComponent(json_summarizer_ = JSON_Engine(
            prompt="""
            Summarize the given text into list of key points such that each key point describes a small chunk of text differently.
            Also give examples for each key point as present in the text to support the key point.
            Also provide a boolean value that indicates whether the small chunk of text is a denotes of a rule, risk or prohibition.

            Also provide a title for the whole text such that it describes the whole text.

            Note: The key points should be brief and 4 to 8 keypoints should be present.
            Note: The keypoints should not be same as title of the text.

            The order of the key points should be the same as the order of their appearance in the text.

            {text}
            """, class_name=KeyPointList,temperature=0.0
            ))

        self.sem_chunk_comp = SemanticChunkerComponent()

        self.query_pipeline = QueryPipeline(verbose=False)
        self.query_pipeline.add_modules(
            {
                "input": InputComponent(),
                "key_point_comp":self.key_point_comp,
                "sem_chunk_comp":self.sem_chunk_comp
            }
        )
        self.query_pipeline.add_link("input", "key_point_comp")
        self.query_pipeline.add_link("input", "sem_chunk_comp",dest_key="context")
        self.query_pipeline.add_link("key_point_comp", "sem_chunk_comp",dest_key="key_points")
        

        dotenv.load_dotenv()

        self.rule_list_extractors = [JSON_Engine(
            prompt="""
            Extract the rules and prohibitions along with their risk categories and instances as present in the text.

            Note: The rules and prohibitions should be brief and describes a specific type of rule/prohibition. 
            If there are multiples areas where the rules and prohibitions are to implemented, then put them in the instances of that rule. 
            Keep every type of instances/examples/inferrings seperately of individual rule/prohibition in the repspective instances list.
            Also provide the risk category for each rule/prohibition as mentioned in the text.

            Note: Also mention DO and DON'T for each rules.

            {text}
            """, class_name=RuleList,temperature=0.1,api_key_name=api_key_name) for api_key_name in api_key_name_workers]
        self.shortener_engine = JSON_Engine("""
            Given a text:
            {text}

            Generate short form of the text within 6 words without losing the context.
            """,ShortForm,temperature=0.0)

    def worker(self,worker_id,grouped_sentences_per_worker):
        print(f"Thread : {threading.current_thread().name} | Thread Id : {threading.get_ident()} | Running Triplet Extractor thread unit")
        rule_lists = {}
        for _ in grouped_sentences_per_worker:
            print("Processing Subheading : ",_.get('key_point'))
            ans = self.rule_list_extractors[worker_id].run(text=str(_.get('sub_context')))
            rule_lists[_.get('key_point')] = {"ref":_.get('sub_context'),"ans":ans}
        return rule_lists

    def serialize_into_kg_dict(self,rule_lists,title):
        # It should conin only strings as nodes and the relation between them
        # No Triplet class or any other class object should be present in the dictionary
        kg_dict = {}
        kg_dict["node1"] = title
        kg_dict["relation"] = "infers to" # default relation
        kg_dict["children"] = []
        for k,v in rule_lists.items():
            kg_dict_children = {}
            kg_dict_children["node1"] = str(self.shortener_engine.run(text=k).short_form)
            # kg_dict_children["ref"] = v["ref"]
            # kg_dict_children["detailed_name"] = k
            kg_dict_children["relation"] = "infers to"
            kg_dict_children["children"] = []
            for end_layer in v["ans"].rules:
                node1_str = end_layer.rule_prohibition
                node1_risk = end_layer.risk_category
                for inst in end_layer.instances:
                    kg_dict_children["children"].append({"node1":node1_str,"relation":"infers to","node2":inst,"risk":node1_risk})
            kg_dict["children"].append(kg_dict_children)
        return kg_dict

    def run(self, **kwargs):
        response = self.query_pipeline.run(**kwargs)
        grouped_sentences = response.get("grouped_sentences")
        self.grouped_sentences_store =   grouped_sentences

        if len(grouped_sentences) == 0:
            return {}
        title = response.get("title")
        rule_lists = {}
        count_per_worker = math.ceil(len(grouped_sentences)/len(self.rule_list_extractors))
        grouped_sentences_all_worker = [grouped_sentences[i:i+count_per_worker] for i in range(0,len(grouped_sentences),count_per_worker)]


        with ThreadPoolExecutor() as executor:
            threads = []
            for i in range(min(len(self.rule_list_extractors),len(grouped_sentences_all_worker))):
                try:
                    threads.append(executor.submit(self.worker,i,grouped_sentences_all_worker[i]))
                except:
                    print("---------------------")
                    print("Count per worker : ",count_per_worker)   
                    print("Grouped Sentences : ",len(grouped_sentences))
                    print("Grouped Sentences All Worker : ",len(grouped_sentences_all_worker))
                    print(grouped_sentences_all_worker)
                    print("---------------------")
                    print("Error in creating thread")
                    assert(0)
            for thread in threads:
                rule_lists.update(thread.result())

        rule_lists_title_dict = self.serialize_into_kg_dict(rule_lists,title)
        return rule_lists_title_dict



