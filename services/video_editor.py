import ffmpeg
import os
try:
    from config import Config
except ImportError:
    from ..config import Config

def text_wrap(text, font_size, max_width):
    # Simple estimation: avg char width approx font_size/2
    params = text.split()
    lines = []
    current_line = []
    current_width = 0
    max_chars = max(1, int(max_width / (font_size / 2))) # Rough estimate
    
    for word in params:
        if len(" ".join(current_line + [word])) > max_chars:
            lines.append(" ".join(current_line))
            current_line = [word]
        else:
            current_line.append(word)
    if current_line:
        lines.append(" ".join(current_line))
    return "\n".join(lines)

def assemble_video(script_data, output_path, orientation='landscape'):
    """
    Assembles video segments using ffmpeg-python.
    script_data: List of dicts with 'image_path', 'audio_path'
    """
    input_streams = []
    
    # Target resolution
    if orientation == 'portrait':
        W, H = 1080, 1920
    else:
        W, H = 1920, 1080
    
    for segment in script_data:
        media_path = segment.get('image_path') 
        audio_path = segment.get('audio_path')
        text = segment.get('text', '')
        
        if not media_path or not audio_path:
            continue
            
        # Probe audio duration
        probe = ffmpeg.probe(audio_path)
        audio_duration = float(probe['format']['duration'])
        
        # Prepare Text Overlay
        # Escape special chars for drawtext
        # Escape \ first, then : and % and ' and "
        safe_text = text.replace("\\", "\\\\").replace(":", "\\:").replace("%", "\\%").replace("'", "").replace('"', '')
        wrapped_text = text_wrap(safe_text, 60, W - 200) # Wrap text
        
        # Verify text isn't empty
        if not wrapped_text.strip():
            print(f"Warning: Empty text for segment with audio {audio_path}")
            # Continue without text logic if needed, or just let it render empty
        
        # Handle Video Input: Input Loop -> Scale/Crop -> Fade In/Out -> Subtitles
        # Handle Video Input: Input Loop -> Scale/Crop -> Fade In/Out -> Subtitles
        # Use Mangal (Standard Hindi Font) to support Hindi/English
        font_path_arg = "static/fonts/mangal.ttf"
        
        # Verify it exists physically
        if not os.path.exists(font_path_arg):
             print(f"CRITICAL: Font not found at {font_path_arg}, trying Arial")
             font_path_arg = "static/fonts/arial.ttf"
             if not os.path.exists(font_path_arg):
                 # System fallback
                 font_path_arg = "C:/Windows/Fonts/arial.ttf"

        video_input = (
            ffmpeg
            .input(media_path, stream_loop=-1, t=audio_duration)
            .filter('scale', w=f'{W}', h=f'{H}', force_original_aspect_ratio='increase')
            .filter('crop', w=f'{W}', h=f'{H}') 
            .filter('setsar', 1, 1)
            # Transition: Fade In (0.5s) and Fade Out (0.5s)
            .filter('fade', type='in', start_time=0, duration=0.5)
            .filter('fade', type='out', start_time=audio_duration-0.5, duration=0.5)
            .filter('drawtext', 
                    text=wrapped_text, 
                    fontfile=font_path_arg, 
                    fontsize=60 if orientation=='portrait' else 50, 
                    fontcolor='white', 
                    borderw=3, 
                    bordercolor='black', 
                    x='(w-text_w)/2', 
                    y='h-h/4', 
                    box=1, 
                    boxcolor='black@0.5', 
                    boxborderw=10) 
        )
        
        audio_input = ffmpeg.input(audio_path)
        
        input_streams.append(video_input)
        input_streams.append(audio_input)
        
    # Concatenate all streams
    if not input_streams:
        raise ValueError("No input streams generated. Check script/media.")

    joined = ffmpeg.concat(*input_streams, v=1, a=1).node
    video_stream = joined[0]
    audio_stream = joined[1]
    
    # Add Background Music
    music_folder = 'static/music'
    
    # Determine specific folder based on mood
    if mood != 'random':
        specific_folder = os.path.join(music_folder, mood)
        if os.path.exists(specific_folder) and os.listdir(specific_folder):
            music_folder = specific_folder
    
    # Recursive search for MP3s
    music_files = []
    for root, dirs, files in os.walk(music_folder):
        for file in files:
            if file.lower().endswith('.mp3'):
                music_files.append(os.path.join(root, file))
    
    if music_files:
        import random
        music_path = random.choice(music_files)
        print(f"Adding background music: {music_path}")
        
        # Loop music, lower volume, mix
        bg_music = (
            ffmpeg
            .input(music_path, stream_loop=-1)
            .filter('volume', 0.1) # 10% volume
        )
        # Mix with duration='first' (length of the voiceover video)
        audio_stream = ffmpeg.filter([audio_stream, bg_music], 'amix', inputs=2, duration='first')
        
    # Add Logo Overlay (if exists)
    logo_path = os.path.join('static', 'logo.png')
    if os.path.exists(logo_path):
        logo = ffmpeg.input(logo_path)
        # Scale logo to reasonable size (e.g. 15% of width)
        logo_w = int(W * 0.15)
        logo = logo.filter('scale', logo_w, -1)
        
        # Overlay on top-right with 20px padding (W-w-20, 20)
        video_stream = ffmpeg.overlay(video_stream, logo, x=f'W-w-20', y=20)

    # Output
    out = ffmpeg.output(video_stream, audio_stream, output_path, vcodec='libx264', acodec='aac', pix_fmt='yuv420p', shortest=None)
    
    try:
        out.run(cmd=Config.FFMPEG_PATH, overwrite_output=True, capture_stderr=True)
    except ffmpeg.Error as e:
        error_log = e.stderr.decode() if e.stderr else str(e)
        print("FFmpeg Error:", error_log)
        # Write to debug log for agent to read
        with open('debug_log.txt', 'a', encoding='utf-8') as f:
            f.write(f"\n\n--- FFMPEG ERROR ---\n{error_log}\n--------------------\n")
        raise
