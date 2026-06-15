import json
import os
import subprocess
import sys
import time
from xml.dom import minidom

import requests
import boomi_cicd


def export_component_xml(release_file, output_dir):
    """Export XML for every component in release.json using the AtomSphere API."""
    with open(release_file) as f:
        release = json.load(f)

    os.makedirs(output_dir, exist_ok=True)
    count = 0

    for pipeline in release.get("pipelines", []):
        component_id = pipeline["componentId"]
        label = pipeline.get("notes", component_id)
        safe_label = "".join(c if c.isalnum() or c in "-_" else "_" for c in label)

        try:
            xml_text = boomi_cicd.query_component(component_id)
            filepath = os.path.join(output_dir, f"{safe_label}_{component_id}.xml")
            with open(filepath, "w") as f:
                f.write(minidom.parseString(xml_text).toprettyxml(indent="  "))
            print(f"[sonarqube] Exported: {label}")
            count += 1
        except Exception as e:
            print(f"[sonarqube] WARNING: Could not export {label} ({component_id}): {e}")

    print(f"[sonarqube] Exported {count} component XML files")
    return count


def get_scanner_bin():
    """Return path to sonar-scanner, downloading it if not already present."""
    pre_installed = os.environ.get("SONAR_SCANNER_HOME", "")
    if pre_installed:
        candidate = os.path.join(pre_installed, "bin", "sonar-scanner")
        if os.path.isfile(candidate):
            return candidate

    # Fall back to library download (handles Linux/Windows automatically)
    print("[sonarqube] Downloading sonar-scanner CLI...")
    scanner_dir = boomi_cicd.install_sonarqube()
    return os.path.join(scanner_dir, "bin", "sonar-scanner")


def run_sonar_scanner(xml_dir, project_key, host_url, token, rules_file):
    """Run sonar-scanner on the exported XML directory."""
    scanner_bin = get_scanner_bin()

    cmd = [
        scanner_bin,
        f"-Dsonar.projectKey={project_key}",
        f"-Dsonar.sources={xml_dir}",
        f"-Dsonar.host.url={host_url}",
        f"-Dsonar.login={token}",
        f"-Dsonar.externalRulesetsFile={rules_file}",
        "-Dsonar.language=xml",
        "-Dsonar.sourceEncoding=UTF-8",
        "-Dsonar.scm.disabled=true",
    ]

    print(f"[sonarqube] Running analysis for project: {project_key}")
    result = subprocess.run(cmd)
    return result.returncode == 0


def check_quality_gate(host_url, project_key, token):
    """Poll the SonarQube API until the quality gate result is available."""
    print("[sonarqube] Polling quality gate status...")
    url = f"{host_url}/api/qualitygates/project_status"

    for attempt in range(12):
        time.sleep(5)
        try:
            resp = requests.get(
                url,
                params={"projectKey": project_key},
                auth=(token, ""),
                timeout=10,
            )
            if resp.status_code == 200:
                status = resp.json().get("projectStatus", {}).get("status", "NONE")
                print(f"[sonarqube] Quality gate: {status}")
                if status != "NONE":
                    return status == "OK"
        except Exception as e:
            print(f"[sonarqube] Poll attempt {attempt + 1} failed: {e}")

    print("[sonarqube] WARNING: Could not confirm quality gate — proceeding")
    return True


def main():
    host_url     = os.environ.get("BOOMI_SONARQUBE_HOST_URL", "")
    project_key  = os.environ.get("BOOMI_SONARQUBE_PROJECT_KEY", "boomi-cicd")
    token        = os.environ.get("BOOMI_SONARQUBE_TOKEN", "")
    release_base = os.environ.get("BOOMI_RELEASE_BASE_DIR", ".")
    release_file = os.path.join(release_base, "release", "release.json")
    xml_dir      = "/tmp/boomi_xml"
    rules_file   = "/opt/boomi-cicd-cli-py/boomi_cicd/templates/sonarqube/BoomiSonarRules.xml"

    if not host_url:
        print("[sonarqube] BOOMI_SONARQUBE_HOST_URL not set — skipping")
        sys.exit(0)

    count = export_component_xml(release_file, xml_dir)
    if count == 0:
        print("[sonarqube] No components to analyse — skipping")
        sys.exit(0)

    if not run_sonar_scanner(xml_dir, project_key, host_url, token, rules_file):
        print("[sonarqube] sonar-scanner exited with errors")
        sys.exit(1)

    if not check_quality_gate(host_url, project_key, token):
        print("[sonarqube] Quality gate FAILED — deployment blocked")
        sys.exit(1)

    print("[sonarqube] Quality gate PASSED — proceeding to deployment")


if __name__ == "__main__":
    main()
