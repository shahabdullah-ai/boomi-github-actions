import csv
import json
import time
import re

import requests

import boomi_cicd.util.json.connector_licensing
import boomi_cicd
from boomi_cicd import logging

# https://help.boomi.com/docs/Atomsphere/Integration/AtomSphere%20API/int-Connection_licensing_operation_a1412b83-b14d-4023-b274-b3212902f578


def create_connector_licensing_report(
    environment_id, request_interval_sec=5, max_wait_sec=300
):
    """
    Get the licensing CSV Report for a specific Boomi Environment.
    Pass "*" to get a report for all environments.
    The report can contain duplicates because it lists each process the connector is within.

    :param environment_id: The ID of the environment. Pass "*" to get the report for all environments.
    :type environment_id: str
    :param request_interval_sec: The time to wait between retries in seconds. Default is 5 seconds.
    :type request_interval_sec: int, optional
    :param max_wait_sec: The maximum wait time in seconds. Default is 300 seconds (5 minutes).
    :type max_wait_sec: int, optional
    :return: The response from the Atomsphere API ConnectionLicensing call. \
    Data is returned in CSV format.
    :rtype: Str
    """
    resource_path = f"/ConnectionLicensingReport"
    payload = boomi_cicd.util.json.connector_licensing.create()
    if environment_id != "*":
        payload["QueryFilter"]["expression"]["nestedExpression"][0]["argument"][
            0
        ] = environment_id
    else:
        payload["QueryFilter"]["expression"] = {}

    response = boomi_cicd.atomsphere_request(
        method="post", resource_path=resource_path, payload=payload, pass_error=True
    )

    error_url = _previous_download_check(response)

    cvs_report = None
    if error_url is not None:
        cvs_report = requests.get(
            error_url, auth=(boomi_cicd.USERNAME, boomi_cicd.PASSWORD)
        )
    else:
        attempt = 0
        response_code = 0
        timeout = time.time() + max_wait_sec

        while response_code != 200:
            cvs_report = _get_connector_licensing_report(response.json()["url"])
            response_code = cvs_report.status_code
            attempt += 1
            if response_code == 202:
                logging.info(
                    f"Connection Licensing Report is not complete. Attempt {attempt}. Retrying in {request_interval_sec} seconds."
                )
                time.sleep(request_interval_sec)
            if time.time() > timeout:
                logging.info(
                    f"create_connector_licensing_report failed after {max_wait_sec} seconds."
                )
                raise TimeoutError(
                    f"create_connector_licensing_report failed after {max_wait_sec} seconds."
                )

    return cvs_report.text


def _get_connector_licensing_report(url):
    """
    Get the licensing information for a given environment.

    :param url: The URL of the licensing report.
    :type url: str
    :return: The response from the Atomsphere API ConnectionLicensing call.
    :rtype: requests.Response
    """
    response = requests.get(url, auth=(boomi_cicd.USERNAME, boomi_cicd.PASSWORD))

    return response


def _previous_download_check(response):
    """
    Checks the response from an API call for specific error conditions related to a previous download attempt.

    If the response indicates an error (status code 400 and a message type of "Error"), this function
    extracts the error message, checks if it contains a URL, and logs the appropriate information.
    If a URL is found, it returns the URL; otherwise, it raises a ValueError.

    :param response: The response object from an API call, expected to have a JSON body.
    :type response: requests.Response

    :return: The URL found in the error message if present, otherwise None.
    :rtype: str or None

    :raises ValueError: If the error message does not contain a URL.

    :example JSON input:

    .. code-block:: json

       {
           "@type": "Error",
           "message": "The previous request for the Connection Licensing report did not download.
           To create a new request, complete the previous request with the GET API or download the report.
           Click the link
           to view or download the previous GET API URL report https://platform.boomi.com/account/boomi-account-id/api/download/ConnectionLicensing-6059a734-c149-4d2f-bd9e-1234567"
       }
    """
    message = response.json().get("message")

    if (
        response.json().get("@type") == "Error"
        and message is not None
        and response.status_code == 400
    ):
        logging.error(f"Error: {response.json().get('message')}")
        # Check if the error message contains a URL
        url = re.search(r"https?://\S+", message).group()
        if url is not None:
            logging.info(f"Download the previous report from {url}")
            return url
        else:
            logging.error(f"Unknown Error: {response.text}")
            raise ValueError(f"Unknown Error: {response.text}")

    return None


def convert_csv_report_to_json(csv_data):
    """
    Converts output of create_connector_licensing_report to a JSON-compatible list of dictionaries, where each row
    is represented as a dictionary with keys corresponding to the CSV headers.

    The first line of the CSV data is assumed to be a title and is ignored.

    :param csv_data: The CSV data as a single string.
                     The first line should be a title, and the subsequent lines
                     should contain CSV-formatted data with headers.
    :type csv_data: str

    :return: A list of dictionaries, where each dictionary represents a row from
             the CSV data, with keys corresponding to the headers.
    :rtype: list of dict

    .. code-block:: python

       # Example usage:
       environment_id = boomi_cicd.query_environment("Test Environment")
       csv_report = boomi_cicd.create_connector_licensing_report(environment_id)
       json_report = convert_csv_report_to_json(csv_report)
    """
    csv_lines = csv_data.splitlines()

    # Skip the first line because it contains the title
    csv_lines = csv_lines[1:]
    reader = csv.DictReader(csv_lines)
    json_data = [row for row in reader]

    return json_data
