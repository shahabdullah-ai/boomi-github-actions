import json


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
                            "property": "atomId"
                        },
                        {
                            "argument": [""],
                            "operator": "EQUALS",
                            "property": "processId"
                        }
                    ]
                }
            }
        }"""
    )
    return data


def update():
    data = json.loads(
        """
        {
            "Schedule": [],
            "processId": "",
            "atomId": "",
            "id": ""
        }"""
    )
    return data
