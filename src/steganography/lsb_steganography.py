import logging
import numpy as np
import cv2
import pyexiv2

from bitarray import bitarray
from . import common_operations


class StegPngImage:
    def __init__(self, steg_image: np.ndarray, exif: dict):
        self.steg_image = steg_image
        self.exif = exif

    @classmethod
    def from_file(cls, image_path: str):
        logging.debug(f"Decoding stego PNG file '{image_path}'.")
        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)

        logging.debug(f"Loading EXIF from stego PNG file '{image_path}'.")
        temporary_image = pyexiv2.Image(image_path)
        exif = temporary_image.read_exif()
        temporary_image.close()

        return cls(image, exif)

    def to_file(self, image_path: str):
        logging.debug(f"Encoding PNG file '{image_path}'.")
        cv2.imwrite(image_path, self.steg_image, [cv2.IMWRITE_PNG_COMPRESSION, 0])

        logging.debug(f"Writing EXIF to PNG file '{image_path}'.")
        temporary_image = pyexiv2.Image(image_path)
        temporary_image.modify_exif(self.exif)
        temporary_image.close()

    def extract(self) -> bytes:
        logging.info("Extracting metadata from EXIF.")
        metadata = self.exif.get("Exif.Photo.UserComment")
        data_size, number_of_least_significant_bits = common_operations.extract_parameters_from_metadata(metadata, 'number_of_significant_bits', range(1, 5))

        logging.info("Attempting to extract data from image.")
        data = bitarray()

        for i in range(self.steg_image.shape[0]):
            for j in range(self.steg_image.shape[1]):
                for k in range(3):
                    # get the last 'number_of_least_significant_bits' sized sub-string from the binary representation
                    embedded_bits = f"{self.steg_image[i][j][k]:08b}"[-number_of_least_significant_bits:]
                    data.extend(embedded_bits)
                    data_size -= number_of_least_significant_bits

                    if data_size <= 0:
                        break
                else:
                    continue
                break
            else:
                continue
            break

        # when the value of 'number_of_least_significant_bits' is 3, there might be up to 2 remaining
        # bits in the sequence of bits embedded in the last pixel value, which must be ignored
        if len(data) % 8:
            data = data[:-(len(data) % 8)]

        if data_size > 0:
            logging.warning(f"Could not extract embedded data completely. The size of the embedded data, as it was read from the "
                            f"EXIF of the image, exceeds the storage capacity of the image. A total of {len(data)} bits were read, "
                            f"and the last {data_size} bits are missing. This might be due to cropping, EXIF "
                            f"modifications or other alterations produced by different software")

        return data.tobytes()


class PngImage:
    def __init__(self, image: np.ndarray, exif: dict, number_of_least_significant_bits: int = 1):
        self.image = image
        self.exif = exif
        self.number_of_least_significant_bits = number_of_least_significant_bits
        self.storage_capacity = self.__compute_storage_capacity()

    @classmethod
    def from_file(cls, image_path: str, number_of_least_significant_bits: int = 1):
        if number_of_least_significant_bits not in range(1, 5):
            logging.warning("Number of least significant bits can be between 1 and 4. Applying the default value of 1.")
            number_of_least_significant_bits = 1

        logging.debug(f"Decoding PNG file '{image_path}'.")
        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)

        logging.debug(f"Loading EXIF from PNG file '{image_path}'.")
        temporary_image = pyexiv2.Image(image_path)
        exif = temporary_image.read_exif()
        temporary_image.close()

        return cls(image, exif, number_of_least_significant_bits)

    def __compute_storage_capacity(self) -> int:
        logging.info("Computing storage capacity of image.")
        return (self.image.size * self.number_of_least_significant_bits) // 8

    def embed_data(self, data: bytes) -> StegPngImage:
        if len(data) > self.storage_capacity:
            logging.error("Size of data exceeds storage capacity of image.")
            raise ValueError("Size of data exceeds storage capacity of image.")

        logging.info("Embedding metadata into EXIF.")
        # store the size of the embedded data in number of bits
        metadata = f"{len(data) * 8}-{self.number_of_least_significant_bits}"
        # The UserComment tag is rarely overwritten by other software
        self.exif["Exif.Photo.UserComment"] = metadata

        image = self.image.copy()
        bit_data = bitarray()
        bit_data.frombytes(data)

        logging.info("Embedding data into image.")
        for i in range(image.shape[0]):
            for j in range(image.shape[1]):
                for k in range(3):
                    # indexing is much (MUCH) faster than deletion for bitarray objects
                    left_bound = i * image.shape[1] * 3 * self.number_of_least_significant_bits + j * 3 * self.number_of_least_significant_bits + k * self.number_of_least_significant_bits
                    right_bound = i * image.shape[1] * 3 * self.number_of_least_significant_bits + j * 3 * self.number_of_least_significant_bits + (k + 1) * self.number_of_least_significant_bits

                    # representing a color channel value in binary form, on 8 bits, as a string, and substituting the
                    # last 'number_of_least_significant_bits' bits with the corresponding bits in the covert data
                    pixel_value = f"{image[i][j][k]:08b}"[:-self.number_of_least_significant_bits] + bit_data[left_bound:right_bound].to01()
                    # padding with 0s to the right (when the data size isn't divisible by 3)
                    pixel_value = pixel_value.ljust(8, '0')
                    pixel_value = int(pixel_value, 2)
                    image[i][j][k] = pixel_value

                    if right_bound >= len(bit_data):
                        break
                else:
                    continue
                break
            else:
                continue
            break

        return StegPngImage(image, self.exif)
