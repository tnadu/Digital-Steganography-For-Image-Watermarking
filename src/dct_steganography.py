import numpy as np
from bitarray import bitarray
import logging
import jpeglib
import piexif


class StegJpegImage:
    def __init__(self, steg_image: jpeglib.dct_jpeg.DCTJPEG, exif: dict):
        self.steg_image = steg_image
        self.exif = exif

    @classmethod
    def from_file(cls, image_path: str):
        logging.debug(f"Decoding DCT blocks from stego JPEG file {image_path}.")
        image = jpeglib.read_dct(image_path)
        logging.debug(f"Loading EXIF from stego JPEG file {image_path}.")
        exif = piexif.load(image_path)

        return cls(image, exif)

    def to_file(self, path: str):
        logging.debug(f"Encoding DCT blocks to JPEG file {path}.")
        self.steg_image.write_dct(path)

        logging.debug(f"Writing EXIF to JPEG file {path}.")
        piexif.insert(piexif.dump(self.exif), path)

    def __extract_data_from_channel(self, image_channel: np.ndarray, data_size: int, data: bitarray, perceptibility: int) -> (int, bitarray):
        for i in range(image_channel.shape[0]):
            for j in range(image_channel.shape[1]):
                for k in range(8):
                    for l in range(max(0, 8 - k - perceptibility), 8):
                        if image_channel[i][j][k][l] > 1 or image_channel[i][j][k][l] < 0:
                            data.append(int(image_channel[i][j][k][l]) % 2)
                            data_size -= 1

                            if not data_size:
                                return data_size, data

        return data_size, data

    def extract(self) -> bytes:
        logging.info("Extracting metadata from EXIF.")
        metadata = self.exif["Exif"].get(37510)

        if not metadata:
            logging.error("Metadata about the embedded data is missing from the EXIF of the image."
                          "The image is either corrupted, or has been altered by other software.")
            raise TypeError("Metadata about the embedded data is missing from the EXIF of the image."
                            "The image is either corrupted, or has been altered by other software.")

        metadata = metadata.decode("utf-8").split("-")

        if len(metadata) != 2:
            logging.error("Important fields in the metadata about the embedded data are missing from the EXIF of the image."
                          "The image is either corrupted, or has been altered by other software.")
            raise TypeError("Important fields in the metadata about the embedded data are missing from the EXIF of the image."
                            "The image is either corrupted, or has been altered by other software.")

        try:
            data_size = int(metadata[0])
            # convert bytes to bits
            data_size *= 8
        except ValueError:
            logging.error("The size of the embedded data is not a valid integer. The EXIF of the image has been modified,"
                          "which means that the image is either corrupted, or has been altered by other software.")
            raise TypeError("The size of the embedded data is not a valid integer. The EXIF of the image has been modified,"
                            "which means that the image is either corrupted, or has been altered by other software.")

        if data_size < 1:
            logging.error("The size of the embedded data is invalid. The EXIF of the image has been modified, which"
                          "means that the image is either corrupted, or has been altered by other software.")
            raise TypeError("The size of the embedded data is invalid. The EXIF of the image has been modified, which"
                            "means that the image is either corrupted, or has been altered by other software.")

        try:
            perceptibility = int(metadata[1])
        except ValueError:
            logging.error("The perceptibility value of the embedded data is not a valid integer. The EXIF of the image has been"
                          "modified, which means that the image is either corrupted, or has been altered by other software.")
            raise TypeError("The perceptibility value of the embedded data is not a valid integer. The EXIF of the image has been"
                            "modified, which means that the image is either corrupted, or has been altered by other software.")

        if perceptibility < 1 or perceptibility > 8:
            logging.error("The perceptibility value of the embedded data is invalid. The EXIF of the image has been modified,"
                          "which means that the image is either corrupted, or has been altered by other software.")
            raise TypeError("The perceptibility value of the embedded data is invalid. The EXIF of the image has been modified,"
                            "which means that the image is either corrupted, or has been altered by other software.")

        logging.info("Attempting to extract data from image.")
        data = bitarray()

        data_size, data = self.__extract_data_from_channel(self.steg_image.Y, data_size, data, perceptibility)
        logging.debug(f"Extracted data from Y channel. Total size of extracted data: {len(data)} bits. Remaining: {data_size} bits.")
        if not data_size:
            return data.tobytes()

        data_size, data = self.__extract_data_from_channel(self.steg_image.Cr, data_size, data, perceptibility)
        logging.debug(f"Extracted data from Cr channel. Total size of extracted data: {len(data)} bits. Remaining: {data_size} bits.")
        if not data_size:
            return data.tobytes()

        data_size, data = self.__extract_data_from_channel(self.steg_image.Cb, data_size, data, perceptibility)
        logging.debug(f"Extracted data from Cb channel. Total size of extracted data: {len(data)} bits. Remaining: {data_size} bits.")
        if not data_size:
            logging.warning(f"Could not extract embedded data completely. The size of the embedded data, as it was read from the"
                            f"EXIF of the image, exceeds the storage capacity of the image. A total of {len(data)} bits were read,"
                            f"and the last {data_size} bits are missing. This might be due to cropping, EXIF modifications or other"
                            f"alterations produced by different software")

        return data.tobytes()


class JpegImage:
    def __init__(self, image: jpeglib.dct_jpeg.DCTJPEG, exif: dict, perceptibility: int = 3):
        self.image = image
        self.exif = exif
        self.perceptibility = perceptibility
        self.storage_capacity = self.__get_storage_capacity()

    @classmethod
    def from_file(cls, image_path: str, perceptibility: int = 3):
        if perceptibility < 1 or perceptibility > 8:
            logging.warning("Perceptibility can be between 1 and 8. Setting perceptibility to the default value of 3.")
            perceptibility = 3
        else:
            perceptibility = perceptibility

        logging.debug(f"Decoding DCT blocks from JPEG file {image_path}.")
        image = jpeglib.read_dct(image_path)
        logging.debug(f"Loading EXIF from JPEG file {image_path}.")
        exif = piexif.load(image_path)

        return cls(image, exif, perceptibility)

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
        logging.info("Computing storage capacity of image.")

        total_storage_capacity = 0
        logging.debug("Computing storage capacity within the Y channel.")
        total_storage_capacity += self.__get_number_of_available_coefficients(self.image.Y)
        logging.debug("Computing storage capacity within the Cr channel.")
        total_storage_capacity += self.__get_number_of_available_coefficients(self.image.Cr)
        logging.debug("Computing storage capacity within the Cb channel.")
        total_storage_capacity += self.__get_number_of_available_coefficients(self.image.Cb)

        # return the storage capacity in bytes
        return total_storage_capacity // 8

    def __embed_data_into_channel(self, image_channel: np.ndarray, data: bitarray) -> bitarray:
        for i in range(image_channel.shape[0]):
            for j in range(image_channel.shape[1]):
                for k in range(8):
                    for l in range(max(0, 8 - k - self.perceptibility), 8):
                        if image_channel[i][j][k][l] > 1 or image_channel[i][j][k][l] < 0:
                            # apply bitmasks
                            if data[0] == 0:
                                image_channel[i][j][k][l] &= -2
                            else:
                                image_channel[i][j][k][l] |= 1

                            data.pop(0)

                            if not data:
                                return data

        return data

    def embed_data(self, data: bytes) -> StegJpegImage:
        if len(data) > self.storage_capacity:
            logging.error("Size of data exceeds storage capacity of image.")
            raise ValueError("Size of data exceeds storage capacity of image.")

        logging.info("Embedding metadata into EXIF.")
        metadata = f"{len(data)}-{self.perceptibility}".encode("utf-8")
        # The UserComment tag is rarely overwritten by other software
        self.exif["Exif"][37510] = metadata

        bit_data = bitarray()
        bit_data.frombytes(data)

        logging.info("Embedding data into image.")
        bit_data = self.__embed_data_into_channel(self.image.Y, bit_data)
        logging.debug(f"Embedded data to Y channel. Size of data yet to be embedded: {len(bit_data)} bits.")
        if not bit_data:
            return StegJpegImage(self.image, self.exif)

        bit_data = self.__embed_data_into_channel(self.image.Cr, bit_data)
        logging.debug(f"Embedded data to Cr channel. Size of data yet to be embedded: {len(bit_data)} bits.")
        if not bit_data:
            return StegJpegImage(self.image, self.exif)

        self.__embed_data_into_channel(self.image.Cb, bit_data)
        logging.debug(f"Embedded data to Cb channel. Size of data yet to be embedded: {len(bit_data)} bits.")
        return StegJpegImage(self.image, self.exif)
