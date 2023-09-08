from asyncio import run

import cv2
from numpy import asarray

from get_html_async import SITE, WebConnection


class ImageEdit:
    @staticmethod
    def thumbnail_crop(imagefile: bytes, path: str) -> None:
        # img = cv2.imread(filename)
        img = asarray(bytearray(imagefile), dtype="uint8")
        img = cv2.imdecode(img, cv2.IMREAD_COLOR)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)

        (T, thresh) = cv2.threshold(blurred, 250, 255, cv2.THRESH_BINARY_INV)

        x, y, w, h = cv2.boundingRect(thresh)

        delta = int((w - h) / 2)

        if delta >= 0:  # landscape - w-bound
            Y1 = max(y - delta - int(0.005 * w), 0)
            Y2 = Y1 + w + int(0.01 * w)
            X1 = max(x - int(0.005 * w), 0)
            X2 = x + int(1.005 * w)
        else:  # portrait - h-bound
            Y1 = max(y - int(0.005 * h), 0)
            Y2 = y + int(1.005 * h)
            X1 = max(x + delta - int(0.005 * h), 0)
            X2 = X1 + h + int(0.01 * h)
        
        crop = img[Y1:Y2, X1:X2]

        cv2.imwrite(path, crop)

        # # Display the result
        # cv2.imshow("Result", crop)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()


if __name__ == "__main__":
    from configparser import ConfigParser

    config = ConfigParser()
    config.read("config.ini")

    async def main():
        async with WebConnection(
            config["Login"]["login_url"], dict(config["Login_data"])
        ) as s:
            while True:
                url = input("Adres obrazka: ")
                path = "./miniatury/" + url.split("/")[-1]
                print(path)
                try:
                    imagefile = await s.get_image_binary(url)
                    ImageEdit.thumbnail_crop(imagefile, path=path)
                except Exception as X:
                    print(f"Błąd: {X}")

    run(main())
