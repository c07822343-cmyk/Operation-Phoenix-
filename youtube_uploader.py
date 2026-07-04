import os
import json
import pickle
import time
import random
from datetime import datetime, timedelta, timezone
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube'
]

CREDENTIALS_FILE = 'client_secrets.json'
TOKEN_FILE = 'token.pickle'

UPLOAD_HOUR_WINDOWS = [
    (7, 9),
    (11, 13),
    (19, 21),
    (22, 24)
]

MIN_HOURS_BETWEEN = 3
MAX_PER_DAY = 4


def authenticate():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                print("ERROR: client_secrets.json not found")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'wb') as f:
            pickle.dump(creds, f)
    return build('youtube', 'v3', credentials=creds)


def generate_schedule(count, start_days=0):
    schedule = []
    now = datetime.now(timezone.utc)
    current = now + timedelta(days=start_days, hours=2)
    last = None

    for i in range(count):
        placed = False
        while not placed:
            window = random.choice(UPLOAD_HOUR_WINDOWS)
            hour = random.randint(window[0], window[1] - 1)
            minute = random.randint(0, 59)
            candidate = current.replace(
                hour=hour, minute=minute,
                second=random.randint(0, 59),
                microsecond=0
            )
            if candidate <= now + timedelta(minutes=30):
                candidate += timedelta(days=1)
            if last:
                diff = (candidate - last).total_seconds() / 3600
                if diff < MIN_HOURS_BETWEEN:
                    candidate += timedelta(hours=MIN_HOURS_BETWEEN)
            day_count = sum(
                1 for s in schedule
                if s.date() == candidate.date()
            )
            if day_count >= MAX_PER_DAY:
                current += timedelta(days=1)
                continue
            schedule.append(candidate)
            last = candidate
            placed = True
            if sum(
                1 for s in schedule
                if s.date() == candidate.date()
            ) >= MAX_PER_DAY:
                current += timedelta(days=1)

    schedule.sort()
    return schedule


def upload_video(youtube, video_path, title,
                 description, tags,
                 thumbnail_path=None,
                 publish_at=None):
    if not os.path.exists(video_path):
        print(f"Video not found: {video_path}")
        return None

    body = {
        'snippet': {
            'title': title[:100],
            'description': description[:5000],
            'tags': tags[:30],
            'categoryId': '22',
            'defaultLanguage': 'en',
            'defaultAudioLanguage': 'en'
        },
        'status': {
            'privacyStatus': 'private',
            'selfDeclaredMadeForKids': False,
            'madeForKids': False
        }
    }

    if publish_at:
        body['status']['publishAt'] = (
            publish_at.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        )

    print(f"Uploading: {title[:50]}")
    if publish_at:
        print(
            f"Scheduled: "
            f"{publish_at.strftime('%Y-%m-%d %I:%M %p UTC')}"
        )

    media = MediaFileUpload(
        video_path,
        mimetype='video/mp4',
        resumable=True,
        chunksize=10 * 1024 * 1024
    )

    request = youtube.videos().insert(
        part='snippet,status',
        body=body,
        media_body=media
    )

    response = None
    retries = 0
    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                pct = int(status.progress() * 100)
                print(f"  Progress: {pct}%")
        except Exception as e:
            retries += 1
            if retries > 3:
                print(f"Upload failed: {e}")
                return None
            time.sleep(10)

    video_id = response.get('id')
    print(f"Uploaded: https://youtube.com/shorts/{video_id}")

    if thumbnail_path and os.path.exists(thumbnail_path):
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path)
            ).execute()
            print("Thumbnail set")
        except Exception as e:
            print(f"Thumbnail failed: {e}")

    return video_id


def upload_batch(videos_data, delay_between=45):
    youtube = authenticate()
    if not youtube:
        return []

    print(f"\nUploading {len(videos_data)} videos")
    print("Scheduled to go public automatically")
    print("")

    schedule = generate_schedule(len(videos_data))
    results = []

    for i, (video, publish_time) in enumerate(
        zip(videos_data, schedule)
    ):
        print(f"\nVideo {i+1}/{len(videos_data)}")
        video_id = upload_video(
            youtube=youtube,
            video_path=video['video_path'],
            title=video.get('title', f'Fact #{i+1}'),
            description=video.get(
                'description', '#shorts #facts'
            ),
            tags=video.get(
                'tags', ['shorts', 'facts']
            ),
            thumbnail_path=video.get('thumbnail_path'),
            publish_at=publish_time
        )

        results.append({
            'video_id': video_id,
            'title': video.get('title', ''),
            'scheduled': publish_time.strftime(
                '%Y-%m-%d %I:%M %p UTC'
            ) if publish_time else '',
            'url': (
                f"https://youtube.com/shorts/{video_id}"
                if video_id else None
            )
        })

        if video_id and i < len(videos_data) - 1:
            wait = delay_between + random.randint(-10, 20)
            print(f"Waiting {wait}s...")
            time.sleep(wait)

    return results


def upload_from_batch(batch_id=None,
                      output_dir='output'):
    import glob

    if batch_id:
        pattern = os.path.join(
            output_dir, batch_id, '*/final.mp4'
        )
    else:
        pattern = os.path.join(
            output_dir, '*/*/final.mp4'
        )

    video_files = sorted(glob.glob(pattern))

    if not video_files:
        pattern2 = os.path.join(
            output_dir, 'video_*/final.mp4'
        )
        video_files = sorted(glob.glob(pattern2))

    if not video_files:
        print("No videos found in output folder")
        return []

    print(f"Found {len(video_files)} videos")

    videos_data = []
    for vpath in video_files:
        vdir = os.path.dirname(vpath)
        thumb = os.path.join(vdir, 'thumbnail.png')
        title = os.path.basename(vdir)
        description = '#shorts #facts #mindblown'
        tags = ['shorts', 'facts', 'mindblown', 'didyouknow']

        schedule_files = glob.glob(
            os.path.join(output_dir, 'schedule_*.json')
        )
        for sf in schedule_files:
            try:
                with open(sf) as f:
                    data = json.load(f)
                for item in data:
                    if item.get('video_file') == vpath:
                        title = item.get('title', title)
                        break
            except Exception:
                pass

        videos_data.append({
            'video_path': vpath,
            'thumbnail_path': (
                thumb if os.path.exists(thumb) else None
            ),
            'title': title,
            'description': description,
            'tags': tags
        })

    results = upload_batch(videos_data)

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_path = os.path.join(
        output_dir, f'upload_results_{ts}.json'
    )
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)

    done = sum(1 for r in results if r.get('video_id'))
    print(f"\nDone: {done}/{len(videos_data)} uploaded")
    print("\nUpload Schedule:")
    for r in results:
        if r.get('video_id'):
            print(
                f"  {r['scheduled']} "
                f"— {r['title'][:40]}"
            )

    return results


if __name__ == '__main__':
    upload_from_batch()
