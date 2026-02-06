import requests
import os

def download_sample_music():
    # Direct link to a "Happy" royalty free track (Pixabay or similar direct stable link)
    # Using a known stable copyright-free sample URL
    url = "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3?filename=lofi-study-112191.mp3"
    
    music_dir = os.path.join("static", "music")
    if not os.path.exists(music_dir):
        os.makedirs(music_dir)
        
    filepath = os.path.join(music_dir, "lofi_study.mp3")
    
    print(f"Downloading sample music to {filepath}...")
    try:
        response = requests.get(url)
        with open(filepath, 'wb') as f:
            f.write(response.content)
        print("Download successful!")
    except Exception as e:
        print(f"Failed to download music: {e}")

if __name__ == "__main__":
    download_sample_music()
