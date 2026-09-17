import boomi_cicd
from boomi_cicd.util import logging

# Open release json
releases = boomi_cicd.set_release()

environment_id = boomi_cicd.query_environment(boomi_cicd.ENVIRONMENT_NAME)
atom_id = boomi_cicd.query_atom(boomi_cicd.ATOM_NAME)

for release in releases["pipelines"]:
    process_name = release["processName"]
    component_id = release["componentId"]
    automated_test_component_id = release.get("automatedTestId")
    package_version = release["packageVersion"]
    notes = release.get("notes")

    if not automated_test_component_id:
        logging.warning(
            f"No automated test harness for {process_name}. Add a process named "
            f"'{process_name} - Test' in the same folder to enable one."
        )
        continue

    # Run the harness on EVERY promotion.
    #
    # This previously ran only `if not package_id and not automated_test_package_id`,
    # meaning "only test newly packaged components". That guard could never be true:
    # generate_release.py records the package version of an already-existing package,
    # so package_id was always populated and the test was skipped with a warning while
    # the stage reported success. A gate that silently passes is worse than no gate.
    automated_test_package_id = boomi_cicd.query_packaged_component(
        automated_test_component_id, package_version
    ) or boomi_cicd.create_packaged_component(
        automated_test_component_id,
        package_version,
        notes,
        release.get("branchId"),
    )

    # The harness is packaged at the same version as the process under test so the two
    # stay in lockstep, and deployed because ExecutionRequest can only run a deployed
    # process.
    boomi_cicd.create_deployed_package(
        release, automated_test_package_id, environment_id
    )

    request_id = boomi_cicd.create_execution_request(
        atom_id, automated_test_component_id
    )
    execution_response = boomi_cicd.get_completed_execution_status(request_id)

    # Execution status is the gate, not the JUnit content: a JUnit <failure> alone only
    # marks a Jenkins build UNSTABLE, which would let the promotion continue. The harness
    # is expected to raise an Exception on a failed assertion.
    if execution_response["status"] != "COMPLETE":
        raise AssertionError(
            f"Automated test failed for {process_name} "
            f"(status: {execution_response['status']}). See the process log for details."
        )

    # The harness returns its results at a Return Documents shape; query_execution_connector
    # defaults to connector type "return". The document is already JUnit XML and is written
    # out verbatim for the CI tool to pick up.
    execution_record_id = boomi_cicd.query_execution_connector(
        execution_response["executionId"]
    )
    generic_connector_record = boomi_cicd.query_generic_connector_record(
        execution_response["executionId"],
        execution_record_id["result"][0]["id"],
    )
    get_connector_document = boomi_cicd.get_connector_document(
        generic_connector_record["result"][0]["id"]
    )

    cleaned_document = get_connector_document.replace("\r\n", "\n").strip()
    with open(f"test-{process_name}.xml", "w", encoding="utf-8") as f:
        f.write(cleaned_document)
    logging.info(f"Automated test passed for {process_name}.")


# Once the all tests have completed, the release_pipeline.py script can be used to deploy the processes.
# JUnit test results can often throw errors within the deployment tool when errors are present.
