
from __future__ import annotations

from typing import TYPE_CHECKING

from google.cloud import vision

if TYPE_CHECKING:
    from collections.abc import MutableSequence


client: vision.ImageAnnotatorClient | None = None


def detect_explicit_content(image_uri: str) -> vision.SafeSearchAnnotation:
    global client
    if client is None:
        client = vision.ImageAnnotatorClient()
    image = vision.Image()
    image.source.image_uri = image_uri
    return client.safe_search_detection(image = image).safe_search_annotation


def detect_image_properties(
    image_uri: str
) -> MutableSequence[vision.ColorInfo]:
    global client
    if client is None:
        client = vision.ImageAnnotatorClient()
    image = vision.Image()
    image.source.image_uri = image_uri
    return client.image_properties(  # type: ignore[attribute-error]
        image = image
    ).image_properties_annotation.dominant_colors.colors


def detect_labels(image_uri: str) -> vision.EntityAnnotation:
    global client
    if client is None:
        client = vision.ImageAnnotatorClient()
    image = vision.Image()
    image.source.image_uri = image_uri
    return client.label_detection(image = image).label_annotations

