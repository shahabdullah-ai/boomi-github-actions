import json
import time
import boomi_cicd
import boomi_cicd.util.json.generic_connector_record
from boomi_cicd.util import logging


def query_generic_connector_record(
    execution_id, execution_connector_id, request_interval_sec=10, max_wait_sec=300
):
    """
    Query the GenericConnectorRecord by the Execution ID and ExecutionConnector ID.

    This function sends a request to the AtomSphere API
    to query for a Generic Connector Record from a specific execution.

    :param execution_id: The Boomi execution ID.
    :type execution_id: str
    :param execution_connector_id: The execution connector ID from the ExecutionConnector object.
    :type execution_connector_id: str
    :param request_interval_sec: The time to wait between retries in seconds. Default is 10 seconds.
    :type request_interval_sec: int, optional
    :param max_wait_sec: The maximum wait time in seconds. Default is 300 seconds (5 minutes).
    :type max_wait_sec: int, optional
    :return: The JSON response containing the queried GenericConnectorRecord.
    :rtype: dict
    :raises ValueError: If the GenericConnectorRecord is not found after max wait time.
    :raises requests.RequestException: If the request fails.
    """
    resource_path = "/GenericConnectorRecord/query"

    payload = boomi_cicd.util.json.generic_connector_record.query()
    payload["QueryFilter"]["expression"]["nestedExpression"][0]["argument"][
        0
    ] = execution_id
    payload["QueryFilter"]["expression"]["nestedExpression"][1]["argument"][
        0
    ] = execution_connector_id

    attempt = 0
    json_response = None
    number_of_records = 0
    timeout = time.time() + max_wait_sec

    while number_of_records == 0 and time.time() < timeout:
        response = boomi_cicd.atomsphere_request(
            method="post", resource_path=resource_path, payload=payload
        )
        json_response = json.loads(response.text)
        number_of_records = json_response["numberOfResults"]
        attempt += 1
        if number_of_records == 0:
            logging.info(
                f"GenericConnectorRecord not found. Attempt {attempt}. Retrying in {request_interval_sec} seconds."
            )
            time.sleep(request_interval_sec)

    return json_response


def get_generic_connector_record(generic_connector_record_id):
    """
    Retrieve a specific GenericConnectorRecord by its ID.

    This function sends a GET request to the Boomi AtomSphere API to fetch a GenericConnectorRecord
    using the provided record ID. It is intended to be called after `query_generic_connector_record`
    to fetch the details of a specific record.

    :param generic_connector_record_id: The ID of the GenericConnectorRecord to retrieve.
    :type generic_connector_record_id: str
    :return: The JSON response containing the GenericConnectorRecord details.
    :rtype: dict
    :raises ValueError: If the response cannot be parsed as JSON.
    :raises requests.RequestException: If the request fails.
    :param generic_connector_record_id:
    :return:
    """
    resource_path = f"/GenericConnectorRecord/{generic_connector_record_id}"

    response = boomi_cicd.atomsphere_request(method="get", resource_path=resource_path)

    return json.loads(response.text)
