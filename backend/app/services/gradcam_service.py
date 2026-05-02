"""
MedLens Grad-CAM Service — Visual explainability for CNN predictions.

Generates heatmap overlays showing which regions of the medical image
influenced the AI classification decision.
"""

import os
import uuid
import numpy as np
import torch
from PIL import Image
from torchvision import transforms
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.image import show_cam_on_image
from app.services.ml_service import _load_model, _get_target_layer, preprocess
from app.config import settings


def generate_gradcam(image_path: str, module: str) -> str:
    """
    Generate a Grad-CAM heatmap overlay for a medical image.

    Args:
        image_path: Path to the input medical image
        module: Diagnostic module (chest_xray, skin_lesion, retinal)

    Returns:
        Path to the saved Grad-CAM overlay image
    """
    model = _load_model(module)
    target_layer = _get_target_layer(model, module)

    # Load and prepare image
    img_pil = Image.open(image_path).convert("RGB")
    img_resized = img_pil.resize((224, 224))
    img_array = np.array(img_resized) / 255.0  # Normalize to [0, 1]

    input_tensor = preprocess(img_pil).unsqueeze(0)

    # Generate Grad-CAM
    cam = GradCAM(model=model, target_layers=[target_layer])
    grayscale_cam = cam(input_tensor=input_tensor, targets=None)
    grayscale_cam = grayscale_cam[0, :]

    # Create overlay
    visualization = show_cam_on_image(
        img_array.astype(np.float32),
        grayscale_cam,
        use_rgb=True,
        colormap=2,  # JET colormap — standard for medical imaging
    )

    # Save
    filename = f"gradcam_{uuid.uuid4().hex[:12]}.png"
    output_path = os.path.join(settings.GRADCAM_DIR, filename)
    Image.fromarray(visualization).save(output_path)

    return filename
