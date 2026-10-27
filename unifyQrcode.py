from PIL import Image


def unify(path: str) -> None:
    unify_image(Image.open(path))


def _is_dark(pixel) -> bool:
    if isinstance(pixel, int):
        return pixel < 128
    return sum(pixel[:3]) / 3 < 128


def unify_image(image: Image.Image) -> None:
    width, height = image.size
    for y in range(height):
        row = []
        for x in range(width):
            row.append("██" if _is_dark(image.getpixel((x, y))) else "  ")
        print("".join(row))
