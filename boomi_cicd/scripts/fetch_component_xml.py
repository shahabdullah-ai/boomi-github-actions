import os
import boomi_cicd


def main():
    releases = boomi_cicd.set_release()
    base_dir = os.environ.get("BOOMI_COMPONENT_REPO_NAME", "boomi_components")
    os.makedirs(base_dir, exist_ok=True)

    for release in releases["pipelines"]:
        component_id = release["componentId"]
        name = release.get("notes", component_id)
        xml = boomi_cicd.query_component(component_id)

        safe_name = name.replace("/", "_").replace("\\", "_")
        out_path = os.path.join(base_dir, f"{safe_name}.xml")
        with open(out_path, "w") as f:
            f.write(xml)
        print(f"[fetch] {name} → {out_path}")

    print(f"[fetch] {len(releases['pipelines'])} components written to {base_dir}")


if __name__ == "__main__":
    main()
