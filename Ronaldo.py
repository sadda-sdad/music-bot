import discord

from discord.ext import commands

import yt_dlp

import asyncio

import os

import random

intents = discord.Intents.default()

intents.message_content = True

intents.voice_states = True

intents.guilds = True

# เปลี่ยน prefix เป็น R!

bot = commands.Bot(command_prefix="R!", intents=intents)

queue = {}  # คิวเพลง

loop_mode = {}  # ลูปเพลงปัจจุบัน

autoplay_mode = {}  # เล่นอัตโนมัติ

USER_AGENTS = [

    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",

    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",

    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",

]

class YTDLSource(discord.PCMVolumeTransformer):

    def __init__(self, source, *, data, volume=0.5):

        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')

        self.url = data.get('url')

    @classmethod

    async def from_url(cls, url, *, loop=None, stream=True):

        loop = loop or asyncio.get_event_loop()

        ydl_opts = {

            'format': 'bestaudio/best',

            'quiet': True,

            'no_warnings': True,

            'default_search': 'auto',

            'source_address': '0.0.0.0',

            'noplaylist': True,

            'nocheckcertificate': True,

            'user_agent': random.choice(USER_AGENTS),

            'referer': 'https://www.youtube.com/',

            'extractor_args': {'youtube': {'skip': ['dash', 'hls'], 'player_skip': ['js']}},

            'geo_bypass': True,

            'geo_bypass_country': 'US',

        }

        # แก้ FFmpeg options แล้ว (ไม่มี -re และ -fflags ที่ทำให้ error)

        before_options = '-nostdin -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 15 -timeout 30000000'

        ffmpeg_options = '-vn -bufsize 512M -analyzeduration 0 -probesize 64M -rw_timeout 60000000'

        for attempt in range(5):

            try:

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:

                    info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=not stream))

                    if 'entries' in info:

                        info = info['entries'][0]

                    filename = info['url'] if stream else ydl.prepare_filename(info)

                    return cls(

                        discord.FFmpegPCMAudio(filename, before_options=before_options, options=ffmpeg_options),

                        data=info

                    )

            except Exception as e:

                print(f"Attempt {attempt+1} failed: {e}")

                if attempt == 4:

                    raise Exception("ไม่สามารถดึงเพลงได้ ลองเพลงอื่นดูครับ")

                await asyncio.sleep(5)

async def play_next(guild_id):

    voice_client = discord.utils.get(bot.voice_clients, guild=bot.get_guild(guild_id))

    if not voice_client:

        return

    current_loop = loop_mode.get(guild_id, False)

    if current_loop and queue[guild_id]:

        queue[guild_id].append(queue[guild_id][-1])  # ลูปเพลงเดิม

    if queue[guild_id]:

        next_song = queue[guild_id].pop(0)

        try:

            player = await YTDLSource.from_url(next_song, loop=bot.loop, stream=True)

            voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(guild_id), bot.loop))

            channel = voice_client.guild.text_channels[0]

            await channel.send(f"🎵 กำลังเล่น: **{player.title}**")

        except Exception as e:

            print(f"Error in play_next: {e}")

    elif autoplay_mode.get(guild_id, False):

        try:

            player = await YTDLSource.from_url("ytsearch1:lofi hip hop radio beats to relax study to", loop=bot.loop, stream=True)

            voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(guild_id), bot.loop))

            channel = voice_client.guild.text_channels[0]

            await channel.send(f"🔄 Autoplay: **{player.title}**")

        except:

            pass

@bot.event

async def on_ready():

    print(f'บอทออนไลน์แล้ว: {bot.user}')

    print('พร้อมใช้งาน 24/7!')

@bot.command(name="คำสั่งทั้งหมด", aliases=["commands"])

async def help_command(ctx):

    embed = discord.Embed(title="📋 รายการคำสั่งของ Ronaldo Music", color=0x00ff00)

    embed.add_field(name="``R!join``", value="<:emoji_5:1449689928207175812> เข้าร่วมช่องเสียง", inline=False)

    embed.add_field(name="``R!leave``", value="<:emoji_5:1449689928207175812> ออกจากช่องเสียง", inline=False)

    embed.add_field(name="``R!play`` <ชื่อเพลง/URL>", value="<:emoji_5:1449689928207175812> เล่นเพลง ถ้าอยากเล่นเพลงต่อให้ใช้คำสั่งR!playนี้อีกครั้งบอทจะเพิ่มลงไปในคิวแล้วเมื่อเพลงจบจะต่อให้เองอัตโนมัติ", inline=False)

    embed.add_field(name="``R!pause``", value="<:emoji_5:1449689928207175812> หยุดชั่วคราว", inline=False)

    embed.add_field(name="``R!resume``", value="<:emoji_5:1449689928207175812> เล่นต่อ", inline=False)

    embed.add_field(name="``R!skip``", value="<:emoji_5:1449689928207175812> ข้ามเพลง", inline=False)

    embed.add_field(name="``R!queue``", value="<:emoji_5:1449689928207175812> ดูคิว", inline=False)

    embed.add_field(name="``R!loop``", value="<:emoji_5:1449689928207175812> เปิด/ปิดลูปเพลงปัจจุบัน", inline=False)

    embed.add_field(name="``R!autoplay``", value="<:emoji_5:1449689928207175812> เปิด/ปิดเล่นอัตโนมัติเมื่อคิวหมด", inline=False)

    embed.set_footer(text="Ronaldo Music พร้อมให้บริการฟรี")

    await ctx.send(embed=embed)

@bot.command()

async def join(ctx):

    if ctx.author.voice:

        channel = ctx.author.voice.channel

        await channel.connect()

        await ctx.send(f"🤖 เข้าร่วมช่องเสียง: **{channel}**")

    else:

        await ctx.send("❌ คุณต้องอยู่ในช่องเสียงก่อน!")

@bot.command()

async def leave(ctx):

    voice_client = ctx.guild.voice_client

    if voice_client:

        await voice_client.disconnect()

        queue.pop(ctx.guild.id, None)

        await ctx.send("👋 ออกจากช่องเสียงแล้ว")

    else:

        await ctx.send("❌ บอทไม่ได้อยู่ในช่องเสียง")

@bot.command()

async def play(ctx, *, query: str):

    if not ctx.guild.voice_client:

        await ctx.invoke(bot.get_command('join'))

    voice_client: discord.VoiceClient = ctx.guild.voice_client

    if ctx.guild.id not in queue:

        queue[ctx.guild.id] = []

    if voice_client.is_playing() or voice_client.is_paused():

        queue[ctx.guild.id].append(query)

        await ctx.send(f"➕ เพิ่มลงคิว: **{query}**")

        return

    await ctx.send("🔍 กำลังโหลดเพลง...")

    try:

        player = await YTDLSource.from_url(query, loop=bot.loop, stream=True)

        voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx.guild.id), bot.loop))

        await ctx.send(f"🎵 กำลังเล่น: **{player.title}**")

    except Exception as e:

        await ctx.send("❌ ไม่สามารถเล่นเพลงนี้ได้ ลองเพลงอื่นดูครับ")

        print(e)

@bot.command()

async def pause(ctx):

    voice = ctx.guild.voice_client

    if voice and voice.is_playing():

        voice.pause()

        await ctx.send("⏸ หยุดชั่วคราว")

@bot.command()

async def resume(ctx):

    voice = ctx.guild.voice_client

    if voice and voice.is_paused():

        voice.resume()

        await ctx.send("▶ เล่นต่อ")

@bot.command()

async def skip(ctx):

    voice = ctx.guild.voice_client

    if voice and (voice.is_playing() or voice.is_paused()):

        voice.stop()

        await ctx.send("⏭ ข้ามเพลง")

        await play_next(ctx.guild.id)

@bot.command(name="queue")

async def queue_list(ctx):

    if ctx.guild.id in queue and queue[ctx.guild.id]:

        q = "\n".join([f"{i+1}. {song}" for i, song in enumerate(queue[ctx.guild.id])])

        await ctx.send(f"📑 คิวเพลง:\n{q}")

    else:

        await ctx.send("📭 คิวว่างเปล่า")

@bot.command()

async def loop(ctx):

    guild_id = ctx.guild.id

    loop_mode[guild_id] = not loop_mode.get(guild_id, False)

    status = "เปิด" if loop_mode[guild_id] else "ปิด"

    await ctx.send(f"🔁 โหมดลูป: **{status}**")

@bot.command()

async def autoplay(ctx):

    guild_id = ctx.guild.id

    autoplay_mode[guild_id] = not autoplay_mode.get(guild_id, False)

    status = "เปิด" if autoplay_mode[guild_id] else "ปิด"

    await ctx.send(f"🔄 Autoplay: **{status}**")

# ใส่ Token บอทของคุณตรงนี้

bot.run("Token")