import configparser
import datetime
import sys
import time
from datetime import datetime
import discord
import requests

basepromurl = ""
client = discord.Client()
token = ""
channel = 0
message = 0


@client.event
async def on_ready():
    print('We have logged in as ' + client.user.name)
    while True:
        await updateembed()
        time.sleep(60)


def checkconfig():
    try:
        file = open("config.ini")
        file.close()
    except IOError:
        print("Config file doesn't exist yet, making one...")
        config = configparser.ConfigParser()
        config['bot'] = {'token': '', 'channel': '', 'message': ''}
        config['prometheus'] = {'baseurl': ''}
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
        print("Config created! stopping...")
        sys.exit(0)
    print("Config exists. continuing...")


def loadconfig():
    global token, basepromurl, channel, message
    config = configparser.ConfigParser()
    config.read("config.ini")
    token = config["bot"]["token"]
    channel = int(config["bot"]["channel"])
    message = int(config["bot"]["message"])
    basepromurl = config["prometheus"]["baseurl"]


async def updateembed():
    chan = client.get_channel(channel)
    msg = await chan.fetch_message(message)

    totalreq = requests.get(basepromurl + "sum(infrared_connected)").json()
    total = 0
    if totalreq["status"] == "success":
        for key in totalreq["data"]["result"]:
            total = key["value"][1]

    proxies = {}
    serverreq = requests.get(basepromurl + "sum by(host)(infrared_connected)").json()
    if serverreq["status"] == "success":
        for key in serverreq["data"]["result"]:
            if int(key["value"][1]) != 0:
                proxies[key["metric"]["host"]] = key["value"][1]
    proxies = dict(sorted(proxies.items(), reverse=True, key=lambda item: int(item[1])))
    serverlist = ""
    for key in proxies:
        serverlist = serverlist + proxies[key] + ": " + key + "\n"

    instances = {}
    instancereq = requests.get(basepromurl + "sum by(instance)(infrared_connected)").json()
    if instancereq["status"] == "success":
        for key in instancereq["data"]["result"]:
            instance = key["metric"]["instance"].split(".")[0]
            instances[instance] = key["value"][1]
    instances = dict(sorted(instances.items(), reverse=True, key=lambda item: int(item[1])))
    proxylist = ""
    for key in instances:
        proxylist = proxylist + instances[key] + ": " + key + "\n"

    nginx = {}
    instancereq = requests.get(basepromurl + "nginx_connections_active").json()
    if instancereq["status"] == "success":
        for key in instancereq["data"]["result"]:
            nginx[key["metric"]["node"]] = key["value"][1]
    nginx = dict(sorted(nginx.items(), reverse=True, key=lambda item: int(item[1])))
    nginxlist = ""
    for key in nginx:
        nginxlist = nginxlist + nginx[key] + ": " + key + "\n"

    embed = discord.Embed(title="Infrared cluster", color=0x00ff00)
    embed.add_field(name="Total players", value=total, inline=False)
    if serverlist is not "":
        embed.add_field(name="Players per server", value=serverlist)
    if proxylist is not "":
        embed.add_field(name="Players per instance", value=proxylist)
    if nginxlist is not "":
        embed.add_field(name="Nginx", value=nginxlist)
    embed.set_footer(text="© Infrastat 2021")
    embed.timestamp = datetime.utcnow()
    await msg.edit(embed=embed)


# start
if __name__ == "__main__":
    checkconfig()
    loadconfig()
    client.run(token)
