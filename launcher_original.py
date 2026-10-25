import subprocess
import minecraft_launcher_lib

# 1. Define where the Minecraft files will be downloaded and saved
# This creates a folder named "my_cracked_minecraft" in your current directory
minecraft_directory = "./my_cracked_minecraft"

# 2. Choose the version you want to play
version = "1.20.1"

# 3. Download the version files if they don't exist yet
print(f"Checking/Downloading Minecraft {version}... This may take a few minutes.")
minecraft_launcher_lib.install.install_minecraft_version(version, minecraft_directory)

# 4. Set up the "Cracked" / Offline credentials
# Instead of a real Microsoft access token, we pass dummy data
username = input("Enter your custom offline username: ")

options = {
    "username": username,
    "uuid": "00000000-0000-0000-0000-000000000000", # A dummy UUID
    "token": "0",                                    # An empty/dummy session token
}

# 5. Generate the massive Java command required to boot the game
print("Launching Minecraft...")
launch_command = minecraft_launcher_lib.command.get_minecraft_command(version, minecraft_directory, options)

# 6. Execute the command to start the game
subprocess.run(launch_command)
