from common_imports import *


# Pydanctic classes for Rule 
class Rule(BaseModel):
    rule_prohibition: str = Field(..., description=
                                                """
                                                It must be a specific type of rule/prohibition.
                                                It must be within 3 to 4 words that describes the rule/prohibition.
                                                """)
    risk_category: str = Field(..., description=
                                                """
                                                It denotes the severity of the violation of rules and prohibitions.
                                                "minimal" risk is for least severe violation, "medium" risk is for not so severe violation,
                                                "high" risk is for highly severe violation, "critical" risk is for most severe violation.
                                                """, enum= ["minimal","medium","high","critical"])
    instances: List[str] = Field(..., description=
                                 """
                                    A list of all instances/examples which are applicable to the rule/prohibition as present in the text.
                                    These can be the examples, inferrings, or instances of the rules/prohibitions.
                                    Keep every type of instances/examples/inferrings seperately in the instances list as mentioned in the text.  
                                    This list should contain more than 5 instances.

                                    DON'T miss any instances/examples/inferrings.
                                    """
    )

# Pydanctic classes for RuleList
class RuleList(BaseModel):
    rules: List[Rule] = Field(..., description=
                            """
                            A list of rules/prohibitions along with their risk categories and All instances as present in the text.
                            """)