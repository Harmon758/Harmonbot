
from __future__ import annotations

from typing import TYPE_CHECKING

from google.cloud import vision

if TYPE_CHECKING:
    from collections.abc import MutableSequence


client = vision.ImageAnnotatorClient()


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

