import requests
# arguments parser
import argparse


forbidden_permissions = ["guilds.join"]


def delete_connected_apps(token, matches):
    for i in matches:
        url = "https://discord.com/api/v9/oauth2/tokens/" + i["id"]
        headers = {
            "Authorization": token,
            "Content-Type": "application/json"
        }
        r = requests.delete(url, headers=headers)
        if r.status_code == 204:
            print("Deleted " + i["application"]["name"])
        else:
            print("Failed to delete " + i["application"]["name"])

def check_connected_apps(token):
    url = "https://discord.com/api/v9/oauth2/tokens"
    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }
    r = requests.get(url, headers=headers)
    if not r.status_code == 200:
        print("Invalid token")
        return None
    data = r.json()
    # loop through list and print the id
    matches = []
    for i in data:
        #if forbidden_permissions in i["scopes"]:
        # forbidden_permissions is a python list, and i["scopes"] is a json list
        if any(x in i["scopes"] for x in forbidden_permissions):
            print("Found a application with forbidden permissions:")
            print("Name: " + i["application"]["name"])
            # add to matches list
            matches.append(i)
    if len(matches) == 0:
        return None
    else:
        return matches


def write_end(results):
    with open("result.r", "wb") as f:
        f.write(results.encode())


if __name__ == '__main__':
    token = ""
    #check if token is passed as argument
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--token", help="Your discord token")
    # add type argument -c and -d
    parser.add_argument("-d", "--delete", help="Delete connected apps")
    if not parser.parse_args().token:
        token = input("Enter your token: ")
    else:
        token = parser.parse_args().token
    matches = check_connected_apps(token)
    if not matches:
        print("No matches found")
        write_end("none")
        exit()
    if not parser.parse_args().token:
        confirm = input("Are you sure you want to delete these applications? (y/n): ")
        if confirm == "y":
            delete_connected_apps(token, matches)
            deleted = ""
            for i in matches:
                deleted += i["application"]["name"] + "\n"
            write_end(deleted)
            exit()
    elif parser.parse_args().delete:
        delete_connected_apps(token, matches)
        deleted = ""
        for i in matches:
            deleted += i["application"]["name"] + "\n"
        write_end(deleted)
        exit()
    else:
        deleted = ""
        for i in matches:
            deleted += i["application"]["name"] + "\n"
        write_end(deleted)



