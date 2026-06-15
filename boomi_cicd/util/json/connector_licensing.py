def create():
    data = {
        "@type": "ConnectionLicensingReport",
        "QueryFilter": {
            "expression": {
                "operator": "and",
                "nestedExpression": [
                    {
                        "argument": [""],
                        "operator": "EQUALS",
                        "property": "environmentId",
                    }
                ],
            }
        },
    }
    return data
