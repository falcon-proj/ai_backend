from common_imports import *
from query_pipeline import *

class PDFProcessor:
    def __init__(self, api_key_name_workers , pdf_path):
        self.convert_context_to_rulelists_ingestion_pipeline = ConvertContextToRuleListsIngestionPipeline(api_key_name_workers=api_key_name_workers)
        self.pdf_path = pdf_path
        rule_documents = llama_index.core.SimpleDirectoryReader(input_files=[pdf_path]).load_data()
        embed_model = OpenAIEmbedding()
        splitter = SemanticSplitterNodeParser(buffer_size=1, breakpoint_percentile_threshold=95, embed_model=embed_model)
        nodes = splitter.get_nodes_from_documents(rule_documents)
        print(f"Number of nodes : {len(nodes)}")
        self.contexts = [_.get_content() for _ in nodes]
        
    def __call__(self,root_name,init_dict_path=None):

        self.init_dict = {
            "node1": "All rules and prohibitions",
            "relation": "points to",
            "children":[]
        }
        if init_dict_path is not None:
            try:
                with open(init_dict_path,"r") as f:
                    self.init_dict = json.load(f)

                # Check duplicate root_name in the init_dict
                for _ in self.init_dict["children"]:
                    print(_["node1"])
                    if _["node1"] == root_name:
                        print("WARNING: Root name already present in the init_dict")
                        return self.init_dict
            except:
                print("Error in loading the init_dict ... Creating a new one")

        pdf_dict = {
            "node1":root_name,
            "relation":"points to",
            "children":[]
        }

        for i,context in enumerate(self.contexts):
            print(f"Processing Context : {i}")
            try:
                rulelists_title_dict = self.convert_context_to_rulelists_ingestion_pipeline.run(context=context)
                pdf_dict["children"].append(rulelists_title_dict)
            except:
                print("************* Error in processing *****************")
                assert(0)
                continue
        self.init_dict["children"].append(pdf_dict)
        return self.init_dict
    



