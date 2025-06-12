import discord
import datetime
import json
import os
import asyncio
import re
from discord.ext import commands
from discord import app_commands
from typing import Optional, Union, List
from pathlib import Path

class RegisterForm(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="ลงทะเบียนเข้าสู่ Dekเบียว")
        
        self.add_item(discord.ui.TextInput(
            label="ชื่อเล่น :",
            placeholder="กรุณากรอกชื่อเล่น [ภาษาอังกฤษเท่านั้น]",
            required=True,
            style=discord.TextStyle.short,
            max_length=100
        ))
        
        self.add_item(discord.ui.TextInput(
            label="กรอกอายุ :",
            placeholder="กรุณากรอกอายุ (ตัวเลขเท่านั้น)",
            required=True,
            style=discord.TextStyle.short,
            max_length=2
        ))
        
        self.add_item(discord.ui.TextInput(
            label="เพศ :",
            placeholder="กรุณากรอกเพศ (ชายหรือหญิง)",
            required=True,
            style=discord.TextStyle.short,
            max_length=5
        ))
        
        self.add_item(discord.ui.TextInput(
            label="ชอบเลขไร :",
            placeholder="กรุณากรอกเลข (ตัวเลขเท่านั้น)",
            required=True,
            style=discord.TextStyle.short,
            max_length=10
        ))
        
        self.add_item(discord.ui.TextInput(
            label="ชอบทำอะไร :",
            placeholder="ชอบทำอะไร",
            required=True,
            style=discord.TextStyle.short,
            max_length=100
        ))

    async def on_submit(self, interaction: discord.Interaction):
        full_name = self.children[0].value
        age = self.children[1].value
        gender = self.children[2].value
        phone_number = self.children[3].value
        weapon = self.children[4].value
        
        # ตรวจสอบชื่อ-นามสกุล (ภาษาอังกฤษเท่านั้น)
        if not re.match(r'^[a-zA-Z\s]*$', full_name):
            return await interaction.response.send_message("⚠️ กรุณากรอกชื่อ-นามสกุลเป็นภาษาอังกฤษเท่านั้น", ephemeral=False)
        
        # ตรวจสอบอายุ (ตัวเลขเท่านั้น)
        if not age.isdigit() or int(age) < 1 or int(age) > 99:
            return await interaction.response.send_message("⚠️ กรุณากรอกอายุเป็นตัวเลข 1-99 เท่านั้น", ephemeral=True)
        
        # ตรวจสอบเพศ (ชายหรือหญิง)
        if gender.lower() not in ["ชาย", "หญิง"]:
            return await interaction.response.send_message("⚠️ กรุณากรอกเพศเป็น 'ชาย' หรือ 'หญิง' เท่านั้น", ephemeral=True)
        
        # ตรวจสอบเบอร์โทร (ตัวเลขเท่านั้น)
        if not phone_number.isdigit() or len(phone_number) < 1 or len(phone_number) > 2:
            return await interaction.response.send_message("⚠️ กรุณากรอกเบอร์โทรเป็นตัวเลข 9-10 หลักเท่านั้น", ephemeral=True)
        
        await interaction.response.send_message("✅ ส่งข้อมูลเรียบร้อยแล้ว กรุณารอการตรวจสอบ", ephemeral=True)
        
        config = load_json("database/Config.json")
        
        if "Setup_slytherin_verify" not in config or "channel_id" not in config["Setup_slytherin_verify"]:
            return await interaction.followup.send("⚠️ ยังไม่ได้ตั้งค่าช่องทางสำหรับส่งข้อมูล", ephemeral=True)
        
        channel_id = int(config["Setup_slytherin_verify"]["channel_id"])
        channel = interaction.guild.get_channel(channel_id)
        
        if not channel:
            return await interaction.followup.send("⚠️ ไม่พบช่องทางสำหรับส่งข้อมูล", ephemeral=True)
        
        embed = discord.Embed(
            description=f"ผู้ใช้: {interaction.user.mention} ({interaction.user.id})",
            color=discord.Color.green()
        )
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        embed.add_field(name="👤 ชื่อเล่น", value=f"#️⃣  {full_name}", inline=False)
        embed.add_field(name="📑 อายุ", value=f"#️⃣  {age}", inline=False)
        embed.add_field(name="📑 เพศ", value=f"#️⃣  {gender}", inline=False)
        embed.add_field(name="📑 เลขที่ชอบ", value=f"#️⃣  {phone_number}", inline=False)
        embed.add_field(name="📑 ชอบทำไร", value=f"#️⃣  {weapon}", inline=False)
        embed.add_field(name="เวลาที่ส่ง", value=f"<t:{int(datetime.datetime.now().timestamp())}:F>", inline=False)
        embed.set_thumbnail(url=f"{interaction.user.display_avatar.url}")
        embed.set_footer(text=f"ID : {interaction.user.id}", icon_url="https://cdn.discordapp.com/attachments/1381964473103028309/1381969271562965022/images.png?ex=684972ae&is=6848212e&hm=164b6a5f4aaccff29c4964b6be62daf0c517719ae29b9c1ef93ab7f6740b7f9a&")
        
        verify_button = discord.ui.Button(
            label="ยืนยันเอกสาร", 
            emoji="✅", 
            style=discord.ButtonStyle.green,
            custom_id=f"verify_doc_{interaction.user.id}"
        )
        
        view = discord.ui.View()
        view.add_item(verify_button)
        
        message = await channel.send(embed=embed, view=view)
        
        current_time = datetime.datetime.now().strftime("%d/%m/%Y | เวลา %H:%M นาที %S วินาที")
        
        users_data = load_json("database/Users.json")
        
        if str(interaction.user.id) not in users_data:
            users_data[str(interaction.user.id)] = {
                "user_id": str(interaction.user.id),
                "send_info": "1",
                "verify_info": "0",
                "user_system": [
                    {
                        "send_info_user": {
                            "message_link_embed_info": f"https://discord.com/channels/{interaction.guild.id}/{channel.id}/{message.id}",
                            "time": current_time,
                            "send_info_point": "1",
                            "full_name": full_name,
                            "age": age,
                            "gender": gender,
                            "phone_number": phone_number,
                            "weapon": weapon
                        },
                        "verify_info_user": {
                            "give_role_id": "",
                            "verify_by_user_id": "",
                            "time": "",
                            "verify_info_point": "0"
                        }
                    }
                ]
            }
        else:
            users_data[str(interaction.user.id)]["send_info"] = "1"
            users_data[str(interaction.user.id)]["user_system"][0]["send_info_user"] = {
                "message_link_embed_info": f"https://discord.com/channels/{interaction.guild.id}/{channel.id}/{message.id}",
                "time": current_time,
                "send_info_point": "1",
                "full_name": full_name,
                "age": age,
                "gender": gender,
                "phone_number": phone_number,
                "weapon": weapon
            }
        
        save_json("database/Users.json", users_data)

class SlytherinBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(command_prefix="!", intents=intents)
        self.cooldowns = {}
        
    async def setup_hook(self):
        await self.create_directories_and_files()
        print(f"🟢 พร้อมใช้งานแล้ว | {datetime.datetime.now().strftime('%d/%m/%Y | เวลา %H:%M นาที %S วินาที')}")
        
    async def on_ready(self):
        try:
            print(f"🔄 กำลังซิงค์คำสั่ง...")
            await self.tree.sync()
            print(f"✅ ซิงค์คำสั่งเรียบร้อยแล้ว | {datetime.datetime.now().strftime('%d/%m/%Y | เวลา %H:%M นาที %S วินาที')}")
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในการซิงค์คำสั่ง: {e}")
        
        await self.display_bot_info()
        
    async def create_directories_and_files(self):
        os.makedirs("database", exist_ok=True)
        
        if not os.path.exists("database/Config.json"):
            default_config = {
                "token": "",
                "server_id": "",
                "user_id": [
                    "",
                    ""
                ],
                "role_id": [
                    "",
                    "",
                    "",
                    "",
                    "",
                    ""
                ],
                "Setup_slytherin_verify": {
                    "channel_id": "",
                    "give_role_id": ""
                }
            }
            save_json("database/Config.json", default_config)
            print("✅ สร้างไฟล์ Config.json เรียบร้อยแล้ว")
            
        if not os.path.exists("database/Users.json"):
            default_users = {}
            save_json("database/Users.json", default_users)
            print("✅ สร้างไฟล์ Users.json เรียบร้อยแล้ว")
            
        if not os.path.exists("database/Embed.json"):
            default_embed = {}
            save_json("database/Embed.json", default_embed)
            print("✅ สร้างไฟล์ Embed.json เรียบร้อยแล้ว")
    
    async def display_bot_info(self):
        config = load_json("database/Config.json")
        server_count = len(self.guilds)
        
        print("=" * 50)
        print(f"🟢 บอทพร้อมใช้งานแล้ว: {self.user.name} ({self.user.id})")
        print(f"🌐 เซิร์ฟเวอร์ทั้งหมด: {server_count}")
        
        if config.get("server_id"):
            guild = self.get_guild(int(config["server_id"]))
            if guild:
                print(f"🏰 เซิร์ฟเวอร์หลัก: {guild.name} ({guild.id})")
            else:
                print(f"⚠️ ไม่พบเซิร์ฟเวอร์หลักที่กำหนดใน Config")
        else:
            print(f"⚠️ ยังไม่ได้กำหนด server_id ใน Config.json")
            
        print("=" * 50)
        
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.component:
            custom_id = interaction.data.get("custom_id", "")
            
            user_id = interaction.user.id
            current_time = datetime.datetime.now().timestamp()
            
            if user_id in self.cooldowns:
                if current_time - self.cooldowns[user_id] < 2: 
                    await interaction.response.send_message("⚠️ กรุณารอสักครู่ก่อนใช้คำสั่งอีกครั้ง", ephemeral=True)
                    return
            
            self.cooldowns[user_id] = current_time
            
            if custom_id == "register_slytherin_home":
                await interaction.response.send_modal(RegisterForm())
                
            elif custom_id.startswith("verify_doc_"):
                target_user_id = custom_id.split("_")[-1]
                await self.verify_document(interaction, target_user_id)
                
        await self.process_app_commands(interaction)
                
    async def verify_document(self, interaction: discord.Interaction, target_user_id: str):
        config = load_json("database/Config.json")
        users_data = load_json("database/Users.json")
        
        has_permission = False
        
        if str(interaction.user.id) in config.get("user_id", []):
            has_permission = True
            
        user_roles = [str(role.id) for role in interaction.user.roles]
        for role_id in config.get("role_id", []):
            if role_id in user_roles:
                has_permission = True
                break
        
        if not has_permission:
            return await interaction.response.send_message(
                f"❌ คุณไม่ได้รับอนุญาตโดยรอดำเนินการจาก <@&{config['role_id'][0]}> นะครับ", 
                ephemeral=True
            )
        
        if target_user_id not in users_data:
            return await interaction.response.send_message(
                "❌ ไม่พบข้อมูลของผู้ใช้นี้", 
                ephemeral=True
            )
        
        if users_data[target_user_id]["verify_info"] == "1":
            verified_button = discord.ui.Button(
                label="ยืนยันเอกสารเรียบร้อยแล้ว", 
                emoji="✅", 
                style=discord.ButtonStyle.green,
                disabled=True
            )
            view = discord.ui.View()
            view.add_item(verified_button)
            
            await interaction.message.edit(view=view)
            return await interaction.response.send_message(
                "✅ ผู้ใช้นี้ได้รับการยืนยันเอกสารแล้ว", 
                ephemeral=True
            )
        
        role_id = config.get("Setup_slytherin_verify", {}).get("give_role_id", "")
        if not role_id:
            return await interaction.response.send_message(
                "❌ ยังไม่ได้กำหนดยศที่จะให้", 
                ephemeral=True
            )
        
        guild = interaction.guild
        member = guild.get_member(int(target_user_id))
        role = guild.get_role(int(role_id))
        
        if not member:
            return await interaction.response.send_message(
                "❌ ไม่พบผู้ใช้นี้ในเซิร์ฟเวอร์", 
                ephemeral=True
            )
        
        if not role:
            return await interaction.response.send_message(
                "❌ ไม่พบยศที่จะให้", 
                ephemeral=True
            )
        
        bot_member = guild.get_member(self.user.id)
        if not bot_member.guild_permissions.manage_roles or not bot_member.guild_permissions.manage_nicknames:
            return await interaction.response.send_message(
                "❌ โปรดทำการมอบสิทธิ์ให้บอทนั้นมีสิทธิ์ปรับแต่ง มอบยศ, ปรับแก้ไขชื่อด้วยครับ", 
                ephemeral=True
            )
        
        if bot_member.top_role <= role:
            return await interaction.response.send_message(
                "❌ โปรดทำการมอบสิทธิ์ให้บอทนั้นสูงกว่ายศที่จะให้ด้วยครับ", 
                ephemeral=True
            )
        
        form_data = interaction.message.embeds[0].fields
        ic_name = ""
        
        for field in form_data:
            if field.name == "👤 ชื่อ (IC)":
                ic_name = field.value
                break
        
        try:
            await member.add_roles(role)
            
            if ic_name:
                clean_ic_name = ic_name.replace("#️⃣  ", "").strip()
                
                if len(clean_ic_name) > 32:
                    clean_ic_name = clean_ic_name[:32] 
                
                try:
                    await member.edit(nick=clean_ic_name)
                except discord.Forbidden:
                    await interaction.response.send_message(
                        "✅ บอทได้มอบยศแล้ว แต่ไม่สามารถแก้ไขชื่อได้เนื่องจากสิทธิ์ไม่เพียงพอ",
                        ephemeral=True
                    )
                    return
            
            current_time = datetime.datetime.now().strftime("%d/%m/%Y | เวลา %H:%M นาที %S วินาที")
            
            users_data[target_user_id]["verify_info"] = "1"
            users_data[target_user_id]["user_system"][0]["verify_info_user"] = {
                "give_role_id": role_id,
                "verify_by_user_id": str(interaction.user.id),
                "time": current_time,
                "verify_info_point": "1"
            }
            
            save_json("database/Users.json", users_data)
            
            verified_button = discord.ui.Button(
                label="ยืนยันเอกสารเรียบร้อยแล้ว", 
                emoji="✅", 
                style=discord.ButtonStyle.green,
                disabled=True
            )
            view = discord.ui.View()
            view.add_item(verified_button)
            
            await interaction.message.edit(view=view)
            
            await interaction.response.send_message(
                "✅ บอทได้มอบยศและทำการปรับแต่งชื่อแล้วเรียบร้อย", 
                ephemeral=True
            )
            
            try:
                embed = discord.Embed(
                    description=f"ผู้ใช้: {member.mention}",
                    color=discord.Color.blue()
                )
                embed.add_field(name="รายละเอียดเอกสาร", value="✅ คุณได้รับการตรวจสอบเอกสารเรียบร้อยแล้ว", inline=False)
                embed.add_field(name="เวลา", value=f"<t:{int(datetime.datetime.now().timestamp())}:F>", inline=False)
                embed.set_footer(text=f"ID : {target_user_id}", icon_url="https://cdn.discordapp.com/attachments/1381964473103028309/1381969271562965022/images.png?ex=684972ae&is=6848212e&hm=164b6a5f4aaccff29c4964b6be62daf0c517719ae29b9c1ef93ab7f6740b7f9a&")
                
                await member.send(embed=embed)
            except discord.Forbidden:
                pass
            
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ บอทไม่มีสิทธิ์เพียงพอในการมอบยศ", 
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ เกิดข้อผิดพลาด: {str(e)}", 
                ephemeral=True
            )

    async def process_app_commands(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.application_command:
            return
        
    pass

bot = SlytherinBot()

@bot.tree.command(name="setup_slytherin_verify", description="คำสั่งนี้ไว้ใช้งานสำหรับการสร้างเมนูกรอกเข้าบ้าน")
async def setup_slytherin_verify(interaction: discord.Interaction):
    config = load_json("database/Config.json")
    has_permission = False
    
    if str(interaction.user.id) in config.get("user_id", []):
        has_permission = True
        
    user_roles = [str(role.id) for role in interaction.user.roles]
    for role_id in config.get("role_id", []):
        if role_id in user_roles:
            has_permission = True
            break
    
    if not has_permission:
        return await interaction.response.send_message(
            f"❌ คุณไม่ได้รับอนุญาตให้ใช้คำสั่งนี้", 
            ephemeral=True
        )
    
    await interaction.response.send_message("🔄 กำลังสร้างเมนูลงทะเบียน...", ephemeral=True)
    
    embed = discord.Embed(
        description="เมนูกรอกลงทะเบียนเข้าสู่เซิฟเวอร์ Dekเบียว ",
        color=discord.Color.green()
    )
    
    embed.add_field(
        name="เด็กๆ ที่เข้ามาใหม่รบกวนลงชื่อ",
        value="เพื่อรับยศด้วยนะครับ จะได้ไม่พลาดข่าวสารต่างๆ น๊าา",
        inline=False
    )
    
    embed.set_image(url="https://cdn.discordapp.com/attachments/1381964473103028309/1381969271562965022/images.png?ex=684972ae&is=6848212e&hm=164b6a5f4aaccff29c4964b6be62daf0c517719ae29b9c1ef93ab7f6740b7f9a&")
    embed.set_footer(text="By James Karlov Dek Dahood | 2025", icon_url="https://cdn.discordapp.com/attachments/1381964473103028309/1381969271562965022/images.png?ex=684972ae&is=6848212e&hm=164b6a5f4aaccff29c4964b6be62daf0c517719ae29b9c1ef93ab7f6740b7f9a&")
    
    register_button = discord.ui.Button(
        label="ลงทะเบียนเข้าสู่เซิฟเวอร์", 
        emoji="🟢", 
        style=discord.ButtonStyle.green,
        custom_id="register_slytherin_home"
    )
    
    view = discord.ui.View(timeout=None)
    view.add_item(register_button)
    
    message = await interaction.channel.send(embed=embed, view=view)
    
    embed_data = load_json("database/Embed.json")
    
    current_time = datetime.datetime.now().strftime("%d/%m/%Y | เวลา %H:%M นาที %S วินาที")
    
    embed_data["message_link_embed_Setup_slytherin_verify"] = {
        "message_link": f"https://discord.com/channels/{interaction.guild.id}/{interaction.channel.id}/{message.id}",
        "use_commands_by_user_id": str(interaction.user.id),
        "time": current_time
    }
    
    save_json("database/Embed.json", embed_data)
    
    await interaction.followup.send(
        f"✅ สร้างเมนูลงทะเบียนเรียบร้อยแล้ว", 
        ephemeral=True
    )

@bot.tree.command(name="setconfig", description="ตั้งค่าระบบ")
@app_commands.describe(
    role="ยศที่ต้องการเพิ่มให้ยืนยันเอกสารให้เด็กได้",
    user="คนที่ต้องการเพิ่มให้ยืนยันเอกสารให้เด็กได้",
    channel_id="ห้องที่จะแจ้งเอกสารเมื่อมีการกรอกเอกสาร",
    roleverify="เพิ่มยศที่จะยืนยันเมื่อทำการกดยืนยันเอกสาร จะเพิ่มโดยไปทับกับตัวเก่านะครับ"
)
async def setconfig(
    interaction: discord.Interaction, 
    role: Optional[discord.Role] = None,
    user: Optional[discord.Member] = None,
    channel_id: Optional[discord.TextChannel] = None,
    roleverify: Optional[discord.Role] = None
):
    config = load_json("database/Config.json")
    has_permission = False
    
    if str(interaction.user.id) in config.get("user_id", []):
        has_permission = True
        
    user_roles = [str(role_id) for role_id in [r.id for r in interaction.user.roles]]
    for role_id in config.get("role_id", []):
        if role_id in user_roles:
            has_permission = True
            break
    
    if not has_permission:
        return await interaction.response.send_message(
            f"❌ คุณไม่ได้รับอนุญาตให้ใช้คำสั่งนี้", 
            ephemeral=True
        )
    
    if not any([role, user, channel_id, roleverify]):
        return await interaction.response.send_message(
            "⚠️ กรุณาระบุอย่างน้อยหนึ่งตัวเลือก", 
            ephemeral=True
        )
    
    if role:
        if str(role.id) not in config.get("role_id", []):
            config.setdefault("role_id", []).append(str(role.id))
            save_json("database/Config.json", config)
            await interaction.response.send_message(
                f"✅ เพิ่มยศ {role.mention} เป็นผู้ยืนยันเอกสารเรียบร้อยแล้ว", 
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"⚠️ ยศ {role.mention} เป็นผู้ยืนยันเอกสารอยู่แล้ว", 
                ephemeral=True
            )
        return
    
    if user:
        if str(user.id) not in config.get("user_id", []):
            config.setdefault("user_id", []).append(str(user.id))
            save_json("database/Config.json", config)
            await interaction.response.send_message(
                f"✅ เพิ่ม {user.mention} เป็นผู้ยืนยันเอกสารเรียบร้อยแล้ว", 
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"⚠️ {user.mention} เป็นผู้ยืนยันเอกสารอยู่แล้ว", 
                ephemeral=True
            )
        return
    
    if channel_id:
        config.setdefault("Setup_slytherin_verify", {})["channel_id"] = str(channel_id.id)
        save_json("database/Config.json", config)
        await interaction.response.send_message(
            f"✅ ตั้งค่าห้อง {channel_id.mention} เป็นห้องแจ้งเตือนการกรอกเอกสารเรียบร้อยแล้ว", 
            ephemeral=True
        )
        return
    
    if roleverify:
        config.setdefault("Setup_slytherin_verify", {})["give_role_id"] = str(roleverify.id)
        save_json("database/Config.json", config)
        await interaction.response.send_message(
            f"✅ ตั้งค่ายศ {roleverify.mention} เป็นยศที่จะให้เมื่อยืนยันเอกสารเรียบร้อยแล้ว", 
            ephemeral=True
        )
        return

@bot.tree.command(name="info", description="เช็คข้อมูลการกรอกเอกสาร")
@app_commands.describe(
    userdele="คนที่ต้องการที่จะลบประวัติการกรอกที่เคยกรอกมา",
    usercheck="คนที่ต้องการเช่นว่าเคยได้ทำการกรอกมาแล้วหรือป่าวหรือยังไม่ได้กรอก"
)
async def info(
    interaction: discord.Interaction, 
    userdele: Optional[discord.Member] = None,
    usercheck: Optional[discord.Member] = None
):
    config = load_json("database/Config.json")
    has_permission = False
    
    if str(interaction.user.id) in config.get("user_id", []):
        has_permission = True
        
    user_roles = [str(role_id) for role_id in [r.id for r in interaction.user.roles]]
    for role_id in config.get("role_id", []):
        if role_id in user_roles:
            has_permission = True
            break
    
    if not has_permission:
        return await interaction.response.send_message(
            f"❌ คุณไม่ได้รับอนุญาตให้ใช้คำสั่งนี้", 
            ephemeral=True
        )
    
    if not any([userdele, usercheck]):
        return await interaction.response.send_message(
            "⚠️ กรุณาระบุอย่างน้อยหนึ่งตัวเลือก", 
            ephemeral=True
        )
    
    users_data = load_json("database/Users.json")
    
    if userdele:
        if str(userdele.id) in users_data:
            del users_data[str(userdele.id)]
            save_json("database/Users.json", users_data)
            await interaction.response.send_message(
                f"✅ ลบข้อมูลของ {userdele.mention} เรียบร้อยแล้ว", 
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"⚠️ ไม่พบข้อมูลของ {userdele.mention} ในระบบ", 
                ephemeral=True
            )
        return
    
    if usercheck:
        if str(usercheck.id) in users_data:
            user_info = users_data[str(usercheck.id)]
            
            embed = discord.Embed(
                title=f"ข้อมูลของ {usercheck.display_name}",
                color=discord.Color.blue()
            )
            
            if user_info.get("send_info") == "1":
                embed.add_field(
                    name="✅ การส่งข้อมูล",
                    value="ส่งข้อมูลแล้ว",
                    inline=False
                )
                
                if "user_system" in user_info and user_info["user_system"]:
                    send_info = user_info["user_system"][0].get("send_info_user", {})
                    embed.add_field(
                        name="เวลาที่ส่ง",
                        value=send_info.get("time", "ไม่พบข้อมูล"),
                        inline=True
                    )
                    
                    message_link = send_info.get("message_link_embed_info", "")
                    if message_link:
                        embed.add_field(
                            name="ลิงก์ข้อความ",
                            value=f"[คลิกที่นี่]({message_link})",
                            inline=True
                        )
            else:
                embed.add_field(
                    name="❌ การส่งข้อมูล",
                    value="ยังไม่ได้ส่งข้อมูล",
                    inline=False
                )
            
            if user_info.get("verify_info") == "1":
                embed.add_field(
                    name="✅ การยืนยัน",
                    value="ยืนยันแล้ว",
                    inline=False
                )
                
                if "user_system" in user_info and user_info["user_system"]:
                    verify_info = user_info["user_system"][0].get("verify_info_user", {})
                    
                    verify_by = verify_info.get("verify_by_user_id", "")
                    if verify_by:
                        embed.add_field(
                            name="ยืนยันโดย",
                            value=f"<@{verify_by}>",
                            inline=True
                        )
                    
                    embed.add_field(
                        name="เวลาที่ยืนยัน",
                        value=verify_info.get("time", "ไม่พบข้อมูล"),
                        inline=True
                    )
                    
                    role_id = verify_info.get("give_role_id", "")
                    if role_id:
                        embed.add_field(
                            name="ยศที่ได้รับ",
                            value=f"<@&{role_id}>",
                            inline=True
                        )
            else:
                embed.add_field(
                    name="❌ การยืนยัน",
                    value="ยังไม่ได้รับการยืนยัน",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(
                f"⚠️ ไม่พบข้อมูลของ {usercheck.mention} ในระบบ", 
                ephemeral=True
            )
        return

def load_json(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_json(filename, data):
    directory = os.path.dirname(filename)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
        
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    if not os.path.exists("database/Config.json"):
        print("❌ ไม่พบไฟล์ Config.json กำลังสร้างไฟล์...")
        os.makedirs("database", exist_ok=True)
        
        default_config = {
            "token": "",
            "server_id": "",
            "user_id": [
                "",
                ""
            ],
            "role_id": [
                "",
                "",
                "",
                "",
                "",
                ""
            ],
            "Setup_slytherin_verify": {
                "channel_id": "",
                "give_role_id": ""
            }
        }
        
        save_json("database/Config.json", default_config)
        print("✅ สร้างไฟล์ Config.json เรียบร้อยแล้ว")
        print("ℹ️ กรุณาตั้งค่า token ในไฟล์ Config.json ก่อนรันโปรแกรมอีกครั้ง")
        return

    config = load_json("database/Config.json")
    token = config.get("token", "")
    
    if not token:
        print("❌ ไม่พบ Token ในไฟล์ Config.json")
        print("ℹ️ กรุณาตั้งค่า token ในไฟล์ Config.json ก่อนรันโปรแกรมอีกครั้ง")
        return
    
    print("🔄 กำลังเริ่มต้นบอท...")
    bot.run(token)

if __name__ == "__main__":
    main()