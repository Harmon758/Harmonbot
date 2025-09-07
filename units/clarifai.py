
import logging
import os

from clarifai.client.model import Model  # type: ignore[import-untyped]
from pydantic import BaseModel


# Remove root logger handler added by clarifai
# https://github.com/Clarifai/clarifai-python/issues/220
def remove_root_logger_handlers():
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        root_logger.removeHandler(handler)

remove_root_logger_handlers()


# APP_ID = os.getenv("CLARIFAI_APP_ID")
PAT = os.getenv("CLARIFAI_PAT")
# USER_ID = os.getenv("CLARIFAI_USER_ID")


class Color(BaseModel):
    raw_hex: str
    w3c_hex: str
    w3c_name: str
    value: float


class Concept(BaseModel):
    id: str
    name: str
    value: float


def image_color(url: str) -> list[Color]:
    if not PAT:
        raise RuntimeError("Unable to get Clarifai Personal Access Token")

    model = Model(
        app_id = "main", pat = PAT, user_id = "clarifai",
        model_id = "color-recognition"
    )
    response = model.predict_by_url(url, input_type = "image")
    remove_root_logger_handlers()
    return [
        Color(
            raw_hex = color.raw_hex,
            w3c_hex = color.w3c.hex,
            w3c_name = color.w3c.name,
            value = color.value
        )
        for color in response.outputs[0].data.colors
    ]


def image_nsfw(url: str) -> float:
    if not PAT:
        raise RuntimeError("Unable to get Clarifai Personal Access Token")

    model = Model(
        app_id = "main", pat = PAT, user_id = "clarifai",
        model_id = "nsfw-recognition"
    )
    response = model.predict_by_url(url, input_type = "image")
    remove_root_logger_handlers()
    for concept in response.outputs[0].data.concepts:
        if concept.name == "nsfw":
            return concept.value

    raise RuntimeError(
        "\"nsfw\" concept not found "
        "in Clarifai nsfw-recognition model prediction response"
    )


def image_recognition(url: str) -> list[Concept]:
    if not PAT:
        raise RuntimeError("Unable to get Clarifai Personal Access Token")

    model = Model(
        app_id = "main", pat = PAT, user_id = "clarifai",
        model_id = "general-image-recognition"
    )
    response = model.predict_by_url(url, input_type = "image")
    remove_root_logger_handlers()
    return [
        Concept(id = concept.id, name = concept.name, value = concept.value)
        for concept in response.outputs[0].data.concepts
    ]

