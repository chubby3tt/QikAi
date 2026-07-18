import discord
from discord.ext import commands
from gradio_client import Client, handle_file
import requests
import os
import shutil

# Configure Discord bot engine with message tracking capabilities
intents = discord.Intents.default()
intents.message_content = True
intents.presences = True  # Allows status sync updates

bot = commands.Bot(command_prefix="!", intents=intents)

# SECURITY SETUP: 
# These lines pull your private keys safely out of Render's hidden environment variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

@bot.event
async def on_ready():
    # FORCE DISCORD SYNC: Forces the bot to instantly display as active and green in your server member list
    await bot.change_presence(status=discord.Status.online, activity=discord.Game(name="Roblox Image-to-3D"))
    print(f"🚀 Qik AI is successfully online! High-volume free API bridge established.")

@bot.event
async def on_message(message):
    # Ignore bot's own messages
    if message.author == bot.user:
        return

    # SAFETY CHECK: Only trigger if the bot is explicitly tagged/mentioned AND there is an attachment
    if bot.user.mentioned_in(message) and message.attachments:
        attachment = message.attachments
        
        # Filter strictly for standard image formats
        if attachment.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            
            # --- DISTINCT STATE MESSAGE 1 ---
            await message.channel.send("🤖 **Qik AI:** Target file identified via mention. Downloading asset data from Discord servers...")
            
            # Initialize unique isolated workspace directory for this process task
            task_directory = f"workspace_{message.id}"
            os.makedirs(task_directory, exist_ok=True)
            local_image_input = os.path.join(task_directory, attachment.filename)
            
            try:
                # Write original user image down onto temporary system storage
                raw_bytes = requests.get(attachment.url).content
                with open(local_image_input, "wb") as storage_file:
                    storage_file.write(raw_bytes)
                
                # --- DISTINCT STATE MESSAGE 2 ---
                await message.channel.send("⚙️ **Qik AI:** File locked. Handing process off to free Serverless Inference Matrix...")

                # Connect directly to Stable Fast 3D on Hugging Face using your HF token
                client = Client("stabilityai/stable-fast-3d", token=HF_TOKEN)
                
                # Trigger free shape synthesis calculation
                inference_result = client.predict(
                    image=handle_file(local_image_input),
                    api_name="/process"
                )
                
                # --- DISTINCT STATE MESSAGE 3 ---
                await message.channel.send("📥 **Qik AI:** 3D synthesis calculation finished! Extracting `.glb` file pack...")
                
                # Move compiled asset securely into our working task tracker directory
                optimized_filename = f"QikAI_Asset_{message.id[:6]}.glb"
                local_asset_path = os.path.join(task_directory, optimized_filename)
                shutil.move(inference_result, local_asset_path)

                # Prepare the array payload containing our 3D file data
                files_payload = [discord.File(local_asset_path)]

                # --- FINAL STATE MESSAGE: Mention User + Deliver Package ---
                completion_text = f"🏆 **Generation Complete!** {message.author.mention}, your 3D asset is ready!\n\n💡 **Roblox Studio Pro-Tip:** Drag this `.glb` directly into the **Roblox Studio Bulk Import tool**. The engine will automatically parse the high-quality embedded material mapping natively!"
                await message.channel.send(content=completion_text, files=files_payload)

            except Exception as system_crash_log:
                # Independent distinct fallback warning response
                await message.channel.send(f"⚠️ **Qik AI Pipeline Failure:** Processing aborted. Log details: `{str(system_crash_log)}`")
            
            finally:
                # Hard wipe local folder space immediately after delivery to avoid running out of space on Render
                if os.path.exists(task_directory):
                    shutil.rmtree(task_directory)

    # Process other text commands if needed later
    await bot.process_commands(message)

# Initialize application loop
bot.run(DISCORD_TOKEN)
