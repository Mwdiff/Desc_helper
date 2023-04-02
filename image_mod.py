import cv2
from numpy import asarray

from get_html import SITE, WebConnection


class ImageEdit:
    @staticmethod
    def thumbnail_crop(imagefile: bytes, path: str) -> None:

        # img = cv2.imread(filename)
        img = asarray(bytearray(imagefile.read()), dtype="uint8")
        img = cv2.imdecode(img, cv2.IMREAD_COLOR)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)

        (T, thresh) = cv2.threshold(blurred, 250, 255, cv2.THRESH_BINARY_INV)

        x, y, w, h = cv2.boundingRect(thresh)

        delta = int((w - h) / 2)

        if delta >= 0:  # landscape - w-bound
            Y1 = y - delta - int(0.01 * w)
            Y2 = Y1 + w + int(0.02 * w)
            X1 = x - int(0.01 * w)
            X2 = x + int(1.01 * w)
        else:  # portrait - h-bound
            Y1 = y - int(0.01 * h)
            Y2 = y + int(1.01 * h)
            X1 = x + delta - int(0.01 * h)
            X2 = X1 + h + int(0.02 * h)

        crop = img[Y1:Y2, X1:X2]

        cv2.imwrite("test_image.jpg", crop)

        # # Display the result
        # cv2.imshow("Result", crop)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()


if __name__ == "__main__":
    from configparser import ConfigParser

    config = ConfigParser()
    config.read("config.ini")
    s = WebConnection(config["Login"]["login_url"], dict(config["Login_data"]))

    while True:
        url = input("Adres obrazka: ")
        path = "./miniatury/" + url.split("/")[-1]
        print(path)

        ImageEdit.thumbnail_crop(imagefile=s.get_image_binary(url), path=path)
