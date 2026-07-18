import discord
from gradio_client import Client, handle_file
import requests
import os
import shutil
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- BACKGROUND WEB SERVER TO KEEP RENDER HAPPY ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Qik AI V2 Awake Keep Active.")

def run_web_server():
    server_address = ('0.0.0.0', 10000)
    try:
        httpd = HTTPServer(server_address, HealthCheckHandler)
        print("🌍 Health monitoring server active on Port 10000")
        httpd.serve_forever()
    except Exception as e:
        print(f"Web server warning: {e}")

# Start the web server instantly in a separate thread
threading.Thread(target=run_web_server, daemon=True).start()

# --- DISCORD BOT MAIN LOGIC ---
intents = discord.Intents.default()
intents.message_content = True  
intents.presences = True

client = discord.Client(intents=intents)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.online)
    print(f"🤖 Qik AI V2 is officially online and ready to help you!")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # STRICT CHECK: Triggers ONLY if the bot user is directly tagged/mentioned AND an attachment exists
    if client.user.mentioned_in(message) and message.attachments:
        
        # Grab the very first attachment out of the list safely
        attachment = message.attachments[0]
        
        is_image = attachment.content_type and attachment.content_type.startswith("image/")
        is_extension = attachment.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))
        
        if is_image or is_extension:
            
            # --- HUMANE MESSAGE 1 ---
            await message.channel.send("Got the image! Downloading it right now... 📥")
            
            task_directory = f"workspace_{message.id}"
            os.makedirs(task_directory, exist_ok=True)
            local_image_input = os.path.join(task_directory, attachment.filename)
            
            try:
                # Save the image from Discord locally
                raw_bytes = requests.get(attachment.url).content
                with open(local_image_input, "wb") as storage_file:
                    storage_file.write(raw_bytes)
                
                # --- HUMANE MESSAGE 2 ---
                await message.channel.send("File saved. Processing the textures and generating the 3D mesh... ⏳")

                # FIX: Updated keyword argument to 'hf_token' for the newer Gradio Client library versions
                hf_client = Client("stabilityai/stable-fast-3d", hf_token=HF_TOKEN)
                
                # Positional prediction to prevent API name search errors
                inference_result = hf_client.predict(
                    image=handle_file(local_image_input)
                )
                
                # --- HUMANE MESSAGE 3 ---
                await message.channel.send("Generation complete! Wrapping everything into a clean asset package... 📦")
                
                actual_file_path = inference_result if isinstance(inference_result, tuple) else inference_result

                optimized_filename = f"QikAI_Asset_{str(message.id)[:6]}.glb"
                local_asset_path = os.path.join(task_directory, optimized_filename)
                shutil.move(actual_file_path, local_asset_path)

                files_payload = [discord.File(local_asset_path)]
                
                # --- FINAL STATE DELIVERY ---
                completion_text = f"Here is your model, {message.author.mention}! 🎮\n\nThe materials and textures are fully embedded. Enjoy modeling!"
                await message.channel.send(content=completion_text, files=files_payload)

            except Exception as system_crash_log:
                await message.channel.send(f"Oops, ran into an issue building that model. 🛠️\nError details: `{str(system_crash_log)}`")
            finally:
                if os.path.exists(task_directory):
                    shutil.rmtree(task_directory)

# Initialize application loop
client.run(DISCORD_TOKEN)
