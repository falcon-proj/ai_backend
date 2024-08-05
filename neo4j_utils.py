from common_imports import *

"""
Converts the knowledge graph dictionary to a list of tuples for the Neo4j Ingestor
The triplets are in the form of (node1,relation,node2)
"""
def convert_listoftuple_from_pdfs_dict(pdfs_dict_arg):
    listoftuple = []
    
    if pdfs_dict_arg["node1"] != "All rules and prohibitions":
        pdfs_dict = {
            "node1": "All rules and prohibitions",
            "relation": "points to",
            "children":[pdfs_dict_arg]
        } 
    else:
        pdfs_dict = pdfs_dict_arg
        

    for single_pdf_node in pdfs_dict["children"]:
        # emptiness check single_pdf_node
        if len(single_pdf_node.keys()) == 0:
            continue;        
        listoftuple.append((pdfs_dict["node1"],pdfs_dict["relation"],single_pdf_node["node1"]))
        for single_context_node in single_pdf_node["children"]:
            if len(single_context_node.keys()) == 0:
                continue;
            listoftuple.append((single_pdf_node["node1"],single_pdf_node["relation"],single_context_node["node1"]))
            for single_sub_context_node in single_context_node["children"]:
                if len(single_sub_context_node.keys()) == 0:
                    continue;
                listoftuple.append((single_context_node["node1"],single_context_node["relation"],single_sub_context_node["node1"]))
                for single_instance_node in single_sub_context_node["children"]:
                    if len(single_instance_node.keys()) == 0:
                        continue;
                    listoftuple.append((single_sub_context_node["node1"],single_sub_context_node["relation"],single_instance_node["node2"]))

    return listoftuple



"""
Data Ingestor for Neo4j
"""
class Neo4jIngestor:
    def __init__(self):
        username = os.getenv("NEO4J_USERNAME")
        password = os.getenv("NEO4J_PASSWORD")
        url = os.getenv("NEO4J_URI")
        database = "neo4j"
        self.neo4j_store = Neo4jGraphStore(
            username=username,
            password=password,
            url=url,
            database=database,
        )
        print("Connected to Neo4j")
        self.storage_context = StorageContext.from_defaults(graph_store=self.neo4j_store)
        index_name = "knackhack_1234"
        print("Creating Index")
        self.index = KnowledgeGraphIndex.from_documents([], storage_context=self.storage_context)
    
    def ingest(self,triplet_tuples):
        for _ in tqdm(triplet_tuples):
            # print(".",end="")
            self.index.upsert_triplet((_[0],_[1],_[2]))
        return True