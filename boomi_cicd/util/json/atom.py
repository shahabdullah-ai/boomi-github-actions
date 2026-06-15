import json


def query():
    data = json.loads(
        """
        {
            "QueryFilter": {
                "expression": {
                    "argument": [""],
                    "operator": "EQUALS",
                    "property": "name"
                }
            }
        }"""
    )
    return data
