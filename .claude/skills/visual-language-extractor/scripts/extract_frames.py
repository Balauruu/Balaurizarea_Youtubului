import os
import sys
import subprocess
import glob

def find_video(directory):
    extensions = ('*.mp4', '*.webm', '*.mkv', '*.avi', '*.mov')
    for ext in extensions:
        matches = glob.glob(os.path.join(directory, ext))
        if matches:
            return matches[0]
    return None

def extract_frames(directory):
    print(f"Checking directory: {directory}")
    
    frames_dir = os.path.join(directory, "frames")
    if os.path.exists(frames_dir) and len(glob.glob(os.path.join(frames_dir, "*.jpg"))) > 0:
        print(f"Frames already exist in {frames_dir}. Skipping extraction.")
        return

    video_path = find_video(directory)
    if not video_path:
        print("Error: No video file found in the directory.")
        sys.exit(1)
        
    print(f"Found video: {video_path}")
    os.makedirs(frames_dir, exist_ok=True)
    
    # ffmpeg command to extract 1 frame every 5 seconds
    # -vf fps=1/5 outputs one frame every 5 seconds
    # frame_%04d.jpg will pad the numbers with zeros (e.g., frame_0001.jpg)
    output_pattern = os.path.join(frames_dir, "frame_%04d.jpg")
    
    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-vf", "fps=1/5",
        "-q:v", "2", # High quality jpeg
        output_pattern
    ]
    
    print("Running extraction...")
    try:
        subprocess.run(cmd, check=True)
        print(f"Successfully extracted frames to {frames_dir}")
    except FileNotFoundError:
        print("Error: ffmpeg is not installed or not in the system PATH.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error extracting frames: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_frames.py <directory_path>")
        sys.exit(1)
        
    target_dir = sys.argv[1]
    extract_frames(target_dir)