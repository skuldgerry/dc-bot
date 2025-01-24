import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View
import json
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.voice_states = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

class SettingsView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=60)
        self.guild_id = guild_id
        self.settings = load_settings(guild_id)

    @discord.ui.button(label="Add to Whitelist", style=discord.ButtonStyle.primary, row=0)
    async def add_whitelist(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(WhitelistAddModal())

    @discord.ui.button(label="Remove from Whitelist", style=discord.ButtonStyle.primary, row=0)
    async def remove_whitelist(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(WhitelistRemoveModal())

    @discord.ui.button(label="Set Log Channel", style=discord.ButtonStyle.primary, row=1)
    async def set_log_channel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(LogChannelModal())

    @discord.ui.button(label="Set Kick Message", style=discord.ButtonStyle.primary, row=1)
    async def set_kick_message_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(KickMessageModal())

    @discord.ui.button(label="Toggle Join Messages", style=discord.ButtonStyle.primary, row=2)
    async def toggle_join_messages(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.settings['join_messages'] = not self.settings['join_messages']
        save_settings(self.guild_id, self.settings)
        await self.update_settings_message(interaction)

    @discord.ui.button(label="Toggle Bot", style=discord.ButtonStyle.danger, row=3)
    async def toggle_bot_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.settings['bot_enabled'] = not self.settings.get('bot_enabled', True)
        save_settings(self.guild_id, self.settings)
        await self.update_settings_message(interaction)

    async def update_settings_message(self, interaction: discord.Interaction):
        embed = create_settings_embed(self.settings)
        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(view=self)
        except:
            pass

class WhitelistView(discord.ui.View):
    def __init__(self, whitelist_info):
        super().__init__(timeout=60)
        self.whitelist_info = whitelist_info
        self.current_page = 0
        self.items_per_page = 10

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.gray)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_message(interaction)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.gray)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if (self.current_page + 1) * self.items_per_page < len(self.whitelist_info):
            self.current_page += 1
            await self.update_message(interaction)

    def create_embed(self):
        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        current_items = self.whitelist_info[start_idx:end_idx]
        
        embed = discord.Embed(title="Whitelist", color=0x00ff00)
        if current_items:
            embed.description = "\n".join(current_items)
        else:
            embed.description = "No users in this page."
        
        total_pages = (len(self.whitelist_info) - 1) // self.items_per_page + 1
        embed.set_footer(text=f"Page {self.current_page + 1} of {total_pages}")
        return embed

    async def update_message(self, interaction: discord.Interaction):
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

class WhitelistAddModal(discord.ui.Modal, title="Add to Whitelist"):
    user_id = discord.ui.TextInput(
        label="User ID",
        placeholder="Enter the user ID",
        required=True,
        min_length=17,
        max_length=20
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = str(int(self.user_id.value))  # Validate it's a number
            member = interaction.guild.get_member(int(user_id))
            
            if member:
                whitelist = load_whitelist(interaction.guild.id)
                if user_id not in whitelist:
                    whitelist.append(user_id)
                    save_whitelist(interaction.guild.id, whitelist)
                    await interaction.response.send_message(f"{member.display_name} has been added to the whitelist.")
                else:
                    await interaction.response.send_message(f"{member.display_name} is already in the whitelist.")
            else:
                await interaction.response.send_message("User not found in this server.", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("Please enter a valid user ID.", ephemeral=True)

class WhitelistRemoveModal(discord.ui.Modal, title="Remove from Whitelist"):
    user_id = discord.ui.TextInput(
        label="User ID",
        placeholder="Enter the user ID",
        required=True,
        min_length=17,
        max_length=20
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = str(int(self.user_id.value))  # Validate it's a number
            member = interaction.guild.get_member(int(user_id))
            whitelist = load_whitelist(interaction.guild.id)
            
            if user_id in whitelist:
                whitelist.remove(user_id)
                save_whitelist(interaction.guild.id, whitelist)
                name = member.display_name if member else f"User (ID: {user_id})"
                await interaction.response.send_message(f"{name} has been removed from the whitelist.")
            else:
                await interaction.response.send_message("This user is not in the whitelist.", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("Please enter a valid user ID.", ephemeral=True)

class KickMessageModal(discord.ui.Modal, title="Set Kick Message"):
    message = discord.ui.TextInput(
        label="Kick Message",
        placeholder="Enter the message to send when kicking users",
        required=True,
        style=discord.TextStyle.paragraph,  # Allows multiple lines
        max_length=1000
    )

    async def on_submit(self, interaction: discord.Interaction):
        settings = load_settings(interaction.guild.id)
        settings['kick_message'] = self.message.value
        save_settings(interaction.guild.id, settings)
        await interaction.response.send_message("Kick message updated successfully.", ephemeral=True)

class LogChannelModal(discord.ui.Modal, title="Set Log Channel"):
    channel_id = discord.ui.TextInput(
        label="Channel ID",
        placeholder="Enter the channel ID",
        required=True,
        min_length=17,
        max_length=20
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            channel_id = int(self.channel_id.value)
            channel = interaction.guild.get_channel(channel_id)
            
            if channel and isinstance(channel, discord.TextChannel):
                settings = load_settings(interaction.guild.id)
                settings['logs_channel'] = channel.id
                save_settings(interaction.guild.id, settings)
                await interaction.response.send_message(f"Log channel set to {channel.mention}", ephemeral=True)
            else:
                await interaction.response.send_message("Please enter a valid text channel ID.", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("Please enter a valid channel ID.", ephemeral=True)

def load_settings(guild_id: int) -> dict:
    """Load settings from the guild's directory or create defaults if not exists."""
    guild_dir = f"config/{guild_id}"
    settings_path = f"{guild_dir}/settings.json"
    
    # Default settings that should always be present
    default_settings = {
        'enabled': True,
        'join_messages': True,
        'whitelist_enabled': False,
        'logs_channel': None,
        'dm_message': "Welcome to the server!",
        'kick_message': "You have been disconnected from the voice channel.",
        'bot_enabled': True,
        'whitelist': []
    }
    
    # Create directory if it doesn't exist
    if not os.path.exists(guild_dir):
        os.makedirs(guild_dir)
    
    try:
        # Load existing settings
        with open(settings_path, 'r') as f:
            existing_settings = json.load(f)
            
        # Merge with defaults (ensures new settings are added to old files)
        merged_settings = default_settings.copy()
        merged_settings.update(existing_settings)
        
        return merged_settings
            
    except FileNotFoundError:
        # If no settings exist, create new file with defaults
        save_settings(guild_id, default_settings)
        return default_settings

def load_whitelist(guild_id: int) -> list:
    """Load whitelist from the guild's directory or create if not exists."""
    guild_dir = f"config/{guild_id}"
    whitelist_path = f"{guild_dir}/whitelist.json"
    
    if not os.path.exists(guild_dir):
        os.makedirs(guild_dir)
    
    try:
        with open(whitelist_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        empty_whitelist = []
        save_whitelist(guild_id, empty_whitelist)
        return empty_whitelist

def save_settings(guild_id: int, settings: dict) -> None:
    """Save settings to the guild's directory."""
    guild_dir = f"config/{guild_id}"
    settings_path = f"{guild_dir}/settings.json"
    
    if not os.path.exists(guild_dir):
        os.makedirs(guild_dir)
        
    with open(settings_path, 'w') as f:
        json.dump(settings, f, indent=4)

def save_whitelist(guild_id: int, whitelist: list) -> None:
    """Save whitelist to the guild's directory."""
    guild_dir = f"config/{guild_id}"
    whitelist_path = f"{guild_dir}/whitelist.json"
    
    if not os.path.exists(guild_dir):
        os.makedirs(guild_dir)
        
    with open(whitelist_path, 'w') as f:
        json.dump(whitelist, f, indent=4)

def create_settings_embed(settings: dict) -> discord.Embed:
    """Create an embed displaying the current settings."""
    embed = discord.Embed(title="Settings Menu", color=0x00ff00)
    embed.add_field(
        name="Bot Status", 
        value=f"{'✅' if settings['bot_enabled'] else '❌'} Enabled",
        inline=False
    )
    embed.add_field(
        name="Join Messages", 
        value=f"{'✅' if settings['join_messages'] else '❌'} Enabled",
        inline=False
    )
    if settings.get('logs_channel'):
        embed.add_field(
            name="Log Channel",
            value=f"<#{settings['logs_channel']}>",
            inline=False
        )
    return embed

@bot.tree.command(name="settings", description="Access the settings menu")
@app_commands.checks.has_permissions(administrator=True)
async def settings(interaction: discord.Interaction):
    view = SettingsView(interaction.guild.id)
    embed = create_settings_embed(view.settings)
    await interaction.response.send_message(embed=embed, view=view)
    view.message = await interaction.original_response()

@bot.tree.command(name="set_log_channel", description="Set the channel for logs")
@app_commands.checks.has_permissions(administrator=True)
async def set_log_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    settings = load_settings(interaction.guild.id)
    settings['logs_channel'] = channel.id
    save_settings(interaction.guild.id, settings)
    await interaction.response.send_message(f"Log channel set to {channel.mention}")

@bot.tree.command(name="set_kick_message", description="Set custom message for kicks")
@app_commands.checks.has_permissions(administrator=True)
async def set_kick_message(interaction: discord.Interaction, message: str):
    settings = load_settings(interaction.guild.id)
    settings['kick_message'] = message
    save_settings(interaction.guild.id, settings)
    await interaction.response.send_message("Kick message updated successfully.")

@bot.tree.command(name="toggle_bot", description="Enable or disable the bot")
@app_commands.checks.has_permissions(administrator=True)
async def toggle_bot(interaction: discord.Interaction):
    settings = load_settings(interaction.guild.id)
    settings['bot_enabled'] = not settings.get('bot_enabled', True)
    save_settings(interaction.guild.id, settings)
    status = "enabled" if settings['bot_enabled'] else "disabled"
    await interaction.response.send_message(f"Bot has been {status}.")

@bot.tree.command(name="whitelist_add", description="Add a member to the whitelist")
@app_commands.checks.has_permissions(administrator=True)
async def whitelist_add(interaction: discord.Interaction, member: discord.Member):
    whitelist = load_whitelist(interaction.guild.id)
    if str(member.id) not in whitelist:
        whitelist.append(str(member.id))
        save_whitelist(interaction.guild.id, whitelist)
        await interaction.response.send_message(f"{member.name} has been added to the whitelist.")
    else:
        await interaction.response.send_message(f"{member.name} is already in the whitelist.")

@bot.tree.command(name="whitelist_remove", description="Remove a member from the whitelist")
@app_commands.checks.has_permissions(administrator=True)
async def whitelist_remove(interaction: discord.Interaction, member: discord.Member):
    whitelist = load_whitelist(interaction.guild.id)
    if str(member.id) in whitelist:
        whitelist.remove(str(member.id))
        save_whitelist(interaction.guild.id, whitelist)
        await interaction.response.send_message(f"{member.name} has been removed from the whitelist.")
    else:
        await interaction.response.send_message(f"{member.name} is not in the whitelist.")

@bot.tree.command(name="list_whitelist", description="List all whitelisted members")
@app_commands.checks.has_permissions(administrator=True)
async def list_whitelist(interaction: discord.Interaction):
    whitelist = load_whitelist(interaction.guild.id)
    
    if whitelist:
        whitelist_info = []
        for member_id in whitelist:
            member = interaction.guild.get_member(int(member_id))
            if member:
                whitelist_info.append(f"{member.display_name} (ID: {member_id})")
            else:
                whitelist_info.append(f"Unknown Member (ID: {member_id})")
        
        view = WhitelistView(whitelist_info)
        embed = view.create_embed()
        await interaction.response.send_message(embed=embed, view=view)
    else:
        embed = discord.Embed(title="Whitelist", description="The whitelist is empty.", color=0x00ff00)
        await interaction.response.send_message(embed=embed)

@bot.event
async def on_ready():
    # Try multiple ways of outputting
    print("BOT IS STARTING") # Basic print
    logger.info("BOT IS STARTING") # Logger
    
    print(f'{bot.user.name} has connected to Discord!')
    logger.info(f'{bot.user.name} has connected to Discord!')
    
    # Generate invite link with required permissions
    permissions = discord.Permissions(
        administrator=True,
        view_channel=True,
        send_messages=True,
        manage_messages=True,
        read_message_history=True,
        move_members=True,
        send_messages_in_threads=True
    )
    
    invite_link = discord.utils.oauth_url(
        bot.user.id,
        permissions=permissions
    )
    
    # Try both print and logging for the invite link
    logger.info("\n" + "="*50)
    logger.info(f"Invite {bot.user.name} to your server using this link:")
    logger.info(f"{invite_link}")
    logger.info("="*50 + "\n")
    
    print("\n" + "="*50)
    print(f"Invite {bot.user.name} to your server using this link:")
    print(f"{invite_link}")
    print("="*50 + "\n")
    
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
        logger.info(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)
        logger.error(f"Error during sync: {e}")

@bot.event
async def on_voice_state_update(member, before, after):
    settings = load_settings(member.guild.id)
    bot_enabled = settings.get('bot_enabled', True)
    
    if member.bot:  # Ignore bot users
        return

    if after.self_mute and after.self_deaf:  # If member is both muted and deafened
        if member.voice:  # If member is in a voice channel
            if bot_enabled:
                whitelist = load_whitelist(member.guild.id)
                if str(member.id) in whitelist:
                    return  # Member is in whitelist, do not disconnect
                
                await member.move_to(None)  # Disconnect member
                
                # Log the disconnection
                log_channel_id = settings.get('logs_channel')
                if log_channel_id:
                    log_channel = member.guild.get_channel(log_channel_id)
                    if log_channel:
                        await log_channel.send(f"{member.mention} was disconnected.")
                
                # Send kick message
                kick_message = settings.get('kick_message', 'You have been disconnected from the voice channel.')
                await member.send(kick_message)


@settings.error
@set_log_channel.error
@set_kick_message.error
@toggle_bot.error
@whitelist_add.error
@whitelist_remove.error
@list_whitelist.error
async def command_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message("You need administrator permissions to use this command.", ephemeral=True)
    else:
        await interaction.response.send_message(f"An error occurred: {str(error)}", ephemeral=True)

bot.run(os.environ.get("BOT_TOKEN"))
