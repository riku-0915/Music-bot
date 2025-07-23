import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os 

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

music_queue = []
is_playing = False

@bot.event
async def on_ready():
    print(f'ログインしました: {bot.user}')

def get_audio_url(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'extract_flat': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'entries' in info:
                if info['entries']:
                    first_entry = info['entries'][0]
                    return first_entry['url'], first_entry.get('title', '不明なタイトル')
                else:
                    return None, None
            else:
                return info['url'], info.get('title', '不明なタイトル')
    except Exception as e:
        print(f"URL取得エラー: {e}")
        return None, None

async def play_music(ctx):
    global is_playing

    if music_queue and ctx.voice_client:
        is_playing = True
        url, title = music_queue.pop(0)
        try:
            ctx.voice_client.play(
                discord.FFmpegPCMAudio(url),
                after=lambda e: asyncio.run_coroutine_threadsafe(play_music(ctx), bot.loop)
            )
            await ctx.send(f" 再生中: {title}")
        except Exception as e:
            await ctx.send(f"❌ 再生中にエラーが発生しました: {title} ({e})")
            print(f"再生エラー: {title} - {e}")
            asyncio.run_coroutine_threadsafe(play_music(ctx), bot.loop)
    else:
        is_playing = False
        if ctx.voice_client and not music_queue:
            await ctx.send("🎶 キューの再生が終了しました")

@bot.command()
async def join(ctx):
    if ctx.author.voice:
        if ctx.voice_client:
            await ctx.send("既にVCに参加しています")
            return
        await ctx.author.voice.channel.connect()
        await ctx.send("VCに参加しました")
    else:
        await ctx.send("先にVCに参加してください")

@bot.command()
async def play(ctx, url: str):
    global is_playing

    if not ctx.voice_client:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
            await ctx.send("VCに参加しました")
        else:
            await ctx.send("先にVCに参加してから`!play <URL>`コマンドを実行してください")
            return

    audio_url, title = get_audio_url(url)
    if not audio_url: # URL取得に失敗した場合
        await ctx.send("無効なURL 音源情報の取得に失敗しました。URLを確認してください")
        return

    music_queue.append((audio_url, title))
    await ctx.send(f"✅ キューに追加: {title}")

    if not is_playing:
        await play_music(ctx)

@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭ スキップしました")
    else:
        await ctx.send("再生中の曲がありません")

@bot.command()
async def stop(ctx):
    global music_queue, is_playing
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        is_playing = False
    music_queue.clear()
    await ctx.send("🛑 再生を停止し、キューをクリアしました")

@bot.command()
async def leave(ctx):
    global music_queue, is_playing
    music_queue.clear()
    is_playing = False
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 ボイスチャンネルから切断しました")
    else:
        await ctx.send("VCに参加していません")

@bot.command()
async def queue(ctx):
    if music_queue:
        queue_list = '\n'.join(f"{i+1}. {title}" for i, (_, title) in enumerate(music_queue))
        await ctx.send(f"📃 キュー:\n{queue_list}")
    else:
        await ctx.send("🎶 キューは空です")

# Discord Botトークンを環境変数から取得するように変更
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if DISCORD_BOT_TOKEN is None:
    print("エラー: Discord ボットトークンが設定されていません。環境変数 'DISCORD_BOT_TOKEN' を設定してください。")
    exit(1)

bot.run(DISCORD_BOT_TOKEN)
