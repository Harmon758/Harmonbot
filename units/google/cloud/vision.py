
from __future__ import annotations

from typing import TYPE_CHECKING

import google.auth
from google.cloud import vision

if TYPE_CHECKING:
    from collections.abc import MutableSequence


try:
    client = vision.ImageAnnotatorClient()
except google.auth.exceptions.DefaultCredentialsError as e:
    print(f"Failed to initialize Google Cloud Vision Client: {e}")


def detect_explicit_content(image_uri: str) -> vision.SafeSearchAnnotation:
    image = vision.Image()
    image.source.image_uri = image_uri
    return client.safe_search_detection(image = image).safe_search_annotation


def detect_image_properties(
    image_uri: str
) -> MutableSequence[vision.ColorInfo]:
    image = vision.Image()
    image.source.image_uri = image_uri

    return client.image_properties(
        image = image
    ).image_properties_annotation.dominant_colors.colors


def detect_labels(image_uri: str) -> vision.EntityAnnotation:
    image = vision.Image()
    image.source.image_uri = image_uri
    return client.label_detection(image = image).label_annotations

