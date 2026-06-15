import boomi_cicd
from boomi_cicd import logger


def get_package_component_manifest(packaged_component_id):
    """
    Get the manifest of a packaged component. This will include a list of components and their versions that are
    packaged within the packaged component.

    :param packaged_component_id: The ID of the packaged component.
    :type packaged_component_id: str
    :return: The manifest of the packaged component.
    :rtype: str
    """
    resource_path = f"/PackagedComponentManifest/{packaged_component_id}"
    logger.info(resource_path)

    response = boomi_cicd.atomsphere_request(method="get", resource_path=resource_path, accept_header="application/xml")

    return response.text
