from common_imports import *
from utils import *
from graph_maker_utils import *

# This class is a cache implementation
# For similar queries, we can use the cache to avoid redundant computation
# Use langchain_openai_emb to similarity between queries 
# If the similarity is above a certain threshold, we can use the cached response
# After 2 cache Hit on a same query, we can report cache miss and delete the cache for that query
class QCache:
    def __init__(self,threshold = 0.98,window_size = 3):
        self.cache_meta = []
        self.cache_emb = []
        self.embedder = langchain_OpenAIEmbeddings()
        self.threshold = threshold
        self.window_size = window_size

    def get_cache(self,query):
        try:
            qry_emb = self.embedder.embed_documents([query])
            sim_scores = cosine_similarity(qry_emb,self.cache_emb)[0]
            top_match = np.argmax(sim_scores)
            if sim_scores[top_match] > self.threshold:
                if self.cache_meta[top_match]['catche_hit_count'] > self.window_size:
                    self.cache_meta.pop(top_match)
                    self.cache_emb.pop(top_match)
                    print(f"Log : Cache Window Exceeded | Sim : {sim_scores[top_match]}")
                    return None
                self.cache_meta[top_match]['catche_hit_count'] += 1
                print(f"Log : Cache Hit | Sim : {sim_scores[top_match]}")
                return self.cache_meta[top_match]["response"]
            else:
                print(f"Log : Cache Miss | Sim : {sim_scores[top_match]}")
                return None
        except:
            print("Log : Cache Miss (Exception)")
            return None
        
    def add_cache(self,query,response,force_add = True):
        if not force_add:
            _ = self.get_cache(query)
            print("LOG : Cache miss | Adding Cache")
            if _ is not None:
                return False
        qry_emb = self.embedder.embed_documents([query])[0]
        self.cache_meta.append({
            'query': query,
            'response': response,
            'catche_hit_count': 0
        })
        self.cache_emb.append(qry_emb)
        print("Log : Cache Added")
        return True





"""

**************************************************** PYDACTIC CLASSES ************************************************

"""


class RuleIDAction(BaseModel):
    rule_id: int =  Field(..., title="Rule ID")
    action: str =  Field(..., title="Reason for violation of the rule")

class ViolatedRuleIDs(BaseModel):
    rule_id_list: List[RuleIDAction] =  Field(..., title="List of Rule IDs and User Actions that violate the rules related to AI and Digital Ethics and Practices.")

class ListOfSentences(BaseModel):
    sentence_list: List[str] =  Field(..., title="List of sentences.")

class BotResponse(BaseModel):
    response: str = Field(..., title="Response from AI Bot")

class RuleViolationResult(BaseModel):
    is_a_violation: bool = Field(..., title="""
                                 Is the given context violating the given rules and prohibitions? 
                                 True means the context is violating the rules and prohibitions.
                                 False means the context is NOT violating the rules and prohibitions.
                                 """)
    
    is_rule_related_to_context: bool = Field(..., title="""
                                            Does the action in the context relate to the given rules and prohibitions?
                                            True means the context is related to the rules and prohibitions.
                                            False means the context is NOT related to the rules and prohibitions.
                                            """)

    is_realted_ai_digital_ethics: bool = Field(..., title="""
                                            Is the Context related to AI and Digital Ethics and Practices?
                                            True means the Context is related to and violating AI and Digital Ethics and Practices.
                                            False means the Context is NOT related to and violating AI and Digital Ethics and Practices.
                                               """)
    
    is_user_trying_to_violate : bool = Field(..., title="""
                                    Is the user trying to violate the rules and prohibitions ? This includes 
                                    user is trying to generate some vulnerable contents , or trying to get suggestion to do so , or trying to break the rules.
                                    True means the user is trying to violate the rules and prohibitions.
                                    False means the user is NOT trying to violate the rules and prohibitions.
                                    """
                                    )

    reason: str = Field(..., title="""
                        Very brief Reason for the violation of the rules and prohibitions. 
                        It should be from the contexts ONLY.
                        """
    )


class ContextValidator(BaseModel):
    is_related:bool = Field(..., title='''
                            To check if two given contexts are related or not.
                            True means the two contexts are related.
                            False means the two contexts are NOT related.
                            '''
                            )

class RuleValidator(BaseModel):
    is_related:bool = Field(..., title='''
                            To check if the given context is somehow violating the rules and prohibitions.
                            True means the context is violating the rules and prohibitions.
                            False means the context is NOT violating the rules and prohibitions.
                            '''
                            )









"""

**************************************************** QUERY PROCESSING CLASS ************************************************

"""

class QueryProcessing:
    def __init__(self, kg_path_dict_path:str, vector_store_wrapper:VectorStoreWrapper,store_new:bool=False):
        """
        kg_path_dict_path : str : Path to the dictionary containing the paths of the knowledge graph
        vector_store_wrapper : VectorStoreWrapper : VectorStoreWrapper object
        store_new : bool : If True, store the new knowledge graph
        """
        self.qry_degen_engine = JSON_Engine(prompt="""
                               Here is the user query:
                               {text}
                               
                               '''
                               Break down the user query into a list of sentences which may monitored for assessing the AI and Digital Ethics and Practices. 
                               '''

                               '''
                               Note: Each sentence should be a complete sentence and from the user query.
                               Note: Empy list may be returned if no sentences are found. 
                               '''
                               
                               """, class_name=ListOfSentences)
        
        
        self.rule_check_engine = JSON_Engine(prompt="""
                                Context (between <<< and >>>)
                                <<<                
                                {text_sub_prompt}
                                >>>
                                
                                
                                Rule and Prohibition (between ### and ###)
                                ###
                                {single_rule_sub_prompt}
                                ###

                                Your task is to check if the Context (the text between <<< and >>>) violates the Rule and Prohibition (the text between ### and ###).
                                """, class_name=RuleViolationResult,temperature=0.0)

        self.context_validator_engine = JSON_Engine(prompt="""  
                                Context 1 (between <<< and >>>)
                                <<<
                                {context1}
                                >>>
                                                    
                                Context 2 (between ### and ###)
                                ###
                                {context2}
                                ###
                                                    
                                Your task is to check if the Context 1 (the text between <<< and >>>) implies to the Context 2 (the text between ### and ###) for the AI and Digital Ethics Violations.
                                       """ , class_name=ContextValidator,temperature=0.0) 

        self.rule_validator_engine = JSON_Engine(prompt="""
                                Rule (between <<< and >>>)
                                <<<
                                {rule_sub_prompt}
                                >>>
                                       

                                Action (between ### and ###)
                                ###
                                {action_sub_prompt}
                                ###
                                                           
                                Does any of the actions in the Action (the text between ### and ###) relate to the Rule (the text between <<< and >>>) ?
                                                 """
                                                 , class_name=RuleValidator,temperature=0.0)


        self.reply_engine = ChatOpenAI(model="gpt-3.5-turbo",temperature=0.1)
        self.graph_store_obj = GraphMaker(dict_path=kg_path_dict_path,vector_store_wrapper=vector_store_wrapper,store_new=store_new)
        self.rule_ret = self.graph_store_obj.index.as_retriever(similarity_top_k=1)
        self.qcache = QCache(threshold = 0.95,window_size = 1)
    

    # method to retrieve rules from the knowledge graph
    def rule_retrieval(self, sub_qry_list):
        rules = set()
        for _ in sub_qry_list:
            rules_ = self.rule_ret.retrieve(_)
            for __ in rules_:
                rules.add(__.text)
        return list(rules)
    

    # method to get the response from the chatgpt model
    def chatgpt_reponse_engine(self,user_req_text):
        response = self.reply_engine.run(query=user_req_text)
        return response

    
    # method to process the user query
    def process_query(self, user_req_text,verbose=False,cached=True):
        """
        user_req_text : str : User query text
        verbose : bool : If True, print the details of the processing
        cached : bool : If True, use the cache for the response
        """
        if cached:
            cache_response = self.qcache.get_cache(user_req_text)
            if cache_response is not None:
                return cache_response
        
        sub_qry_list = self.qry_degen_engine.run(text=user_req_text).sentence_list
        if len(sub_qry_list)<=3:
            sub_qry_list = [user_req_text]
        rules = self.rule_retrieval(sub_qry_list)

        for i in range(len(rules)):
            rules[i] =  (rules[i].split('->')[-2]+"->"+rules[i].split('->')[-1])
        rules = list(set(rules))

        rule_sub_prompt = "\n".join([f"Rule-id {str(i)} : {rules[i]}" for i in range(len(rules))])
        action_sub_prompt = "\n".join([_ for _ in sub_qry_list])

        # Using rule_check engine Use action_sub_prompt and each rules
        root_to_leaf_lists = []
        for i in range(len(rules)):
            single_rule_sub_prompt = rules[i]
            rule_check_ans = self.rule_check_engine.run(text_sub_prompt=action_sub_prompt, single_rule_sub_prompt=single_rule_sub_prompt)
            if rule_check_ans.is_a_violation and rule_check_ans.is_rule_related_to_context: # and rule_check_ans.is_user_trying_to_violate:# and rule_check_ans.is_realted_ai_digital_ethics:
                root_to_leaf_lists.append([self.graph_store_obj.get_path_from_root_to_node(rules[i].split(" -> ")[-1]),rule_check_ans.reason])
            else:
                pass

            
        # Print with indentation and risk too
        filtered_root_to_leaf_lists = []
        for i in range(len(root_to_leaf_lists)):
            path = root_to_leaf_lists[i][0]
            action = root_to_leaf_lists[i][1]
            is_related = self.context_validator_engine.run(context1=action_sub_prompt, context2=action).is_related
            is_related_rule = self.rule_validator_engine.run(action_sub_prompt=action, rule_sub_prompt=rules[i]).is_related
            if is_related and is_related_rule:
                filtered_root_to_leaf_lists.append([path,action])
            else:
                pass
        root_to_leaf_lists = filtered_root_to_leaf_lists


        risk_list = {
            "minimal" : 1,
            "medium" : 2,
            "high" : 3,
            "critical" : 4
        }

        response_dict = {
            "query":user_req_text,
            "High level violations":defaultdict(list),
            "risk":0,
            "response":"Sorry, I can not help you with this query."
        }


        for i in range(len(root_to_leaf_lists)):
            root_to_leaf_list = root_to_leaf_lists[i]
            path = root_to_leaf_list[0]
            action = root_to_leaf_list[-1]
            if len(path)<3:
                continue
            response_dict["High level violations"][path[-3]].append([path[-2]+"->"+path[-1],action])
            response_dict["risk"]=max(response_dict["risk"],risk_list[self.graph_store_obj.children_list_dict[path[-1]]["risk"]])
            for j in range(len(path)):
                node = path[j]
                node_properties = self.graph_store_obj.children_list_dict[node]
                if verbose:
                    print(f"{'  ' * j} node: {node}, depth: {node_properties.get('depth', None)}, risk: {node_properties.get('risk', None)}")
        
        if response_dict["risk"]==0:
            response_dict["response"] = self.reply_engine.invoke(user_req_text).content

        if cached:
            self.qcache.add_cache(user_req_text,response_dict)
        return response_dict