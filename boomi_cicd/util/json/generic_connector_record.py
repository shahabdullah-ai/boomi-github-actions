def query():
    data = {
        "QueryFilter": {
            "expression": {
                "operator": "and",
                "nestedExpression": [
                    {
                        "argument": [""],
                        "operator": "EQUALS",
                        "property": "executionId",
                    },
                    {
                        "argument": [""],
                        "operator": "EQUALS",
                        "property": "executionConnectorId",
                    },
                ],
            }
        }
    }
    return data
