---
name: visual-language-extractor
description: Analyzes a video or a folder of extracted frames to create a definitive implementation guide for recreating its visual style. Generates a new VISUAL_LANGUAGE.md file detailing the color palette, layered asset hierarchy, typography, and global filters, using the project's standard template structure. Use when asked to extract, document, or reverse-engineer the visual language of a new video.
---
# Visual Language Extractor Skill

This skill allows you to extract screenshots from a video every 5 seconds and generate a comprehensive `VISUAL_LANGUAGE.md` implementation guide that serves as a blueprint for recreating the video's aesthetic programmatically (e.g., using Remotion).

## Process

1. **Check Directory Contents**: Examine the provided directory path.
   - If there is a `frames/` subdirectory containing `.jpg` or `.png` files, skip extraction and proceed to **Analysis**.
   - If there are no extracted frames but there is a video file, proceed to **Extraction**.

2. **Extraction**:
   - Run the included extraction script: `python scripts/extract_frames.py <directory_path>`.
   - The script will automatically find the video in the directory and create a `frames/` folder, saving a frame every 5 seconds.
   - Once extraction is complete, proceed to **Analysis**.

3. **Contact Sheet Generation**:
   - Run the included contact sheet script: `python scripts/generate_contact_sheet.py <directory_path>/frames`.
   - This script creates a `contact_sheets/` directory containing large montages (grids) of the extracted frames. This compresses the visual timeline into a few images, preventing you from losing details or hallucinating scene transitions.
   - Wait for the script to finish successfully.

4. **Analysis (No Subagents needed)**:
   - Use your file reading tools to view ALL the `.jpg` images inside the `contact_sheets/` directory.
   - Because these images are collages of the entire video in chronological order, you can easily observe the progression of scenes, exact transitions between them, and recurring motifs (like specific silhouettes or overlays).
   - Analyze the visual language comprehensively, paying close attention to:
     - Color palettes and global filters.
     - Specific, repeated elements (e.g., silhouettes, maps, types of archival footage).
     - Layered compositions (what is in the background, midground, foreground).
     - Exact transition techniques between scenes (as visible from one frame block to the next in the contact sheet).

5. **Generation**:
   - Read the reference template: `references/VISUAL_LANGUAGE_TEMPLATE.md` to understand the required structure.
   - This template is designed as a **guide to recreate the visual style**, not merely an observation or analysis. It focuses heavily on a Layered Asset Hierarchy.
   - Create a **new** file named `VISUAL_LANGUAGE.md` in the target directory (or a specified output directory).
   - This new file must strictly follow the headings and tables structure of the template. Fill it exclusively with actionable, generalized rules, colors, layer structures (Backgrounds, Main Elements, Overlays, Typography), and constraints you discovered. Focus on how a developer would programmatically implement this style.