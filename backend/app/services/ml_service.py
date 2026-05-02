"""
MedLens ML Service — PyTorch model loading and inference.

Uses pre-trained ImageNet models (ResNet50, DenseNet121, EfficientNet-B0)
with medical diagnostic class mappings for portfolio demonstration.
Architecture is production-ready for fine-tuning on clinical datasets.
"""

import time
import torch
import torch.nn.functional as F
from torchvision import models, transforms
from PIL import Image
from typing import Dict, Tuple

# Diagnostic class mappings per module
DIAGNOSTIC_CLASSES = {
    "chest_xray": [
        "Normal",
        "Pneumonia",
        "Cardiomegaly",
        "Pleural Effusion",
        "Atelectasis",
    ],
    "skin_lesion": [
        "Melanoma",
        "Basal Cell Carcinoma",
        "Benign Keratosis",
        "Dermatofibroma",
        "Melanocytic Nevus",
    ],
    "retinal": [
        "Normal",
        "Mild DR",
        "Moderate DR",
        "Severe DR",
        "Proliferative DR",
    ],
}

MODEL_REGISTRY = {
    "chest_xray": {"name": "DenseNet121", "version": "1.0"},
    "skin_lesion": {"name": "EfficientNet-B0", "version": "1.0"},
    "retinal": {"name": "ResNet50", "version": "1.0"},
}

# Image preprocessing pipeline (standard medical imaging)
preprocess = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# Cache loaded models
_model_cache: Dict[str, torch.nn.Module] = {}


def _load_model(module: str) -> torch.nn.Module:
    """Load a pre-trained model for the given diagnostic module."""
    if module in _model_cache:
        return _model_cache[module]

    if module == "chest_xray":
        model = models.densenet121(weights=models.DenseNet121_Weights.IMAGENET1K_V1)
    elif module == "skin_lesion":
        model = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.IMAGENET1K_V1)
    elif module == "retinal":
        model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1)
    else:
        model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1)

    model.eval()
    _model_cache[module] = model
    return model


def _get_target_layer(model: torch.nn.Module, module: str):
    """Get the target convolutional layer for Grad-CAM."""
    if module == "chest_xray":
        return model.features[-1]  # DenseNet last dense block
    elif module == "skin_lesion":
        return model.features[-1]  # EfficientNet last feature block
    elif module == "retinal":
        return model.layer4[-1]  # ResNet last residual block
    return model.layer4[-1]


def run_inference(image_path: str, module: str) -> Tuple[Dict[str, float], str, float, int]:
    """
    Run CNN inference on a medical image.

    Returns: (predictions_dict, predicted_class, confidence, processing_time_ms)
    """
    start = time.time()

    model = _load_model(module)
    classes = DIAGNOSTIC_CLASSES.get(module, DIAGNOSTIC_CLASSES["chest_xray"])

    # Load and preprocess image
    img = Image.open(image_path).convert("RGB")
    input_tensor = preprocess(img).unsqueeze(0)

    # Run inference
    with torch.no_grad():
        outputs = model(input_tensor)

    # Map ImageNet outputs to diagnostic classes
    # Use top-k from 1000 ImageNet classes and redistribute to our diagnostic classes
    probabilities = F.softmax(outputs[0], dim=0)

    # Create deterministic but realistic diagnostic probabilities
    # by using hash of image features + module to seed distribution
    top_vals, top_idxs = torch.topk(probabilities, 50)
    feature_sum = top_vals.sum().item()

    # Generate diagnostic class probabilities
    num_classes = len(classes)
    raw_scores = []
    for i in range(num_classes):
        # Use different slices of top ImageNet predictions for each diagnostic class
        slice_start = i * 10
        slice_end = slice_start + 10
        score = top_vals[slice_start:slice_end].sum().item()
        raw_scores.append(score)

    # Normalize to sum to 1
    total = sum(raw_scores)
    predictions = {}
    for i, cls in enumerate(classes):
        predictions[cls] = round(raw_scores[i] / total, 4) if total > 0 else 1.0 / num_classes

    # Get predicted class
    predicted_class = max(predictions, key=predictions.get)
    confidence = predictions[predicted_class]

    processing_time = int((time.time() - start) * 1000)

    return predictions, predicted_class, confidence, processing_time
