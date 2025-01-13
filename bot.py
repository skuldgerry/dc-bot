import os
import discord
import asyncio
from discord.ext import commands
import json

# Set bot prefix
prefix = "#"

# Define intents
intents = discord.Intents.default()
intents.voice_states = True  # Required for voice state updates
intents.messages = True  # Enable message content intent
intents.message_content = True  # Enable message content intent

# Create bot instance with intents and custom help command
bot = commands.Bot(command_prefix=prefix, intents=intents, help_command=None)

# Function to load server settings from JSON file
def load_settings(guild_id):
    file_path = f"config/{guild_id}/settings.json"
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    else:
        return {}

# Function to save server settings to JSON file
def save_settings(guild_id, settings):
    os.makedirs(f"config/{guild_id}", exist_ok=True)
    file_path = f"config/{guild_id}/settings.json"
    with open(file_path, "w") as f:
        json.dump(settings, f, indent=4)

# Function to load whitelist from JSON file
def load_whitelist(guild_id):
    file_path = f"config/{guild_id}/whitelist.json"
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    else:
        return []

# Function to save whitelist to JSON file
def save_whitelist(guild_id, whitelist):
    os.makedirs(f"config/{guild_id}", exist_ok=True)
    file_path = f"config/{guild_id}/whitelist.json"
    with open(file_path, "w") as f:
        json.dump(whitelist, f, indent=4)

# Event: When bot is ready
@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

# Command: Ping
@bot.command()
async def ping(ctx):
    latency = bot.latency * 1000  # Convert to milliseconds
    await ctx.send(f'Pong! Latency: {latency:.2f}ms')

# Command: Settings menu
@bot.command()
@commands.has_permissions(administrator=True)
async def settings(ctx):
    # Load server settings
    settings = load_settings(ctx.guild.id)

    embed = discord.Embed(title="Settings Menu", color=0x00ff00)
    embed.add_field(name="1️⃣ Set Log Channel", value="Set a channel for logs", inline=False)
    embed.add_field(name="2️⃣ Set Whitelist", value="Set a whitelist of members", inline=False)
    embed.add_field(name="3️⃣ Remove from Whitelist", value="Remove members from the whitelist", inline=False)
    embed.add_field(name="4️⃣ Set Kick Message", value="Set a custom message for kicks", inline=False)
    embed.add_field(name="5️⃣ Disable Bot", value="Disable the bot", inline=False)
    embed.add_field(name="6️⃣ Enable Bot", value="Enable the bot", inline=False)
    embed.add_field(name="7️⃣ Bot Status", value="Check if the bot is enabled or disabled", inline=False)
    
    # Send the embedded message
    msg = await ctx.send(embed=embed)
    
    # Add reactions to the message
    for emoji in ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣']:
        await msg.add_reaction(emoji)
    
    # Function to wait for reaction
    def check(reaction, user):
        return user == ctx.message.author and str(reaction.emoji) in ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣']
    
    try:
        # Wait for reaction from the message author
        reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
        
        # Perform action based on reaction
        if str(reaction.emoji) == '1️⃣':
            await set_log_channel(ctx, settings)
        elif str(reaction.emoji) == '2️⃣':
            await set_whitelist(ctx, settings)
        elif str(reaction.emoji) == '3️⃣':
            await remove_from_whitelist(ctx, settings)
        elif str(reaction.emoji) == '4️⃣':
            await set_kick_message(ctx, settings)
        elif str(reaction.emoji) == '5️⃣':
            await disable_bot(ctx, settings)
        elif str(reaction.emoji) == '6️⃣':
            await enable_bot(ctx, settings)
        elif str(reaction.emoji) == '7️⃣':
            await bot_status(ctx, settings)
            
    except asyncio.TimeoutError:
        await ctx.send("You took too long to make a selection.")

# Command: Set Log Channel
async def set_log_channel(ctx, settings):
    await ctx.send("Please mention the channel you want to set for logs.")
    try:
        message = await bot.wait_for('message', timeout=60.0, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
        if message.channel_mentions:
            channel = message.channel_mentions[0]
            # Update settings
            settings['log_channel'] = channel.id
            save_settings(ctx.guild.id, settings)
            await ctx.send(f"Log channel set to {channel.mention}")
        else:
            await ctx.send("No channels were mentioned. Please mention a channel.")
    except asyncio.TimeoutError:
        await ctx.send("You took too long to mention a channel.")

# Command: Set Whitelist
async def set_whitelist(ctx, settings):
    await ctx.send("Please provide member IDs to add to the whitelist, separated by spaces.")
    try:
        message = await bot.wait_for('message', timeout=60.0, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
        member_ids = message.content.split()
        # Filter out non-integer IDs
        member_ids = [member_id for member_id in member_ids if member_id.isdigit()]
        if member_ids:
            # Load whitelist
            whitelist = load_whitelist(ctx.guild.id)
            # Add new member IDs to whitelist
            whitelist.extend(member_ids)
            # Deduplicate the whitelist
            whitelist = list(set(whitelist))
            # Save whitelist
            save_whitelist(ctx.guild.id, whitelist)
            await ctx.send("Whitelist updated successfully.")
        else:
            await ctx.send("Invalid input. Please provide valid member IDs.")
    except asyncio.TimeoutError:
        await ctx.send("You took too long to provide member IDs.")

# Command: Remove from Whitelist
async def remove_from_whitelist(ctx, settings):
    await ctx.send("Please provide member IDs to remove from the whitelist, separated by spaces.")
    try:
        message = await bot.wait_for('message', timeout=60.0, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
        member_ids = message.content.split()
        # Filter out non-integer IDs
        member_ids = [member_id for member_id in member_ids if member_id.isdigit()]
        if member_ids:
            # Load whitelist
            whitelist = load_whitelist(ctx.guild.id)
            # Remove provided member IDs from whitelist
            whitelist = [member_id for member_id in whitelist if member_id not in member_ids]
            # Save whitelist
            save_whitelist(ctx.guild.id, whitelist)
            await ctx.send("Members removed from whitelist successfully.")
        else:
            await ctx.send("Invalid input. Please provide valid member IDs.")
    except asyncio.TimeoutError:
        await ctx.send("You took too long to provide member IDs.")

# Command: Set Kick Message
async def set_kick_message(ctx, settings):
    await ctx.send("Please enter the custom kick message.")
    try:
        message = await bot.wait_for('message', timeout=60.0, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
        kick_message = message.content
        # Update settings
        settings['kick_message'] = kick_message
        save_settings(ctx.guild.id, settings)
        await ctx.send("Kick message updated successfully.")
    except asyncio.TimeoutError:
        await ctx.send("You took too long to enter the custom kick message.")

# Command: Disable Bot
@bot.command()
@commands.has_permissions(administrator=True)
async def disable_bot(ctx, settings):
    # Update bot status in settings
    settings['bot_enabled'] = False
    save_settings(ctx.guild.id, settings)
    await ctx.send("Bot has been disabled.")

# Command: Enable Bot
@bot.command()
@commands.has_permissions(administrator=True)
async def enable_bot(ctx, settings):
    # Update bot status in settings
    settings['bot_enabled'] = True
    save_settings(ctx.guild.id, settings)
    await ctx.send("Bot has been enabled.")

# Command: Bot Status
async def bot_status(ctx, settings):
    bot_enabled = settings.get('bot_enabled', True)  # Default to True if not set
    status = "enabled" if bot_enabled else "disabled"
    await ctx.send(f"The bot is currently {status}.")

# Command: List Whitelist
@bot.command()
async def list_whitelist(ctx):
    whitelist = load_whitelist(ctx.guild.id)
    if whitelist:
        whitelist_info = []
        for member_id in whitelist:
            member = ctx.guild.get_member(int(member_id))
            if member:
                whitelist_info.append(f"{member.name} (ID: {member_id})")
            else:
                whitelist_info.append(f"Unknown Member (ID: {member_id})")
        await ctx.send("Whitelist:\n" + "\n".join(whitelist_info))
    else:
        await ctx.send("The whitelist is empty.")

# Command: Custom Help
@bot.command()
async def help(ctx):
    help_embed = discord.Embed(title="Available Commands", color=0x00ff00)
    help_embed.add_field(name="ping", value="Check bot latency", inline=False)
    help_embed.add_field(name="settings", value="Access the settings menu", inline=False)
    help_embed.add_field(name="list_whitelist", value="List members in the whitelist", inline=False)
    help_embed.add_field(name="disable_bot", value="Disable the bot", inline=False)
    help_embed.add_field(name="enable_bot", value="Enable the bot", inline=False)
    help_embed.add_field(name="bot_status", value="Check the bot status", inline=False)
    await ctx.send(embed=help_embed)

# Event: When a member's voice state changes
@bot.event
async def on_voice_state_update(member, before, after):
    settings = load_settings(member.guild.id)  # Load server settings
    bot_enabled = settings.get('bot_enabled', True)  # Default to True if not set
    
    if member.bot:  # Ignore bot users
        return

    if after.self_mute and after.self_deaf:  # If member is both muted and deafened
        if member.voice:  # If member is in a voice channel
            # Check if bot is enabled
            if bot_enabled:
                # Check if member is in whitelist
                whitelist = load_whitelist(member.guild.id)
                if str(member.id) in whitelist:
                    return  # Member is in whitelist, do not disconnect
                await member.move_to(None)  # Disconnect member from voice channel
                # Log the member disconnection
                log_channel_id = settings.get('log_channel')
                if log_channel_id:
                    log_channel = member.guild.get_channel(log_channel_id)
                    if log_channel:
                        await log_channel.send(f"{member.mention} was disconnected.")
                # Get custom kick message, or use default if not set
                kick_message = settings.get('kick_message', 'You have been disconnected from the voice channel.')
                # Send custom kick message to the member
                await member.send(kick_message)

# Run the bot with the token from environment variable
bot.run(os.environ.get("BOT_TOKEN"))
