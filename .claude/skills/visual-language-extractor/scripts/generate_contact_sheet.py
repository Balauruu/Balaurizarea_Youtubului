import os
import sys
import glob
from PIL import Image

def create_contact_sheets(frames_dir, cols=5, rows=5):
    # Find all frames
    frame_files = sorted(glob.glob(os.path.join(frames_dir, "*.jpg")) + glob.glob(os.path.join(frames_dir, "*.png")))
    if not frame_files:
        print(f"No frames found in {frames_dir}")
        return

    output_dir = os.path.join(os.path.dirname(frames_dir), "contact_sheets")
    os.makedirs(output_dir, exist_ok=True)
    
    # Check if contact sheets already exist
    existing_sheets = glob.glob(os.path.join(output_dir, "*.jpg"))
    if existing_sheets:
        print(f"Contact sheets already exist in {output_dir}. Skipping generation.")
        return
    
    frames_per_sheet = cols * rows
    sheet_count = 0
    
    for i in range(0, len(frame_files), frames_per_sheet):
        batch = frame_files[i:i + frames_per_sheet]
        
        # Open first image to get dimensions
        first_img = Image.open(batch[0])
        first_img.thumbnail((320, 320)) # scale down to save memory
        w, h = first_img.size
        
        sheet_w = cols * w
        sheet_h = rows * h
        sheet = Image.new('RGB', (sheet_w, sheet_h), (0, 0, 0))
        
        for idx, file in enumerate(batch):
            img = Image.open(file)
            img.thumbnail((w, h))
            
            x = (idx % cols) * w
            y = (idx // cols) * h
            
            sheet.paste(img, (x, y))
            
        sheet_path = os.path.join(output_dir, f"contact_sheet_{sheet_count:03d}.jpg")
        sheet.save(sheet_path, quality=85)
        print(f"Saved {sheet_path}")
        sheet_count += 1
        
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_contact_sheet.py <frames_directory>")
        sys.exit(1)
        
    create_contact_sheets(sys.argv[1])
