import requests
import os
import random
try:
    from config import Config
except ImportError:
    # Handle standalone testing if config isn't importable
    from ..config import Config

def fetch_content(query, api_key, orientation='landscape'):
    """
    Fetches a VIDEO from Pexels based on the query.
    Returns the path to the saved local file.
    """
    headers = {
        'Authorization': api_key
    }
    # Pexels orientation values: 'landscape', 'portrait', 'square'
    url = f"https://api.pexels.com/videos/search?query={query}&per_page=3&orientation={orientation}&size=medium"
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        
        videos = data.get('videos', [])
        if not videos:
            print(f"No videos found for {query}. Trying AI Image...")
            return generate_ai_image(query, orientation) 
            
        video = random.choice(videos)
        video_files = video.get('video_files', [])
        best_file = None
        
        # Target Dimensions
        target_w = 1920 if orientation == 'landscape' else 1080
        target_h = 1080 if orientation == 'landscape' else 1920
        
        # Sort by best fit
        def score_file(vf):
            w, h = vf.get('width', 0), vf.get('height', 0)
            if w == target_w and h == target_h: return 100 # Exact match
            if w >= target_w and h >= target_h: return 50 # Higher res is good
            return w # Else sort by width
            
        video_files.sort(key=score_file, reverse=True)
        if video_files:
            best_file = video_files[0]
            
        if not best_file:
            return None

        video_url = best_file['link']
        
        # Download
        # Use a timeout to avoid hanging
        video_response = requests.get(video_url, stream=True, timeout=30)
        
        # Save
        filename = f"vid_{video['id']}.mp4"
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        
        if not os.path.exists(filepath):
            with open(filepath, 'wb') as f:
                for chunk in video_response.iter_content(chunk_size=8192):
                    f.write(chunk)
        
        return filepath

    except Exception as e:
        print(f"Error fetching Pexels video for '{query}': {e}")
        # Fallback to AI Image
        return generate_ai_image(query, orientation)

def generate_ai_image(prompt, orientation='landscape'):
    """
    Generates an image using Pollinations.ai (Free Flux Model).
    """
    try:
        print(f"Generating AI Image for: {prompt}")
        
        # Dimensions
        width = 1920 if orientation == 'landscape' else 1080
        height = 1080 if orientation == 'landscape' else 1920
        
        # Clean Prompt
        seed = random.randint(1, 99999)
        url = f"https://image.pollinations.ai/prompt/{prompt}?width={width}&height={height}&model=flux&seed={seed}&nologo=true"
        
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            filename = f"ai_{seed}_{random.randint(100,999)}.jpg"
            filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            return filepath
        else:
            print(f"Pollinations Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"AI Image Gen Failed: {e}")
        return None
