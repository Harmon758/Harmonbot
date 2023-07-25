
import os


def create_folder(folder: str) -> None:
    if not os.path.exists(folder):
        os.makedirs(folder)

