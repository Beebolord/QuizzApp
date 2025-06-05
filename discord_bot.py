import discord
import asyncio
import os
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True

client = discord.Client(intents=intents)
scheduler = AsyncIOScheduler()
job_added = False

@client.event
async def on_ready():
    global job_added
    print(f"🤖 Bot connected as {client.user}")
    if not job_added:
        scheduler.add_job(send_daily_checkin, 'cron', hour=20, minute=13)  # Adjust time
        scheduler.start()
        job_added = True

send_lock = asyncio.Lock()

async def send_daily_checkin():
    async with send_lock:
        guild = client.get_guild(GUILD_ID)
        if guild is None:
            print(f"Could not find guild with ID {GUILD_ID}")
            return

        channel = guild.get_channel(CHANNEL_ID)
        if channel is None:
            print(f"Could not find channel with ID {CHANNEL_ID} in guild {guild.name}")
            return

        # Send the daily check-in message
        msg = await channel.send("👋 Daily check-in! Please react with ✅")
        await msg.add_reaction("✅")
        print(f"Sent daily check-in message (ID: {msg.id}) in #{channel.name}")

        # Wait 1 hour (3600 seconds) — change if you want
        await asyncio.sleep(8)

        # Fetch the message again to update reaction info
        msg = await channel.fetch_message(msg.id)

        reacted_users = set()
        for reaction in msg.reactions:
            if str(reaction.emoji) == "✅":
                async for user in reaction.users():
                    if not user.bot:
                        reacted_users.add(user.id)

        print(f"Users who reacted with ✅: {len(reacted_users)}")

        # Check members who haven't reacted
        non_reactors = []
        async for member in guild.fetch_members(limit=None):
            if not member.bot:
                # If you want to check only online members, uncomment:
                # if member.status == discord.Status.offline:
                #     continue

                if member.id not in reacted_users:
                    non_reactors.append(member)

        if non_reactors:
            print("Users who did NOT react:")
            for member in non_reactors:
                print(f"- {member.display_name} ({member.id})")
                try:
                    await member.send("⏰ You missed the daily check-in!")
                except discord.Forbidden:
                    print(f"Cannot DM {member.display_name}")
        else:
            print("Everyone reacted! No DMs sent.")


def start_bot():
    client.run(TOKEN)
