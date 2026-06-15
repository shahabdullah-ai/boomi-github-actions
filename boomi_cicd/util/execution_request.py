import json
import boomi_cicd
import boomi_cicd.util.json.execution_request
from boomi_cicd import logger


def create_execution_request(atom_id, process_id):
    """
    Creates an execution request for a deployed process on a specific Boomi runtime.

    :param atom_id: The Id of the atom where the process will be executed.
    :type atom_id: str
    :param process_id: The component Id of the process to be executed.
    :type process_id: str
    :return: The Id of the execution request.
    :rtype: str
    :raises ValueError: If the execution request was not successful.
    """
    resource_path = "/ExecutionRequest"

    payload = boomi_cicd.util.json.execution_request.create()
    payload["atomId"] = atom_id
    payload["processId"] = process_id

    response = boomi_cicd.atomsphere_request(method="post", resource_path=resource_path, payload=payload)

    json_response = json.loads(response.text)
    if not json_response.get("requestId"):
        logger.error("ExecutionRequest was not successful")
        raise ValueError("ExecutionRequest was not successful")
    return json_response["requestId"]
