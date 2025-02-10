import requests
from requests.auth import HTTPBasicAuth

# Azure DevOps Configuration
ORGANIZATION = "humber-college"
PROJECT = "EA Capstone"
PAT = "F9hSZMXQ8bf2IgPtysoiFwfh96tXtuHf24wlw7xQWW5BwTQISWobJQQJ99BBACAAAAAAmWDJAAASAZDO1kUm"

# API URL for fetching backlog tasks
WIQL_QUERY_URL = f"https://dev.azure.com/{ORGANIZATION}/{PROJECT}/_apis/wit/wiql?api-version=7.1-preview.2"

# Authentication
auth = HTTPBasicAuth("", PAT)
headers = {"Content-Type": "application/json"}

# Define WIQL Query (Fetch active backlog items)
query = {
    "query": "SELECT [System.Id], [System.Title], [System.State] FROM WorkItems WHERE [System.WorkItemType] = 'Product Backlog Item' AND [System.State] <> 'Done'"
}

# Send Request
response = requests.post(WIQL_QUERY_URL, json=query, headers=headers, auth=auth)

# Process Response
if response.status_code == 200:
    work_items = response.json()
    print("Successfully retrieved backlog tasks:", work_items)
else:
    print(f"Error {response.status_code}: {response.text}")

'''# Extract Work Item Details
data = []
for item in work_items:
    work_item_id = item["id"]
    details_url = f"{BASE_URL}/{work_item_id}?api-version=7.1-preview.2"
    details_response = requests.get(details_url, headers=headers, auth=auth)

    if details_response.status_code == 200:
        details = details_response.json()
        data.append({
            "ID": work_item_id,
            "Title": details["fields"]["System.Title"],
            "State": details["fields"]["System.State"],
            "Assigned To": details["fields"].get("System.AssignedTo", {}).get("displayName", "Unassigned"),
            "Description": details["fields"].get("System.Description", "No description available")
        })
    else:
        print(f"Failed to fetch details for Work Item {work_item_id}")

# Convert to DataFrame for better readability
df = pd.DataFrame(data)
print(df)'''