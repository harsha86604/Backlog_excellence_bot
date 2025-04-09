import os
import requests
from requests.auth import HTTPBasicAuth
from urllib.parse import quote
from dotenv import load_dotenv

load_dotenv()

# Load environment variables
AZURE_ORG = os.getenv("AZURE_DEVOPS_ORG")      # e.g., "mycompany"
AZURE_PROJECT = os.getenv("AZURE_DEVOPS_PROJECT")  # e.g., "MyProject"
AZURE_PAT = os.getenv("AZURE_DEVOPS_PAT")      # Your Personal Access Token

if not (AZURE_ORG and AZURE_PROJECT and AZURE_PAT):
    raise ValueError("Azure DevOps environment variables are missing.")

BASE_URL = f"https://dev.azure.com/{AZURE_ORG}"
PROJECT_ENCODED = quote(AZURE_PROJECT)

def get_work_items():
    """
    Fetches all work items (by ID) from the specified Azure DevOps project.
    In practice, you’d likely use a WIQL query to refine which work items you want.
    """
    wiql_query = {
        "query": f"SELECT [System.Id] FROM WorkItems WHERE [System.TeamProject] = '{AZURE_PROJECT}'"
    }
    wiql_url = f"{BASE_URL}/{PROJECT_ENCODED}/_apis/wit/wiql?api-version=6.0"
    response = requests.post(wiql_url, json=wiql_query, auth=HTTPBasicAuth('', AZURE_PAT))
    response.raise_for_status()
    data = response.json()
    work_item_ids = [str(item["id"]) for item in data.get("workItems", [])]
    if not work_item_ids:
        return []
    # Now fetch details of each work item
    ids_str = ",".join(work_item_ids)
    details_url = f"{BASE_URL}/{PROJECT_ENCODED}/_apis/wit/workitems?ids={ids_str}&api-version=6.0"
    items_resp = requests.get(details_url, auth=HTTPBasicAuth('', AZURE_PAT))
    items_resp.raise_for_status()
    return items_resp.json().get("value", [])

def query_work_items(wiql: str):
    """
    Allows a custom WIQL query to retrieve work items.
    """
    wiql_query = {"query": wiql}
    wiql_url = f"{BASE_URL}/{PROJECT_ENCODED}/_apis/wit/wiql?api-version=6.0"
    response = requests.post(wiql_url, json=wiql_query, auth=HTTPBasicAuth('', AZURE_PAT))
    response.raise_for_status()
    data = response.json()
    return data.get("workItems", [])

def create_work_item(title: str, description: str, assignee: str = None, due_date: str = None, status: str = "To Do"):
    create_url = f"{BASE_URL}/{PROJECT_ENCODED}/_apis/wit/workitems/$Task?api-version=6.0"
    headers = {"Content-Type": "application/json-patch+json"}
    patch_document = [
        {"op": "add", "path": "/fields/System.Title", "value": title},
        {"op": "add", "path": "/fields/System.Description", "value": description},
        {"op": "add", "path": "/fields/System.State", "value": status},
        {"op": "add", "path": "/fields/Microsoft.VSTS.Scheduling.CompletedWork", "value": 1.0},
        {"op": "add", "path": "/fields/Microsoft.VSTS.Scheduling.RemainingWork", "value": 2.0},
        {"op": "add", "path": "/fields/Microsoft.VSTS.Scheduling.OriginalEstimate", "value": 8.0}
    ]
    if assignee:
        patch_document.append({"op": "add", "path": "/fields/System.AssignedTo", "value": assignee})
    if due_date:
        due_date_iso = f"{due_date}T00:00:00Z"
        patch_document.append({"op": "add", "path": "/fields/Microsoft.VSTS.Scheduling.DueDate", "value": due_date_iso})

    response = requests.patch(create_url, json=patch_document, headers=headers, auth=HTTPBasicAuth('', AZURE_PAT))
    response.raise_for_status()
    return response.json().get("id")

def update_task_assignment(work_item_id: int, assignee: str):
    """
    Updates the assigned user for an existing work item (task).
    """
    update_url = f"{BASE_URL}/{PROJECT_ENCODED}/_apis/wit/workitems/{work_item_id}?api-version=6.0"
    headers = {"Content-Type": "application/json-patch+json"}
    patch_document = [{"op": "add", "path": "/fields/System.AssignedTo", "value": assignee}]
    response = requests.patch(update_url, json=patch_document, headers=headers, auth=HTTPBasicAuth('', AZURE_PAT))
    response.raise_for_status()
    return response.json()

def update_time_fields(work_item_id, time_spent, time_remaining):
    """
    Updates time spent and remaining for the specified work item.
    This function uses the Azure DevOps REST API PATCH method to update:
      - Microsoft.VSTS.Scheduling.CompletedWork (time spent)
      - Microsoft.VSTS.Scheduling.RemainingWork (time remaining)
    It first attempts a 'replace' operation and, if that fails, falls back to 'add'.
    """
    AZURE_ORG = os.getenv("AZURE_DEVOPS_ORG")
    AZURE_PROJECT = os.getenv("AZURE_DEVOPS_PROJECT")
    AZURE_PAT = os.getenv("AZURE_DEVOPS_PAT")
    if not (AZURE_ORG and AZURE_PROJECT and AZURE_PAT):
        raise ValueError("Missing Azure DevOps environment variables.")
    base_url = f"https://dev.azure.com/{AZURE_ORG}"
    project_encoded = quote(AZURE_PROJECT)
    update_url = f"{base_url}/{project_encoded}/_apis/wit/workitems/{work_item_id}?api-version=6.0"
    headers = {"Content-Type": "application/json-patch+json"}
    patch_document = [
        {"op": "replace", "path": "/fields/Microsoft.VSTS.Scheduling.TimeSpent", "value": time_spent},
        {"op": "replace", "path": "/fields/Microsoft.VSTS.Scheduling.RemainingWork", "value": time_remaining}
    ]
    try:
        response = requests.patch(update_url, json=patch_document, headers=headers,
                                  auth=HTTPBasicAuth('', AZURE_PAT))
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        patch_document = [
            {"op": "add", "path": "/fields/Microsoft.VSTS.Scheduling.CompletedWork", "value": time_spent},
            {"op": "add", "path": "/fields/Microsoft.VSTS.Scheduling.RemainingWork", "value": time_remaining}
        ]
        response = requests.patch(update_url, json=patch_document, headers=headers,
                                  auth=HTTPBasicAuth('', AZURE_PAT))
        response.raise_for_status()
    return response.json()

def update_task_status(work_item_id: int, status: str):
    update_url = f"{BASE_URL}/{PROJECT_ENCODED}/_apis/wit/workitems/{work_item_id}?api-version=6.0"
    headers = {"Content-Type": "application/json-patch+json"}
    patch_document = [
        {"op": "add", "path": "/fields/System.State", "value": status}
    ]
    response = requests.patch(update_url, json=patch_document, headers=headers, auth=HTTPBasicAuth('', AZURE_PAT))
    response.raise_for_status()
    return response.json()

def delete_work_item(work_item_id):
    delete_url = f"{BASE_URL}/{PROJECT_ENCODED}/_apis/wit/workitems/{work_item_id}?api-version=6.0"
    response = requests.delete(delete_url, auth=HTTPBasicAuth('', AZURE_PAT))
    response.raise_for_status()
    return True 