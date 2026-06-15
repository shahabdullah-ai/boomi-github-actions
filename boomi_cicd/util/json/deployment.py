import json


def query():
    data = json.loads(
        """
        {
            "QueryFilter" : 
                {
                    "expression" : 
                        {
                            "operator" : "and",
                            "nestedExpression": [
                                {
                                    "argument" : ["${envId}"],
                                     "operator":"EQUALS",
                                    "property":"environmentId"
                                },
                                {
                                    "argument":["${processId}"],
                                    "operator":"EQUALS",
                                    "property":"processId"
                                },
                                {
                                    "argument":["${current}"],
                                    "operator":"EQUALS",
                                    "property":"current"
                                }
                            ]
                        }
                }
        }"""
    )
    return data
