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
    # Set standard clean online presence without any game activity text
    await bot.change_presence(status=discord.Status.online)
    print(f"🤖 Qik AI is officially online and ready to help the studio!")

@bot.event
async def on_message(message):
    # Ignore bot's own messages
    if message.author == bot.user:
        return

    # BULLETPROOF CHECK: Trigger if the bot is tagged OR if the user types "qik ai" in the message, AND an image is attached
    is_mentioned = bot.user.mentioned_in(message) or "qik ai" in message.content.lower()
    
    if is_mentioned and message.attachments:
        attachment = message.attachments
        
        # Filter strictly for standard image formats
        if attachment.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            
            # --- HUMANE MESSAGE 1 ---
            await message.channel.send("Got the image! Downloading it right now... 📥")
            
            # Initialize unique isolated workspace directory for this process task
            task_directory = f"workspace_{message.id}"
            os.makedirs(task_directory, exist_ok=True)
            local_image_input = os.path.join(task_directory, attachment.filename)
            
            try:
                # Write original user image down onto temporary system storage
                raw_bytes = requests.get(attachment.url).content
                with open(local_image_input, "wb") as storage_file:
                    storage_file.write(raw_bytes)
                
                # --- HUMANE MESSAGE 2 ---
                await message.channel.send("File saved. Processing the textures and generating the 3D mesh... ⏳")

                # Connect directly to Stable Fast 3D on Hugging Face using your HF token
                client = Client("stabilityai/stable-fast-3d", token=HF_TOKEN)
                
                # Trigger free shape synthesis calculation
                inference_result = client.predict(
                    image=handle_file(local_image_input),
                    api_name="/process"
                )
                
                # --- HUMANE MESSAGE 3 ---
                await message.channel.send("Generation complete! Wrapping everything into a clean asset package... 📦")
                
                # Move compiled asset securely into our working task tracker directory
                optimized_filename = f"QikAI_Asset_{message.id[:6]}.glb"
                local_asset_path = os.path.join(task_directory, optimized_filename)
                shutil.move(inference_result, local_asset_path)

                # Prepare the array payload containing our 3D file data
                files_payload = [discord.File(local_asset_path)]

                            # --- FINAL STATE MESSAGE: Mention User + Deliver Package ---
                completion_text = f"Here is your model, {message.author.mention}! 🎮\n\nThe materials and textures are fully embedded. Enjoy modeling!"
                await message.channel.send(content=completion_text, files=files_payload)


            except Exception as system_crash_log:
                # Independent distinct fallback warning response
                await message.channel.send(f"Oops, ran into an issue building that model. 🛠️\nError log: `{str(system_crash_log)}`")
            
            finally:
                # Hard wipe local folder space immediately after delivery to avoid running out of space on Render
                if os.path.exists(task_directory):
                    shutil.rmtree(task_directory)

    # Process other text commands if needed later
    await bot.process_commands(message)

# Initialize application loop
bot.run(DISCORD_TOKEN)
