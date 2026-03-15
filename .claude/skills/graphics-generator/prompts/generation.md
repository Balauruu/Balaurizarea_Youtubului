# Graphics Generator — Generation Planning Prompt

You are planning visual parameters for code-generated graphics. For each `shotlist_type: animation` shot, plan the renderer-specific parameters.

## Context

You have:
- The shotlist with building block assignments
- The VISUAL_STYLE_GUIDE production specs for each building block
- Channel DNA for tone/mood guidance

## Per-Shot Planning

For each animation shot, determine:

### Silhouette Figure
- **figure_count**: 1 (solo), 2 (pair), or "crowd" (5-8 figures)
- **label_text**: Role label to display (e.g., "FAITH HEALER") or null
- **background_style**: "red_gradient" | "black" | "black_red_stripe"
- **glow**: true/false — whether the central figure glows

### Symbolic Icon
- **icon_type**: Brief description of the icon shape (e.g., "skull", "chalice", "vial")
- **background**: "crimson" | "black"

### Abstract Texture
- **streak_count**: 5-15 — number of dark vertical streaks
- **drip_intensity**: "light" | "medium" | "heavy"

### Glitch Stinger
- **variant**: "red_bar" | "digital_corruption"
- **intensity**: "light" | "heavy"

### Static Noise / Corruption
- **silhouette_shape**: "building" | "figure" | "none"
- **noise_density**: "medium" | "heavy"

### Retro Code Screen
- **code_lines**: 10-30 — number of code lines to render
- **glow_intensity**: "subtle" | "medium" | "bright"

### Character Profile Card
- **card_count**: 2-4 — number of profile card slots
- **names**: List of character names/roles to label

## Output Format

Plan as a JSON array of shot param objects, each with `shot_id`, `building_block`, and the relevant params above. Only include shots with `shotlist_type: animation` that route to Pillow renderers.
