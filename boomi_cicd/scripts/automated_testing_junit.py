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

    # Check if automated testing is required
    if automated_test_component_id:
        # The same package version for the main process will be used to keep the versions in parallel.
        automated_test_package_id = boomi_cicd.query_packaged_component(
            automated_test_component_id, package_version
        )
        package_id = boomi_cicd.query_packaged_component(component_id, package_version)

        # Only perform deployments and tests on newly packaged components.
        if not package_id and not automated_test_package_id:
            automated_test_package_id = boomi_cicd.create_packaged_component(
                automated_test_component_id, package_version, notes
            )
            package_id = boomi_cicd.query_packaged_component(
                component_id, package_version
            )

            # Deploy the automated test harness
            boomi_cicd.create_deployed_package(
                release, automated_test_package_id, environment_id
            )

            # Execute the test process
            request_id = boomi_cicd.create_execution_request(
                atom_id, automated_test_component_id
            )

            # Check the execution's completion status.
            execution_response = boomi_cicd.get_completed_execution_status(request_id)

            # Log the results of the test.  Anything other than COMPLETE means the executed failed.
            if execution_response["status"] == "COMPLETE":
                # Since the process executed successfully,
                # query the execution to get the document at the return document shape.
                # That document should be in a JUnit format and writen to disk.
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
            else:
                raise AssertionError(
                    "One or more automated tests failed. Please see logs for more information."
                )
        else:
            logging.warning(
                f"Automation test for {process_name} was skipped. Package already exists."
            )
    else:
        logging.warning(f"Automation test for {process_name} was skipped.")


# Once the all tests have completed, the release_pipeline.py script can be used to deploy the processes.
# JUnit test results can often throw errors within the deployment tool when errors are present.
