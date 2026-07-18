import discord
from discord.ext import commands
from gradio_client import Client, handle_file
import requests
import os
import shutil
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- BACKGROUND WEB SERVER FOR UPTIMEROBOT ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Qik AI Awake Keep Active.")

def run_web_server():
    # Binds server traffic to Port 10000 which Render scans automatically
    server_address = ('0.0.0.0', 10000)
    httpd = HTTPServer(server_address, HealthCheckHandler)
    print("🌍 Health monitoring server active on Port 10000")
    httpd.serve_forever()

# Launch the web server on a separate background thread so it doesn't block the Discord bot
threading.Thread(target=run_web_server, daemon=True).start()

# --- DISCORD BOT STABLE LOGIC ENGINE ---
intents = discord.Intents.default()
intents.message_content = True
intents.presences = True  # Allows status sync updates

bot = commands.Bot(command_prefix="!", intents=intents)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online)
    print(f"🤖 Qik AI is officially online and ready to help the studio!")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    is_mentioned = bot.user.mentioned_in(message) or "qik ai" in message.content.lower()
    
    if is_mentioned and message.attachments:
        attachment = message.attachments
        if attachment.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            
            await message.channel.send("Got the image! Downloading it right now... 📥")
            
            task_directory = f"workspace_{message.id}"
            os.makedirs(task_directory, exist_ok=True)
            local_image_input = os.path.join(task_directory, attachment.filename)
            
            try:
                raw_bytes = requests.get(attachment.url).content
                with open(local_image_input, "wb") as storage_file:
                    storage_file.write(raw_bytes)
                
                await message.channel.send("File saved. Processing the textures and generating the 3D mesh... ⏳")

                client = Client("stabilityai/stable-fast-3d", token=HF_TOKEN)
                inference_result = client.predict(
                    image=handle_file(local_image_input),
                    api_name="/process"
                )
                
                await message.channel.send("Generation complete! Wrapping everything into a clean asset package... 📦")
                
                optimized_filename = f"QikAI_Asset_{message.id[:6]}.glb"
                local_asset_path = os.path.join(task_directory, optimized_filename)
                shutil.move(inference_result, local_asset_path)

                files_payload = [discord.File(local_asset_path)]
                completion_text = f"Here is your model, {message.author.mention}! 🎮\n\nThe materials and textures are fully embedded. Enjoy modeling!"
                await message.channel.send(content=completion_text, files=files_payload)

            except Exception as system_crash_log:
                await message.channel.send(f"Oops, ran into an issue building that model. 🛠️\nError log: `{str(str(system_crash_log))}`")
            finally:
                if os.path.exists(task_directory):
                    shutil.rmtree(task_directory)

    await bot.process_commands(message)

bot.run(DISCORD_TOKEN)
