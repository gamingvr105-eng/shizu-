"""
Shizu Security - Automated Bot Profile & Asset Applicator
Applies the new video-type animated avatar and banner to your Discord bot.
"""

import sys
import os
import asyncio
import discord

AVATAR_PATH = os.path.join("assets", "shizu_avatar_animated.gif")
BANNER_PATH = os.path.join("assets", "shizu_banner_animated.gif")

def print_banner():
    print("=" * 65)
    print("      [SHIZU SECURITY -- BOT PROFILE APPLICATOR]")
    print("=" * 65)

async def apply_profile(token: str):
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f"\n[+] Successfully authenticated as: {client.user} (ID: {client.user.id})")
        
        kwargs = {}
        if os.path.exists(AVATAR_PATH):
            with open(AVATAR_PATH, "rb") as f:
                kwargs["avatar"] = f.read()
            print(f"[+] Loaded Animated Avatar: {AVATAR_PATH} ({len(kwargs['avatar']) / 1024:.1f} KB)")
        else:
            print(f"[-] Avatar file not found at {AVATAR_PATH}")

        if not kwargs:
            print("[-] No valid avatar file found.")
            await client.close()
            return

        try:
            print("[*] Uploading profile assets to Discord API...")
            await client.user.edit(**kwargs)
            print("\n[SUCCESS] Bot profile successfully updated with animated avatar!")
            print("          Check your bot profile in Discord or on Discord Developer Portal.")
        except discord.HTTPException as e:
            print(f"\n[-] Discord API Notice: {e}")
        finally:
            await client.close()

    try:
        await client.start(token)
    except discord.LoginFailure:
        print("\n[ERROR] Invalid token provided. Please verify your Bot Token.")
    except Exception as e:
        print(f"\n[ERROR] Connection error: {e}")

def main():
    token = ""
    if len(sys.argv) > 1:
        token = sys.argv[1].strip()
    elif os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("DISCORD_TOKEN="):
                    token = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break

    if not token or token == "your_bot_token_here":
        print_banner()
        token = input("Enter your Discord Bot Token: ").strip()

    if not token:
        print("[-] No token provided. Exiting.")
        return

    asyncio.run(apply_profile(token))

if __name__ == "__main__":
    main()
