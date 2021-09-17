
'''
Discord Music bot - Zing MP3
version:    1.0.1
author:     Bao LT
website:    luthebao.com
'''

import discord, requests
from discord.ext import commands


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.executable = 'C:/ffmpeg/bin/ffmpeg.exe'
        self.is_playing = False
        self.music_queue = []
        self.loop = False
        self.indexing = 0
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
        self.vc = ""
    
    def search_zmp3(self, item, index=0):
        with requests.Session() as ss :
            try: 
                if "http" in item:
                    name = item
                    id = (item.split("/"))[-1].split(".htm")[0]
                    artist = "default"
                    thumb = "https://cdn.discordapp.com/avatars/850416535583719485/a7f70c1b32e1d91ea44e7ea8ef700b57.png"
                else:
                    info = ss.get(f"http://ac.mp3.zing.vn/complete?type=artist,song,key,code&num=5&query={item}")
                    
                    name = info.json()["data"][0]["song"][index]["name"]
                    id = info.json()["data"][0]["song"][index]["id"]
                    artist = info.json()["data"][0]["song"][index]["artist"]
                    thumb = "https://photo-resize-zmp3.zadn.vn/w240_r1x1_jpeg/"+info.json()["data"][0]["song"][index]["thumb"]

            except Exception: 
                return False

        return {
            'source': f"http://api.mp3.zing.vn/api/streaming/audio/{id}/128", 
            'title': name,
            "artist": artist,
            "thumb": thumb
        }

    async def play_next(self, ctx):
        if len(self.music_queue) > 0:
            self.is_playing = True

            if self.loop:
                if self.indexing <= len(self.music_queue):
                    self.indexing = 0
                else:
                    self.indexing += 1
                m_url = self.music_queue[self.indexing][0]['source']
                await ctx.send(content=f"Playing {self.music_queue[self.indexing][0]['title']} by {self.music_queue[self.indexing][0]['artist']}", embed=discord.Embed().set_image(url=self.music_queue[self.indexing][0]['thumb']))
            else:
                m_url = self.music_queue[0][0]['source']
                await ctx.send(content=f"Playing {self.music_queue[0][0]['title']} by {self.music_queue[0][0]['artist']}", embed=discord.Embed().set_image(url=self.music_queue[0][0]['thumb']))
                self.music_queue.pop(0)

            self.vc.play(discord.FFmpegPCMAudio(executable=self.executable, source=m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.bot.loop.create_task(self.play_next(ctx)))
        else:
            self.is_playing = False
            await ctx.send("Queue stopped ...")

    # infinite loop checking 
    async def play_music(self, ctx):
        if len(self.music_queue) > 0:
            self.is_playing = True

            m_url = self.music_queue[0][0]['source']
            await ctx.send(content=f"Playing {self.music_queue[0][0]['title']} by {self.music_queue[0][0]['artist']}", embed=discord.Embed().set_image(url=self.music_queue[0][0]['thumb']))

            if self.vc == "" or not self.vc.is_connected() or self.vc == None:
                self.vc = await self.music_queue[0][1].connect()
            else:
                await self.vc.move_to(self.music_queue[0][1])
            
            #remove the first element as you are currently playing it
            self.music_queue.pop(0)

            self.vc.play(discord.FFmpegPCMAudio(executable=self.executable, source=m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.bot.loop.create_task(self.play_next(ctx)))
        else:
            self.is_playing = False
            await ctx.send(content="Queue stopped...")

    @commands.command(name="play", help="Plays a selected song from ZingMp3")
    async def p(self, ctx, *args):
        query = " ".join(args)
        
        voice_channel = ctx.author.voice.channel
        
        if voice_channel is None:
            #you need to be connected so that the bot knows where to go
            await ctx.send("You are not in a voice chanel !")
        else:
            if len(ctx.bot.voice_clients) > 0 and ctx.bot.voice_clients[0].channel != voice_channel:
                await ctx.send("I'm in other channel !")
                return
            try:
                index = int(args[-1])
            except:
                index = 0
            song = self.search_zmp3(query, index)
            if type(song) == type(True):
                await ctx.send("Could not download the song. Incorrect format try another keyword. This could be due to playlist or a livestream format.")
            else:
                await ctx.send(content="`Song added to the queue: " + song["title"] + " by " + song['artist'] + ".`", embed=discord.Embed().set_image(url=song['thumb']))
                self.music_queue.append([song, voice_channel])
                
                if self.is_playing == False:
                    await self.play_music(ctx)

    @commands.command(name="queue", help="Displays the current songs in queue")
    async def q(self, ctx):
        if len(self.music_queue) > 0:
            retval = "`"
            for i in range(0, len(self.music_queue)):
                retval += str(i+1) + ". "+ self.music_queue[i][0]['title'] + f" by {self.music_queue[i][0]['artist']}\n"
            retval += "`"
            await ctx.send(retval)
        else:
            await ctx.send("No song in queue")

    @commands.command(name="skip", help="Skips the current song being played")
    async def skip(self, ctx):
        if self.vc != "" and self.vc:
            self.vc.stop()

    @commands.command(name = "leave", help="leave...")
    async def leave(self, ctx):
        if self.vc != "" and self.vc:
            self.vc.stop()
        if (ctx.voice_client):
            await ctx.guild.voice_client.disconnect()
            await ctx.send('Bot left')
        else:
            await ctx.send("I'm not in a voice channel, use the join command to make me join")

    @commands.command(name="remove", help="Remove song from queue")
    async def remove(self, ctx, *args):
        try:
            index = int(args[-1])
        except:
            index = 0
        if (ctx.voice_client):
            if len(self.music_queue) > 0 and index <= len(self.music_queue):
                self.music_queue.pop(index-1)
                await self.q(ctx)
            else:
                await ctx.send(content="No song in queue...")
        else:
            await ctx.send("I'm not in a voice channel, use the join command to make me join")

bot = commands.Bot(command_prefix='c!')
bot.add_cog(Music(bot))
print("=== START BOT ===")
bot.run("TOKEN")