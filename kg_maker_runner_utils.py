from common_imports import *
from query_pipeline import *
from pdf_processor import *
from utils import *
from neo4j_utils import *


# Wrapper function to run all the functions realted to the knowledge graph generation from the pdf
# This function will return the knowledge graph in the form of a dictionary

def kg_maker_run(pdf_path,pdf_title,api_key_name_workers,init_dict_path,reset_neo4j=True,store_at_neo4j=True):
    """
    pdf_path : str : Path to the pdf file
    pdf_title : str : Title of the pdf User wants to give
    api_key_name_workers : List[str] : List of api key names
    init_dict_path : str : This is the path where the existing knowledge graph dict is stored
    reset_neo4j : bool : Whether to reset the neo4j database or not
    store_at_neo4j : bool : Whether to store the knowledge graph at neo4j or not

    return : dict : The knowledge graph dictionary
    """
    pdf_processor = PDFProcessor(api_key_name_workers=api_key_name_workers,pdf_path=pdf_path)
    pdf_dict = pdf_processor(pdf_title,init_dict_path)
    triplet_tuples = convert_listoftuple_from_pdfs_dict(pdf_dict)

    if store_at_neo4j:
        neo4j_ingestor = Neo4jIngestor()

        if reset_neo4j:
            neo4j_ingestor.neo4j_store.query(
                """
            MATCH (n) DETACH DELETE n
            """
            )

        neo4j_ingestor.ingest(triplet_tuples)
    
    return pdf_dict
