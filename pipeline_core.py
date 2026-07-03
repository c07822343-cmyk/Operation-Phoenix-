import os
import time
import json
import random
import requests
import subprocess
import threading
import shutil
import asyncio
import urllib.parse
from datetime import datetime, timedelta
from config import (
    GROQ_MODEL, GROQ_MIN_GAP, GROQ_MAX_RETRIES,
    VIDEO_WIDTH, VIDEO_HEIGHT, FPS,
    VIDEO_BITRATE, AUDIO_BITRATE,
    TTS_VOICE, TTS_RATE, TTS_PITCH,
    SUBTITLE_FONTSIZE, SUBTITLE_HIGHLIGHT_SIZE,
    SUBTITLE_COLOR, SUBTITLE_HIGHLIGHT_COLOR,
    SUBTITLE_POSITION, SUBTITLE_BORDERW,
    WORDS_PER_SUBTITLE, OUTPUT_DIR, TEMP_DIR,
    BLACKLISTED_FACTS, HUMAN_UPLOAD_HOURS
)


class PhoenixPipeline:

    def __init__(self, groq_key, pexels_key,
                 pixabay_key, niche, tone,
                 audience, reference_urls,
                 style_types, enable_evasion):
        self.groq_key = groq_key
        self.pexels_key = pexels_key
        self.pixabay_key = pixabay_key
        self.niche = niche or "random mind-blowing facts"
        self.tone = tone or "shocking and dramatic"
        self.audience = audience or "everyone"
        self.reference_urls = reference_urls or []
        self.style_types = style_types or []
        self.enable_evasion = enable_evasion
        self.style_guide = None
        self.schedule_path = None
        self._groq_last_call = 0
        self._groq_lock = threading.Lock()
        self.batch_id = (
            f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        self.progress = {
            "running": False,
            "phase": 0,
            "phase_name": "",
            "current_video": 0,
            "total_videos": 0,
            "percent": 0,
            "videos": [],
            "done": False,
            "error": "",
            "start_time": 0,
            "eta_seconds": 0,
            "successful": 0,
            "failed": 0,
            "batch_id": self.batch_id
        }
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        os.makedirs(TEMP_DIR, exist_ok=True)

    def _set_phase(self, num, name):
        self.progress["phase"] = num
        self.progress["phase_name"] = name
        print(f"[Phoenix] Phase {num}: {name}")

    def _update_eta(self, index, total):
        if index == 0:
            return
        elapsed = time.time() - self.progress["start_time"]
        per_video = elapsed / index
        remaining = (total - index) * per_video
        self.progress["eta_seconds"] = int(remaining)
        self.progress["percent"] = int((index / total) * 90)

    def _safe_exists(self, path):
        return (
            path is not None
            and isinstance(path, str)
            and os.path.exists(path)
            and os.path.getsize(path) > 100
        )

    def _call_groq(self, system_prompt, user_prompt,
                   temperature=0.9, max_tokens=2048):
        for attempt in range(GROQ_MAX_RETRIES):
            with self._groq_lock:
                gap = time.time() - self._groq_last_call
                if gap < GROQ_MIN_GAP:
                    time.sleep(GROQ_MIN_GAP - gap)
                try:
                    resp = requests.post(
                        "https://api.groq.com/openai/v1/"
                        "chat/completions",
                        headers={
                            "Authorization":
                                f"Bearer {self.groq_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "llama-3.3-70b-versatile",
                            "messages": [
                                {
                                    "role": "system",
                                    "content": system_prompt
                                },
                                {
                                    "role": "user",
                                    "content": user_prompt
                                }
                            ],
                            "temperature": temperature,
                            "max_tokens": max_tokens
                        },
                        timeout=45
                    )
                    self._groq_last_call = time.time()
                    if resp.status_code == 200:
                        return (
                            resp.json()
                            ["choices"][0]
                            ["message"]["content"]
                        )
                    elif resp.status_code == 429:
                        wait = (attempt + 1) * 20
                        print(f"[Groq] Rate limited. Waiting {wait}s")
                        time.sleep(wait)
                    elif resp.status_code == 401:
                        print("[Groq] Invalid API key")
                        return None
                    else:
                        print(f"[Groq] Error {resp.status_code}")
                        time.sleep(10)
                except requests.exceptions.Timeout:
                    print(f"[Groq] Timeout attempt {attempt + 1}")
                    time.sleep(15)
                except Exception as e:
                    print(f"[Groq] Exception: {e}")
                    time.sleep(10)
        return None

    def _parse_json(self, text):
        if not text:
            return None
        try:
            s = text.find('[')
            o = text.find('{')
            if s == -1 or (o != -1 and o < s):
                s = o
                e = text.rfind('}') + 1
            else:
                e = text.rfind(']') + 1
            if s == -1 or e == 0:
                return None
            return json.loads(text[s:e])
        except Exception as ex:
            print(f"[JSON] Parse error: {ex}")
            return None

    def _run_ffmpeg(self, cmd, timeout=120):
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=timeout
            )
            if result.returncode != 0:
                err = result.stderr.decode(
                    errors='ignore'
                )[:200]
                print(f"[FFmpeg] Error: {err}")
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            print(f"[FFmpeg] Timeout after {timeout}s")
            return False
        except Exception as e:
            print(f"[FFmpeg] Exception: {e}")
            return False

    def _get_duration(self, path):
        try:
            r = subprocess.run(
                [
                    'ffprobe', '-v', 'quiet',
                    '-show_entries', 'format=duration',
                    '-of', 'csv=p=0', path
                ],
                capture_output=True,
                text=True,
                timeout=10
            )
            return float(r.stdout.strip())
        except Exception:
            return 40.0

    def _colored_bg(self, duration, out, text=""):
        colors = [
            "0x1a1a2e", "0x0f3460", "0x16213e",
            "0x2d132c", "0x1b1b2f", "0x162447"
        ]
        bg = random.choice(colors)
        safe = (
            text.replace("'", "")
                .replace('"', '')
                .replace(':', '')[:25]
        )
        vf = (
            f"drawtext=text='{safe}':"
            f"fontcolor=white:fontsize=80:"
            f"x=(w-text_w)/2:y=(h-text_h)/2:"
            f"borderw=4:bordercolor=black"
            if safe else "null"
        )
        return self._run_ffmpeg([
            'ffmpeg', '-y', '-f', 'lavfi',
            '-i', (
                f'color=c={bg}:'
                f's={VIDEO_WIDTH}x{VIDEO_HEIGHT}:'
                f'd={duration}:r={FPS}'
            ),
            '-vf', vf,
            '-c:v', 'libx264', '-preset', 'fast',
            '-pix_fmt', 'yuv420p', out
        ], timeout=30)

    def _silent_audio(self, duration, out):
        self._run_ffmpeg([
            'ffmpeg', '-y', '-f', 'lavfi',
            '-i', 'anullsrc=r=48000:cl=stereo',
            '-t', str(duration),
            '-c:a', 'aac', out
        ], timeout=20)
        return out

    def _pillow_thumbnail(self, topic, out):
        try:
            from PIL import Image, ImageDraw
            schemes = [
                [(26, 26, 46), (233, 69, 96)],
                [(15, 15, 35), (100, 20, 120)],
                [(10, 25, 47), (0, 150, 136)],
                [(40, 0, 0), (200, 30, 30)],
                [(0, 20, 50), (0, 120, 200)]
            ]
            c = random.choice(schemes)
            img = Image.new('RGB', (1280, 720), c[0])
            draw = ImageDraw.Draw(img)
            for y in range(720):
                r2 = y / 720
                px = tuple(
                    max(0, min(255,
                        int(c[0][i] + (c[1][i] - c[0][i]) * r2)
                    ))
                    for i in range(3)
                )
                draw.line([(0, y), (1280, y)], fill=px)
            t = topic.upper()[:35]
            for dx in range(-3, 4):
                for dy in range(-3, 4):
                    draw.text(
                        (104 + dx, 304 + dy),
                        t, fill=(0, 0, 0)
                    )
            draw.text((104, 304), t, fill=(255, 255, 255))
            os.makedirs(
                os.path.dirname(out)
                if os.path.dirname(out) else '.',
                exist_ok=True
            )
            img.save(out, 'PNG')
            return out
        except Exception as e:
            print(f"[Pillow] Error: {e}")
            return None

    def _analyze_style(self):
        titles = []
        channels = []
        for url in self.reference_urls:
            url = url.strip()
            if not url:
                continue
            try:
                if 'watch?v=' in url:
                    vid = url.split('watch?v=')[1].split('&')[0]
                    r = requests.get(
                        f"https://www.youtube.com/oembed"
                        f"?url=https://www.youtube.com/"
                        f"watch?v={vid}&format=json",
                        timeout=10
                    )
                    if r.status_code == 200:
                        d = r.json()
                        titles.append(d.get('title', ''))
                        channels.append(
                            d.get('author_name', '')
                        )
                elif '@' in url or '/channel/' in url:
                    channels.append(
                        url.rstrip('/').split('/')[-1]
                    )
            except Exception as e:
                print(f"[Style] URL error: {e}")
            time.sleep(0.2)

        sys_p = (
            "You are a YouTube Shorts content strategist. "
            "Analyze references and create a detailed "
            "style guide. Return only valid JSON."
        )
        usr_p = (
            f"Niche: {self.niche}\n"
            f"Tone: {self.tone}\n"
            f"Audience: {self.audience}\n"
            f"Channels: {', '.join(channels) or 'none'}\n"
            f"Titles: {', '.join(titles) or 'none'}\n\n"
            f"Return JSON with these exact keys:\n"
            f"hook_style, pacing, "
            f"tone_words (array of 5),\n"
            f"typical_structure, "
            f"language_patterns (array of 5),\n"
            f"topics_covered (array of 10 topic ideas),\n"
            f"what_makes_viral, content_guidelines,\n"
            f"avoid_these (array of 5),\n"
            f"example_hooks (array of 5 opening lines)"
        )
        result = self._parse_json(
            self._call_groq(sys_p, usr_p, temperature=0.7)
        )
        return result if result else self._default_style()

    def _default_style(self):
        sys_p = (
            "YouTube Shorts content expert. "
            "Create a viral content style guide. "
            "Return only valid JSON."
        )
        usr_p = (
            f"Create style guide for: {self.niche}\n"
            f"Tone: {self.tone}\n"
            f"Audience: {self.audience}\n"
            f"Return JSON with: hook_style, pacing,\n"
            f"tone_words, typical_structure,\n"
            f"language_patterns, topics_covered,\n"
            f"what_makes_viral, content_guidelines,\n"
            f"avoid_these, example_hooks"
        )
        result = self._parse_json(
            self._call_groq(sys_p, usr_p, temperature=0.8)
        )
        if result:
            return result
        return {
            "hook_style": "Start with the shocking claim directly",
            "pacing": "Fast paced short punchy sentences",
            "tone_words": [
                "shocking", "direct", "urgent", "real", "raw"
            ],
            "typical_structure": "Hook then context then payoff",
            "language_patterns": [
                "And it gets worse",
                "Here is the part nobody talks about",
                "Wait until you hear this",
                "This is where it gets insane",
                "Nobody knows this"
            ],
            "topics_covered": [self.niche] * 10,
            "what_makes_viral": "Shock value plus truth",
            "content_guidelines": "Direct fast and shocking",
            "avoid_these": [
                "Did you know", "Fun fact",
                "Hey guys", "Buckle up",
                "Like and subscribe"
            ],
            "example_hooks": [
                f"This {self.niche} fact ruins your day.",
                f"Nobody talks about this {self.niche} secret.",
                f"The truth about {self.niche} is disturbing.",
                f"What they never told you about {self.niche}.",
                f"This changed everything about {self.niche}."
            ]
        }

    def _generate_ideas(self, count):
        sg = self.style_guide or {}
        avoid = sg.get('avoid_these', [])
        examples = sg.get('example_hooks', [])
        topics = sg.get('topics_covered', [])
        guidelines = sg.get('content_guidelines', '')
        archetypes = (
            ', '.join(self.style_types)
            if self.style_types else (
                "single shocking fact, "
                "comparison that breaks your brain, "
                "common misconception corrected, "
                "timeline collapse same era different worlds, "
                "biological body horror fact, "
                "fact that sounds fake but is real"
            )
        )
        blacklist = ', '.join(BLACKLISTED_FACTS)
        sys_p = (
            f"You generate viral YouTube Shorts ideas.\n"
            f"Niche: {self.niche}\n"
            f"Tone: {self.tone}\n"
            f"Audience: {self.audience}\n"
            f"Guidelines: {guidelines}\n"
            f"Never say: {', '.join(avoid)}\n"
            f"Example hooks: {', '.join(examples[:3])}\n"
            f"BLACKLISTED never allowed: {blacklist}\n"
            f"Every idea must be 100 percent true.\n"
            f"Every idea must be shocking and visual.\n"
            f"Return only valid JSON array. No other text."
        )
        usr_p = (
            f"Generate exactly {count} unique viral ideas\n"
            f"for a {self.niche} YouTube Shorts channel.\n"
            f"Audience: {self.audience}\n"
            f"Use formats: {archetypes}\n"
            f"Topics: {', '.join(topics[:5]) or self.niche}\n\n"
            f"Each item must have exactly:\n"
            f"topic (3-6 words),\n"
            f"category (animal/history/science/body/space/"
            f"food/technology/psychology/geography/"
            f"culture/crime/facts),\n"
            f"core_fact (one shocking verifiable sentence),\n"
            f"archetype (the format name),\n"
            f"shock_factor (number 1-10),\n"
            f"visual_potential (footage description),\n"
            f"target_emotion (awe/disgust/surprise/"
            f"curiosity/fear/wonder)"
        )
        raw = self._call_groq(
            sys_p, usr_p,
            temperature=0.95, max_tokens=6000
        )
        result = self._parse_json(raw)
        if not isinstance(result, list):
            return []
        return [
            idea for idea in result
            if not any(
                bl in idea.get('core_fact', '').lower()
                for bl in BLACKLISTED_FACTS
            )
        ]

    def _write_script(self, idea):
        sg = self.style_guide or {}
        sys_p = (
            f"You write viral YouTube Shorts scripts.\n"
            f"Niche: {self.niche} Tone: {self.tone}\n"
            f"Hook: {sg.get('hook_style', 'Shocking claim')}\n"
            f"Use: {', '.join(sg.get('language_patterns', []))}\n"
            f"Avoid: {', '.join(sg.get('avoid_these', []))}\n"
            f"Examples: "
            f"{', '.join(sg.get('example_hooks', [])[:2])}\n"
            f"0-3s HOOK: Shocking claim open loop\n"
            f"3-8s CONTEXT: Why more shocking\n"
            f"8-15s ESCALATION: Stack details\n"
            f"15s+ PAYOFF: Biggest shock haunting kicker\n"
            f"Short sentences. 80-180 words total.\n"
            f"Return only valid JSON. No other text."
        )
        usr_p = (
            f"Topic: {idea.get('topic', '')}\n"
            f"Fact: {idea.get('core_fact', '')}\n"
            f"Archetype: "
            f"{idea.get('archetype', 'single shocking fact')}\n"
            f"Emotion: "
            f"{idea.get('target_emotion', 'surprise')}\n"
            f"Visuals: {idea.get('visual_potential', '')}\n\n"
            f"Return JSON with:\n"
            f"hook, full_script, word_count,\n"
            f"estimated_duration_seconds (15-58),\n"
            f"scenes (array 3-6 each with scene_number,\n"
            f"duration_seconds, narration,\n"
            f"visual_description, text_overlay,\n"
            f"camera_movement, sfx),\n"
            f"key_words (array 3-5),\n"
            f"title (under 60 chars),\n"
            f"description (100-200 words),\n"
            f"tags (array 12 no hash),\n"
            f"pinned_comment"
        )
        raw = self._call_groq(sys_p, usr_p, max_tokens=3000)
        result = self._parse_json(raw)
        return result if isinstance(result, dict) else None

    def _generate_voice(self, text, output_path):
        if not text or not text.strip():
            return None
        raw = output_path.replace('.mp3', '_raw.mp3')
        try:
            import edge_tts

            async def _do_tts():
                c = edge_tts.Communicate(
                    text,
                    voice=TTS_VOICE,
                    rate=TTS_RATE,
                    pitch=TTS_PITCH
                )
                await c.save(raw)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(_do_tts())
            finally:
                loop.close()

            if not self._safe_exists(raw):
                return None

            if self.enable_evasion:
                ok = self._humanize(raw, output_path)
                if ok and self._safe_exists(output_path):
                    return output_path

            shutil.copy2(raw, output_path)
            return output_path
        except Exception as e:
            print(f"[Voice] Error: {e}")
            return None

    def _humanize(self, inp, out):
        pitch = random.uniform(-0.03, 0.03)
        speed = random.uniform(0.98, 1.02)
        shifted = int(44100 * (1 + pitch))
        filters = (
            f"asetrate={shifted},"
            f"aresample=44100,"
            f"atempo={speed},"
            f"aecho=0.8:0.7:20|30:0.04|0.03,"
            f"highpass=f=80,"
            f"lowpass=f=14000,"
            f"loudnorm=I=-16:TP=-1.5:LRA=11"
        )
        return self._run_ffmpeg([
            'ffmpeg', '-y', '-i', inp,
            '-af', filters,
            '-c:a', 'libmp3lame', '-b:a', '192k', out
        ], timeout=60)

    def _get_media(self, desc, topic, vdir, snum):
        sources = [
            lambda d=desc, v=vdir, n=snum: self._pexels_video(d, v, n),
            lambda d=desc, v=vdir, n=snum: self._pixabay_video(d, v, n),
            lambda d=desc, v=vdir, n=snum: self._pexels_image(d, v, n),
            lambda d=desc, v=vdir, n=snum: self._pixabay_image(d, v, n),
            lambda d=desc, v=vdir, n=snum: self._pollinations(d, v, n),
            lambda d=topic, v=vdir, n=snum: self._pollinations(d, v, n),
        ]
        for fn in sources:
            try:
                r = fn()
                if self._safe_exists(r):
                    ext = os.path.splitext(r)[1].lower()
                    return r, (
                        'video' if ext == '.mp4' else 'image'
                    )
            except Exception as e:
                print(f"[Media] Error: {e}")
            time.sleep(0.3)
        return None, None

    def _pexels_video(self, q, d, n):
        if not self.pexels_key:
            return None
        try:
            r = requests.get(
                "https://api.pexels.com/videos/search",
                headers={"Authorization": self.pexels_key},
                params={
                    "query": q[:50],
                    "per_page": 5,
                    "orientation": "portrait"
                },
                timeout=15
            )
            if r.status_code != 200:
                return None
            vids = r.json().get('videos', [])
            if not vids:
                return None
            v = random.choice(vids)
            files = v.get('video_files', [])
            hd = [f for f in files if f.get('height', 0) >= 720]
            chosen = (
                random.choice(hd if hd else files)
                if files else None
            )
            if not chosen:
                return None
            p = os.path.join(d, f"s{n}_vid.mp4")
            resp = requests.get(chosen['link'], timeout=60)
            with open(p, 'wb') as f:
                f.write(resp.content)
            return p
        except Exception as e:
            print(f"[Pexels Video] {e}")
            return None

    def _pixabay_video(self, q, d, n):
        if not self.pixabay_key:
            return None
        try:
            r = requests.get(
                "https://pixabay.com/api/videos/",
                params={
                    "key": self.pixabay_key,
                    "q": q[:100],
                    "per_page": 5,
                    "safesearch": "true"
                },
                timeout=15
            )
            if r.status_code != 200:
                return None
            hits = r.json().get('hits', [])
            if not hits:
                return None
            h = random.choice(hits)
            vids = h.get('videos', {})
            url = (
                vids.get('medium', {}).get('url') or
                vids.get('small', {}).get('url') or
                vids.get('tiny', {}).get('url')
            )
            if not url:
                return None
            p = os.path.join(d, f"s{n}_vid.mp4")
            resp = requests.get(url, timeout=60)
            with open(p, 'wb') as f:
                f.write(resp.content)
            return p
        except Exception as e:
            print(f"[Pixabay Video] {e}")
            return None

    def _pexels_image(self, q, d, n):
        if not self.pexels_key:
            return None
        try:
            r = requests.get(
                "https://api.pexels.com/v1/search",
                headers={"Authorization": self.pexels_key},
                params={
                    "query": q[:50],
                    "per_page": 5,
                    "orientation": "portrait"
                },
                timeout=15
            )
            if r.status_code != 200:
                return None
            photos = r.json().get('photos', [])
            if not photos:
                return None
            p = os.path.join(d, f"s{n}_img.jpg")
            resp = requests.get(
                random.choice(photos)['src']['large2x'],
                timeout=30
            )
            with open(p, 'wb') as f:
                f.write(resp.content)
            return p
        except Exception as e:
            print(f"[Pexels Image] {e}")
            return None

    def _pixabay_image(self, q, d, n):
        if not self.pixabay_key:
            return None
        try:
            r = requests.get(
                "https://pixabay.com/api/",
                params={
                    "key": self.pixabay_key,
                    "q": q[:100],
                    "per_page": 5,
                    "image_type": "photo",
                    "safesearch": "true"
                },
                timeout=15
            )
            if r.status_code != 200:
                return None
            hits = r.json().get('hits', [])
            if not hits:
                return None
            hit = random.choice(hits)
            url = hit.get(
                'largeImageURL',
                hit.get('webformatURL', '')
            )
            if not url:
                return None
            p = os.path.join(d, f"s{n}_img.jpg")
            resp = requests.get(url, timeout=30)
            with open(p, 'wb') as f:
                f.write(resp.content)
            return p
        except Exception as e:
            print(f"[Pixabay Image] {e}")
            return None

    def _pollinations(self, desc, d, n):
        try:
            prompt = (
                f"{desc} cinematic dramatic 8k "
                f"professional dark moody vertical"
            )
            enc = urllib.parse.quote(prompt[:400], safe='')
            seed = random.randint(1, 999999)
            url = (
                f"https://image.pollinations.ai/prompt/{enc}"
                f"?width=1080&height=1920"
                f"&nologo=true&seed={seed}&model=flux"
            )
            for attempt in range(3):
                try:
                    resp = requests.get(
                        url,
                        headers={"User-Agent": "Mozilla/5.0"},
                        timeout=90
                    )
                    if (resp.status_code == 200 and
                            len(resp.content) > 5000):
                        p = os.path.join(d, f"s{n}_ai.png")
                        with open(p, 'wb') as f:
                            f.write(resp.content)
                        return p
                except Exception as e:
                    print(f"[Pollinations] Attempt {attempt+1}: {e}")
                time.sleep(5)
        except Exception as e:
            print(f"[Pollinations] Error: {e}")
        return None

    def _thumbnail(self, topic, vdir):
        out = os.path.join(vdir, "thumbnail.png")
        try:
            prompt = (
                f"dramatic cinematic YouTube thumbnail "
                f"{topic} dark moody background vibrant "
                f"colors 8k no text no words no letters"
            )
            enc = urllib.parse.quote(prompt[:400], safe='')
            url = (
                f"https://image.pollinations.ai/prompt/{enc}"
                f"?width=1280&height=720&nologo=true"
                f"&seed={random.randint(1, 999999)}&model=flux"
            )
            for attempt in range(3):
                try:
                    resp = requests.get(
                        url,
                        headers={"User-Agent": "Mozilla/5.0"},
                        timeout=90
                    )
                    if (resp.status_code == 200 and
                            len(resp.content) > 5000):
                        with open(out, 'wb') as f:
                            f.write(resp.content)
                        return out
                except Exception as e:
                    print(f"[Thumb] Attempt {attempt+1}: {e}")
                time.sleep(5)
        except Exception as e:
            print(f"[Thumb] Error: {e}")
        return self._pillow_thumbnail(topic, out)
            def _build_video(self, scenes, voice_path,
                      output_path, vdir,
                      script_text, key_words):
        clips = []

        for j, scene in enumerate(scenes):
            clip = os.path.join(vdir, f"clip_{j}.mp4")
            dur = max(scene.get('duration_seconds', 5), 2)
            media = scene.get('media_path')
            mtype = scene.get('media_type', 'image')
            overlay = scene.get('text_overlay', '')
            built = False

            if self._safe_exists(media) and mtype == 'video':
                ok = self._run_ffmpeg([
                    'ffmpeg', '-y', '-i', media,
                    '-t', str(dur),
                    '-vf', (
                        f'scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:'
                        f'force_original_aspect_ratio=increase,'
                        f'crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},'
                        f'fps={FPS},'
                        f'eq=contrast=1.1:saturation=1.15'
                    ),
                    '-c:v', 'libx264', '-preset', 'fast',
                    '-pix_fmt', 'yuv420p', '-an', clip
                ])
                built = ok and self._safe_exists(clip)

            if (not built and
                    self._safe_exists(media) and
                    mtype == 'image'):
                frames = int(dur * FPS)
                mvs = [
                    (
                        f"zoompan=z='min(zoom+0.002,1.5)':"
                        f"x='iw/2-(iw/zoom/2)':"
                        f"y='ih/2-(ih/zoom/2)':"
                        f"d={frames}:"
                        f"s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:"
                        f"fps={FPS}"
                    ),
                    (
                        f"zoompan=z='if(eq(on,1),1.4,"
                        f"max(zoom-0.002,1))':"
                        f"x='iw/2-(iw/zoom/2)':"
                        f"y='ih/2-(ih/zoom/2)':"
                        f"d={frames}:"
                        f"s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:"
                        f"fps={FPS}"
                    )
                ]
                ok = self._run_ffmpeg([
                    'ffmpeg', '-y', '-loop', '1',
                    '-i', media,
                    '-vf', (
                        f'{random.choice(mvs)},'
                        f'eq=contrast=1.1:saturation=1.1'
                    ),
                    '-t', str(dur),
                    '-c:v', 'libx264', '-preset', 'fast',
                    '-pix_fmt', 'yuv420p', clip
                ], timeout=120)
                built = ok and self._safe_exists(clip)

            if not built:
                self._colored_bg(dur, clip, overlay)
                built = self._safe_exists(clip)

            if built:
                clips.append(clip)

        if not clips:
            return None

        lst = os.path.join(vdir, "concat.txt")
        with open(lst, 'w') as f:
            for c in clips:
                f.write(f"file '{os.path.abspath(c)}'\n")

        cat = os.path.join(vdir, "concat.mp4")
        ok = self._run_ffmpeg([
            'ffmpeg', '-y', '-f', 'concat',
            '-safe', '0', '-i', lst,
            '-c:v', 'libx264', '-preset', 'fast',
            '-pix_fmt', 'yuv420p', cat
        ])
        if not ok or not self._safe_exists(cat):
            return None

        cur = cat

        if self._safe_exists(voice_path):
            vcd = os.path.join(vdir, "voiced.mp4")
            ok = self._run_ffmpeg([
                'ffmpeg', '-y',
                '-i', cur, '-i', voice_path,
                '-c:v', 'copy',
                '-c:a', 'aac', '-b:a', AUDIO_BITRATE,
                '-map', '0:v:0', '-map', '1:a:0',
                '-shortest', vcd
            ])
            if ok and self._safe_exists(vcd):
                cur = vcd

        sub = os.path.join(vdir, "subbed.mp4")
        if self._burn_subs(cur, script_text, key_words, sub):
            if self._safe_exists(sub):
                cur = sub

        grn = os.path.join(vdir, "grained.mp4")
        ok = self._run_ffmpeg([
            'ffmpeg', '-y', '-i', cur,
            '-vf', 'noise=alls=3:allf=t',
            '-c:v', 'libx264', '-preset', 'fast',
            '-c:a', 'copy', grn
        ])
        if ok and self._safe_exists(grn):
            cur = grn

        ok = self._run_ffmpeg([
            'ffmpeg', '-y', '-i', cur,
            '-c:v', 'libx264', '-preset', 'medium',
            '-crf', '20', '-b:v', VIDEO_BITRATE,
            '-maxrate', '8M', '-bufsize', '16M',
            '-c:a', 'aac', '-b:a', AUDIO_BITRATE,
            '-ar', '48000', '-pix_fmt', 'yuv420p',
            '-movflags', '+faststart', output_path
        ], timeout=300)

        return (
            output_path
            if (ok and self._safe_exists(output_path))
            else None
        )

    def _burn_subs(self, vpath, script, kwords, out):
        if not script:
            return False
        dur = self._get_duration(vpath)
        words = script.split()
        groups = [
            ' '.join(words[i:i + WORDS_PER_SUBTITLE])
            for i in range(0, len(words), WORDS_PER_SUBTITLE)
        ]
        if not groups:
            return False
        tpg = dur / len(groups)
        kw = [w.lower() for w in (kwords or [])]
        filters = []
        for i, grp in enumerate(groups):
            s = i * tpg
            e = (i + 1) * tpg
            safe = (
                grp.replace("'", "\u2019")
                   .replace('"', '\\"')
                   .replace(':', '\\:')
                   .replace('%', '%%')
            )
            is_key = any(w in grp.lower() for w in kw)
            color = (
                SUBTITLE_HIGHLIGHT_COLOR
                if is_key else SUBTITLE_COLOR
            )
            size = (
                SUBTITLE_HIGHLIGHT_SIZE
                if is_key else SUBTITLE_FONTSIZE
            )
            filters.append(
                f"drawtext=text='{safe}'"
                f":fontcolor={color}:fontsize={size}"
                f":x=(w-text_w)/2:y=h*{SUBTITLE_POSITION}"
                f":borderw={SUBTITLE_BORDERW}"
                f":bordercolor=black"
                f":shadowcolor=black@0.7"
                f":shadowx=2:shadowy=2"
                f":enable='between(t,{s:.2f},{e:.2f})'"
            )
        ok = self._run_ffmpeg([
            'ffmpeg', '-y', '-i', vpath,
            '-vf', ','.join(filters),
            '-c:v', 'libx264', '-preset', 'fast',
            '-c:a', 'copy', out
        ], timeout=300)
        return ok

    def _make_schedule(self):
        done = [
            v for v in self.progress['videos']
            if v['status'] == 'done'
        ]
        now = datetime.now()
        schedule = []
        for i, v in enumerate(done):
            day = (i // 3) + random.randint(0, 1)
            hour = random.choice(HUMAN_UPLOAD_HOURS)
            minute = random.randint(0, 59)
            t = now + timedelta(
                days=day,
                hours=hour,
                minutes=minute
            )
            schedule.append({
                'video_number': v['number'],
                'topic': v['topic'],
                'title': v['title'],
                'upload_date': t.strftime('%Y-%m-%d'),
                'upload_time': t.strftime('%I:%M %p'),
                'video_file': v.get('video_path', ''),
                'thumbnail_file': v.get('thumbnail_path', '')
            })
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        p = os.path.join(
            OUTPUT_DIR,
            f"schedule_{self.batch_id}.json"
        )
        with open(p, 'w') as f:
            json.dump(schedule, f, indent=2)
        self.schedule_path = p
