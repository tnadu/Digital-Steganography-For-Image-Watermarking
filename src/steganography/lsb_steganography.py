import cv2
import numpy as np
import logging


class StegPNGImage:
    byte_size = 8
    size_encoding = 4

    def __init__(self, steg_image: np.ndarray):
        self.steg_image = steg_image

    @classmethod
    def from_file(cls, image_path: str):
        logging.debug(f"Loading PNG file {image_path}.")
        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        return cls(image)

    def to_file(self, path: str):
        logging.debug(f"Saving modified PNG file {path}.")
        cv2.imwrite(path, self.steg_image)

    def extract(self) -> str:
        logging.info("Extracting data from PNG image using LSB method.")
        message_size = 0
        size_extracted = False
        message_extracted = False
        size_bits = []
        message_bits = []

        for i, line in enumerate(self.steg_image):
            for j, pixel in enumerate(line):
                for c, channel in enumerate(pixel):
                    if not size_extracted and len(size_bits) == self.size_encoding * self.byte_size:
                        message_size = int("".join(size_bits), 2)
                        size_extracted = True

                    if not size_extracted:
                        size_bits.append(bin(channel)[-1])

                    if size_extracted and not message_extracted:
                        message_bits.append(bin(channel)[-1])
                        if len(message_bits) == message_size * self.byte_size:
                            message_extracted = True
                            break

                if message_extracted:
                    break
            if message_extracted:
                break

        return self.__bits_to_string(message_bits)

    def __bits_to_string(self, bits):
        message = []
        for i in range(0, len(bits), self.byte_size):
            byte = bits[i:i + self.byte_size]
            message.append(chr(int(''.join(byte), 2)))
        return "".join(message)


class PNGImage:
    def __init__(self, image: np.ndarray):
        self.image = image
        self.storage_capacity = self.__calculate_storage_capacity()

    @classmethod
    def from_file(cls, image_path: str):
        logging.debug(f"Loading PNG file {image_path}.")
        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        return cls(image)

    def to_file(self, path: str):
        logging.debug(f"Saving PNG file {path}.")
        cv2.imwrite(path, self.image)

    def __calculate_storage_capacity(self) -> int:
        return (self.image.shape[0] * self.image.shape[1] * self.image.shape[2]) // 8

    # def __convert_message_to_bits(self, message: str) -> list:
    #     message_length = len(message)
    #     if message_length > self.storage_capacity:
    #         raise ValueError(f"Message is too long. Maximum length: {self.storage_capacity} characters")
    #
    #     message_bytes = message.encode('utf-8')
    #     message_bits = []
    #
    #     # Encoding the length of the message in the first 32 bits
    #     length_bits = bin(message_length)[2:].zfill(32)
    #     message_bits.extend(length_bits)
    #
    #     # Encoding the message
    #     for byte in message_bytes:
    #         byte_bits = bin(byte)[2:].zfill(8)
    #         message_bits.extend(byte_bits)
    #
    #     return message_bits

    def __convert_message_to_bits(self, message) -> list:
        if isinstance(message, str):
            message = message.encode('utf-8')

        message_length = len(message)
        if message_length > self.storage_capacity:
            raise ValueError(f"Message is too long. Maximum length: {self.storage_capacity} characters")

        message_bits = []

        # Encoding the length of the message in the first 32 bits
        length_bits = bin(message_length)[2:].zfill(32)
        message_bits.extend(length_bits)

        # Encoding the message
        for byte in message:
            byte_bits = bin(byte)[2:].zfill(8)
            message_bits.extend(byte_bits)

        return message_bits

    # def embed_data(self, data: str):
    #     message_bits = self.__convert_message_to_bits(data)
    #     counter = 0
    #     new_image = self.image.copy()
    #
    #     for i in range(self.image.shape[0]):
    #         for j in range(self.image.shape[1]):
    #             for c in range(self.image.shape[2]):
    #                 binary_pixel = bin(new_image[i, j, c])[:-1] + message_bits[counter]
    #                 new_image[i, j, c] = int(binary_pixel, 2)
    #                 counter += 1
    #                 if counter == len(message_bits):
    #                     self.image = new_image
    #                     return
    #
    #     self.image = new_image

    def embed_data(self, data: str):
        message_bits = self.__convert_message_to_bits(data)
        counter = 0
        new_image = self.image.copy()

        for i in range(self.image.shape[0]):
            for j in range(self.image.shape[1]):
                for c in range(self.image.shape[2]):
                    if counter >= len(message_bits):
                        self.image = new_image
                        return self

                    binary_pixel = bin(new_image[i, j, c])[:-1] + message_bits[counter]
                    new_image[i, j, c] = int(binary_pixel, 2)
                    counter += 1

        self.image = new_image
        return self

