import json


def create():
    data = json.loads(
        """
        {
          "environmentId": "",
          "packageId": "",
          "notes": ""
        }"""
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
                            "argument": [
                                ""
                            ],
                            "operator": "EQUALS",
                            "property": "environmentId"
                        },
                        {
                            "argument": [
                                ""
                            ],
                            "operator": "EQUALS",
                            "property": "packageId"
                        }
                    ]
                }
            }
        }"""
    )
    return data
