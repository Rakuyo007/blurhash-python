from PIL import Image
import math
import numpy as np

# 编码/解码字典
encode_characters = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz#$%*+,-.:;=?@[]^_{|}~"
decode_characters = {char: i for i, char in enumerate(encode_characters)}

# decode83
def decode83(string):
    value = 0
    for c in string:
        value = value * 83 + decode_characters[c]
    return value

# sRGB => Linear
def sRGB_to_linear(value):
    v = value / 255.0
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

# Linear => sRGB
def linear_to_sRGB(value):
    v = max(0.0, min(1.0, value))
    if v <= 0.0031308:
        return int(v * 12.92 * 255 + 0.5)
    return int((1.055 * (v ** (1 / 2.4)) - 0.055) * 255 + 0.5)

# signPow
def sign_pow(value, exp):
    return math.copysign(abs(value) ** exp, value)

# decodeDC
def decode_dc(value):
    r = value >> 16
    g = (value >> 8) & 255
    b = value & 255
    return (sRGB_to_linear(r), sRGB_to_linear(g), sRGB_to_linear(b))

# decodeAC
def decode_ac(value, maximum_value):
    quant_r = value // (19 * 19)
    quant_g = (value // 19) % 19
    quant_b = value % 19

    r = sign_pow((quant_r - 9) / 9.0, 2.0) * maximum_value
    g = sign_pow((quant_g - 9) / 9.0, 2.0) * maximum_value
    b = sign_pow((quant_b - 9) / 9.0, 2.0) * maximum_value
    return (r, g, b)

# 主函数：解码 blurhash 字符串为 Pillow Image
def decode_blurhash(blurhash: str, width: int, height: int, punch: float = 1.0) -> Image.Image:
    if len(blurhash) < 6:
        raise ValueError("BlurHash too short")

    size_flag = decode83(blurhash[0])
    num_y = (size_flag // 9) + 1
    num_x = (size_flag % 9) + 1

    quant_max = decode83(blurhash[1])
    max_value = (quant_max + 1) / 166.0

    expected_len = 4 + 2 * num_x * num_y
    if len(blurhash) != expected_len:
        raise ValueError("Invalid blurhash length")

    colors = []
    for i in range(num_x * num_y):
        if i == 0:
            value = decode83(blurhash[2:6])
            colors.append(decode_dc(value))
        else:
            start = 4 + i * 2
            value = decode83(blurhash[start:start + 2])
            colors.append(decode_ac(value, max_value * punch))

    img_array = np.zeros((height, width, 3), dtype=np.uint8)

    for y in range(height):
        for x in range(width):
            r = g = b = 0.0
            for j in range(num_y):
                for i in range(num_x):
                    basis = math.cos(math.pi * x * i / width) * math.cos(math.pi * y * j / height)
                    color = colors[i + j * num_x]
                    r += color[0] * basis
                    g += color[1] * basis
                    b += color[2] * basis
            img_array[y, x, 0] = linear_to_sRGB(r)
            img_array[y, x, 1] = linear_to_sRGB(g)
            img_array[y, x, 2] = linear_to_sRGB(b)

    return Image.fromarray(img_array, mode='RGB')

if __name__ == "__main__":
    blurhash = "LvI#oo00WCV@oJofaxV@kCRjayxu"  # 示例字符串
    img = decode_blurhash(blurhash, width=1792, height=1024, punch=1.0)
    img.show()  # 显示图像
    # img.save("decoded_image.png")  # 保存图像