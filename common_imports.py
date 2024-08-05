from llama_index.core.query_pipeline import (
    AgentFnComponent,
    AgentInputComponent,
    ToolRunnerComponent,
)
from llama_index.core.agent import Task, AgentChatResponse, ReActChatFormatter
# from llama_index.core.memory.types import BaseMemory
from llama_index.core.llms import ChatMessage
from llama_index.core.tools import BaseTool
from llama_index.core.tools.tool_spec.base import BaseToolSpec
from llama_index.llms.llama_cpp.llama_utils import (
                completion_to_prompt,
                messages_to_prompt,
            ) 
from llama_index.core.base.llms.types import ChatMessage, MessageRole
# from llama_index.core.agent.react.output_parser import ReActOutputParser
from llama_index.core.llms import ChatResponse
from llama_index.core.query_pipeline import QueryPipeline
from llama_index.llms.openai import OpenAI
import llama_index
from llama_index.core.agent import QueryPipelineAgentWorker, AgentRunner
from llama_index.core.callbacks import CallbackManager
from llama_index.core.output_parsers import PydanticOutputParser
from llama_index.core import PromptTemplate
from llama_index.agent.openai import OpenAIAgent # Had to change agent.openai
from llama_index.llms.openai import OpenAI
from llama_index.core import  Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from langchain_openai import OpenAIEmbeddings as langchain_OpenAIEmbeddings
from llama_index.core.query_pipeline import InputComponent,CustomQueryComponent
from llama_index.graph_stores.neo4j import Neo4jGraphStore
from llama_index.core import Document,KnowledgeGraphIndex,StorageContext,VectorStoreIndex
from llama_index.vector_stores.neo4jvector import Neo4jVectorStore
from llama_index.core.node_parser import (
    SemanticSplitterNodeParser,
)
import qdrant_client
from llama_index.core import SimpleDirectoryReader
from llama_index.vector_stores.qdrant import QdrantVectorStore

from langchain_openai import ChatOpenAI

import os
import dotenv
import urllib.request

# import phoenix as px
from typing import List,Dict,Any, Optional, Sequence, Tuple

from pydantic import BaseModel, Field
import re

import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from random import randint
from time import sleep
import math
import asyncio

from concurrent.futures import ThreadPoolExecutor
import threading
import json

from tqdm import tqdm
from collections import defaultdict
import shutil
import datetime
import random
import numpy as np

dotenv.load_dotenv()