import os
import random
import time
from asyncio import run

import requests
import segno
from remoteauthclient import RemoteAuthClient

import unifyQrcode

# load whitelist:#

whitelist = []
whitelist_desc = []
with open("whitelist.txt", "r") as f:
    whitelist_l = f.read().splitlines()
    for c in whitelist_l:
        c, d = c.split("#")
        c = c.strip()
        d = d.strip()
        if c != "":
            whitelist.append(c)
            if d != "":
                whitelist_desc.append(d)
            else:
                whitelist_desc.append("[NO DESC]")






legify_settings = {
    "enabled": True,
    "forced time": 4,
    "random time range": 3
}

whitelist_settings = {
    "enabled": True,
    "whitelist": whitelist
}

forbidden_permissions = ["guilds.join"]
Global_token = None
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



def delete_connected_apps(token, matches):
    for i in matches:
        if is_whitelisted(i["application"]["id"]):
            print("Skipping " + i["application"]["name"] + " (whitelisted)")
            continue
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
        legify()


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
    os.system(plattform().clear())
    print("Permissions List:")
    for i in range(len(Permissions.list())):
        if Permissions.list()[i] in forbidden_permissions:
            print(f"{bcolors.OKGREEN}{i+1}) {Permissions.list()[i]} {bcolors.ENDC}")
        else:
            print(f"{bcolors.FAIL}{i+1}) {Permissions.list()[i]} {bcolors.ENDC}")
    print(f"{bcolors.OKBLUE}0) Back{bcolors.ENDC}")
    choice = input("Enter your choice: ")
    if choice == "0":
        os.system(plattform().clear())
        return
    elif int(choice)-1 > len(Permissions.list()):
        os.system(plattform().clear())
        print("Invalid Choice")
        return
    else:
        if Permissions.list()[int(choice)-1] in forbidden_permissions:
            forbidden_permissions.remove(Permissions.list()[int(choice)-1])
        else:
            forbidden_permissions.append(Permissions.list()[int(choice)-1])
        os.system(plattform().clear())
        SetPermissions()


def token_qr():
    c = RemoteAuthClient()

    @c.event("on_fingerprint")
    async def on_fingerprint(data):
        print(f"Fingerprint: {data}")
        img = segno.make_qr(data)
        img.save("qrcode.png")
        unifyQrcode.unify("qrcode.png")
        print()

    @c.event("on_userdata")
    async def on_userdata(user):
        print(f"{bcolors.OKGREEN} Qr Code Scanned {bcolors.ENDC}")
        print(f"{bcolors.OKGREEN}ID: {user.id}{bcolors.ENDC}")
        print(f"{bcolors.OKGREEN}Username: {user.username}{bcolors.ENDC}")
        print(f"{bcolors.OKGREEN}Name: {user.getName()}{bcolors.ENDC}")
        # print waiting for confirmation
        print(f"{bcolors.WARNING}Waiting for confirmation...{bcolors.ENDC}")

    @c.event("on_token")
    async def on_token(token):
        print(f"{bcolors.OKBLUE}Got Token...{bcolors.ENDC}")
        global Global_token
        Global_token = token
        time.sleep(2)
        os.system(plattform().clear())

    run(c.run())


def menu():
    os.system(plattform().clear())
    global Global_token
    print(bcolors.OKBLUE + "=====================" + bcolors.ENDC)
    print(bcolors.OKBLUE + "Discord Token Checker" + bcolors.ENDC)
    print(bcolors.OKCYAN + "By: Blazzycrafter" + bcolors.ENDC)
    print(bcolors.OKBLUE + "=====================" + bcolors.ENDC)
    if Global_token == None:
        print("Token:" +  bcolors.FAIL + " Not Set" + bcolors.ENDC)
    else:
        print("Token:" + bcolors.OKGREEN + " Set" + bcolors.OKCYAN + f"( {Global_token[0:3]}...{Global_token[-1:-4]} )" + bcolors.ENDC)
    print(bcolors.OKBLUE + "=====================" + bcolors.ENDC)
    print(bcolors.FAIL + "1. Set Token" + bcolors.ENDC)
    print(bcolors.FAIL + "2. Set Dangerous Permissions" + bcolors.ENDC)
    print(bcolors.FAIL + "3. Options" + bcolors.ENDC)
    print(bcolors.FAIL + "4. Start" + bcolors.ENDC)
    print("0. Exit")

    choice = input("Enter your choice: ")
    if choice == "1":
        # ask for manual mode or automatic mode via qr code
        print("1. Manual")
        print("2. QR Code")
        choice = input("Enter your choice: ")
        if choice == "1":
            Global_token = input("Enter your token: ")
            os.system(plattform().clear())
        elif choice == "2":
            token_qr()

    elif choice == "2":
        os.system(plattform().clear())
        SetPermissions()
    elif choice == "3":
        options()
    elif choice == "4":
        os.system(plattform().clear())
        Main(token=Global_token)
    elif choice == "0":
        exit()


def legify_settings_menu():
    while True:
        if legify_settings["enabled"]:
            print(f"{bcolors.OKGREEN}1. Legify [ENABLED]{bcolors.ENDC}")
        else:
            print(f"{bcolors.FAIL}1. Legify [DISABLED]{bcolors.ENDC}")
        print(f"{bcolors.OKCYAN}2. set Forced Time [{legify_settings['forced time']}]{bcolors.ENDC}")
        print(f"{bcolors.OKCYAN}3. set Random Time Range [{legify_settings['random time range']}]{bcolors.ENDC}")
        print(f"{bcolors.FAIL}0. Back{bcolors.ENDC}")
        choice = input("Enter your choice: ")
        if choice == "0":
            break
        elif choice == "1":
            if legify_settings["enabled"]:
                legify_settings["enabled"] = False
            else:
                legify_settings["enabled"] = True
        elif choice == "2":
            try:
                legify_settings["forced time"] = int(input("Enter forced time: "))
            except ValueError:
                print("Invalid input")
        elif choice == "3":
            try:
                legify_settings["random time range"] = int(input("Enter random time range: "))
            except ValueError:
                print("Invalid input")
        os.system(plattform().clear())


def whitelist_settings_menu():
    # todo: change legify_settings to whitelist_settings
    while True:
        if whitelist_settings["enabled"]:
            print(f"{bcolors.OKGREEN}1. Whitelist [ENABLED]{bcolors.ENDC}")
        else:
            print(f"{bcolors.FAIL}1. Whitelist [DISABLED]{bcolors.ENDC}")
        print(f"{bcolors.OKCYAN}2. List whitelist{bcolors.ENDC}")
        print(f"{bcolors.FAIL}0. Back{bcolors.ENDC}")
        choice = input("Enter your choice: ")
        if choice == "0":
            break
        elif choice == "1":
            if whitelist_settings["enabled"]:
                whitelist_settings["enabled"] = False
            else:
                whitelist_settings["enabled"] = True
        elif choice == "2":
            print("Whitelist:")
            for i in range(len(whitelist)):
                print(f"{bcolors.OKCYAN}{whitelist[i]} #{whitelist_desc[i]}{bcolors.ENDC}")
            input("Press Enter to continue...")
        os.system(plattform().clear())

def options():
    while True:
        print(f"{bcolors.OKGREEN}1. Legify Settings{bcolors.ENDC}")
        print(f"{bcolors.OKGREEN}2. Whitelist Settings{bcolors.ENDC}")
        print(f"{bcolors.FAIL}0. Back{bcolors.ENDC}")
        choice = input("Enter your choice: ")
        if choice == "0":
            break
        elif choice == "1":
            legify_settings_menu()
        elif choice == "2":
            whitelist_settings_menu()
        os.system(plattform().clear())


def is_whitelisted(client_id):
    return whitelist_settings["enabled"] and client_id in whitelist

def legify():
    if not legify_settings["enabled"]:
        return
    time.sleep(legify_settings["forced time"])
    time.sleep(random.randint(0, legify_settings["random time range"]))

def Main(token):
    matches = check_connected_apps(token)
    if not matches:
        print("No matches found")
        write_end("none")
        return
    confirm = input("Are you sure you want to delete these applications? (y/n): ")
    if confirm == "y":
        delete_connected_apps(token, matches)
        deleted = ""
        for i in matches:
            deleted += i["application"]["name"] + "\n"
        write_end(deleted)
    else:
        deleted = ""
        for i in matches:
            deleted += i["application"]["name"] + "\n"
        write_end(deleted)

def Debug():
    options()
    CID = input("Enter Client ID: ")
    print(f"is whitelisted: {is_whitelisted(CID)}")



DEBUG = False # used to test experimental features / code
if __name__ == '__main__':
    if not DEBUG:
        while True:
            menu()
    else:
        Debug()
        
        
