import json

import boomi_cicd
import boomi_cicd.util.json.deployed_package
from boomi_cicd import logger


# https://help.boomi.com/bundle/developer_apis/page/r-atm-Deployed_Package_object.html


def create_deployed_package(release, package_id, environment_id, atom_id=None):
    """
    Create a deployed package in the Boomi environment.

    :param release: The release information.
    :type release: dict
    :param package_id: The ID of the package.
    :type package_id: str
    :param environment_id: The ID of the environment.
    :type environment_id: str
    :param atom_id: Optional atom ID to target deployment to a specific atom within the environment.
    :type atom_id: str or None
    :return: The deployment ID of the created package.
    :rtype: str
    """
    resource_path = "/DeployedPackage"

    payload = boomi_cicd.util.json.deployed_package.create()
    payload["environmentId"] = environment_id
    payload["packageId"] = package_id
    payload["notes"] = release["notes"]

    if "listenerStatus" in release:
        payload["listenerStatus"] = release["listenerStatus"]

    response = boomi_cicd.atomsphere_request(method="post", resource_path=resource_path, payload=payload)

    return json.loads(response.text)["deploymentId"]


def query_deployed_package(package_id, environment_id, currently_deployed=True, atom_id=None):
    """
    Query the deployed package status in the Boomi environment.

    :param package_id: The ID of the package.
    :type package_id: str
    :param environment_id: The ID of the environment.
    :type environment_id: str
    :param currently_deployed: Flag indicating if currently deployed packages should be queried (default: True).
    :type currently_deployed: bool
    :param atom_id: Optional atom ID to scope the query to a specific atom within the environment.
    :type atom_id: str or None
    :return: True if the package has already been deployed, False otherwise.
    :rtype: bool
    """
    resource_path = "/DeployedPackage/query"

    payload = boomi_cicd.util.json.deployed_package.query()
    payload["QueryFilter"]["expression"]["nestedExpression"][0]["argument"][0] = environment_id
    payload["QueryFilter"]["expression"]["nestedExpression"][1]["argument"][0] = package_id

    if currently_deployed:
        active_status = {"argument": [True], "operator": "EQUALS", "property": "active"}
        payload["QueryFilter"]["expression"]["nestedExpression"].append(active_status)

    response = boomi_cicd.atomsphere_request(method="post", resource_path=resource_path, payload=payload)

    number_of_results = json.loads(response.text)["numberOfResults"]
    if number_of_results:
        logger.info("Package has already been deployed.")
        return True
    else:
        return False


def delete_deployed_package(deployment_id):
    """
    Delete a deployed package in the Boomi environment.

    :param deployment_id: The ID of the deployment.
    :type deployment_id: str
    :return: The response text.
    :rtype: str
    """
    resource_path = "/DeployedPackage/{}".format(deployment_id)

    response = boomi_cicd.atomsphere_request(method="delete", resource_path=resource_path)
    return response.text
