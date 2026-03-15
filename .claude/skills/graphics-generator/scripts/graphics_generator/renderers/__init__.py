"""Renderer registry — maps building block names to renderer functions.

Each renderer signature: render(shot: dict, output_dir: Path) -> Path
Code-gen blocks route to Pillow renderers.
ComfyUI blocks route to render_comfyui dispatcher (requires a client instance).
"""
from pathlib import Path
from typing import Optional

from graphics_generator.renderers.silhouette import render as render_silhouette
from graphics_generator.renderers.icon import render as render_icon
from graphics_generator.renderers.texture import render as render_texture
from graphics_generator.renderers.glitch import render as render_glitch
from graphics_generator.renderers.noise import render as render_noise
from graphics_generator.renderers.code_screen import render as render_code_screen
from graphics_generator.renderers.profile_card import render as render_profile_card


# Building block name → renderer function (code-gen / Pillow)
RENDERER_REGISTRY: dict[str, callable] = {
    "Silhouette Figure": render_silhouette,
    "Symbolic Icon": render_icon,
    "Abstract Texture": render_texture,
    "Glitch Stinger": render_glitch,
    "Static Noise / Corruption": render_noise,
    "Static Noise": render_noise,
    "Retro Code Screen": render_code_screen,
    "Character Profile Card": render_profile_card,
}

# Building blocks that require ComfyUI (not in RENDERER_REGISTRY)
COMFYUI_BLOCKS: set[str] = {
    "Concept Diagram",
    "Ritual Illustration",
    "Glitch Icon",
    "Data Moshing Montage",
}


def is_comfyui_block(building_block: str) -> bool:
    """Check if a building block requires ComfyUI for rendering."""
    return building_block in COMFYUI_BLOCKS


def render_comfyui(
    shot: dict,
    output_dir: Path,
    client: "ComfyUIClient",  # noqa: F821 — forward ref to avoid circular import
) -> Path:
    """Dispatch a ComfyUI building block through the workflow pipeline.

    1. Build prompt from shot context
    2. Select workflow template for the building block
    3. Queue prompt on ComfyUI server
    4. Poll until complete
    5. Download the generated image

    Args:
        shot: Shot dict from shotlist.json.
        output_dir: Directory to save the generated image.
        client: An initialized ComfyUIClient instance.

    Returns:
        Path to the downloaded image file.

    Raises:
        ComfyUIUnavailableError: If ComfyUI is unreachable.
        ValueError: If building block has no workflow template.
    """
    import sys

    from graphics_generator.comfyui.workflows import (
        WORKFLOW_TEMPLATES,
        build_prompt,
    )

    bb = shot.get("building_block", "")
    shot_id = shot.get("id", "???")

    template_fn = WORKFLOW_TEMPLATES.get(bb)
    if template_fn is None:
        raise ValueError(
            f"No ComfyUI workflow template for building block '{bb}' "
            f"(shot {shot_id})"
        )

    # Build prompt and workflow
    prompt_text = build_prompt(shot)
    workflow = template_fn(prompt_text)

    print(f"  Queuing ComfyUI prompt for {shot_id} ({bb})...", file=sys.stderr)

    # Queue → Poll → Download
    prompt_id = client.queue_prompt(workflow)
    print(f"  Prompt {prompt_id} queued, polling...", file=sys.stderr)

    outputs = client.poll_history(prompt_id)

    # Find the SaveImage output node
    image_info: Optional[dict] = None
    for _node_id, node_output in outputs.items():
        if "images" in node_output:
            for img in node_output["images"]:
                image_info = img
                break
            if image_info:
                break

    if image_info is None:
        raise RuntimeError(
            f"ComfyUI prompt {prompt_id} completed but no images found "
            f"in outputs (shot {shot_id})"
        )

    filename = image_info["filename"]
    subfolder = image_info.get("subfolder", "")

    result_path = client.download_image(filename, subfolder, output_dir)
    print(f"  Downloaded: {result_path.name}", file=sys.stderr)
    return result_path
