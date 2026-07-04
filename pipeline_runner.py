import os
import time
import threading
from pipeline_core import PhoenixPipeline


def run(pipeline: PhoenixPipeline, count: int):
    pipeline.progress['running'] = True
    pipeline.progress['total_videos'] = count
    pipeline.progress['start_time'] = time.time()

    try:
        pipeline._set_phase(1, "Analyzing Style References")
        pipeline.style_guide = pipeline._analyze_style()

        pipeline._set_phase(2, "Generating Ideas")
        ideas = pipeline._generate_ideas(count)

        if not ideas:
            pipeline.progress['error'] = (
                'Failed to generate ideas. '
                'Check your Groq API key at console.groq.com'
            )
            return

        ideas = ideas[:count]

        semaphore = threading.Semaphore(3)
        results = [None] * len(ideas)
        threads = []

        def process_with_semaphore(idea, index, vinfo):
            with semaphore:
                ok = _process_one(
                    pipeline, idea, index, count, vinfo
                )
                results[index] = ok

        for i, idea in enumerate(ideas):
            pipeline._update_eta(i, count)
            pipeline.progress['current_video'] = i + 1

            vinfo = {
                'number': i + 1,
                'topic': idea.get('topic', f'Fact {i+1}'),
                'category': idea.get('category', 'facts'),
                'status': 'processing',
                'error': '',
                'title': '',
                'video_path': None,
                'thumbnail_path': None
            }
            pipeline.progress['videos'].append(vinfo)

            t = threading.Thread(
                target=process_with_semaphore,
                args=(idea, i, vinfo),
                daemon=True
            )
            threads.append(t)
            t.start()

            time.sleep(0.5)

        for t in threads:
            t.join()

        for ok in results:
            if ok:
                pipeline.progress['successful'] += 1
            else:
                pipeline.progress['failed'] += 1

        pipeline._set_phase(7, "Packaging Everything")
        pipeline._make_schedule()

    except Exception as e:
        import traceback
        traceback.print_exc()
        pipeline.progress['error'] = str(e)
    finally:
        pipeline.progress['done'] = True
        pipeline.progress['running'] = False
        pipeline.progress['percent'] = 100
        print(
            f"[Phoenix] Complete. "
            f"Done: {pipeline.progress['successful']} "
            f"Failed: {pipeline.progress['failed']}"
        )


def _process_one(pipeline, idea, index, total, vinfo):
    from config import OUTPUT_DIR
    vdir = os.path.join(
        OUTPUT_DIR, f"video_{index + 1:03d}"
    )
    os.makedirs(vdir, exist_ok=True)

    try:
        pipeline._set_phase(
            3, f"Writing Script {index+1}/{total}"
        )
        script = pipeline._write_script(idea)
        if not script:
            vinfo['status'] = 'failed'
            vinfo['error'] = 'Script generation failed'
            return False

        vinfo['title'] = script.get(
            'title', idea.get('topic', '')
        )
        time.sleep(1)

        pipeline._set_phase(
            4, f"Creating Voice {index+1}/{total}"
        )
        vpath = os.path.join(vdir, "voice.mp3")
        voice = pipeline._generate_voice(
            script.get('full_script', ''), vpath
        )
        if not voice:
            voice = pipeline._silent_audio(
                script.get(
                    'estimated_duration_seconds', 40
                ),
                vpath
            )

        pipeline._set_phase(
            5, f"Getting Visuals {index+1}/{total}"
        )
        scenes = script.get('scenes', [])
        if not scenes:
            dur = script.get(
                'estimated_duration_seconds', 40
            )
            n = max(3, int(dur / 10))
            scenes = [
                {
                    'scene_number': k + 1,
                    'duration_seconds': dur / n,
                    'narration': '',
                    'visual_subject': idea.get(
                        'visual_potential', ''
                    ),
                    'visual_description': idea.get(
                        'visual_potential',
                        idea.get('topic', 'dramatic scene')
                    ),
                    'text_overlay': (
                        idea.get('topic', '')[:20].upper()
                    ),
                    'camera_movement': 'zoom_in',
                    'sfx': 'none'
                }
                for k in range(n)
            ]

        for j, scene in enumerate(scenes):
            # Use visual_subject for focused search
            # Fall back to visual_description
            visual_subject = scene.get(
                'visual_subject',
                scene.get('visual_description', '')
            )
            visual_description = scene.get(
                'visual_description',
                visual_subject
            )

            mp, mt = pipeline._get_media(
                visual_subject=visual_subject,
                visual_description=visual_description,
                topic=idea.get('topic', ''),
                vdir=vdir,
                snum=j + 1,
                core_fact=idea.get('core_fact', '')
            )
            scene['media_path'] = mp
            scene['media_type'] = mt
            time.sleep(0.2)

        thumb = pipeline._thumbnail(
            idea.get('topic', ''), vdir
        )
        vinfo['thumbnail_path'] = thumb

        pipeline._set_phase(
            6, f"Editing Video {index+1}/{total}"
        )
        final = os.path.join(vdir, "final.mp4")
        built = pipeline._build_video(
            scenes=scenes,
            voice_path=voice,
            output_path=final,
            vdir=vdir,
            script_text=script.get('full_script', ''),
            key_words=script.get('key_words', [])
        )

        if built and pipeline._safe_exists(built):
            size = os.path.getsize(built) / (1024 * 1024)
            vinfo['status'] = 'done'
            vinfo['video_path'] = built
            vinfo['file_size_mb'] = round(size, 1)
            return True
        else:
            vinfo['status'] = 'failed'
            vinfo['error'] = 'Video build failed'
            return False

    except Exception as e:
        import traceback
        traceback.print_exc()
        vinfo['status'] = 'failed'
        vinfo['error'] = str(e)
        return False
