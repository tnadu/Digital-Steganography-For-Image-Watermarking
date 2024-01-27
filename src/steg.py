import logging
import argparse
import pyexiv2

from steganography import lsb_steganography
from steganography import dct_steganography


def data_embedding(args):
    logging.info("Loading data from disk, in preparation for embedding.")
    with open(args.data, "rb") as file:
        data = file.read()

    logging.info("Reading image from disk.")
    if args.type_of_image == "jpeg":
        image = dct_steganography.JpegImage.from_file(image_path=args.input_image, perceptibility=args.perceptibility)

        if args.watermark:
            logging.info("Multiplying data for watermarking.")
            data *= image.storage_capacity // len(data)
    else:
        image = lsb_steganography.PngImage.from_file(image_path=args.input_image, number_of_least_significant_bits=args.number_of_least_significant_bits)

        if args.watermark:
            logging.info("Multiplying data for watermarking.")
            data *= image.storage_capacity // len(data)

    try:
        stego_image = image.embed_data(data)
        logging.info("Writing stego image to disk.")
        stego_image.to_file(args.output_image)
    except ValueError:
        pass


def data_extraction(args):
    logging.info("Reading image from disk.")
    if args.type_of_image == "jpeg":
        stego_image = dct_steganography.StegJpegImage.from_file(args.input_stego_image)
    else:
        stego_image = lsb_steganography.StegPngImage.from_file(args.input_stego_image)

    try:
        data = stego_image.extract()

        logging.info("Writing extracted data to disk.")
        with open(args.output_extracted_data, "wb") as file:
            file.write(data)
    except TypeError:
        pass


def compute_storage_capacity(args):
    logging.info("Reading image from disk.")
    if args.type_of_image == "jpeg":
        image = dct_steganography.JpegImage.from_file(image_path=args.input_image, perceptibility=args.perceptibility)
    else:
        image = lsb_steganography.PngImage.from_file(image_path=args.input_image, number_of_least_significant_bits=args.number_of_least_significant_bits)

    print(f"Storage capacity: {image.storage_capacity}B")


def data_detection(args):
    logging.info("Reading image from disk.")

    if args.grayscale:
        pass
    else:
        pass


def main():
    parser = argparse.ArgumentParser(description="Interface for command line use of the built-in image steganography package. "
                                                 "This program supports embedding arbitrary binary data into png and jpeg images. "
                                                 "It can be used to share and store sensitive information, but it can also be used "
                                                 "to digitally watermark copyrighted material, via a special flag. For practical "
                                                 "security purposes, it is strongly advised to encrypt data before embedding it "
                                                 "into images.")

    parser.add_argument("-l", "--log-level", choices=[10, 20, 30, 40], default=20, dest="log_level", metavar="LOG-LEVEL", type=int, help="DEBUG=10, INFO=20, WARNING=30, ERROR=40")
    parser.add_argument("-t", "--type-of-image", choices=["jpeg", "png"], dest="type_of_image", metavar="TYPE-OF-IMAGE", required=True, help="when 'jpeg', the JSTEG algorithm is used; when 'png', the LSB algorithm is used")
    subparsers = parser.add_subparsers(title="subcommands", dest="subcommand", required=True)

    embedding_parser = subparsers.add_parser("embed", aliases=["em", "m"], description="Subcommand for embedding arbitrary data into an image.")
    embedding_parser.add_argument("-i", "--input-image", dest="input_image", metavar="INPUT-IMAGE", type=str, required=True, help="path to image in which data will be embedded")
    embedding_parser.add_argument("-o", "--output-image", dest="output_image", metavar="OUTPUT-IMAGE", type=str, required=True, help="path to which the stego image will be saved")
    embedding_parser.add_argument("-d", "--data", type=str, required=True, help="path to the data which will be embedded into the chosen image")
    embedding_parser.add_argument("-w", "--watermark", action="store_true", help="fill the whole storage capacity of the image with sequential copies of the specified data; will only embed as many full copies as the space allows")
    embedding_parser.add_argument("-n", "--number-of-least-significant-bits", choices=range(1, 5), default=1, dest="number_of_least_significant_bits", type=int, help="only available for PNG images")
    embedding_parser.add_argument("-p", "--perceptibility", choices=range(1, 9), default=3, type=int, help="only available for JPEG images; this controls how much of the top-left corner of each DCT block is used to store the embedded data")

    extraction_parser = subparsers.add_parser("extract", aliases=["ex", "x"], description="Subcommand for extracting arbitrary data from a stego image.")
    extraction_parser.add_argument("-i", "--input-stego-image", dest="input_stego_image", metavar="INPUT-STEGO-IMAGE", type=str, required=True, help="path to the stego image from which data will be extracted")
    extraction_parser.add_argument("-o", "--output-extracted-data", dest="output_extracted_data", metavar="OUTPUT-EXTRACTED-DATA", type=str, required=True, help="path to which the extracted data will be saved")

    storage_capacity_parser = subparsers.add_parser("storage", aliases=["s"], description="Subcommand for computing the storage capacity of a given image.")
    storage_capacity_parser.add_argument("-i", "--input-image", dest="input_image", metavar="INPUT-IMAGE", type=str, required=True, help="path to image for which the storage capacity will be computed")
    storage_capacity_parser.add_argument("-n", "--number-of-least-significant-bits", choices=range(1, 5), default=1, dest="number_of_least_significant_bits", type=int, help="only available for PNG images")
    storage_capacity_parser.add_argument("-p", "--perceptibility", choices=range(1, 9), default=3, type=int, help="only available for JPEG images; this controls how much of the top-left corner of each DCT block is used to store the embedded data")

    detection_parser = subparsers.add_parser("detect", aliases=["d"], description="Subcommand for detecting if covert data has been embedded into an image.")
    detection_parser.add_argument("-i", "--input-image", dest="input_image", metavar="INPUT-IMAGE", type=str, required=True, help="path to image which will be analyzed")
    detection_parser.add_argument("-g", "--grayscale", action="store_true", help="whether or not the input image is grayscale")

    arguments = parser.parse_args()
    logging.basicConfig(level=arguments.log_level, format="%(levelname)s: %(message)s")
    pyexiv2.set_log_level(3)

    if arguments.subcommand in ["embed", "em", "m"]:
        data_embedding(arguments)
    elif arguments.subcommand in ["extract", "ex", "x"]:
        data_extraction(arguments)
    elif arguments.subcommand in ["storage", "s"]:
        compute_storage_capacity(arguments)
    elif arguments.subcommand in ["detect", "d"]:
        data_detection(arguments)


if __name__ == '__main__':
    main()
