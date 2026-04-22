
from google.cloud import vision


client = vision.ImageAnnotatorClient()


def detect_labels(image_uri: str) -> vision.EntityAnnotation:
    image = vision.Image()
    image.source.image_uri = image_uri
    return client.label_detection(image = image).label_annotations

