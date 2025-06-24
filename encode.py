from PIL import Image
import math
import numpy as np

encode_characters = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz#$%*+,-.:;=?@[]^_{|}~"

def encode83(value, length):
    result = ""
    for i in range(length):
        digit = (value // (83 ** (length - i - 1))) % 83
        result += encode_characters[digit]
    return result

def sRGB_to_linear(value):
    v = value / 255.0
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

def linear_to_sRGB(value):
    v = max(0.0, min(1.0, value))
    if v <= 0.0031308:
        return int(v * 12.92 * 255 + 0.5)
    return int((1.055 * (v ** (1 / 2.4)) - 0.055) * 255 + 0.5)

def sign_pow(value, exp):
    return math.copysign(abs(value) ** exp, value)

def multiply_basis_function(pixels, width, height, bytes_per_row, bytes_per_pixel, pixel_offset, basis_func):
    r = g = b = 0.0
    for y in range(height):
        for x in range(width):
            idx = y * bytes_per_row + x * bytes_per_pixel + pixel_offset
            basis = basis_func(x, y)
            r += basis * sRGB_to_linear(pixels[idx])
            g += basis * sRGB_to_linear(pixels[idx + 1])
            b += basis * sRGB_to_linear(pixels[idx + 2])
    scale = 1.0 / (width * height)
    return (r * scale, g * scale, b * scale)

def encode_dc(value):
    r = linear_to_sRGB(value[0])
    g = linear_to_sRGB(value[1])
    b = linear_to_sRGB(value[2])
    return (r << 16) + (g << 8) + b

def encode_ac(value, max_value):
    quant_r = int(max(0, min(18, math.floor(sign_pow(value[0] / max_value, 0.5) * 9 + 9.5))))
    quant_g = int(max(0, min(18, math.floor(sign_pow(value[1] / max_value, 0.5) * 9 + 9.5))))
    quant_b = int(max(0, min(18, math.floor(sign_pow(value[2] / max_value, 0.5) * 9 + 9.5))))
    return quant_r * 19 * 19 + quant_g * 19 + quant_b

def blur_hash(image: Image.Image, components=(4, 3)):
    image = image.convert("RGBA")
    width, height = image.size
    pixels = np.array(image).astype(np.uint8).flatten()
    bytes_per_pixel = 4
    bytes_per_row = width * bytes_per_pixel
    pixel_offset = 0

    factors = []
    for y in range(components[1]):
        for x in range(components[0]):
            normalisation = 1 if (x == 0 and y == 0) else 2
            basis_func = lambda i, j: normalisation * math.cos(math.pi * x * i / width) * math.cos(math.pi * y * j / height)
            factor = multiply_basis_function(pixels, width, height, bytes_per_row, bytes_per_pixel, pixel_offset, basis_func)
            factors.append(factor)

    dc = factors[0]
    ac = factors[1:]

    hash_str = ""
    size_flag = (components[0] - 1) + (components[1] - 1) * 9
    hash_str += encode83(size_flag, 1)

    if ac:
        max_value = max(max(abs(c) for c in f) for f in ac)
        quant_max = int(max(0, min(82, math.floor(max_value * 166 - 0.5))))
        max_value_encoded = (quant_max + 1) / 166
        hash_str += encode83(quant_max, 1)
    else:
        max_value_encoded = 1
        hash_str += encode83(0, 1)

    hash_str += encode83(encode_dc(dc), 4)

    for f in ac:
        hash_str += encode83(encode_ac(f, max_value_encoded), 2)

    return {
        "blurhash": hash_str,
        "width": width,
        "height": height
    }

if __name__ == "__main__":
    img = Image.open("./static/test_1.png")
    print(blur_hash(img, components=(4, 3)))