# PE-Core-L14-336 Usage Reference

## Model Loading

```python
import sys
sys.path.insert(0, "C:/Users/iorda/repos/perception_models")
import core.vision_encoder.pe as pe
import core.vision_encoder.transforms as transforms

model = pe.CLIP.from_config("PE-Core-L14-336", pretrained=True)
model = model.to("cuda").eval()

tokenizer = transforms.get_text_tokenizer(model.context_length)
preprocess = transforms.get_image_transform(model.image_size)
```

Note: The repo is cloned to `C:/Users/iorda/repos/perception_models` and installed in editable mode in the conda env. The `from embed import load_model` function in the scripts wraps this.

## Image Encoding

```python
from PIL import Image
import torch

img = preprocess(Image.open("frame.jpg"))
batch = img.unsqueeze(0).to("cuda")

with torch.no_grad(), torch.amp.autocast("cuda"):
    emb = model.encode_image(batch)
    emb = emb / emb.norm(dim=-1, keepdim=True)
```

## Text Encoding

```python
tokens = tokenizer(["a photo of a cathedral", "cartoon character"])
if isinstance(tokens, dict):
    tokens = {k: v.to("cuda") for k, v in tokens.items()}
else:
    tokens = tokens.to("cuda")

with torch.no_grad(), torch.amp.autocast("cuda"):
    emb = model.encode_text(tokens)
    emb = emb / emb.norm(dim=-1, keepdim=True)
```

## Cosine Similarity

After L2 normalization, cosine similarity = dot product:

```python
scores = image_emb @ text_emb.T  # [N_images, N_texts]
```

## Input Resolution

PE-Core-L14-336 expects 336x336 pixel input. The `preprocess` transform handles resizing and normalization.

## VRAM Usage

- Model weights: ~2 GB
- Batch of 64 frames at 336x336: ~1.5 GB
- Total peak: ~3.5 GB (well within 8 GB RTX 4070)

## Conda Environment

```
C:/Users/iorda/miniconda3/envs/perception-models/python.exe
```
