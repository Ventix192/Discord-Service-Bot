import discord
import asyncio
import datetime
import random
from colorama import *
from discord.ext import tasks
from discord.ext import commands
from discord.commands import Option

import config

import io
import chat_exporter

def get_config(key):
    return getattr(config, key, None)

intents = discord.Intents.all()
intents.members = True
intents.messages = True
intents.moderation = True

client = commands.Bot(intents=intents)

servers = [get_config("Main")["Guild-ID"]]

@client.event
async def on_ready():
    debug("Bot is ready!")
   
    if get_config("Verify")["Enabled"] == True:
        client.add_view(VerifyButton())

    if get_config("Stats")["Enabled"] == True:
        stats.start()

    if get_config("Ticketsystem")["Enabled"] == True:
        client.add_view(TicketOptions())
        client.add_view(ReopenButton())

# Join System

@client.event
async def on_member_join(member):
    channel = client.get_channel(get_config("Channels")["Welcome"])

    embed = discord.Embed(title="\👋 Ceru - Willkommen", description=f"Willkommen auf dem Server!\nDu bist das {len(member.guild.members)}. Mitglied.", color=get_config("Main")["Color"])
    embed.set_author(name=get_config("Texts")["Author"], icon_url=get_config("Images")["Author"])
    embed.set_footer(text=get_config("Texts")["Footer"], icon_url=get_config("Images")["Footer"])
    embed.set_thumbnail(url=member.avatar.url)
    embed.add_field(name=f"<:user:1295356198786433095> Name:", value=f"> {member.name}", inline=False)
    embed.add_field(name=f"<:pin:1295374082476474442> Erwähnung:", value=f"> {member.mention}", inline=False)
    embed.add_field(name=f"<:global:1295373873633558538> ID:", value=f"> {member.id}", inline=False)
    embed.add_field(name=f"<:time:1295375248635592766> Server beigetreten:", value=f"> <t:{int(round(member.joined_at.timestamp()))}:R> (<t:{int(round(member.joined_at.timestamp()))}:f>)", inline=False)
    embed.add_field(name=f"<:time:1295375248635592766> Account erstellt:", value=f"> <t:{int(round(member.created_at.timestamp()))}:R> (<t:{int(round(member.created_at.timestamp()))}:f>)", inline=False)
    embed.add_field(name=f"<:info:1295375358803050586> Mitglieder:", value=f"> {len(member.guild.members)}", inline=False)
    await channel.send(embed=embed)

# Leave System

@client.event
async def on_member_remove(member):
    channel = client.get_channel(get_config("Channels")["Leave"])

    embed = discord.Embed(title="\👋 Ceru - Leave", description=f"Ein Member hat den Server verlassen.\nWir sind jetzt nur noch {len(member.guild.members)} Mitglieder.", color=get_config("Main")["Color"])
    embed.set_author(name=get_config("Texts")["Author"], icon_url=get_config("Images")["Author"])
    embed.set_footer(text=get_config("Texts")["Footer"], icon_url=get_config("Images")["Footer"])
    embed.set_thumbnail(url=member.avatar.url)
    embed.add_field(name=f"<:user:1295356198786433095> Name:", value=f"> {member.name}", inline=False)
    embed.add_field(name=f"<:pin:1295374082476474442> Erwähnung:", value=f"> {member.mention}", inline=False)
    embed.add_field(name=f"<:global:1295373873633558538> ID:", value=f"> {member.id}", inline=False)
    await channel.send(embed=embed)

# Boost System

@client.event
async def on_member_update(before, after):
    if before.premium_since is None and after.premium_since is not None:
        channel = client.get_channel(get_config("Channels")["Boosts"])

        embed = discord.Embed(title="\🩷 Ceru - Boost", description=f"Ein Member hat den Server geboostet.\nWir haben jetzt {len(after.guild.premium_subscribers)} Boosts.", color=get_config("Main")["Color"])
        embed.set_author(name=get_config("Texts")["Author"], icon_url=get_config("Images")["Author"])
        embed.set_footer(text=get_config("Texts")["Footer"], icon_url=get_config("Images")["Footer"])
        embed.set_thumbnail(url=get_config("Images")["Thumbnail"])
        await channel.send(embed=embed)

# Verify System

if get_config("Verify")["Enabled"] == True:
    @client.slash_command(guild_ids = servers, name="setup-verify", description="🟢 Setzt das Verify System auf")
    @commands.has_permissions(administrator=True)
    async def setup_verify(ctx, channel: Option(discord.TextChannel, description="📝 Der Channel, in dem die Nachricht gesendet wird", required=False)):
        if channel is None:
            channel = ctx.channel

        embed = discord.Embed(title=get_config("Verify")["Embed"]["Title"], description=get_config("Verify")["Embed"]["Description"], color=get_config("Main")["Color"])
        embed.set_author(name=get_config("Texts")["Author"], icon_url=get_config("Images")["Author"])
        embed.set_footer(text=get_config("Texts")["Footer"], icon_url=get_config("Images")["Footer"])
        embed.set_thumbnail(url=get_config("Images")["Thumbnail"])
        await channel.send(embed=embed, view=VerifyButton())
        await asyncio.sleep(1)
        await ctx.respond(get_config("Verify")["Language"]["Setuped"], ephemeral=True)

    class VerifyButton(discord.ui.View):
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs, timeout=None)

        @discord.ui.button(label="🟢 Verifizieren", style=discord.ButtonStyle.red, custom_id="TicketDelete")
        async def first_button_callback(self, button, interaction):
            roles = [interaction.guild.get_role(role) for role in get_config("Verify")["Roles"]]

            if not any(role in interaction.user.roles for role in roles):
                for role in roles:
                    await interaction.user.add_roles(role)
                await interaction.response.send_message(get_config("Verify")["Langauge"]["Verified"], ephemeral=True)
            else:
                for role in roles:
                    await interaction.user.remove_roles(role)
                await interaction.response.send_message(get_config("Verify")["Language"]["Unverified"], ephemeral=True)

    @setup_verify.error
    async def setup_verify_error(ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.respond("Du hast keine Berechtigung, diesen Command auszuführen!", ephemeral=True)

        else:
            await ctx.respond("Ein Fehler ist aufgetreten!", ephemeral=True)
            raise error

# Vorschläge System

if get_config("Vorschläge")["Enabled"] == True:
    @client.event
    async def on_message(message):
        if message.channel.id == get_config("Channels")["Vorschläge"]:
            if not message.author.bot:
                embed = discord.Embed(title=get_config("Vorschläge")["Embed"]["Title"], description=f"> {message.content}", color=get_config("Main")["Color"])
                embed.set_author(name=message.author.name, icon_url=message.author.avatar.url)
                embed.set_footer(text=f"Vorschlag von {message.author.name}", icon_url=message.author.avatar.url)
                embed.set_thumbnail(url=message.author.avatar.url)
                await message.delete()
                # await asyncio.sleep(1)
                msg = await message.channel.send(embed=embed)
                reactions = get_config("Vorschläge")["Reactions"]
                for reaction in reactions:
                    await msg.add_reaction(reaction)

# @client.event
# async def on_member_update(before, after):
#     # await asyncio.sleep(1)
#     async for entry in before.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_role_update):
#         channel = client.get_channel(1295887439138918471)
#         if entry.target.id == before.id:
#             if len(before.roles) < len(after.roles):
#                 added_roles = [role for role in after.roles if role not in before.roles]
#                 for role in added_roles:
#                     embed = discord.Embed(title="🔒 Role Added", description=f"Role '{role.name}' added to {before.name} by {entry.user.name}", color=0x00bfff)
#                     embed.set_author(name=get_config("Texts")["Author"], icon_url=get_config("Images")["Author"])
#                     embed.set_footer(text=get_config("Texts")["Footer"], icon_url=get_config("Images")["Footer"])
#                     embed.set_thumbnail(url=before.avatar.url)
#                     await channel.send(embed=embed)
#             elif len(before.roles) > len(after.roles):
#                 removed_roles = [role for role in before.roles if role not in after.roles]
#                 for role in removed_roles:
#                     embed = discord.Embed(title="🔓 Role Removed", description=f"Role '{role.name}' removed from {before.name} by {entry.user.name}", color=0x00bfff)
#                     embed.set_author(name=get_config("Texts")["Author"], icon_url=get_config("Images")["Author"])
#                     embed.set_footer(text=get_config("Texts")["Footer"], icon_url=get_config("Images")["Footer"])
#                     embed.set_thumbnail(url=before.avatar.url)
#                     await channel.send(embed=embed)

# Payment System

if get_config("Payments")["PayPal"]["Enabled"] == True:
    @client.slash_command(guild_ids = servers, name="paypal", description="🟢 Payments - PayPal")
    @commands.has_permissions(administrator=True)
    async def paypal(ctx, betrag: Option(int, description="💰 Der Betrag, der bezahlt wird", required=True)):
        embed = discord.Embed(title="\🟢 Payments - PayPal", description=f"> Bitte überweise {betrag}€ an email@gmail.com!", color=get_config("Main")["Color"])
        embed.set_author(name=get_config("Texts")["Author"], icon_url=get_config("Images")["Author"])
        embed.set_footer(text=get_config("Texts")["Footer"], icon_url=get_config("Images")["Footer"])
        embed.set_thumbnail(url=get_config("Images")["Thumbnail"])
        await ctx.respond(embed=embed)

@paypal.error
async def paypal_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.respond("Du hast keine Berechtigung, diesen Command auszuführen!", ephemeral=True)

    else:
        await ctx.respond("Ein Fehler ist aufgetreten!", ephemeral=True)
        raise error

if get_config("Payments")["Paysafecard"]["Enabled"] == True:
    @client.slash_command(guild_ids = servers, name="paysafecard", description="🟢 Payments - Paysafecard")
    @commands.has_permissions(administrator=True)
    async def paysafecard(ctx, betrag: Option(int, description="💰 Der Betrag, der bezahlt wird", required=True)):
        embed = discord.Embed(title="\🟢 Payments - Paysafecard", description=f"> Bitte sende den Code per DM an {ctx.author.mention}!", color=get_config("Main")["Color"])
        embed.set_author(name=get_config("Texts")["Author"], icon_url=get_config("Images")["Author"])
        embed.set_footer(text=get_config("Texts")["Footer"], icon_url=get_config("Images")["Footer"])
        embed.set_thumbnail(url=get_config("Images")["Thumbnail"])
        await ctx.respond(embed=embed)

@paysafecard.error
async def paysafecard_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.respond("Du hast keine Berechtigung, diesen Command auszuführen!", ephemeral=True)

    else:
        await ctx.respond("Ein Fehler ist aufgetreten!", ephemeral=True)
        raise error

if get_config("Payments")["Banküberweisung"]["Enabled"] == True:
    @client.slash_command(guild_ids = servers, name="banküberweisung", description="🟢 Payments - Banküberweisung")
    @commands.has_permissions(administrator=True)
    async def banküberweisung(ctx, betrag: Option(int, description="💰 Der Betrag, der bezahlt wird", required=True), verwendungszweck: Option(description="📝 Der Verwendungszweck für die Bezahlung", required=True)):
        embed = discord.Embed(title="\🟢 Payments - Banküberweisung", description=f"> Bitte überweise {betrag}€ an die folgende Bankverbindung:\n\n> Bank: Musterbank\n> IBAN: DE12345678901234567890\n> BIC: MUBADEFFXXX\n> Verwendungszweck: {verwendungszweck}", color=get_config("Main")["Color"])
        embed.set_author(name=get_config("Texts")["Author"], icon_url=get_config("Images")["Author"])
        embed.set_footer(text=get_config("Texts")["Footer"], icon_url=get_config("Images")["Footer"])
        embed.set_thumbnail(url=get_config("Images")["Thumbnail"])
        await ctx.respond(embed=embed)

@banküberweisung.error
async def banküberweisung_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.respond("Du hast keine Berechtigung, diesen Command auszuführen!", ephemeral=True)

    else:
        await ctx.respond("Ein Fehler ist aufgetreten!", ephemeral=True)
        raise error

# Stats System

@tasks.loop(minutes=1)
async def stats():
    members = client.get_channel(get_config("Stats")["Members"])
    customers = client.get_channel(get_config("Stats")["Customers"])

    customerrole = client.get_guild(get_config("Main")["Guild-ID"]).get_role(get_config("Stats")["Customer-Role"])

    membercount = len(client.get_guild(get_config("Main")["Guild-ID"]).members)
    customercount = len(customerrole.members)

    await members.edit(name=f"👥 Mitglieder: {membercount}")
    await customers.edit(name=f"🛒 Customer: {customercount}")

# Embed Creator

@client.slash_command(guild_ids = servers, name="create-embed", description="🟢 Erstellt ein Embed")
@commands.has_permissions(administrator=True)
async def create_embed(ctx, title: Option(str, description="📝 Der Titel des Embeds", required=True), description: Option(str, description="📝 Die Beschreibung des Embeds", required=True), image: Option(discord.Attachment, description="🖼️ Das Große Bild das Embeds", required=False), thumbnail: Option(discord.Attachment, description="🖼️ Das kleine Bild des Embeds", required=False)):
    embed = create_embed(title, description, image, thumbnail, get_config("Main")["Color"])
    await ctx.respond(embed=embed)

@create_embed.error
async def create_embed_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.respond("Du hast keine Berechtigung, diesen Command auszuführen!", ephemeral=True)

    else:
        await ctx.respond("Ein Fehler ist aufgetreten!", ephemeral=True)
        raise error

def create_embed(title, description, image, thumbnail, color):
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_author(name=get_config("Texts")["Author"], icon_url=get_config("Images")["Author"])
    embed.set_footer(text=get_config("Texts")["Footer"], icon_url=get_config("Images")["Footer"])
    if thumbnail is not None:
        embed.set_thumbnail(url=thumbnail)
    else:
        embed.set_thumbnail(url=get_config("Images")["Thumbnail"])
    if image is not None:
        embed.set_image(url=image)
    return embed

# Changelogs System
if get_config("Changelogs")["Enabled"] == True:

    @client.slash_command(guild_ids = servers, name="post-changelog", description="🟢 Changelog erstellen")
    @commands.has_permissions(administrator=True)
    async def post_changelog(ctx, description: Option(str, description="📝 Die Beschreibung des Changelogs", required=True), version: Option(str, description="📝 Die Version des Changelogs", required=True), script: Option(discord.TextChannel, description="📝 Das Script für den Changelog", required=True)):
        channel = client.get_channel(get_config("Changelogs")["Channel"])
        embed = discord.Embed(title=f"🟢 Neuer Changelog!", description=f"> {description}", color=get_config("Main")["Color"])
        embed.add_field(name="\📝 Script:", value=f"> {script.mention}", inline=False)
        embed.add_field(name="\📝 Version:", value=f"> {version}", inline=False)
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M")
        embed.add_field(name="\📅 Datum:", value=f"> {timestamp}", inline=False)
        embed.set_author(name=get_config("Texts")["Author"], icon_url=get_config("Images")["Author"])
        embed.set_footer(text=get_config("Texts")["Footer"], icon_url=get_config("Images")["Footer"])
        embed.set_thumbnail(url=get_config("Images")["Thumbnail"])
        await channel.send(embed=embed)
        await ctx.respond("> Der Changelog wurde erfolgreich erstellt!", ephemeral=True)

@post_changelog.error
async def post_changelog_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.respond("Du hast keine Berechtigung, diesen Command auszuführen!", ephemeral=True)

    else:
        await ctx.respond("Ein Fehler ist aufgetreten!", ephemeral=True)
        raise error
    
# Moderation

if get_config("Moderation")["Ban"]["Enabled"] == True:
    @client.slash_command(guild_ids = servers, name="ban", description="🟢 Bannt einen User")
    @commands.has_permissions(ban_members=True)
    async def ban(ctx, user: Option(discord.Member, description="👤 Der User, der gebannt wird", required=True), reason: Option(str, description="📝 Der Grund für den Ban", required=False)):
        if reason is None:
            reason = "Kein Grund angegeben!"
        await user.ban(reason=reason)
        await ctx.respond(f"> {user.name} wurde erfolgreich gebannt!", ephemeral=True)

@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.respond("Du hast keine Berechtigung, diesen Command auszuführen!", ephemeral=True)

    else:
        await ctx.respond("Ein Fehler ist aufgetreten!", ephemeral=True)
        raise error
    
if get_config("Moderation")["Kick"]["Enabled"] == True:
    @client.slash_command(guild_ids = servers, name="kick", description="🟢 Kickt einen User")
    @commands.has_permissions(kick_members=True)
    async def kick(ctx, user: Option(discord.Member, description="👤 Der User, der gekickt wird", required=True), reason: Option(str, description="📝 Der Grund für den Kick", required=False)):
        if reason is None:
            reason = "Kein Grund angegeben!"
        await user.kick(reason=reason)
        await ctx.respond(f"> {user.name} wurde erfolgreich gekickt!", ephemeral=True)

@kick.error
async def kick_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.respond("Du hast keine Berechtigung, diesen Command auszuführen!", ephemeral=True)

    else:
        await ctx.respond("Ein Fehler ist aufgetreten!", ephemeral=True)
        raise error

# Guess the Number

if get_config("Numberguess")["Enabled"] == True:

    game_active = False
    target_number = None

    @client.event
    async def on_message(message):
        global game_active
        global target_number

        if game_active and message.content.strip() == str(target_number):
            game_active = False
            await message.channel.send(f"> Glückwunsch, {message.author.mention}! Du hast die Zahl ({target_number}) erraten!\n > Bitte sende <@825085110357327934> eine DM mit deinem CFX Name!")

    @client.slash_command(guild_ids = servers, name="game-start", description="🎮 Startet das Zahlen erraten Game")
    @commands.has_permissions(administrator=True)
    async def game_start(ctx, min: Option(int, description="Von:", required=True), max: Option(int, description="Bis:", required=True), script: Option(discord.TextChannel, description="Script:", required=True)):
        global game_active
        global target_number

        target_number = random.randint(min, max)
        game_active = True

        print(target_number)

        msg = await ctx.send(content=f"**Zahl erraten -> Script gewinnen**\n\n> Zahl: {min}-{max}\n\n> Script: {script.mention}\n\n> Spammen erlaubt, der erste der unsere Zahl errät gewinnt!\n\n> @everyone")
        await msg.pin()
        await asyncio.sleep(1)
        await ctx.respond(f"> Das Game wurde gestartet! (Zahl: {target_number})", ephemeral=True)

        print(target_number)

    @game_start.error
    async def game_start_error(ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.respond("Du hast keine Berechtigung, diesen Command auszuführen!", ephemeral=True)

        else:
            await ctx.respond("Ein Fehler ist aufgetreten!", ephemeral=True)
            raise error
    
# Giveaway System

if get_config("Giveaway")["Enabled"] == True:
    async def funktion(ctx, msg, when: datetime.datetime):
        await client.wait_until_ready()
        await discord.utils.sleep_until(when=when)
        new_msg = await ctx.channel.fetch_message(msg.id)

        user_list = [u for u in await new_msg.reactions[0].users().flatten() if
            u != client.user]

        if len(user_list) == 0:
            em = discord.Embed(
                title="Niemand hat Reagiert!",
                color=0x992d22
            )

            await ctx.send(embed=em)

        else:
            winner = random.choice(user_list)
            em = discord.Embed(title="\🎉 Giveaway Beendet \🎉", description=f"Herzlichen Glückwunsch!\nGewinner: {winner.mention}\nInformation: Bitte melde dich bei {ctx.author.mention} per Dm!", color=get_config("Main")["Color"])
            em.set_author(name=get_config("Texts")["Author"], icon_url=get_config("Images")["Author"])
            em.set_footer(text=get_config("Texts")["Footer"], icon_url=get_config("Images")["Footer"])

            await ctx.send(embed=em, content=f"> {winner.mention} hat das Giveaway gewonnen!")

    @client.slash_command(description="Erstellt ein Giveaway")
    @discord.guild_only()
    @commands.has_permissions(administrator=True)
    async def giveaway(ctx, time: Option(str, "Gebe die Zeit an.", required=True), *, prize: Option(str, "Gebe die Zeit an.", required=True)):
        time_convert = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        gawtime = int(time[:-1]) * time_convert[time[-1]]
        t1 = (datetime.datetime.now().timestamp() + gawtime - 3600)
        t2 = datetime.datetime.fromtimestamp(int(t1))

        result = t2 + datetime.timedelta(hours=1)
        embed = discord.Embed(title="\🎉 Neues Giveaway \🎉", color=get_config("Main")["Color"])
        embed.add_field(name="Preis", value=f"{prize}", inline=False)
        embed.add_field(name="Dauer", value=f"<t:{int(result.timestamp())}:R> (<t:{int(result.timestamp())}:f>", inline=False)
        embed.add_field(name="Hoster", value=f"{ctx.author.mention}", inline=False)
        embed.set_author(name=get_config("Texts")["Author"], icon_url=get_config("Images")["Author"])
        embed.set_footer(text=get_config("Texts")["Footer"], icon_url=get_config("Images")["Footer"])
        await ctx.respond("> Giveaway wurde erfolgreich gestartet!", ephemeral=True)

        msg = await ctx.send(embed=embed)
        await msg.add_reaction("🎉")

        asyncio.create_task(funktion(ctx, msg, result))

    @giveaway.error
    async def giveaway_error(ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.respond("Du hast keine Berechtigung, diesen Command auszuführen!", ephemeral=True)

        else:
            await ctx.respond("Ein Fehler ist aufgetreten!", ephemeral=True)
            raise error

# Ticket System

if get_config("Ticketsystem")["Enabled"] == True:

    @client.slash_command(
        guild_ids=servers,
        name="ticket_sendembed",
        description="🎫 Sendet das Ticket Embed.",
    )
    @commands.has_permissions(administrator=True)
    async def ticketsend(
        ctx,
        channel: Option(
            discord.TextChannel, description="Channel für das Ticket Embed.", required=False
        ),
    ):
        if channel is None:
            channel = ctx.channel

        embed = discord.Embed(
            title="Ceru - Ticketsystem",
            description="Hier können sie ein Ticket erstellen.",
            color=get_config("Main")["Color"],
        )
        embed.set_author(name=get_config("Texts")["Author"], icon_url=get_config("Images")["Author"])
        embed.set_footer(text=get_config("Texts")["Footer"], icon_url=get_config("Images")["Footer"])
        embed.set_thumbnail(url=get_config("Images")["Thumbnail"])
        embed.set_image(url=get_config("Ticketsystem")["Image"])
        await channel.send(embed=embed, view=TicketOptions())
        await ctx.respond(
            f"> Das Ticket Embed wurde erfolgreich in {channel.mention} gepostet!",
            ephemeral=True,
        )


@ticketsend.error
async def error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.respond(
            f"> Du hast keine Rechte dazu! Fehlende Permission: ``Administrator``",
            ephemeral=True,
        )
    else:
        await ctx.respond(
            "> Es gibt ein Problem mit dem Bot, bitte kontaktiere das Team!",
            ephemeral=True,
        )
        raise error


class Ticket(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Kaufen",
                emoji="🟢",
                description="Wenn sie etwas kaufen möchten.",
            ),
        ]
        super().__init__(
            placeholder="Wähle eine Ticket Kategorie aus.",
            max_values=1,
            min_values=1,
            options=options,
            custom_id="Ticketgründe",
        )

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "Kaufen":
            category = client.get_channel(get_config("Ticketsystem")["Kaufen"]["Category"])
            for channel in category.channels:
                if interaction.user.name in channel.name:
                    await interaction.response.edit_message(view=TicketOptions())
                    await interaction.followup.send(
                        f"> Sie haben bereits ein Ticket in dieser Kategorie offen! ({channel.mention})",
                        ephemeral=True,
                    )
                    return

            category = client.get_channel(get_config("Ticketsystem")["Kaufen"]["Category"])
            channel = await category.create_text_channel(
                f"🟢〢kaufen {interaction.user.name}",
                topic=f"Author {interaction.user.mention} | {interaction.user.id}",
            )
            everyone = interaction.guild.get_role(get_config("Main")["Guild-ID"])
            team = interaction.guild.get_role(get_config("Ticketsystem")["Kaufen"]["Role1"])
            team2 = interaction.guild.get_role(get_config("Ticketsystem")["Kaufen"]["Role2"])
            team3 = interaction.guild.get_role(get_config("Ticketsystem")["Kaufen"]["Role3"])
            await channel.set_permissions(
                everyone, view_channel=False, send_messages=True
            )
            await channel.set_permissions(interaction.user, view_channel=True)
            await channel.set_permissions(team, view_channel=True, send_messages=True)
            await channel.set_permissions(team2, view_channel=True, send_messages=True)
            await channel.set_permissions(team3, view_channel=True, send_messages=True)
            embed = discord.Embed(
                title="Ticket erstellt!",
                description=f"> Das **Ceru-Dev** Team wird dir gleich helfen.\n\n**Ticket Owner:**\n > {interaction.user.mention}\n\n**Ticket Kategorie:**\n> Kaufen",
                color=get_config("Main")["Color"],
            )
            # embed.add_field(name="Ticket Grund:", value=self.children[0].value, inline=False)
            embed.set_author(name=get_config("Texts")["Author"], icon_url=get_config("Images")["Author"])
            embed.set_footer(text=get_config("Texts")["Footer"], icon_url=get_config("Images")["Footer"])
            embed.set_thumbnail(url=get_config("Images")["Thumbnail"])
            embed.set_image(url=get_config("Ticketsystem")["Image"])
            # embed.set_image(url=f"https://cdn.discordapp.com/attachments/1086713212726161603/1086743118818312343/Banner2.gif")
            message = await channel.send(
                content="<@&"
                + str(get_config("Ticketsystem")["Kaufen"]["Role1"])
                + "> <@&"
                + str(get_config("Ticketsystem")["Kaufen"]["Role2"])
                + "> <@&"
                + str(get_config("Ticketsystem")["Kaufen"]["Role3"])
                + ">",
                embed=embed,
                view=ReopenButton(),
            )
            await message.pin()

            embed2 = discord.Embed(
                title="Ticket erstellt!",
                description=f"> Hey, {interaction.user.mention} dein Ticket ({channel.mention}) wurde erstellt!",
                color=get_config("Main")["Color"],
            )
            embed2.set_author(name=get_config("Texts")["Author"], icon_url=get_config("Images")["Author"])
            embed2.set_footer(text=get_config("Texts")["Footer"], icon_url=get_config("Images")["Footer"])
            embed2.set_thumbnail(url=get_config("Images")["Thumbnail"])
            embed2.set_image(url=get_config("Ticketsystem")["Image"])
            await interaction.response.edit_message(view=TicketOptions())
            await asyncio.sleep(1)
            await interaction.followup.send(embed=embed2, ephemeral=True)

            channel2 = client.get_channel(get_config("Ticketsystem")["Logs"])
            embed3 = discord.Embed(title="Ticket erstellt!", color=get_config("Main")["Color"])
            embed3.set_author(name=get_config("Texts")["Author"], icon_url=get_config("Images")["Author"])
            embed3.set_footer(text=get_config("Texts")["Footer"], icon_url=get_config("Images")["Footer"])
            embed3.set_image(url=get_config("Ticketsystem")["Image"])
            embed3.set_thumbnail(url=get_config("Images")["Thumbnail"])
            embed3.add_field(
                name="Ersteller:", value=f"> {interaction.user.mention}", inline=False
            )
            # embed3.add_field(name="Closer", value=interaction.user.mention, inline=False)
            embed3.add_field(
                name="icket:",
                value=f"> {channel.name} ({channel.mention})",
                inline=False,
            )
            embed3.add_field(name="Kategorie:", value="> Kaufen", inline=False)
            await channel2.send(embed=embed3)

class FeedbackButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="👍 Positiv",
        style=discord.ButtonStyle.green,
        custom_id="FeedbackPositiv",
    )
    async def first_button_callback(self, button, interaction):
        await interaction.response.send_message(
            "> Danke für dein Feedback!", ephemeral=True
        )
        channel = client.get_channel(get_config("Ticketsystem")["Logs"])
        embed = discord.Embed(title="Feedback", color=get_config("Main")["Color"])
        embed.set_author(name=get_config("Texts")["Author"], icon_url=get_config("Images")["Author"])
        embed.set_footer(text=get_config("Texts")["Footer"], icon_url=get_config("Images")["Footer"])
        embed.set_thumbnail(url=get_config("Images")["Thumbnail"])
        embed.add_field(name="Ersteller:", value=f"> {interaction.user.mention}", inline=False)
        embed.add_field(name="Feedback:", value="> Positiv", inline=False)
        await channel.send(embed=embed)

        # Disable buttons
        self.disable_all_items()
        await interaction.message.edit(view=self)

    @discord.ui.button(
        label="👎 Negativ",
        style=discord.ButtonStyle.red,
        custom_id="FeedbackNegativ",
    )
    async def second_button_callback(self, button, interaction):
        await interaction.response.send_message(
            "> Danke für dein Feedback!", ephemeral=True
        )
        channel = client.get_channel(get_config("Ticketsystem")["Logs"])
        embed = discord.Embed(title="Feedback", color=get_config("Main")["Color"])
        embed.set_author(name=get_config("Texts")["Author"], icon_url=get_config("Images")["Author"])
        embed.set_footer(text=get_config("Texts")["Footer"], icon_url=get_config("Images")["Footer"])
        embed.set_thumbnail(url=get_config("Images")["Thumbnail"])
        embed.add_field(name="Ersteller:", value=f"> {interaction.user.mention}", inline=False)
        embed.add_field(name="Feedback:", value="> Negativ", inline=False)
        await channel.send(embed=embed)

        # Disable buttons
        self.disable_all_items()
        await interaction.message.edit(view=self)

    def disable_all_items(self):
        for item in self.children:
            item.disabled = True

class TicketOptions(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Ticket())

class ReopenButton(discord.ui.View):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs, timeout=None)

    @discord.ui.button(
        label="🛑 Ticket Löschen",
        style=discord.ButtonStyle.red,
        custom_id="TicketDelete",
    )
    async def first_button_callback(self, button, interaction):
        user = interaction.guild.get_member(
            int(interaction.channel.topic.split("|")[1].strip())
        )
        embed = discord.Embed(
            title="Ticket geschlossen!",
            description=f"> Das Ticket wird in ein paar Sekunden gelöscht!",
            color=get_config("Main")["Color"],
        )
        embed.set_author(name=get_config("Texts")["Author"], icon_url=get_config("Images")["Author"])
        embed.set_footer(text=get_config("Texts")["Footer"], icon_url=get_config("Images")["Footer"])
        embed.set_thumbnail(url=get_config("Images")["Thumbnail"])
        # embed.set_image(url=ticket_img)
        await interaction.response.send_message(embed=embed, ephemeral=False)
        await asyncio.sleep(2)

        transcript = await chat_exporter.export(
            interaction.channel,
            limit=None,
            tz_info="CET",
            military_time=True,
            bot=client,
        )

        if transcript is None:
            return

        transcript_file2 = discord.File(
            io.BytesIO(transcript.encode()),
            filename=f"transcript_{interaction.channel.name}.html",
        )

        await interaction.channel.delete()
        dm = discord.Embed(
            title="Ticket geschlossen!",
            description="> Dein Ticket auf **Ceru-Dev** wurde geschlossen.",
            color=get_config("Main")["Color"],
        )
        dm.add_field(name="\🔐 Geschlossen von:", value=f"> {interaction.user.mention}", inline=False)
        # dm.add_field(name="\📅 Geschlossen am:", value=f"> {}", inline=False)
        dm.set_author(name=get_config("Texts")["Author"], icon_url=get_config("Images")["Author"])
        dm.set_footer(text=get_config("Texts")["Footer"], icon_url=get_config("Images")["Footer"])
        dm.set_thumbnail(url=get_config("Images")["Thumbnail"])
        # await interaction.channel.send(file=transcript_file)
        await user.send(embed=dm)
        await asyncio.sleep(1)
        feedback = discord.Embed(
            title="Feedback",
            description="> Bitte bewerte dein Ticket.",
            color=get_config("Main")["Color"],
        )
        feedback.add_field(
            name="Positiv", value="> Reagiere mit 👍", inline=False)
        feedback.add_field(
            name="Negativ", value="> Reagiere mit 👎", inline=False)
        feedback.set_author(name=get_config("Texts")["Author"], icon_url=get_config("Images")["Author"])
        feedback.set_footer(text=get_config("Texts")["Footer"], icon_url=get_config("Images")["Footer"])
        feedback.set_thumbnail(url=get_config("Images")["Thumbnail"])
        await user.send(embed=feedback, view=FeedbackButtons())
        await asyncio.sleep(1)
        # await user.send(file=transcript_file)
        channel = client.get_channel(get_config("Ticketsystem")["Logs"])
        embed = discord.Embed(title="Ticket geschlossen!", color=get_config("Main")["Color"])
        embed.set_author(name=get_config("Texts")["Author"], icon_url=get_config("Images")["Author"])
        embed.set_footer(text=get_config("Texts")["Footer"], icon_url=get_config("Images")["Footer"])
        embed.set_thumbnail(url=get_config("Images")["Thumbnail"])
        embed.set_image(url=get_config("Ticketsystem")["Image"])
        embed.add_field(name="Ersteller:", value=f"> {user.mention}", inline=False)
        embed.add_field(
            name="Löschender:", value=f"> {interaction.user.mention}", inline=False
        )
        embed.add_field(
            name="Ticket:", value=f"> {interaction.channel.name}", inline=False
        )
        await channel.send(embed=embed)
        await asyncio.sleep(1)
        await channel.send(file=transcript_file2)

    @discord.ui.button(
        label="👤 User Hinzufügen", style=discord.ButtonStyle.green, custom_id="AddUser"
    )
    async def second_button_callback(self, button, interaction):
        team = interaction.guild.get_role(1309580249801166899)
        if team in interaction.user.roles:
            await interaction.response.send_modal(
                MemberPlusModal(title="User hinzufügen")
            )
        else:
            await interaction.respond(
                "> Sie haben keine Rechte dies zu tun!", ephemeral=True
            )

    @discord.ui.button(
        label="👤 User Entfernen",
        style=discord.ButtonStyle.green,
        custom_id="RemoveUser",
    )
    async def third_button_callback(self, button, interaction):
        team = interaction.guild.get_role(1309580249801166899)
        if team in interaction.user.roles:
            await interaction.response.send_modal(
                MemberMinusModal(title="User entfernen")
            )
        else:
            await interaction.respond(
                "> Sie haben keine Rechte dies zu tun!", ephemeral=True
            )


class MemberPlusModal(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.add_item(
            discord.ui.InputText(label="Member-ID", placeholder="825085110357327934")
        )

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = guild.get_member(int(self.children[0].value))
        await interaction.channel.set_permissions(
            member, view_channel=True, send_messages=True
        )
        embed = discord.Embed(
            title="\👤 User hinzugefügt!",
            description=f"> {member.mention} wurde zum Ticket hinzugefügt.",
            color=get_config("Main")["Color"],
        )
        await interaction.response.send_message(embed=embed)


class MemberMinusModal(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.add_item(
            discord.ui.InputText(label="Member-ID", placeholder="825085110357327934")
        )

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = guild.get_member(int(self.children[0].value))
        await interaction.channel.set_permissions(
            member, view_channel=False, send_messages=False
        )
        embed = discord.Embed(
            title="\👤 User entfernt!",
            description=f"> {member.mention} wurde aus dem Ticket entfernt.",
            color=get_config("Main")["Color"],
        )
        await interaction.response.send_message(embed=embed)

def debug(msg):
    print(Fore.RED + "[Debug]:" + Fore.RESET + f" {msg}" + Fore.RESET)

client.run(get_config("Main")["Token"])