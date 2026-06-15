import boomi_cicd


def query_component_metadata(component_id):
    """
    Query a component's metadata by its ID in the Boomi platform.

    This function retrieves metadata information for a specified component
    within the Boomi platform using the provided component ID.

    Upon a successful request, the response containing the component's
    metadata is returned in JSON format.

    :param component_id: The Boomi component id that will be used within the query.
    :type component_id: str
    :return:
        A dictionary representation of the JSON response containing the
        metadata of the queried component.
    :rtype: dict
    """
    resource_path = f"/ComponentMetadata/{component_id}"
    response = boomi_cicd.atomsphere_request(method="get", resource_path=resource_path)
    return response.json()