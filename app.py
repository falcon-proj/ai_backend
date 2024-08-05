import os,time
from flask import Flask, request,jsonify
from werkzeug.utils import secure_filename
import json
from flask_cors import CORS
from dotenv import load_dotenv
from flask_pymongo import PyMongo
from query_proc_utils import *
import networkx as nx
from kg_maker_runner_utils import *
from azure.storage.blob import BlobServiceClient
import certifi
from pypdf import PdfReader

load_dotenv()

ALLOWED_EXTENSIONS = set({ 'pdf'})


app = Flask(__name__)
app.config['MONGO_URI'] = os.getenv('MONGO_URI')
mongo = PyMongo(app,tlsCAFile=certifi.where())

CORS(app)

# To create a global Qdrant DB client

vector_store_wrapper = VectorStoreWrapper("qdrant_db")
pdf_dict_path=os.path.join("./","pdf_dict_new.json")


def check_pdf_dict():
    if  os.path.exists(pdf_dict_path):
        
        with open(pdf_dict_path,'r') as f:
            data=json.load(f)

        keys=data.keys()
        if "node1" in keys and "relation" in keys and "children" in keys:
            return True
    
    with open(pdf_dict_path,'w') as f:
        json.dump({
            "node1": "All rules and prohibitions",
            "relation": "points to",
            "children":[]
        },f,indent=4)
        
    return True




check_pdf_dict()

# Global object for QueryProcessing

query_proc_obj = QueryProcessing(kg_path_dict_path=pdf_dict_path,vector_store_wrapper=vector_store_wrapper,store_new=False)


# This function is to upload the rule book to Azure Blob Storage

def upload_pdf_to_blob_storage(pdf_file_path, connection_string, container_name):
    # Create a BlobServiceClient object which will be used to create a container client
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)

    # Create a ContainerClient
    container_client = blob_service_client.get_container_client(container_name)

    # Create a BlobClient
    blob_client = container_client.get_blob_client(os.path.basename(pdf_file_path))

    # Upload the PDF file to the blob
    with open(pdf_file_path, "rb") as data:
        blob_client.upload_blob(data)

    print(f"Uploaded {pdf_file_path} to Azure Blob Storage container {container_name}")


def handle_pdf_processing(pdf_path,pdf_title,pdf_dict_path):
    pdf_dict = kg_maker_run(
            pdf_path = pdf_path, # Path to the pdf file
            pdf_title = pdf_title, # Title of the pdf User wants to give
            api_key_name_workers = ["OPENAI_API_KEY"],
            init_dict_path = pdf_dict_path, # This is the path where the existing dict is stored
            reset_neo4j = True,
            store_at_neo4j = True
        )

    # Save
    with open(pdf_dict_path,"w") as f:
        json.dump(pdf_dict,f,indent=4)
    print("json updated!!")

    # Store the pdf_dict in COSMOS DB

    mongo.db.rule_kg.insert_one(pdf_dict)

    global query_proc_obj 
    query_proc_obj = QueryProcessing(kg_path_dict_path=pdf_dict_path,vector_store_wrapper=vector_store_wrapper,store_new=True)



@app.route('/upload', methods=['POST'])
def fileUpload():
    """
    This function is to upload the rule book to the server

    Returns:
        response: str: Response message to the frontend

    """
    target = os.path.join('./ruleBooks/', 'test')
    if not os.path.isdir(target):
        os.mkdir(target)
    file,file_name = request.files['file'],request.form['name']
    

    if file and file.filename.lower().endswith(tuple(ALLOWED_EXTENSIONS)):
        filename = secure_filename(file.filename)
        destination = os.path.join(target, filename)
        file.save(destination)

        reader=PdfReader(destination)

        if len(reader.pages)>50:
            response = jsonify({"error": "File Too Large. Please upload a PDF file with less than 50 pages."})
             
            return response

        response = "Rule Book is uploaded successfully but it will be processed in the background. Please wait..."


        pdf_path=destination
        pdf_title=file_name
        

        # Upload the PDF to Azure Blob Storage if it doesn't already exist

        try:
            upload_pdf_to_blob_storage(pdf_path, os.getenv('AZURE_STORAGE_CONNECTION_STRING'), os.getenv('AZURE_STORAGE_CONTAINER_NAME'))
        except Exception as e:
            print('*********************ALREADY EXISTS IN BLOB STORAGE*********************')

        pdf_processing_thread=threading.Thread(target=handle_pdf_processing,args=(pdf_path,pdf_title,pdf_dict_path))
        pdf_processing_thread.start()
        return response
    else:
        return "Invalid file format. Please upload a PDF file."

@app.route('/query',methods=['POST'])
def getMsg():
    """
    This function is to process the query from the frontend
    Insert the query in the COSMOS DB

    Returns:
        response: dict: Response message to the frontend which includes the violations and the risk category of the query along the response
    """
    # get the msg which the frontend sends and return response
    query = request.get_json()
    print(query) 
   
    
    start=time.time()

    # process the query through the query processing pipeline
    response=query_proc_obj.process_query(query["query"])

    end=time.time()
    # to append the time stamp . elapsed time and length of the query in a csv file
    with open("latency.csv","a") as file:
        file.write(f"{query['date_time']},{end-start},{len(query['query'])}\n")
    
    print(response)

    query.update(response)

    # Store the query in COSMOS DB

    mongo.db.query.insert_one(query)

    return jsonify(response)



# This function is to get the Knowledge graph in the form of json from the backend and return it to the frontend

@app.route('/getJson',methods=['GET'])
def getJson():
    try:
        with open(pdf_dict_path,'r') as file:
            data=json.load(file)
        print("json fetched!!")
        return jsonify(data)
    except:
        return jsonify({
            "node1": "All rules and prohibitions",
            "relation": "points to",
            "children":[]
        })


# Fetch the knowledge graph data from json and give it to the graph maker function to create the graph 

def getData():
    try :
        with open(pdf_dict_path,'r') as file:
            data=json.load(file)
        return data
    except:
        return {
            "node1": "All rules and prohibitions",
            "relation": "points to",
            "children":[]
        }


# Add nodes and edges to the graph

def add_nodes_and_edges(graph, data, parent_node=None, parent_relation=None):
    for main_parent_node in data.get("children"):
        main_parent=main_parent_node.get("node1")
        main_parent_relation=main_parent_node.get("relation")
        if main_parent is not None:
            graph.add_node(main_parent,label=main_parent)
            graph.add_edge(parent_node, main_parent,label=parent_relation)

            for child_node in main_parent_node.get("children"):
                child=child_node.get("node1")
                child_relation=child_node.get("relation")
                if child is not None:
                    graph.add_node(child,label=child)
                    graph.add_edge(main_parent, child,label=main_parent_relation)

                    for grandchild_node in child_node.get("children"):
                        grandchild=grandchild_node.get("node1")
                        grandchild_relation=grandchild_node.get("relation")
                        if grandchild is not None:
                            graph.add_node(grandchild,label=grandchild)
                            graph.add_edge(child, grandchild,label=child_relation)

                            for great_grandchild_node in grandchild_node.get("children"):
                                great_grandchild=great_grandchild_node.get("node1")
                                great_grandchild_relation=great_grandchild_node.get("relation")
                                great_grandchild_node2=great_grandchild_node.get("node2")
                                if great_grandchild is not None:
                                    graph.add_node(great_grandchild,label=great_grandchild,risk=great_grandchild_node.get("risk"))
                                    graph.add_edge(grandchild, great_grandchild,label=grandchild_relation)

                                    graph.add_node(great_grandchild_node2,label=great_grandchild_node2,risk=great_grandchild_node.get("risk"))
                                    graph.add_edge(great_grandchild, great_grandchild_node2,label=great_grandchild_relation)




@app.route('/getGraph',methods=['GET','POST'])
def getGraph():
    """
    GET route: This function is to get the Knowledge graph in the form of json from the backend and return nodes and links of the graph to the frontend

    POST route: This function is to update the Knowledge graph in the form of json from the frontend and return nodes and links of the updated graph to the frontend

    Returns:
        nodes: list: List of nodes in the graph
        links: list: List of links in the graph
    """

    if request.method=='POST':
        data=request.get_json()
        # print(data)


        with open(pdf_dict_path,'w') as file:
            json.dump(data["data"],file,indent=4)
        print("json updated!!")

        check_pdf_dict() # check if the pdf_dict is in the correct format


        # Store the new data in COSMOS DB
        mongo.db.rule_kg.insert_one(data["data"])

        global query_proc_obj
        query_proc_obj = QueryProcessing(kg_path_dict_path=pdf_dict_path,vector_store_wrapper=vector_store_wrapper,store_new=True)

   
    data=getData()
    graph = nx.DiGraph()
   
    
    root_node=data.get("node1")
    root_node_relation=data.get("relation")
    graph.add_node(root_node,label=root_node)
    add_nodes_and_edges(graph, data,root_node,root_node_relation)

    nodes = []
    links = []

    # Iterate over nodes and add their attributes to the nodes list
    for node, attrs in graph.nodes(data=True):
        node_info = {'id': node}
        node_info.update(attrs)
        nodes.append(node_info)


    # Iterate over edges and add their attributes to the edges list
    for source, target, attrs in graph.edges(data=True):
        edge_info = {'source': source, 'target': target}
        edge_info.update(attrs)
        links.append(edge_info)

    return jsonify(nodes,links)


@app.route('/analytics',methods=['GET'])
def getAnalytics():
    """
    This function is to get the analytics of the queries from the COSMOS DB and return it to the frontend

    Returns:
        data: list: List of queries from the COSMOS DB
    """
    _data=list(mongo.db.query.find())
    
    data=[]
    for d in _data:
        d.pop('_id',None)
        data.append(d)
    return jsonify(data)





if __name__ == "__main__":
    app.secret_key = os.urandom(24)
    app.run(debug=False,threaded=True,port=8000,host='0.0.0.0')