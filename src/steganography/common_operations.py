import logging


def extract_parameters_from_metadata(metadata: str, custom_parameter_name: str, range_of_custom_parameter: range) -> (int, int):
    if not metadata:
        logging.error("Metadata about the embedded data is missing from the EXIF of the image. "
                      "The image is either corrupted, or has been altered by other software.")
        raise TypeError("Metadata about the embedded data is missing from the EXIF of the image. "
                        "The image is either corrupted, or has been altered by other software.")

    metadata = metadata.split("-")

    if len(metadata) != 2:
        logging.error("Important fields in the metadata about the embedded data are missing from the EXIF of the image. "
                      "The image is either corrupted, or has been altered by other software.")
        raise TypeError("Important fields in the metadata about the embedded data are missing from the EXIF of the image. "
                        "The image is either corrupted, or has been altered by other software.")

    try:
        data_size = int(metadata[0])
    except ValueError:
        logging.error("The size of the embedded data is not a valid integer. The EXIF of the image has been modified, "
                      "which means that the image is either corrupted, or has been altered by other software.")
        raise TypeError("The size of the embedded data is not a valid integer. The EXIF of the image has been modified, "
                        "which means that the image is either corrupted, or has been altered by other software.")

    if data_size < 1:
        logging.error("The size of the embedded data is invalid. The EXIF of the image has been modified, which "
                      "means that the image is either corrupted, or has been altered by other software.")
        raise TypeError("The size of the embedded data is invalid. The EXIF of the image has been modified, which "
                        "means that the image is either corrupted, or has been altered by other software.")

    try:
        custom_parameter = int(metadata[1])
    except ValueError:
        logging.error(f"The '{custom_parameter_name}' value of the embedded data is not a valid integer. The EXIF of the image has been "
                      "modified, which means that the image is either corrupted, or has been altered by other software.")
        raise TypeError(f"The '{custom_parameter_name}' value of the embedded data is not a valid integer. The EXIF of the image has been "
                        "modified, which means that the image is either corrupted, or has been altered by other software.")

    if custom_parameter not in range_of_custom_parameter:
        logging.error(f"The '{custom_parameter_name}' value of the embedded data is invalid. The EXIF of the image has been modified, "
                      "which means that the image is either corrupted, or has been altered by other software.")
        raise TypeError(f"The '{custom_parameter_name}' value of the embedded data is invalid. The EXIF of the image has been modified, "
                        "which means that the image is either corrupted, or has been altered by other software.")

    return data_size, custom_parameter
