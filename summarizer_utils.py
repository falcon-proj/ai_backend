from common_imports import *



#Pydanctic classes for the key points list
class KeyPoint(BaseModel):
    key_point: str = Field(..., description=
                            """
                            A title that describes the a small chunk of text 
                            """)
    examples: List[str] = Field(..., description=
                            """
                            A list of examples that are present for the key point
                            as present in the text
                            """)
    
    contains_rule_risk: bool = Field(..., description=
                            """
                            This indicates whether or not the text is related to AI practices or digital practices.
                            True if the text is a definition of a rule or risk related to AI practices or digital practices.
                            False if it is a random text or does not contain ny relation to AI practices or digital practices.
                            """)




#Pydanctic classes for the key points list
class KeyPointList(BaseModel):
    title : str = Field(..., description=
                            """
                            A title that describes the whole text
                            """)
    key_points: List[KeyPoint] = Field(..., description=
                            """
                            A list of key points along with their examples as present in the text
                            """)
    



#Pydanctic classes for short form of large text
class ShortForm(BaseModel):
    short_form: str = Field(..., description=
                            """
                            A short form of the text
                            """)
    
