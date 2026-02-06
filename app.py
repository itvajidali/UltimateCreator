from flask import Flask, render_template, request, jsonify, send_file
from config import Config
from services.script_gen import generate_script
from services.media_source import fetch_content
from services.tts import generate_audio
from services.video_editor import assemble_video
from services.thumbnail_generator import generate_thumbnail
from services.script_gen import generate_script, translate_script
import os
import uuid
import threading

app = Flask(__name__)
app.config.from_object(Config)

# In-memory job store
jobs = {}

def process_video_job(job_id, prompt, duration, voice_id, orientation, mood):
    with app.app_context():
        try:
            print(f"Job {job_id} Started: {prompt} ({duration}, {orientation}, {mood})")
            jobs[job_id]['status'] = 'generating_script'
            jobs[job_id]['progress'] = 10
            
            # 1. Generate Script (Groq)
            script_data = generate_script(prompt, duration, voice_id, Config.GROQ_API_KEY)
            jobs[job_id]['script'] = script_data
            jobs[job_id]['progress'] = 30
            jobs[job_id]['status'] = 'fetching_media'

            # 2. Fetch Media (Video)
            for segment in script_data:
                segment['image_path'] = fetch_content(segment['image_query'], Config.PEXELS_API_KEY, orientation)
            
            jobs[job_id]['progress'] = 50
            jobs[job_id]['status'] = 'generating_audio'

            # 3. Generate Audio
            for segment in script_data:
                segment['audio_path'] = generate_audio(segment['text'], voice_id)
            
            jobs[job_id]['progress'] = 70
            jobs[job_id]['status'] = 'rendering_video'

            # 4. Assemble Video (Main)
            output_path = os.path.join(Config.OUTPUT_FOLDER, f"{job_id}.mp4")
            assemble_video(script_data, output_path, orientation, mood)
            
            # 5. [NEW] Generate Thumbnail
            thumb_path = os.path.join(Config.OUTPUT_FOLDER, f"{job_id}.jpg")
            generate_thumbnail(output_path, prompt, thumb_path)
            
            jobs[job_id]['output_path'] = output_path
            jobs[job_id]['thumbnail_path'] = thumb_path
            jobs[job_id]['dubbed_versions'] = []
            jobs[job_id]['progress'] = 90 # almost done
            
            # 6. [NEW] Multi-Language Dubbing
            # Automatically generate Hindi version if original is English
            if "en-" in voice_id and "hi-IN" not in voice_id:
                try:
                    print("Auto-Dubbing to Hindi...")
                    target_lang = "Hindi"
                    target_voice = "hi-IN-SwaraNeural" # Female Hindi
                    
                    # A. Translate Script
                    dub_script = translate_script(script_data, target_lang, Config.GROQ_API_KEY)
                    
                    # B. Generate Audio for Dub
                    for segment in dub_script:
                        # Regenerate audio with new text and voice
                        segment['audio_path'] = generate_audio(segment['text'], target_voice)
                        # Keep original image_path!
                    
                    # C. Assemble Dubbed Video
                    dub_output_path = os.path.join(Config.OUTPUT_FOLDER, f"{job_id}_hi.mp4")
                    assemble_video(dub_script, dub_output_path, orientation, mood)
                    
                    jobs[job_id]['dubbed_versions'].append({
                        'lang': 'Hindi',
                        'path': dub_output_path
                    })
                    print(f"Dubbing complete: {dub_output_path}")
                    
                except Exception as e:
                    print(f"Dubbing failed: {e}")
                    # Don't fail the whole job, just log it

            jobs[job_id]['progress'] = 100
            jobs[job_id]['status'] = 'completed'

        except Exception as e:
            jobs[job_id]['status'] = 'failed'
            jobs[job_id]['error'] = str(e)
            print(f"Job {job_id} failed: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create', methods=['POST'])
def create_video():
    data = request.json
    prompt = data.get('prompt')
    duration = data.get('duration', 'short')
    voice_id = data.get('voice_id', 'en-US-GuyNeural')
    orientation = data.get('orientation', 'landscape')
    mood = data.get('mood', 'random')
    
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        'status': 'queued',
        'progress': 0,
        'prompt': prompt
    }
    
    thread = threading.Thread(target=process_video_job, args=(job_id, prompt, duration, voice_id, orientation, mood))
    thread.start()
    
    return jsonify({'job_id': job_id})

@app.route('/status/<job_id>')
def get_status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify(job)

@app.route('/download/<job_id>')
def download_video(job_id):
    try:
        job = jobs.get(job_id)
        if not job or job['status'] != 'completed':
            return jsonify({'error': 'Video not ready'}), 400
        
        # Ensure absolute path
        abs_path = os.path.abspath(job['output_path'])
        if not os.path.exists(abs_path):
             return jsonify({'error': 'File not found on server'}), 404

        return send_file(abs_path, as_attachment=True)
    except Exception as e:
        print(f"Download Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/download/thumbnail/<job_id>')
def download_thumbnail(job_id):
    try:
        job = jobs.get(job_id)
        if not job or 'thumbnail_path' not in job:
            return jsonify({'error': 'Thumbnail not ready'}), 400
            
        abs_path = os.path.abspath(job['thumbnail_path'])
        if not os.path.exists(abs_path):
             return jsonify({'error': 'File not found'}), 404
             
        return send_file(abs_path, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/dub/<job_id>/<lang>')
def download_dub(job_id, lang):
    try:
        job = jobs.get(job_id)
        if not job or 'dubbed_versions' not in job:
            return jsonify({'error': 'Dub not found'}), 404
            
        target_path = None
        for dub in job['dubbed_versions']:
            if dub['lang'].lower() == lang.lower():
                target_path = dub['path']
                break
        
        if not target_path or not os.path.exists(target_path):
             return jsonify({'error': 'File not found'}), 404
             
        return send_file(target_path, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
