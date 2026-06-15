import json
import time

import boomi_cicd
import boomi_cicd.util.json.execution_connector
from boomi_cicd.util import logging

# https://help.boomi.com/docs/Atomsphere/Integration/AtomSphere%20API/int-Execution_connector_object_abb28203-9946-4c03-9205-8dc95b8f3f41


def query_execution_connector(
    execution_id, connector_type="return", request_interval_sec=10, max_wait_sec=300
):
    """
    Query the ExecutionConnector by the Execution ID and connector type.

    This function sends a request to the AtomSphere API to query for an ExecutionConnector
    with the specified execution ID and connector type. It retries the request at
    specified intervals until a record is found or the maximum wait time is reached.
    The default connector type is "return" because it is mainly intended for use within automated testing.

    :param execution_id: The Boomi execution ID.
    :type execution_id: str
    :param connector_type: The type of the connector to query. Default is "return".
    :type connector_type: str, optional
    :param request_interval_sec: The time to wait between retries in seconds. Default is 10 seconds.
    :type request_interval_sec: int, optional
    :param max_wait_sec: The maximum wait time in seconds. Default is 300 seconds (5 minutes).
    :type max_wait_sec: int, optional
    :return: The JSON response containing the queried ExecutionConnector.
    :rtype: dict
    :raises ValueError: If the ExecutionConnector is not found after max wait time.
    :raises requests.RequestException: If the request fails.
    """
    resource_path = "/ExecutionConnector/query"

    payload = boomi_cicd.util.json.execution_connector.query()
    payload["QueryFilter"]["expression"]["nestedExpression"][0]["argument"][
        0
    ] = execution_id
    payload["QueryFilter"]["expression"]["nestedExpression"][1]["argument"][
        0
    ] = connector_type

    # The ExecutionConnector may not be immediately available. Loop if needed.
    attempt = 0
    number_of_records = 0
    response = None
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
                f"ExecutionConnector not found. Attempt {attempt}. Retrying in {request_interval_sec} seconds."
            )
            time.sleep(request_interval_sec)

    return json.loads(response.text)
