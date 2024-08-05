from kg_maker_runner_utils import *

if __name__ == "__main__":
    pdf_dict = kg_maker_run(
        pdf_path = "./Artificial intelligence act_short.pdf", # Path to the pdf file
        pdf_title = "Artificial intelligence act_short", # Title of the pdf User wants to give
        api_key_name_workers = ["DR_OPENAI_API_KEY","AD_OPENAI_API_KEY"],
        init_dict_path = "./pdf_dict_new.json", # This is the path where the existing dict is stored
        reset_neo4j = True,
        store_at_neo4j = True
    )

    # Save
    with open("pdf_dict_new.json","w") as f:
        json.dump(pdf_dict,f,indent=4)