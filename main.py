import os

import requests
# arguments parser
import argparse
import os



token = None

class plattform:
    # init with os platform name to return later the right command
    # init gets the name of the os by calling the os module
    def __init__ (self):
        self.name = os.name

    def clear(self):
        if self.name == 'nt':
            return 'cls'
        else:
            return 'clear'




class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Permissions:
    @staticmethod
    def list():
        permissions = [
            "activities.read",
            "activities.write",
            "applications.builds.read",
            "applications.builds.upload",
            "applications.commands",
            "applications.commands.update",
            "applications.commands.permissions.update",
            "applications.entitlements",
            "applications.store.update",
            "bot",
            "connections",
            "dm_channels.read",
            "email",
            "gdm.join",
            "guilds",
            "guilds.join",
            "guilds.members.read",
            "identify",
            "messages.read",
            "relationships.read",
            "role_connections.write",
            "rpc",
            "rpc.activities.write",
            "rpc.notifications.read",
            "rpc.voice.read",
            "rpc.voice.write",
            "voice",
            "webhook.incoming"
        ]
        return permissions
    @staticmethod
    def category():
        cat = []
        for i in range(len(Permissions.list())):
            split = Permissions.list()[i].split(".")
            if not split[0] in cat:
                cat.append(split[0])
        return cat
    @staticmethod
    def categorized_list(category):
        ls = []
        if category.lower() == "misc":
            for i in range(len(Permissions.list())):
                split = Permissions.list()[i].split(".")
                print(f"i: {i} | split: {split[0]}")
                if not split[0] in Permissions.category():
                    ls.append(Permissions.list()[i])
        else:
            for i in range(len(Permissions.list())):
                split = Permissions.list()[i].split(".")
                if split[0] == category:
                    ls.append(Permissions.list()[i])
        return ls


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
    print("Found a application with forbidden permissions:")
    for i in data:
        #if forbidden_permissions in i["scopes"]:
        # forbidden_permissions is a python list, and i["scopes"] is a json list
        if any(x in i["scopes"] for x in forbidden_permissions):
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


def SetPermissions():
    print("Permissions List:")
    for i in range(len(Permissions.list())):
        if Permissions.list()[i] in forbidden_permissions:
            print(bcolors.OKGREEN + Permissions.list()[i] + bcolors.ENDC)
        else:
            print(bcolors.FAIL + Permissions.list()[i] + bcolors.ENDC)



def menu():
    global token
    print(bcolors.OKBLUE + "=====================" + bcolors.ENDC)
    print(bcolors.OKBLUE + "Discord Token Checker" + bcolors.ENDC)
    print(bcolors.OKCYAN + "By: Blazzycrafter" + bcolors.ENDC)
    print(bcolors.OKBLUE + "=====================" + bcolors.ENDC)
    if token == None:
        print("Token:" +  bcolors.FAIL + " Not Set" + bcolors.ENDC)
    else:
        print("Token:" +  bcolors.OKGREEN + " Set" + bcolors.OKCYAN + f"( {token[0:3]}...{token[-1:-4]} )" + bcolors.ENDC)
    print(bcolors.OKBLUE + "=====================" + bcolors.ENDC)
    print(bcolors.FAIL + "1. Set Token" + bcolors.ENDC)
    print(bcolors.FAIL + "2. Set Dangerous Permissions" + bcolors.ENDC)
    print(bcolors.FAIL + "3. Start" + bcolors.ENDC)
    print("4. Exit")

    choice = input("Enter your choice: ")
    if choice == "1":
        token = input("Enter your token: ")
        os.system(plattform().clear())
    elif choice == "2":
        os.system(plattform().clear())
        SetPermissions()

def Main():
    token = ""
    # check if token is passed as argument
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--token", help="Your discord token")
    # add type argument -c and -d
    parser.add_argument("-d", "--delete", help="Delete connected apps")
    if not parser.parse_args().token:
        token = input("Enter your token: ")
        os.system(plattform().clear())
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

def Debug():
    print(Permissions.categorized_list("misc"))


DEBUG = True
if __name__ == '__main__':
    if not DEBUG:
        while True:
            menu()
    else:
        Debug()
