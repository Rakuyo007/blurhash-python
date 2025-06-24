from PIL import Image

from decode import decode_blurhash
from encode import blur_hash

if __name__ == "__main__":
    img_path = "./static/0002.jpg"
    img = Image.open(img_path)
    blurhash_result = blur_hash(img, components=(4, 3))
    print("BlurHash:", blurhash_result["blurhash"])
    decoded_image = decode_blurhash(blurhash_result["blurhash"], blurhash_result["width"], blurhash_result["height"])
    # decoded_image.show()  # 显示解码后的图像
    decoded_image.save(f"{img_path}".replace(".jpg", "_blurhash.jpg"))  # 保存解码后的图像
