# setup_cs2_extension.py
import os
import sys
import subprocess

def install_dependencies():
    """Install required packages for the CS2 Stats extension"""
    print("Installing required dependencies...")
    
    # Required packages
    packages = [
        "aiohttp",
        "beautifulsoup4"
    ]
    
    # Install each package
    for package in packages:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    
    print("All dependencies installed successfully!")

def create_extension_folder():
    """Create extensions folder if it doesn't exist"""
    if not os.path.exists("extensions"):
        print("Creating extensions folder...")
        os.makedirs("extensions")
        print("Extensions folder created!")
    else:
        print("Extensions folder already exists.")

def modify_main_bot():
    """Check if main bot.py needs modification and suggest changes"""
    if os.path.exists("bot.py"):
        with open("bot.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check if extension loading code exists
        if "load_extension" not in content:
            print("\n=== IMPORTANT: Bot.py Modification Required ===")
            print("Please add the following code near the bottom of your bot.py file,")
            print("just before the bot.run() line:")
            print("\n# Load CS2 Stats extension")
            print("bot.load_extension('cs2_stats_extension')")
            print("\nThis will enable the CS2 stats functionality in your bot.")

def main():
    print("===== CS2 Stats Extension Setup =====")
    
    # Install required dependencies
    install_dependencies()
    
    # Check bot.py for extension loading
    modify_main_bot()
    
    print("\nSetup complete!")
    print("\nTo use the extension, make sure to:")
    print("1. Place cs2_stats_extension.py in the same folder as your bot.py")
    print("2. Add the extension loading code to your bot.py")
    print("3. Restart your bot")
    print("\nYou can then use the following commands:")
    print("  /cs2stats - Get CS2 stats for a player")
    print("  /trackcs2 - Track a player in your dedicated channel")
    print("\nMake sure to update the channel ID in the cs2_stats_extension.py file!")

if __name__ == "__main__":
    main()