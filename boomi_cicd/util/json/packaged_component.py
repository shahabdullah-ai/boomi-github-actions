import json


def create():
    data = json.loads(
        """
        {
            "componentId": "",
            "packageVersion": "",
            "notes": ""
        }
        """
    )
    return data


def query():
    data = json.loads(
        """
        {
            "QueryFilter": {
                "expression": {
                    "operator": "and",
                    "nestedExpression": [
                        {
                            "argument": [""],
                            "operator": "EQUALS",
                            "property": "componentId"
                        },
                        {
                            "argument": [""],
                            "operator": "EQUALS",
                            "property": "packageVersion"
                        }
                    ]   
                }
            }
        }"""
    )
    return data
