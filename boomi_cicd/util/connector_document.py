import json
import time
import requests
import boomi_cicd
from boomi_cicd import logger


# https://help.boomi.com/bundle/developer_apis/page/r-atm-Atom_object.html


def get_connector_document(
    generic_connector_record_id, /, *, request_interval_sec=10, max_wait_sec=300
):
    """
    Download and view the connector document data for a Generic Connector Record.
    The Connector Document operation allows you to download the raw, document data
    for a specific Generic Connector Record. The data is equivalent to viewing and
    downloading document data through the Process Reporting page.

    :param generic_connector_record_id: The ID of the GenericConnectorRecord.
    :type generic_connector_record_id: str
    :param request_interval_sec: The time to wait between retries in seconds. Default is 10 seconds.
    :type request_interval_sec: int, optional
    :param max_wait_sec: The maximum wait time in seconds. Default is 300 seconds (5 minutes).
    :type max_wait_sec: int, optional
    :return: The payload of the connector document.
    :rtype: str
    :raises TimeoutError: If the connector document is not available after the maximum wait time.
    :raises requests.RequestException: If the request fails.
    """
    resource_path = "/ConnectorDocument"

    payload = {"genericConnectorRecordId": generic_connector_record_id}

    status_code = 202
    response = None
    timeout = time.time() + max_wait_sec

    while status_code == 202:
        response = boomi_cicd.atomsphere_request(
            method="post", resource_path=resource_path, payload=payload
        )
        status_code = response.status_code
        if status_code == 202:
            time.sleep(request_interval_sec)
        if time.time() > timeout:
            logger.info(f"get_connector_document failed after {max_wait_sec} seconds.")
            raise TimeoutError(
                f"get_connector_document failed after {max_wait_sec} seconds."
            )

    url = json.loads(response.text)["url"]
    headers = {"Accept": "*/*"}
    status_code = 202
    timeout = time.time() + max_wait_sec

    while status_code == 202:
        response = requests.get(
            url, auth=(boomi_cicd.USERNAME, boomi_cicd.PASSWORD), headers=headers
        )
        status_code = response.status_code
        if status_code == 202:
            time.sleep(request_interval_sec)
        if time.time() > timeout:
            logger.info(f"get_connector_document failed after {max_wait_sec} seconds.")
            raise TimeoutError(
                f"get_connector_document failed after {max_wait_sec} seconds."
            )

    return response.text
