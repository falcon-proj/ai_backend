from common_imports import *
from utils import *


# Wrapper function to create quadrant client 
class VectorStoreWrapper:
    # Static List
    # We can use this to store the documents and query them

    static_client = None
    
    def __init__(self, path, store_new = False, documents:List[Document] = []):
        self.collection_name = 'depth_345_concat'
        try:
            print("Log: Static Client Closes")
            VectorStoreWrapper.client.close()
        except:
            pass

        self.client = qdrant_client.QdrantClient(path=path)
        VectorStoreWrapper.static_client = self.client
        self.text_store = QdrantVectorStore(
            client=self.client, collection_name=self.collection_name
        )
        self.storage_context = StorageContext.from_defaults(
            vector_store=self.text_store
        )
        self.index = VectorStoreIndex.from_documents(
            [],
            storage_context=self.storage_context,
            show_progress=True
        )
        if store_new:
            self.set_documents(documents)
    
    def set_documents(self,documents:List[Document]):
        self.client.delete_collection(self.collection_name)
        self.text_store = QdrantVectorStore(
            client=self.client, collection_name=self.collection_name
        )
        self.storage_context = StorageContext.from_defaults(
            vector_store=self.text_store
        )
        self.index = VectorStoreIndex.from_documents(
            documents,
            storage_context=self.storage_context,
            show_progress=True
        )
        return self.index

    def close(self):
        self.client.close()


class GraphMaker:
    def __init__(self, dict_path,vector_store_wrapper:VectorStoreWrapper,store_new:bool):
        with open(dict_path) as f:
            self.pdf_dict = json.load(f)
        self.children_list_dict, self.depth_345_concat_dict = self.convert_dict_into_graph(self.pdf_dict)
        self.depth_345_concat_dict_docs = [Document(text=doc) for doc in self.depth_345_concat_dict.values()]
        self.vector_store_wrapper = vector_store_wrapper
        if store_new:
            self.vector_store_wrapper.set_documents(self.depth_345_concat_dict_docs)
        self.index = self.vector_store_wrapper.index
        self.ret = self.index.as_retriever(similarity_top_k=3)

    def convert_dict_into_graph(self, pdfs_dict_arg):
        children_list_dict = {}
        depth_345_concat_dict = {}

        if pdfs_dict_arg["node1"] != "All rules and prohibitions":
            pdfs_dict = {
                "node1": "All rules and prohibitions",
                "relation": "points to",
                "children":[pdfs_dict_arg]
            } 
        else:
            pdfs_dict = pdfs_dict_arg
            
        children_list_dict[pdfs_dict["node1"]] = {"parent": None, "children": [], "depth": 0}
        for single_pdf_node in pdfs_dict["children"]:
            # emptiness check single_pdf_node

            if len(single_pdf_node.keys()) == 0:
                continue; 
            
            children_list_dict[single_pdf_node["node1"]] = {"parent": pdfs_dict["node1"], "children": [], "depth": 1}
            children_list_dict[pdfs_dict["node1"]]["children"].append(single_pdf_node["node1"])


            
            for single_context_node in single_pdf_node["children"]:

                if len(single_context_node.keys()) == 0:
                    continue;
                
                children_list_dict[single_context_node["node1"]] = {"parent": single_pdf_node["node1"], "children": [], "depth": 2}
                children_list_dict[single_pdf_node["node1"]]["children"].append(single_context_node["node1"])

                for single_sub_context_node in single_context_node["children"]:

                    if len(single_sub_context_node.keys()) == 0:
                        continue;
                    
                    children_list_dict[single_sub_context_node["node1"]] = {"parent": single_context_node["node1"], "children": [], "depth": 3}
                    children_list_dict[single_context_node["node1"]]["children"].append(single_sub_context_node["node1"])
                    
                    for single_instance_node in single_sub_context_node["children"]:
                        
                        if len(single_instance_node.keys()) == 0:
                            continue; 
                        
                        children_list_dict[single_instance_node["node1"]] = {"parent": single_sub_context_node["node1"], "children": [], "depth": 4}
                        children_list_dict[single_sub_context_node["node1"]]["children"].append(single_instance_node["node1"])
                   
                        # add node2
                        children_list_dict[single_instance_node["node2"]] = {"parent": single_instance_node["node1"], "children": [], "depth": 5, "risk": single_instance_node["risk"]}
                        children_list_dict[single_instance_node["node1"]]["children"].append(single_instance_node["node2"])



        for key, value in children_list_dict.items():
            if value["depth"] == 5:
                gp = children_list_dict[value["parent"]]["parent"].split("Example")[0]
                p = value["parent"]
                depth_345_concat_dict[key] = gp+" -> "+p+" -> "+key         
        return children_list_dict,depth_345_concat_dict



    def get_path_from_root_to_node(self, node):
        path = []
        temp_node=None
        while node is not None and temp_node!=node:
            path.append(node)
            temp_node = node
            node = self.children_list_dict[node]["parent"]
            
            print("@@@node: ", node)
        return path[::-1]