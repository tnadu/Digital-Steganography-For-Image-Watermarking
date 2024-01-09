import numpy as np
import jpeglib


def get_number_of_available_coefficients(image, diagonal_parameter):
    total = 0

    for i in range(image.shape[0]):
        for j in range(image.shape[1]):
            for k in range(8):
                for l in range(max(0, 8 - k - diagonal_parameter), 8):
                    if image[i, j, k, l] >= 4:
                        total += 1

    return total


def main():
    image = jpeglib.read_dct("../images/forest.jpg")

    diagonal_parameter = 3
    number_of_bits_used_for_message_per_coefficient = 2
    total_theoretical_size_of_steganographic_message = 0
    total_theoretical_size_of_steganographic_message += get_number_of_available_coefficients(image.Y, diagonal_parameter)
    total_theoretical_size_of_steganographic_message += get_number_of_available_coefficients(image.Cb, diagonal_parameter)
    total_theoretical_size_of_steganographic_message += get_number_of_available_coefficients(image.Cr, diagonal_parameter)

    print(f"{total_theoretical_size_of_steganographic_message * number_of_bits_used_for_message_per_coefficient / 8} B")


if __name__ == "__main__":
    main()
