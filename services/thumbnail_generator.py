import os
import random
import ffmpeg
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def generate_thumbnail(video_path, text, output_path):
    """
    Generates a thumbnail for the video.
    1. Extracts a frame from the middle of the video.
    2. Overlays the text (Title).
    """
    try:
        # 1. Probe video to get duration and dimensions
        probe = ffmpeg.probe(video_path)
        duration = float(probe['format']['duration'])
        width = int(probe['streams'][0]['width'])
        height = int(probe['streams'][0]['height'])
        
        # 2. Extract frame at 50% timestamp
        timestamp = duration / 2
        temp_frame = output_path + ".temp.png"
        
        (
            ffmpeg
            .input(video_path, ss=timestamp)
            .filter('scale', width, height)
            .output(temp_frame, vframes=1)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        
        # 3. Process with Pillow
        if os.path.exists(temp_frame):
            img = Image.open(temp_frame).convert("RGBA")
            
            # Add Dark Overlay for text readability
            overlay = Image.new('RGBA', img.size, (0, 0, 0, 100)) # Semi-transparent black
            img = Image.alpha_composite(img, overlay)
            
            draw = ImageDraw.Draw(img)
            
            # Dynamic Font Size (roughly 10% of height)
            font_size = int(height * 0.10)
            
            # Prioritize Hindi-supporting font (Mangal)
            font_path = os.path.join("static", "fonts", "mangal.ttf")
            if not os.path.exists(font_path):
                font_path = os.path.join("static", "fonts", "arial.ttf")
            
            try:
                # Try selected font, fallback to system arial if needed
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, font_size)
                else:
                    font = ImageFont.truetype("arial.ttf", font_size)
            except:
                print("Warning: Custom fonts failed, loading default.")
                font = ImageFont.load_default()
            
            # Wrap Text
            lines = []
            words = text.split()
            current_line = []
            
            # Rough char width estimate
            max_chars = 15 # nice big text
            if width < height: max_chars = 10 # Portrait
            
            for word in words:
                if len(" ".join(current_line + [word])) > max_chars:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                else:
                    current_line.append(word)
            if current_line:
                lines.append(" ".join(current_line))
                
            # Draw Text Centered
            text_y = (height - (len(lines) * font_size * 1.2)) / 2
            
            for line in lines:
                # Text Border/Shadow
                # bbox = draw.textbbox((0, 0), line, font=font)
                # text_w = bbox[2] - bbox[0]
                # text_x = (width - text_w) / 2
                
                # Simple center calculation
                draw.text((width/2, text_y), line, font=font, anchor="mm", fill="white", stroke_width=3, stroke_fill="black")
                text_y += font_size * 1.2
            
            # Save final
            img = img.convert("RGB")
            img.save(output_path, "JPEG", quality=90)
            
            # Cleanup
            os.remove(temp_frame)
            return output_path
            
    except Exception as e:
        print(f"Thumbnail generation failed: {e}")
        return None
