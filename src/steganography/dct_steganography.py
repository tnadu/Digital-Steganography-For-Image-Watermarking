import logging
import numpy as np
import jpeglib
import pyexiv2

from bitarray import bitarray
from . import common_operations


class StegJpegImage:
    def __init__(self, steg_image: jpeglib.dct_jpeg.DCTJPEG, exif: dict):
        self.steg_image = steg_image
        self.exif = exif

    @classmethod
    def from_file(cls, image_path: str):
        logging.debug(f"Decoding DCT blocks from stego JPEG file '{image_path}'.")
        image = jpeglib.read_dct(image_path)

        logging.debug(f"Loading EXIF from stego JPEG file '{image_path}'.")
        temporary_image = pyexiv2.Image(image_path)
        exif = temporary_image.read_exif()
        temporary_image.close()

        return cls(image, exif)

    def to_file(self, image_path: str):
        logging.debug(f"Encoding DCT blocks to JPEG file '{image_path}'.")
        self.steg_image.write_dct(image_path)

        logging.debug(f"Writing EXIF to JPEG file '{image_path}'.")
        temporary_image = pyexiv2.Image(image_path)
        temporary_image.modify_exif(self.exif)
        temporary_image.close()

    def __extract_data_from_channel(self, image_channel: np.ndarray, data_size: int, data: bitarray, perceptibility: int) -> (int, bitarray):
        for i in range(image_channel.shape[0]):
            for j in range(image_channel.shape[1]):
                for k in range(8):
                    for l in range(max(0, 8 - k - perceptibility), 8):
                        if image_channel[i][j][k][l] not in [0, 1]:
                            data.append(int(image_channel[i][j][k][l]) % 2)
                            data_size -= 1

                            if not data_size:
                                return data_size, data

        return data_size, data

    def extract(self) -> bytes:
        logging.info("Extracting metadata from EXIF.")
        metadata = self.exif.get("Exif.Photo.UserComment")
        data_size, perceptibility = common_operations.extract_parameters_from_metadata(metadata, 'perceptibility', range(1, 9))

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
        if data_size:
            logging.warning(f"Could not extract embedded data completely. The size of the embedded data, as it was read from the "
                            f"EXIF of the image, exceeds the storage capacity of the image. A total of {len(data)} bits were read, "
                            f"and the last {data_size} bits are missing. This might be due to cropping, EXIF modifications or other "
                            f"alterations produced by different software")

        return data.tobytes()


class JpegImage:
    def __init__(self, image: jpeglib.dct_jpeg.DCTJPEG, exif: dict, perceptibility: int = 3):
        self.image = image
        self.exif = exif
        self.perceptibility = perceptibility
        self.storage_capacity = self.__compute_storage_capacity()

    @classmethod
    def from_file(cls, image_path: str, perceptibility: int = 3):
        if perceptibility not in range(1, 9):
            logging.warning("Perceptibility can be between 1 and 8. Applying the default value of 3.")
            perceptibility = 3

        logging.debug(f"Decoding DCT blocks from JPEG file '{image_path}'.")
        image = jpeglib.read_dct(image_path)

        logging.debug(f"Loading EXIF from JPEG file '{image_path}'.")
        temporary_image = pyexiv2.Image(image_path)
        exif = temporary_image.read_exif()
        temporary_image.close()

        return cls(image, exif, perceptibility)

    def __compute_number_of_available_coefficients(self, image_channel: np.ndarray) -> int:
        number_of_available_coefficients = 0

        for i in range(image_channel.shape[0]):
            for j in range(image_channel.shape[1]):
                for k in range(8):
                    for l in range(max(0, 8 - k - self.perceptibility), 8):
                        if image_channel[i][j][k][l] not in [0, 1]:
                            number_of_available_coefficients += 1

        return number_of_available_coefficients

    def __compute_storage_capacity(self) -> int:
        logging.info("Computing storage capacity of image.")

        storage_capacity_in_Y = self.__compute_number_of_available_coefficients(self.image.Y)
        logging.debug(f"Storage capacity in the Y channel: {storage_capacity_in_Y} bits.")
        storage_capacity_in_Cr = self.__compute_number_of_available_coefficients(self.image.Cr)
        logging.debug(f"Storage capacity in the Cr channel: {storage_capacity_in_Cr} bits.")
        storage_capacity_in_Cb = self.__compute_number_of_available_coefficients(self.image.Cb)
        logging.debug(f"Storage capacity in the Cb channel: {storage_capacity_in_Cb} bits.")

        # return the storage capacity in bytes
        return (storage_capacity_in_Y + storage_capacity_in_Cr + storage_capacity_in_Cb) // 8

    def __embed_data_into_channel(self, image_channel: np.ndarray, data: bitarray, index: int = 0) -> int:
        for i in range(image_channel.shape[0]):
            for j in range(image_channel.shape[1]):
                for k in range(8):
                    for l in range(max(0, 8 - k - self.perceptibility), 8):
                        if image_channel[i][j][k][l] not in [0, 1]:
                            # apply bitmasks
                            if data[index] == 0:
                                image_channel[i][j][k][l] &= -2
                            else:
                                image_channel[i][j][k][l] |= 1

                            index += 1

                            if index == len(data):
                                return index

        return index

    def embed_data(self, data: bytes) -> StegJpegImage:
        if len(data) > self.storage_capacity:
            logging.error("Size of data exceeds storage capacity of image.")
            raise ValueError("Size of data exceeds storage capacity of image.")

        logging.info("Embedding metadata into EXIF.")
        # store the size of the embedded data in number of bits
        metadata = f"{len(data) * 8}-{self.perceptibility}"
        # The UserComment tag is rarely overwritten by other software
        self.exif["Exif.Photo.UserComment"] = metadata

        image = self.image.copy()
        bit_data = bitarray()
        bit_data.frombytes(data)

        logging.info("Embedding data into image.")
        index = self.__embed_data_into_channel(image.Y, bit_data)
        logging.debug(f"Embedded {index} bits into Y channel.")
        if index == len(bit_data):
            return StegJpegImage(image, self.exif)

        bits_embedded_in_Y = index
        index = self.__embed_data_into_channel(image.Cr, bit_data, index)
        logging.debug(f"Embedded {index - bits_embedded_in_Y} bits into Cr channel.")
        if index == len(bit_data):
            return StegJpegImage(image, self.exif)

        bits_embedded_in_Cr = index - bits_embedded_in_Y
        index = self.__embed_data_into_channel(image.Cb, bit_data, index)
        logging.debug(f"Embedded {index - bits_embedded_in_Y - bits_embedded_in_Cr} bits into Cb channel.")
        return StegJpegImage(image, self.exif)
