from common_imports import *
from utils import *
from graph_maker_utils import *
from query_proc_utils import *


# Call the main function
if __name__ == "__main__":
    dotenv.load_dotenv()
    vector_store_wrapper = VectorStoreWrapper(path="QDRANT_PATH",store_new=False)
    # Create the QueryProcessing object (This is a time consuming process and should be done only once)
    query_proc_obj = QueryProcessing(kg_path_dict_path="pdf_dict_new.json",vector_store_wrapper=vector_store_wrapper,store_new=False)

    user_query = "Hello I am looking for a rule that is applicable on 5th April 2024. Can you help me with that?"

    # Run the query processing
    response = query_proc_obj.process_query(user_query)

    # update the response with a random date_time from 5th April 2024 to 10th April 2024
    random_days = random.randint(0,5)
    random_hours = random.randint(0,23)
    random_minutes = random.randint(0,59)
    generated_date = str(datetime.datetime(2024,4,5,random_hours,random_minutes) + datetime.timedelta(days=random_days))
    response.update({
        "date_time":generated_date
    })

    print(response)

    # Storing
    with open(f"response.json","w") as f:
        json.dump(response,f,indent=4)
    



