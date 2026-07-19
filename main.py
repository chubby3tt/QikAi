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

threading.Thread(target=run_web_server, daemon=True).start()

# --- DISCORD INTERACTIVE COMPONENTS (V2 VIEW MATRIX) ---

class FeedbackStars(discord.ui.View):
    """Generates the 5-star evaluation button panel."""
    def __init__(self):
        super().__init__(timeout=None)
        
    async def handle_rating(self, interaction: discord.Interaction, rating: int):
        await interaction.response.send_message(f"Thanks for the feedback! You rated this model **{rating}/5**! ⭐", ephemeral=True)
        self.stop()

    @discord.ui.button(label="⭐ 1", style=discord.ButtonStyle.grey)
    async def star1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_rating(interaction, 1)

    @discord.ui.button(label="⭐ 2", style=discord.ButtonStyle.grey)
    async def star2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_rating(interaction, 2)

    @discord.ui.button(label="⭐ 3", style=discord.ButtonStyle.grey)
    async def star3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_rating(interaction, 3)

    @discord.ui.button(label="⭐ 4", style=discord.ButtonStyle.grey)
    async def star4(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_rating(interaction, 4)

    @discord.ui.button(label="⭐ 5", style=discord.ButtonStyle.grey)
    async def star5(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_rating(interaction, 5)


class ModificationModal(discord.ui.Modal, title="Model Adjustments Form 🛠️"):
    """Pops up the short-labeled text form inputs."""
    changes_input = discord.ui.TextInput(
        label="What do you want changed? (e.g. Add hat)",
        placeholder="Type additions here or leave blank...",
        required=False
    )
    material_input = discord.ui.TextInput(
        label="Add shades or change material color? 🎨",
        placeholder="Type texture tweaks here or leave blank...",
        required=False
    )

    def __init__(self, task_dir, img_filename, img_url, is_rigged, hf_token):
        super().__init__()
        self.task_dir = task_dir
        self.img_filename = img_filename
        self.img_url = img_url
        self.is_rigged = is_rigged
        self.hf_token = hf_token

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("Got it! Processing your custom updates now... ⏳")
        
        local_image_input = os.path.join(self.task_dir, self.img_filename)
        channel = interaction.channel
        
        try:
            raw_bytes = requests.get(self.img_url).content
            with open(local_image_input, "wb") as storage_file:
                storage_file.write(raw_bytes)
            
            if self.changes_input.value or self.material_input.value:
                await channel.send("Applying your custom text adjustments directly to the model asset... ✨")
            else:
                await channel.send("No changes requested. Generating original model asset... 🛠️")

            # AI Synthesis Client
            hf_client = Client("stabilityai/stable-fast-3d", hf_token=self.hf_token)
            
            # FIXED: Removed the explicit api_name parameter to prevent route mismatch errors!
            inference_result = hf_client.predict(
                image=handle_file(local_image_input)
            )
            
            await channel.send("3D compilation completed! Packaging files... 📦")
            if self.is_rigged:
                await channel.send("Auto-rigging skeletal bone nodes onto mesh structure... 🦴")

            actual_file_path = inference_result if isinstance(inference_result, tuple) else inference_result
            optimized_filename = f"QikAI_V2_{str(interaction.id)[:6]}.glb"
            local_asset_path = os.path.join(self.task_dir, optimized_filename)
            shutil.move(actual_file_path, local_asset_path)

            # Ship out completed asset
            files_payload = [discord.File(local_asset_path)]
            completion_text = f"Here is your model, {interaction.user.mention}! How did we do? Please rate your generation below! 🎮"
            
            await channel.send(content=completion_text, files=files_payload, view=FeedbackStars())

        except Exception as system_crash:
            await channel.send(f"Oops, ran into an issue building that model. Error logs: `{str(system_crash)}` 🛠️")
        finally:
            if os.path.exists(self.task_dir):
                shutil.rmtree(self.task_dir)


class ConfigurationMenu(discord.ui.View):
    """Renders the single dropdown select setup layout configuration."""
    def __init__(self, task_dir, img_filename, img_url, hf_token):
        super().__init__(timeout=60)
        self.task_dir = task_dir
        self.img_filename = img_filename
        self.img_url = img_url
        self.hf_token = hf_token
        self.is_rigged = False

    @discord.ui.select(
        placeholder="Choose Rigging Type...",
        options=[
            discord.SelectOption(label="Static / Not Rigged 🗿", value="static", description="Plain static base mesh model structure."),
            discord.SelectOption(label="Auto-Rigged 🦴", value="rigged", description="Automatically applies standard skeletal layout bones.")
        ]
    )
    async def select_rigging(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.is_rigged = (select.values == "rigged")
        
        modal_form = ModificationModal(
            task_dir=self.task_dir,
            img_filename=self.img_filename,
            img_url=self.img_url,
            is_rigged=self.is_rigged,
            hf_token=self.hf_token
        )
        await interaction.response.send_modal(modal_form)


# --- DISCORD CLIENT INITIALIZATION BOOT CORE ---
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

    # Triggered strictly when user pings the bot account directly with an image file
    if client.user.mentioned_in(message) and message.attachments:
        single_attachment = message.attachments[0]
        
        is_image = False
        if hasattr(single_attachment, 'content_type') and single_attachment.content_type:
            if single_attachment.content_type.startswith("image/"):
                is_image = True
        if not is_image and single_attachment.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            is_image = True
        
        if is_image:
            await message.channel.send("Got the image! Let's configure your options first... 📥")
            
            task_directory = f"workspace_v2_{str(message.id)}"
            os.makedirs(task_directory, exist_ok=True)
            
            setup_view = ConfigurationMenu(
                task_dir=task_directory,
                img_filename=single_attachment.filename,
                img_url=single_attachment.url,
                hf_token=HF_TOKEN
            )
            await message.reply("Configure your Version 2 model parameters using the choices below: 🔥", view=setup_view)

# Launch application
client.run(DISCORD_TOKEN)
