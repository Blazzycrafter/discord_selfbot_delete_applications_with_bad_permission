from PIL import Image

def unify(path):
    image = Image.open("qrcode.png")
    unify_image(image)
def unify_image(image):
    width, height = image.size
    for y in range(height):
        print("\n", end="")
        for x in range(width):
            if not image.getpixel((x, y)) == 0:
                print("░░", end="")
            else:
                print("██", end="")
