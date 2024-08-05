## EthiCheck.AI Backend

### Environment variables 
```
MONGO_URI=<"your mongo uri">
AI71_API_KEY=<"your ai71 api key">
OPENAI_API_KEY=<"your openai api key">
NEO4J_URI=<"your neo4j uri">
NEO4J_USERNAME=<"your neo4j username">
NEO4J_PASSWORD=<"your neo4j password">
AURA_INSTANCEID=<"your neo4j aura-db instance ID">
AURA_INSTANCENAME=<"your neo4j aura-db instance name">
AZURE_STORAGE_CONNECTION_STRING=<"your azure blob storage connection string">
AZURE_STORAGE_CONTAINER_NAME=<"your azure blob storage container name">
```

### Install the requirements (preferred python version > 3.10)
```
pip install -r requirements.txt
```

### How to run the program 
```
python app.py
```

### Sample Credentials to run
> User login credentials
```
username : amit45
password : amit@das
```
> Admin login credentials
```
username : admin
password: toor@admin
secretcode : 123
```

### The endpoints used 

> /upload
: In this route the admin can upload a rule book (in pdf format)

> /getJson
: In this route the knowledge graph is fetched in json form

> /getGraph
: In this route the knowledge graph is fetched in graph form

> /query
: In this route the user queries are handled

> /analytics
: In this route the analytics (day/week wise and user wise) are handled in admin portal 


### Backend High Level Design
![backend_HLD](https://drive.google.com/uc?export=view&id=1OjaCEKjcpnc2tW49rv44v9HoJtNADT5y)


