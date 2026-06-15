import time
import boomi_cicd
from boomi_cicd import logger


def get_execution_record(request_id):
    """
    Sends a GET request to the Boomi AtomSphere API to retrieve the execution record for a given request ID.
    The request ID can be obtained from execution_request.create_execution_request().

    :param request_id: The requeste id from Execution Request.
    :type request_id: str
    :return: The response from the Atomsphere API ExecutionRecord call.
    :rtype: requests.Response
    """

    resource_path = f"/ExecutionRecord/async/{request_id}"
    response = boomi_cicd.atomsphere_request(method="get", resource_path=resource_path)

    return response


def get_execution_status(request_id, request_internal_sec=10, max_wait_sec=300):
    """
    Sends a GET request to the Boomi AtomSphere API to retrieve the execution status for a given request ID.
    The function keeps sending requests until the status code is not 202, which means the execution is still pending
    or until the maximum wait time is exceeded.
    This function will return whatever the status is within Process Reporting.

    :param request_id: The request ID from Execution Request.
    :type request_id: str
    :param request_internal_sec: The interval in seconds between each request. Default is 10 seconds.
    :type request_internal_sec: int
    :param max_wait_sec: The maximum time in seconds to keep making a request.\
    Default is 300 seconds (5 minutes).
    :type max_wait_sec: int
    :return: The first result from the response of the Atomsphere API ExecutionRecord call. \
    The dict will contain executionId and status. \
    The values of status are: ABORTED, COMPLETE, COMPLETE_WARN, DISCARDED, ERROR, INPROCESS, STARTED
    :rtype: dict
    :raises TimeoutError: If the maximum wait time is exceeded, a TimeoutError is raised.
    """

    response = None
    attempt = 0
    response_status_code = 202
    timeout = time.time() + max_wait_sec

    while response_status_code == 202:
        attempt += 1
        logger.info(f"Getting Status of Execution Record. Attempt {attempt}.")
        response = get_execution_record(request_id)
        response_status_code = response.status_code
        if response_status_code == 202:
            time.sleep(request_internal_sec)

        if time.time() > timeout:
            logger.info(f"get_execution_status failed after {max_wait_sec} seconds.")
            raise TimeoutError(
                f"get_execution_status failed after {max_wait_sec} seconds."
            )

    return response.json()["result"][0]


def get_completed_execution_status(
    request_id, request_interval_sec=10, max_wait_sec=300
):
    """
    Sends a GET request to the Boomi AtomSphere API to retrieve the completed execution status for a given request ID.
    The function keeps sending requests until the status is not 'INPROCESS' or until the maximum wait time is exceeded.
    This function will return the final status of the process execution.

    :param str request_id: The request ID from Execution Request.
    :param int request_interval_sec: The interval in seconds between each request. Default is 10 seconds.
    :param int max_wait_sec: The maximum time in seconds to keep making a request. Default is 300 seconds, 5 minutes.
    :return: The response from the Atomsphere API ExecutionRecord call. The dict will contain executionId and status.
    :rtype: dict
    :raises TimeoutError: If the maximum wait time is exceeded, a TimeoutError is raised.
    """

    response = None
    status = "INPROCESS"
    execution_count = 0
    timeout = time.time() + max_wait_sec

    while status == "INPROCESS":
        execution_count += 1
        logger.info(
            f"Getting Completion Status of Execution Record. Attempt {execution_count}."
        )

        response = get_execution_status(request_id, request_interval_sec, max_wait_sec)
        status = response.get("status")

        if status == "INPROCESS" or status is None:
            time.sleep(request_interval_sec)
        if time.time() > timeout:
            logger.info(f"get_execution_status failed after {max_wait_sec} seconds.")
            raise TimeoutError(
                f"get_execution_status failed after {max_wait_sec} seconds."
            )

    return response
