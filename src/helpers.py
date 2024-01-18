import logging
import argparse
import jpeglib
import cv2
import re
from bitarray import bitarray
from steganography import dct_steganography


def storage_stats_jpeg(filename: str):
    logging.info(f"Preparing storage statistics for '{filename}.jpg'...")

    for perceptibility in range(1, 9):
        image = dct_steganography.JpegImage.from_file(f"../placeholder-images/jpeg/{filename}.jpg", perceptibility)
        logging.info(f"For perceptibility {perceptibility}: {image.storage_capacity}B")


def storage_stats_png(filename: str):
    pass


def crop_jpeg(source_file: str, destination: str):
    logging.info(f"Cropping '{source_file}.jpg' to its middle third in both dimensions...")
    image = jpeglib.read_dct(source_file)

    # only keep the middle third of the image in both dimensions
    image.Y = image.Y[image.Y.shape[0] // 3: 2 * image.Y.shape[0] // 3, image.Y.shape[1] // 3: 2 * image.Y.shape[1] // 3]
    logging.info(f"Cropped Y channel.")
    image.Cr = image.Cr[image.Cr.shape[0] // 3: 2 * image.Cr.shape[0] // 3, image.Cr.shape[1] // 3: 2 * image.Cr.shape[1] // 3]
    logging.info(f"Cropped Cr channel.")
    image.Cb = image.Cb[image.Cb.shape[0] // 3: 2 * image.Cb.shape[0] // 3, image.Cb.shape[1] // 3: 2 * image.Cb.shape[1] // 3]
    logging.info(f"Cropped Cb channel.")

    image.height = image.Y.shape[0] * 8
    image.width = image.Y.shape[1] * 8

    image.write_dct(destination)


def crop_png(source_file: str, destination: str):
    pass


def recover(source_file: str, pattern_file: str):
    logging.info(f"Loading '{source_file}' source file from disk...")
    with open(source_file, "rb") as file:
        source = file.read()

    logging.info(f"Loading '{pattern_file}' pattern file from disk...")
    with open(pattern_file, "rb") as file:
        # make sure the content of the binary isn't interpreted as regex syntax
        pattern = re.escape(file.read())

    # initialize with the number of occurrences when no leading bits are removed
    number_of_matches = [len(re.findall(pattern, source))]

    source_as_bits = bitarray()
    source_as_bits.frombytes(source)

    for _ in range(1, 8):
        source_as_bits.pop(0)
        current_source = source_as_bits.tobytes()
        number_of_matches.append(len(re.findall(pattern, current_source)))

    maximum_number_of_matches = max(number_of_matches)
    leading_bits_removed = number_of_matches.index(maximum_number_of_matches)
    logging.info(f"Found {maximum_number_of_matches} matches of the pattern in the source file, after removing the leading {leading_bits_removed} bits.")


def visual_attack_jpeg(source_file: str, destination: str, number_of_least_significant_bits: str, luminance_boost: str):
    logging.info(f"Preparing bitmask for visual attack on {source_file}...")
    bitmask = 255 >> (8 - int(number_of_least_significant_bits))

    image = cv2.imread(source_file, cv2.IMREAD_GRAYSCALE)
    image &= bitmask
    logging.info("Bitmask applied.")

    image <<= int(luminance_boost)
    logging.info("Luminance boosted.")
    cv2.imwrite(destination, image)


def visual_attack_png(source_file: str, destination: str):
    pass


def main(args):
    if args.storage_stats:
        if args.type_of_image == "jpeg":
            storage_stats_jpeg(args.storage_stats)
        else:
            storage_stats_png(args.storage_stats)
    elif args.crop:
        if args.type_of_image == "jpeg":
            crop_jpeg(*args.crop)
        else:
            crop_png(*args.crop)
    elif args.recover:
        recover(*args.recover)
    elif args.visual_attack:
        if args.type_of_image == "jpeg":
            visual_attack_jpeg(*args.visual_attack)
        else:
            visual_attack_png(*args.visual_attack)

    logging.info("Done.")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description="Bundle of helpful functions, making use of the built-in steganography package and data assets.")
    parser.add_argument("-t", "--type-of-image", choices=["jpeg", "png"], dest="type_of_image", metavar="TYPE-OF-IMAGE", required=True)

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-s", "--storage-stats", choices=["cheetah", "forest", "mountain", "snowy", "wolf"], dest="storage_stats", metavar="BUILT-IN-IMAGE")
    group.add_argument("-c", "--crop", nargs=2, metavar=("SOURCE-FILE", "DESTINATION"))
    group.add_argument("-r", "--recover", nargs=2, metavar=("SOURCE-FILE", "DATA-TO-SEARCH-FOR"))
    group.add_argument("-v", "--visual-attack", nargs=4, metavar=("SOURCE-FILE", "DESTINATION", "NUMBER-OF-LEAST-SIGNIFICANT-BITS", "LUMINANCE-BOOST"))

    arguments = parser.parse_args()
    main(arguments)
