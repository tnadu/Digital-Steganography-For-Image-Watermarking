import numpy as np
from bitarray import bitarray
import logging
import jpeglib
import piexif


class StegJpegImage:
    pass


class JpegImage:
    def __init__(self, image_path: str, perceptibility: int = 3):
        if perceptibility < 1 or perceptibility > 8:
            logging.warning("Perceptibility can be between 1 and 8. Setting perceptibility to the default value of 3.")
            self.perceptibility = 3
        else:
            self.perceptibility = perceptibility

        self.image = jpeglib.read_dct(image_path)
        self.exif = piexif.load(image_path)
        self.storage_capacity = self.__get_storage_capacity()

    def __get_number_of_available_coefficients(self, image_channel: np.ndarray) -> int:
        number_of_available_coefficients = 0

        for i in range(image_channel.shape[0]):
            for j in range(image_channel.shape[1]):
                for k in range(8):
                    for l in range(max(0, 8 - k - self.perceptibility), 8):
                        if image_channel[i][j][k][l] > 1 or image_channel[i][j][k][l] < 0:
                            number_of_available_coefficients += 1

        return number_of_available_coefficients

    def __get_storage_capacity(self) -> int:
        total_storage_capacity = 0
        logging.info("Computing storage capacity within the luminance channel.")
        total_storage_capacity += self.__get_number_of_available_coefficients(self.image.Y)
        logging.info("Computing storage capacity within the chrominance red channel.")
        total_storage_capacity += self.__get_number_of_available_coefficients(self.image.Cr)
        logging.info("Computing storage capacity within the chrominance blue channel.")
        total_storage_capacity += self.__get_number_of_available_coefficients(self.image.Cb)

        # return the storage capacity in bytes
        return total_storage_capacity // 8

    def __embed_data_into_channel(self, image_channel: np.ndarray, data: bitarray) -> bitarray:
        for i in range(image_channel.shape[0]):
            for j in range(image_channel.shape[1]):
                for k in range(8):
                    for l in range(max(0, 8 - k - self.perceptibility), 8):
                        if image_channel[i][j][k][l] > 1 or image_channel[i][j][k][l] < 0:
                            if data:
                                # apply bitmasks
                                if data[0] == 0:
                                    image_channel[i][j][k][l] &= -2
                                else:
                                    image_channel[i][j][k][l] |= 1

                                data.pop(0)
                            else:
                                return data

        return data

    def embed_data(self, data: bytes, watermark: bool = False, extension: str = None) -> StegJpegImage:
        if len(data) > self.storage_capacity:
            logging.error("Size of data exceeds storage capacity of image.")
            raise ValueError("Size of data exceeds storage capacity of image.")

        logging.info("Embedding metadata into EXIF.")
        metadata = f"{len(data)}-{int(watermark)}-{extension if extension else ''}".encode("utf-8")
        # The UserComment tag is rarely overwritten by other software
        self.exif["Exif"][37510] = metadata

        logging.info("Embedding data into image.")
        bit_data = bitarray()
        bit_data.frombytes(data)

        bit_data = self.__embed_data_into_channel(self.image.Y, bit_data)
        if not bit_data:
            return StegJpegImage(self.image, self.exif)

        bit_data = self.__embed_data_into_channel(self.image.Cr, bit_data)
        if not bit_data:
            return StegJpegImage(self.image, self.exif)

        bit_data = self.__embed_data_into_channel(self.image.Cb, bit_data)
        if not bit_data:
            return StegJpegImage(self.image, self.exif)



# when decoding, if a coefficient value is not 0 nor 1, check the %2 to get the value of the bit


def main():
    exif = piexif.load("../images/forest.jpg")
    print(exif['Exif'])


if __name__ == "__main__":
    main()
