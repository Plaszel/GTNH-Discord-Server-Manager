import os
import asyncio
import discord
import datetime
import subprocess
from discord.ext import commands

name_of_world = "world" #type in name of your world
path_to_bot = "" #type in path to folder with minecraft server
allowed_users = [] #discord user id  example [123456789876543210,123456789876543210,123456789876543210]
allowed_groups = [] #discord role id  example [123456789876543210,123456789876543210,123456789876543210]
files_to_load = ["playerdata","PERSONAL_DIM_180","backpacks"] #names of files to load

open(f"{path_to_bot}/Discord_logs.txt", "a").close()
open(f"{path_to_bot}/Discord_logs.txt", "w").close()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!",intents=intents, help_command=None)

temp_output = subprocess.run(["ls", "--time=creation", f"{path_to_bot}/backups"],capture_output=True, text=True)
to_load = temp_output.stdout.splitlines()

TMUX_SESSION = "minecraft_backup"

async def authorization(ctx_f):
    allowed = False
    user = ctx_f.author
    role_ids = [role.id for role in user.roles]
    for role_id in role_ids:
        if role_id in allowed_groups:
            allowed = True
    if ctx_f.author.id in allowed_users:
        allowed = True
    if allowed:
        return True
    else:
        await ctx_f.send("You are not allowed to run this!")
        return False

def is_running():
    result = subprocess.run(["tmux","ls"],capture_output=True, text=True)
    output = result.stdout
    if TMUX_SESSION in output:
        return  True
    else:
        return False

async def serverstop():
    try:
        error = False
        subprocess.run(["tmux", "send-keys", "-t", TMUX_SESSION, "stop", "ENTER"], check=True, capture_output=True, text=True)
        for _ in range(60):
            await asyncio.sleep(1)
            if not os.path.exists(path_to_bot+"/logs/fml-server-latest.txt"):
                continue
            with open(path_to_bot+"/logs/fml-server-latest.txt", "r") as f:
                logs = f.read()
            if "Rebooting in:" in logs:
                subprocess.run(["tmux", "send-keys", "-t", TMUX_SESSION, "C-c"], check=True, capture_output=True, text=True)
                break
        subprocess.run(["tmux","kill-session","-t",TMUX_SESSION])
    except Exception as e:
        error = True
        with open(path_to_bot + "/Discord_logs.txt", 'a') as f:
            data = datetime.datetime.now()
            data = data.replace(microsecond=0)
            f.write(f"{data}: {e}\n")
    if error:
        return "Error occured while stoping server, check logs"
    else:
        return "Server stopped"

async def serverstart(ctx=""):
    try:
        error = False
        subprocess.run(["tmux", "new-session", "-d", "-s", TMUX_SESSION], check=True, capture_output=True, text=True)
        subprocess.run(["tmux", "send-keys", "-t", TMUX_SESSION, f"bash {path_to_bot}/startserver-java9.sh", "ENTER"], check=True, capture_output=True, text=True)
        await ctx.send("Server starting")
    except Exception as e:
        error = True
        with open(path_to_bot + "/Discord_logs.txt", 'a') as f:
            data = datetime.datetime.now()
            data = data.replace(microsecond=0)
            f.write(f"{data}: {e}\n")
    if error:
        return "Error occured while starting server, check logs"
    else:
        for _ in range(120):
            await asyncio.sleep(1)
            if not os.path.exists(path_to_bot+"/logs/fml-server-latest.txt"):
                continue
            with open(path_to_bot+"/logs/fml-server-latest.txt", "r") as f:
                logs = f.read()
            if "Reloaded server" in logs:
                return "Server Started!"
        return "Server either loading too long or error occured, manual intervention needed"


@bot.command()
async def backups(ctx):
    if not await authorization(ctx):
        return
    try:
        result = subprocess.run(["ls","--time=creation",f"{path_to_bot}/backups"],check=True, capture_output=True, text=True)
        if result.stdout:
            text = "```\n"
            output = result.stdout.splitlines()
            global to_load
            for x in output:
                to_load.append(x)
            for x in range(len(output)):
                if (len(text)<1900):
                    text += (f"{x+1}|{output[x]}\n")
                else:
                    text += ("...\n")
                    break
            text += "\n```"
            await ctx.send(text)
        else:
            await ctx.send("No Backups available")
    except Exception as e:
        await ctx.send(f"Error occured")
        with open(path_to_bot + "/Discord_logs.txt", 'a') as f:
            data = datetime.datetime.now()
            data = data.replace(microsecond=0)
            f.write(f"{data}: {e}\n")

@bot.command()
async def load(ctx, index="-1", mode="0"):
    if not await authorization(ctx):
        return
    if not str.isdigit(index) or int(index) > len(to_load) or int(index) < 1 :
        await ctx.send("Wrong index file was given")
        return
    index = int(index)
    if not(mode == "0" or mode == "ALL"):
        await ctx.send("Wrong mode chosen, use ALL for copying whole folder or dont put anything for selected files!")
        return
    if is_running():
        await serverstop()
    try:
        error = False
        if os.path.exists(path_to_bot+ "/temp"):
            subprocess.run(["rm", "-r", f"{path_to_bot}/temp"])
        await ctx.send("Loading backup started")
        subprocess.run(["mkdir",f"{path_to_bot}/temp"],check=True, capture_output=True, text=True)
        subprocess.run(["cp",f"{path_to_bot}/backups/{to_load[index-1]}","temp/"], check=True, capture_output=True, text=True)
        subprocess.run(["unzip","-o",f"{path_to_bot}/temp/{to_load[index-1]}","-d",f"{path_to_bot}/temp"], check=True, capture_output=True, text=True)
        match mode:
            case "0":
                for x in files_to_load:
                    subprocess.run(["rm","-r",f"{path_to_bot}/{name_of_world}/{x}"],check=True, capture_output=True, text=True)
                    subprocess.run(["cp","-r",f"{path_to_bot}/temp/{name_of_world}/{x}",f"{path_to_bot}/{name_of_world}/"], check=True, capture_output=True, text=True)
            case "ALL":
                subprocess.run(["rm", "-r", f"{path_to_bot}/{name_of_world}"], check=True, capture_output=True,text=True)
                subprocess.run(["cp", "-r", f"{path_to_bot}/temp/{name_of_world}", f"{path_to_bot}/"], check=True,capture_output=True, text=True)
        subprocess.run(["rm","-r",f"{path_to_bot}/temp"])
    except Exception as e:
        error = True
        await ctx.send(f"Error occured")
        with open(path_to_bot + "/Discord_logs.txt", 'a') as f:
            data = datetime.datetime.now()
            data = data.replace(microsecond=0)
            f.write(f"{data}: {e}\n")
    if not error:
        await ctx.send("Backup loaded sucessfully")
    await serverstart()

@bot.command()
async def start(ctx):
    if not await authorization(ctx):
        return
    if is_running():
        await ctx.send("Server is already running")
    else:
        await ctx.send(await serverstart(ctx))



@bot.command()
async def stop(ctx):
    if not await authorization(ctx):
        return
    if is_running():
        await ctx.send(await serverstop())
    else:
        await ctx.send("Server is not running")

@bot.command()
async def help(ctx):
    await ctx.send("**List of commands:**\n- **!start** - start the server\n- **!stop** - stops the server\n- **!backups** - show list of available backups\n- **!load (index of backup)** - loads chosen backup (additionally \"ALL\" can be added for loading whole world file\n- **!help** - for list of commands")

bot.run("Discord bot token") #put in your bot token