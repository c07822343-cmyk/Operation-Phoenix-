# 🔥 Project Phoenix
### Faceless YouTube Shorts Factory

> Generate 50 complete YouTube Shorts automatically.
> Double click to start. $0/month forever.

---

## What It Does

Project Phoenix automatically generates complete YouTube Shorts videos from start to finish. It creates viral scripts using AI, generates voiceover audio, finds and downloads stock footage, edits everything into 1080x1920 vertical format, adds TikTok-style subtitles, generates thumbnails, and creates an upload schedule — all with one click. You type your niche, click Generate, walk away, and come back to finished videos ready to upload.

---

## Monthly Cost

| Service | Cost |
|---------|------|
| Groq AI | $0 Free tier |
| Edge TTS Voice | $0 No key needed |
| Pexels Stock Video | $0 Free tier |
| Pixabay Stock Video | $0 Free tier |
| Pollinations AI Images | $0 No key needed |
| FFmpeg Video Editing | $0 Open source |
| **Total** | **$0.00** |

---

## What You Need Before Starting

- Python 3.9 or higher
- FFmpeg
- A Groq API key (free)
- A Pexels API key (free, recommended)
- A Pixabay API key (free, recommended)
- An internet connection

---

## Step 1 — Download The Project

### Option A — Using Git (Recommended)

**Mac and Linux:**
```bash
git clone https://github.com/YOUR_USERNAME/project-phoenix.git
cd project-phoenix
```

**Windows:**
```bash
git clone https://github.com/YOUR_USERNAME/project-phoenix.git
cd project-phoenix
```

If you do not have Git installed:
- Mac: Install from [git-scm.com](https://git-scm.com) or run `brew install git`
- Windows: Download from [git-scm.com/download/win](https://git-scm.com/download/win)
- Linux: Run `sudo apt install git`

### Option B — Download ZIP

1. Go to your GitHub repository page
2. Click the green **Code** button
3. Click **Download ZIP**
4. Unzip the file to your Desktop
5. Open the unzipped folder

---

## Step 2 — Install Everything

### Mac

**Run the installer by double clicking:**

1. Open the project folder in Finder
2. Double click `install.py`
3. A Terminal window opens automatically
4. It installs Python packages and FFmpeg
5. Wait until you see **SETUP COMPLETE**
6. Close the window

**If double clicking does not work:**

1. Press `CMD + Spacebar`
2. Type `terminal` and press Enter
3. Drag the project folder into the Terminal window
   (this types the path automatically)
4. Press Enter to go into the folder
5. Type this and press Enter:
```bash
python3 install.py
```

**If Python is not installed on Mac:**
1. Go to [python.org/downloads](https://python.org/downloads)
2. Click the big Download button
3. Open the downloaded file and install it
4. Then run `python3 install.py` again

**If FFmpeg is not installed on Mac:**

The installer handles this automatically using Homebrew.
If it fails, install manually:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install ffmpeg
```

---

### Windows

**Step 2a — Install Python:**

1. Go to [python.org/downloads](https://python.org/downloads)
2. Click **Download Python**
3. Open the downloaded file
4. ⚠️ Check the box that says **Add Python to PATH** before clicking install
5. Click **Install Now**
6. Wait for it to finish
7. Click **Close**

Verify it worked:
1. Press `Windows key + R`
2. Type `cmd` and press Enter
3. Type `python --version` and press Enter
4. You should see `Python 3.x.x`

**Step 2b — Install FFmpeg on Windows:**

1. Go to [ffmpeg.org/download.html](https://ffmpeg.org/download.html)
2. Click **Windows builds from gyan.dev**
3. Under **release builds** download `ffmpeg-release-essentials.zip`
4. Right click the downloaded zip and click **Extract All**
5. Extract to `C:\`
6. Rename the extracted folder to just `ffmpeg`
   so the path is `C:\ffmpeg`
7. Add FFmpeg to PATH:
   - Press Windows key and search **environment variables**
   - Click **Edit the system environment variables**
   - Click **Environment Variables**
   - Under **System variables** find and click **Path**
   - Click **Edit**
   - Click **New**
   - Type `C:\ffmpeg\bin`
   - Click **OK** on everything
8. Close and reopen Command Prompt
9. Type `ffmpeg -version` to verify it works

**Step 2c — Install Python packages on Windows:**

1. Press `Windows key + R`
2. Type `cmd` and press Enter
3. Navigate to your project folder:
```bash
cd Desktop\project-phoenix
```
4. Install packages:
```bash
pip install flask requests edge-tts Pillow
```

---

### Linux (Ubuntu / Debian)

Open Terminal and run these commands one at a time:

**Install Python:**
```bash
sudo apt update
sudo apt install python3 python3-pip -y
python3 --version
```

**Install FFmpeg:**
```bash
sudo apt install ffmpeg -y
ffmpeg -version
```

**Install Python packages:**
```bash
cd project-phoenix
pip3 install flask requests edge-tts Pillow
```

**Run the installer:**
```bash
python3 install.py
```

---

## Step 3 — Get Your Free API Keys

You need 3 keys. All are completely free. No credit card required for any of them. The whole process takes about 5 minutes.

---

### Key 1 — Groq (Required — Powers All AI Features)

This is the brain of Phoenix. It writes all scripts, generates ideas, and creates metadata.

1. Open your browser and go to [console.groq.com](https://console.groq.com)
2. Click **Sign Up** in the top right
3. Sign up with Google or email — both are free
4. Once logged in look at the left sidebar
5. Click **API Keys**
6. Click the **Create API Key** button
7. Give it any name like `phoenix`
8. Click **Submit**
9. A key appears — it starts with `gsk_`
10. Copy it immediately and save it somewhere safe
    (you cannot see it again after closing)

> **Free tier limits:** 30 requests per minute, 14,400 per day.
> This is more than enough to generate 50 videos.

---

### Key 2 — Pexels (Recommended — Stock Photos and Videos)

This gives Phoenix access to millions of free professional stock photos and videos.

1. Go to [pexels.com/api](https://www.pexels.com/api/)
2. Click **Get Started**
3. Fill in your name and what you are building
   (write something like "personal video project")
4. Your API key is shown on the next page
5. It looks like a long string of letters and numbers
6. Copy it and save it

> **Free tier limits:** 200 requests per hour.
> This is plenty for 50 videos.

---

### Key 3 — Pixabay (Recommended — Backup Stock)

This is the backup if Pexels runs out of results.

1. Go to [pixabay.com/api/docs](https://pixabay.com/api/docs/)
2. Click **Sign Up** at the top of the page
3. Sign up free with email
4. Once logged in your API key is shown
   right on the [pixabay.com/api/docs](https://pixabay.com/api/docs/) page
5. Scroll to the top of that page
6. Your key is in the format `12345678-abcdef1234567890abc`
7. Copy it and save it

> **Free tier limits:** 100 requests per minute.
> More than enough.

---

### Where To Enter Your Keys

Once Phoenix is running you enter keys in the dashboard:

1. Launch Phoenix (see Step 4 below)
2. Find the **Free API Keys** card on the dashboard
3. Paste each key into the correct field
4. Click **Save Keys**
5. The dots next to each key turn green when valid
6. Keys are saved automatically for next time

---

## Step 4 — Launch Phoenix

### Mac — Double Click Method (Easiest)

**First time only — set up the launcher:**

1. Open your project folder in Finder
2. Find the file called `Phoenix.command`
3. Right click it
4. Click **Get Info**
5. Find the section called **Open With**
6. Click the dropdown and select **Terminal**
7. Close the Get Info window
8. This only needs to be done once

**Every time you want to use Phoenix:**

1. Double click `Phoenix.command`
2. A Terminal window opens briefly
3. Your browser opens automatically at `http://localhost:5000`
4. The Phoenix dashboard is ready

**If the browser does not open automatically:**

Go to [http://localhost:5000](http://localhost:5000) in your browser manually.

---

### Mac — Terminal Method

1. Press `CMD + Spacebar`
2. Type `terminal` and press Enter
3. Type this and press Enter:
```bash
cd ~/Desktop/project-phoenix
python3 run.py
```
4. Wait for `Phoenix ready at http://localhost:5000`
5. Open [http://localhost:5000](http://localhost:5000) in your browser

---

### Windows — Launch Method

1. Open File Explorer
2. Go to your project-phoenix folder
3. Click the address bar at the top
4. Type `cmd` and press Enter
   (this opens Command Prompt in that folder)
5. Type this and press Enter:
```bash
python run.py
```
6. Wait for `Phoenix ready at http://localhost:5000`
7. Open [http://localhost:5000](http://localhost:5000) in your browser

**Or double click to launch on Windows:**

1. In the project folder right click an empty space
2. Click **New** then **Text Document**
3. Name it `start.bat`
4. Right click it and click **Edit**
5. Paste this inside:
```batch
@echo off
cd /d "%~dp0"
python run.py
pause
```
6. Save and close
7. Double click `start.bat` to launch Phoenix

---

### Linux — Launch Method

1. Open Terminal
2. Navigate to project folder:
```bash
cd ~/Desktop/project-phoenix
```
3. Run Phoenix:
```bash
python3 run.py
```
4. Open [http://localhost:5000](http://localhost:5000) in your browser

**Make a desktop shortcut on Linux:**

1. Create a file called `phoenix.sh`:
```bash
#!/bin/bash
cd "$(dirname "$0")"
python3 run.py
```
2. Make it executable:
```bash
chmod +x phoenix.sh
```
3. Double click `phoenix.sh` to launch

---

## How To Use The Dashboard

Once Phoenix is open in your browser:

1. **Fill in Your Niche**
   Type what kind of videos you want.
   Example: `Random mind-blowing facts` or `True crime under 60 seconds`

2. **Add Reference Channels (Optional)**
   Paste YouTube channel or video links.
   Phoenix analyzes their style and copies it.

3. **Choose Tone and Audience**
   Pick from the dropdowns.

4. **Enter Your API Keys**
   Paste your Groq, Pexels, and Pixabay keys.
   Click **Save Keys**.
   Wait for the dots to turn green.

5. **Set Video Count**
   Use the slider to pick how many videos.
   Start with 5 to test.

6. **Click Generate**
   The big red button.
   Watch the progress bar.

7. **Download Your Videos**
   When done click **Download All Videos (ZIP)**.
   Or download individual videos and thumbnails.

8. **Upload to YouTube**
   Drag your `.mp4` files into YouTube Studio.
   Use the titles and descriptions from `upload_schedule.json`.
   Follow the upload schedule to space them out.

---

## Where Are My Videos?

```
project-phoenix/
└── output/
    ├── video_001/
    │   ├── final.mp4        ← Your video
    │   └── thumbnail.png    ← Your thumbnail
    ├── video_002/
    │   ├── final.mp4
    │   └── thumbnail.png
    └── schedule_batch_XXX.json  ← Upload schedule
```

---

## Every Time After First Setup

### Mac
```
Double click Phoenix.command
Browser opens
Click Generate
Walk away
Come back to finished videos
```

### Windows
```
Double click start.bat
Browser opens at localhost:5000
Click Generate
Walk away
Come back to finished videos
```

### Linux
```
Run: python3 run.py
Open: http://localhost:5000
Click Generate
Walk away
Come back to finished videos
```

---

## Troubleshooting

| Problem | Mac Fix | Windows Fix | Linux Fix |
|---------|---------|-------------|-----------|
| Python not found | Download from python.org | Download from python.org check Add to PATH | `sudo apt install python3` |
| FFmpeg not found | `brew install ffmpeg` | Download from ffmpeg.org add to PATH | `sudo apt install ffmpeg` |
| Port 5000 in use | Change port in main.py | Change port in main.py | Change port in main.py |
| Browser does not open | Go to localhost:5000 manually | Go to localhost:5000 manually | Go to localhost:5000 manually |
| Groq key invalid | Get new key at console.groq.com | Get new key at console.groq.com | Get new key at console.groq.com |
| Videos are black | Check Pexels and Pixabay keys | Check Pexels and Pixabay keys | Check Pexels and Pixabay keys |
| Package not found | `pip3 install flask` | `pip install flask` | `pip3 install flask` |
| Permission denied | `chmod +x Phoenix.command` | Run as administrator | `sudo python3 run.py` |

---

## File Structure

```
project-phoenix/
├── Phoenix.command     ← Mac double click launcher
├── install.py          ← Run once for setup
├── run.py              ← Smart launcher (all platforms)
├── main.py             ← Flask web server
├── pipeline_core.py    ← Video generation engine
├── pipeline_runner.py  ← Pipeline orchestrator
├── config.py           ← All settings
├── database.py         ← SQLite storage
├── requirements.txt    ← Python packages
├── templates/
│   └── index.html      ← Dashboard UI
├── static/
│   ├── style.css       ← Dark theme styles
│   └── app.js          ← Dashboard logic
├── output/             ← Your videos saved here
├── temp/               ← Temporary processing files
└── assets/             ← Supporting files
```

---

## License

MIT License — use it however you want, commercially or personally.

---

⭐ **Star this repo if Phoenix saved you time.**
It helps other people find it.
