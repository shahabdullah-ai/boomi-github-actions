import json


def template():
    data = json.loads(
        """
        {
            "@type": "EnvironmentExtensions",
            "connections": {
                "@type": "Connections",
                "connection": []
            },
            "processProperties": {
                "@type": "OverrideProcessProperties",
                "ProcessProperty": []
            },
            "properties": {
                "@type": "OverrideProperties",
                "property": []
            },
            "crossReferences": {
                "@type": "CrossReferences",
                "crossReference": []
            },
            "environmentId": "",
            "extensionGroupId": "",
            "id": "",
            "partial": true
        }"""
    )
    return data
