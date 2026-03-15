"""ComfyUI workflow templates and prompt builder.

Each template returns a ComfyUI API-format dict (nodes keyed by string IDs,
each with class_type and inputs). Uses the Z-image-turbo checkpoint for
fast generation.

Prompt builder composes generation prompts from shot context dicts using
narrative_context, visual_need, and building_block fields.
"""

from typing import Any

# -- Constants ---------------------------------------------------------------

CHECKPOINT = "z-image-turbo.safetensors"
DEFAULT_RESOLUTION = (1920, 1080)
KSAMPLER_DEFAULTS = {
    "seed": 42,
    "steps": 6,
    "cfg": 1.8,
    "sampler_name": "euler_ancestral",
    "scheduler": "normal",
    "denoise": 1.0,
}

# Style modifiers per building block (from S03 research classification table)
STYLE_MODIFIERS: dict[str, str] = {
    "Concept Diagram": (
        "dark background, profile head silhouette with concentric internal shapes, "
        "subtle glow, concept diagram, flat graphic style, dark mystery documentary"
    ),
    "Ritual Illustration": (
        "black background, stylized flat neon line art, ritual scene, "
        "abstract symbolic, dark mystery documentary"
    ),
    "Glitch Icon": (
        "deep blue-purple gradient, stylized icon, heavy chromatic aberration, "
        "RGB split, dot-matrix LED, dark mystery documentary"
    ),
    "Data Moshing Montage": (
        "black background, collage distorted video fragments, "
        "horizontal red scanline bars, digital corruption, "
        "datamoshing aesthetic, dark mystery documentary"
    ),
}

# The 4 ComfyUI building block names
COMFYUI_BLOCKS = list(STYLE_MODIFIERS.keys())


# -- Prompt Builder ----------------------------------------------------------

def build_prompt(shot: dict) -> str:
    """Compose a generation prompt from shot context fields.

    Extracts narrative_context, visual_need, and building_block to build
    a prompt string with appropriate style modifiers.

    Args:
        shot: A shot dict from shotlist.json with at least building_block.

    Returns:
        A prompt string suitable for ComfyUI text encoding.
    """
    bb = shot.get("building_block", "")
    narrative = shot.get("narrative_context", "")
    visual_need = shot.get("visual_need", "")

    style = STYLE_MODIFIERS.get(bb, "dark mystery documentary style")

    parts = []
    if visual_need:
        parts.append(visual_need)
    if narrative:
        parts.append(narrative)
    parts.append(style)

    return ", ".join(parts)


# -- Shared Nodes ------------------------------------------------------------

def _checkpoint_node(node_id: str = "1") -> tuple[str, dict]:
    """CheckpointLoaderSimple node."""
    return node_id, {
        "class_type": "CheckpointLoaderSimple",
        "inputs": {
            "ckpt_name": CHECKPOINT,
        },
    }


def _empty_latent(
    width: int,
    height: int,
    node_id: str = "2",
    batch_size: int = 1,
) -> tuple[str, dict]:
    """EmptyLatentImage node."""
    return node_id, {
        "class_type": "EmptyLatentImage",
        "inputs": {
            "width": width,
            "height": height,
            "batch_size": batch_size,
        },
    }


def _clip_text_encode(
    text: str,
    clip_source: list,
    node_id: str = "3",
) -> tuple[str, dict]:
    """CLIPTextEncode node (positive prompt)."""
    return node_id, {
        "class_type": "CLIPTextEncode",
        "inputs": {
            "text": text,
            "clip": clip_source,
        },
    }


def _negative_prompt(
    clip_source: list,
    node_id: str = "4",
) -> tuple[str, dict]:
    """CLIPTextEncode node for negative prompt."""
    return node_id, {
        "class_type": "CLIPTextEncode",
        "inputs": {
            "text": (
                "blurry, low quality, watermark, text overlay, "
                "bright colors, cartoon, anime, photorealistic face"
            ),
            "clip": clip_source,
        },
    }


def _ksampler(
    model_source: list,
    positive_source: list,
    negative_source: list,
    latent_source: list,
    node_id: str = "5",
    **overrides: Any,
) -> tuple[str, dict]:
    """KSampler node."""
    inputs = {
        **KSAMPLER_DEFAULTS,
        "model": model_source,
        "positive": positive_source,
        "negative": negative_source,
        "latent_image": latent_source,
        **overrides,
    }
    return node_id, {
        "class_type": "KSampler",
        "inputs": inputs,
    }


def _vae_decode(
    samples_source: list,
    vae_source: list,
    node_id: str = "6",
) -> tuple[str, dict]:
    """VAEDecode node."""
    return node_id, {
        "class_type": "VAEDecode",
        "inputs": {
            "samples": samples_source,
            "vae": vae_source,
        },
    }


def _save_image(
    images_source: list,
    filename_prefix: str = "comfyui_output",
    node_id: str = "7",
) -> tuple[str, dict]:
    """SaveImage node."""
    return node_id, {
        "class_type": "SaveImage",
        "inputs": {
            "images": images_source,
            "filename_prefix": filename_prefix,
        },
    }


def _build_standard_workflow(
    prompt_text: str,
    resolution: tuple[int, int],
    filename_prefix: str = "comfyui_output",
) -> dict[str, dict]:
    """Assemble the standard txt2img pipeline used by all 4 templates."""
    width, height = resolution
    nodes = dict([
        _checkpoint_node("1"),
        _empty_latent(width, height, "2"),
        _clip_text_encode(prompt_text, ["1", 1], "3"),
        _negative_prompt(["1", 1], "4"),
        _ksampler(["1", 0], ["3", 0], ["4", 0], ["2", 0], "5"),
        _vae_decode(["5", 0], ["1", 2], "6"),
        _save_image(["6", 0], filename_prefix, "7"),
    ])
    return nodes


# -- Workflow Templates ------------------------------------------------------

def concept_diagram(
    prompt_text: str,
    resolution: tuple[int, int] = DEFAULT_RESOLUTION,
) -> dict[str, dict]:
    """Workflow template for Concept Diagram building block.

    Generates profile head silhouettes with internal conceptual layers.
    """
    return _build_standard_workflow(prompt_text, resolution, "concept_diagram")


def ritual_illustration(
    prompt_text: str,
    resolution: tuple[int, int] = DEFAULT_RESOLUTION,
) -> dict[str, dict]:
    """Workflow template for Ritual Illustration building block.

    Generates stylized neon line art of cultural/religious scenes.
    """
    return _build_standard_workflow(prompt_text, resolution, "ritual_illustration")


def glitch_icon(
    prompt_text: str,
    resolution: tuple[int, int] = DEFAULT_RESOLUTION,
) -> dict[str, dict]:
    """Workflow template for Glitch Icon building block.

    Generates organic serpentine forms with chromatic aberration.
    """
    return _build_standard_workflow(prompt_text, resolution, "glitch_icon")


def data_moshing(
    prompt_text: str,
    resolution: tuple[int, int] = DEFAULT_RESOLUTION,
) -> dict[str, dict]:
    """Workflow template for Data Moshing Montage building block.

    Generates collage of distorted video fragments.
    """
    return _build_standard_workflow(prompt_text, resolution, "data_moshing")


# Template registry: building block name → template function
WORKFLOW_TEMPLATES: dict[str, callable] = {
    "Concept Diagram": concept_diagram,
    "Ritual Illustration": ritual_illustration,
    "Glitch Icon": glitch_icon,
    "Data Moshing Montage": data_moshing,
}
