import requests
from ratelimit import limits
from datetime import datetime, timezone, timedelta


# Constants
API_KEY = "INSERT KEY HERE"
API_TOKEN = "INSERT TOKEN HERE"
ORG_ID = "INSERT_ORG_ID_HERE"


# Custom exception for API request errors
class ApiRequestError(Exception):
    def __init__(self, status_code):
        super().__init__(f"API response: {status_code}")
        self.status_code = status_code


# Rate limiting decorator for API calls
@limits(calls=100, period=20)
def call_api(url, method="GET"):
    if method == "GET":
        response = requests.get(url)
    elif method == "PUT":
        response = requests.put(url)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")

    if response.status_code != 200:
        raise ApiRequestError(response.status_code)
    return response.json()


# Function to get Trello members
def get_trello_members(org_id):
    print("Getting all members in the organization which are not deactivated....")
    url = f"https://api.trello.com/1/organizations/{org_id}/memberships?key={API_KEY}&token={API_TOKEN}&filter=normal, active&member=true"

    data = call_api(url, "GET")

    members = []
    for user in data:
        if not user['deactivated']:
            members.append(user['idMember'])
            print(f"The user {user['member']['username']} with ID: {user['idMember']} has a paying license and not an admin")

    return members


# Function to get inactive members
def get_inactive_members(members, today):
    inactive_users = []

    for user in members:
        url = f"https://api.trello.com/1/members/{user}/actions?key={API_KEY}&token={API_TOKEN}"
        data = call_api(url, "GET")
        try:
            time2 = datetime.fromisoformat(data[0]['date'])
            timeDiff = today - time2
            if time2 < today:
                inactive_users.append(user)
                print(f"{user} is inactive. They were last active on {time2} which is {timeDiff} ago")
        except (IndexError, KeyError, ValueError) as e:
            print(f"{user} has never logged in and does not have a paying license")

    return inactive_users

# Function to deactivate users
def deactivate_users(inactive_users):
    for user in inactive_users:
        url = f"https://api.trello.com/1/organizations/{ORG_ID}/members/{user}/deactivated?value=true&key={API_KEY}&token={API_TOKEN}"
        data = call_api(url, "PUT")


# Main script
trello_memberID = get_trello_members(ORG_ID)
print(f"\nThere are {len(trello_memberID)} users who are not deactivated and are not admins")

print("\nGetting member actions to determine last activity for member....")

today = datetime.now().replace(tzinfo=timezone.utc) - timedelta(days=60)
inactive_users = get_inactive_members(trello_memberID, today)

print(f"\nThere are {len(inactive_users)} users which are inactive and will now be deactivated...")

deactivate_users(inactive_users)
