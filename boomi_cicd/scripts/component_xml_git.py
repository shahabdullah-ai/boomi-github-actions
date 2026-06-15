import boomi_cicd


# Open release json
releases = boomi_cicd.set_release()

# Clone repo
repo = boomi_cicd.clone_repository()
# Get parent folder name and component ID
file_components = boomi_cicd.get_component_xml_file_refs(boomi_cicd.COMPONENT_REPO_NAME)

for release in releases["pipelines"]:
    boomi_cicd.process_git_release(repo, file_components, release)

# Save parent folder name and component ID
boomi_cicd.set_component_xml_file_refs(boomi_cicd.COMPONENT_REPO_NAME, file_components)
# Commit and push changes
boomi_cicd.commit_and_push(repo)
