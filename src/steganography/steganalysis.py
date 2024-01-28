import logging
import jpeglib
import cv2
import numpy as np

from scipy.stats import chi2_contingency


def lsb_detection(image_path, grayscale=False, alpha=0.05):
    if grayscale:
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        pixel_values = image.flatten()

        # Extract the LSB from each pixel
        lsb_values = pixel_values & 1

        # Count the occurrences of 0s and 1s 
        observed_freq, _ = np.histogram(lsb_values, bins=range(3))

        # Calculate the expected frequencies assuming no steganography (50% chance of 0 or 1)
        expected_freq = np.full_like(observed_freq, fill_value=len(lsb_values) / 2)

        # Chi-squared test
        chi2_stat, p_value, _, _ = chi2_contingency([observed_freq, expected_freq])
        logging.debug(f"p-value = {p_value}")

        if p_value < alpha:
            logging.info("LSB steganography detected!")
        else:
            logging.info("No evidence of LSB steganography.")

    else:
        image = cv2.imread(image_path)

        pixel_values_r = image[0].flatten()
        pixel_values_g = image[1].flatten()
        pixel_values_b = image[2].flatten()

        lsb_values_r = pixel_values_r & 1
        lsb_values_g = pixel_values_g & 1
        lsb_values_b = pixel_values_b & 1

        observed_freq_r, _ = np.histogram(lsb_values_r, bins=range(3))
        observed_freq_g, _ = np.histogram(lsb_values_g, bins=range(3))
        observed_freq_b, _ = np.histogram(lsb_values_b, bins=range(3))

        expected_freq_r = np.full_like(observed_freq_r, fill_value=len(lsb_values_r) / 2)
        expected_freq_g = np.full_like(observed_freq_g, fill_value=len(lsb_values_g) / 2)
        expected_freq_b = np.full_like(observed_freq_b, fill_value=len(lsb_values_b) / 2)

        chi2_stat_r, p_value_r, _, _ = chi2_contingency([observed_freq_r, expected_freq_r])
        chi2_stat_g, p_value_g, _, _ = chi2_contingency([observed_freq_g, expected_freq_g])
        chi2_stat_b, p_value_b, _, _ = chi2_contingency([observed_freq_b, expected_freq_b])

        logging.debug(f"p-value for red channel: {p_value_r}")
        logging.debug(f"p-value for green channel: {p_value_g}")
        logging.debug(f"p-value for blue channel: {p_value_b}")

        if any(p_value < alpha for p_value in [p_value_r, p_value_g, p_value_b]):
            logging.info("LSB steganography detected!")
        else:
            logging.info("No evidence of LSB steganography.")


def dct_detection(image_path, grayscale=False, alpha=0.05):
    dct = jpeglib.read_dct(image_path)
    y_coefficients = dct.Y
    # Remove the 0s and the 1s
    y_coefficients = y_coefficients[(y_coefficients != 0) & (y_coefficients != 1)]

    observed_y = calculate_dct_distribution(y_coefficients)
    expected_y = calculate_expected_frequency(y_coefficients)

    chi2_stat_y, p_value_y, _, _ = chi2_contingency([observed_y, expected_y])
    logging.debug(f"p-value for Y channel = {p_value_y}")
    
    if not grayscale:
        cr_coefficients = dct.Cr
        cb_coefficients = dct.Cb
    
        cr_coefficients = cr_coefficients[(cr_coefficients != 0) & (cr_coefficients != 1)]
        cb_coefficients = cb_coefficients[(cb_coefficients != 0) & (cb_coefficients != 1)]

        observed_cr = calculate_dct_distribution(cr_coefficients)
        observed_cb = calculate_dct_distribution(cb_coefficients)

        expected_cr = calculate_expected_frequency(cr_coefficients)
        expected_cb = calculate_expected_frequency(cb_coefficients)

        chi2_stat_cr, p_value_cr, _, _ = chi2_contingency([observed_cr, expected_cr])
        chi2_stat_cb, p_value_cb, _, _ = chi2_contingency([observed_cb, expected_cb])

        logging.debug(f"p-value for Cr channel = {p_value_cr}")
        logging.debug(f"p-value for Cb channel = {p_value_cb}")

    if grayscale:
        dct_detected = p_value_y < alpha
    else:
        dct_detected = any(p_value < alpha for p_value in [p_value_y, p_value_cr, p_value_cb])
    
    if dct_detected:
        logging.info("DCT steganography detected!")
    else:
        logging.info("No evidence of DCT steganography.")


def calculate_dct_distribution(coefficients):
    lsb_values = coefficients & 1
    observed_freq, _ = np.histogram(lsb_values, bins=range(3))
    return observed_freq


def calculate_expected_frequency(coefficients):
    total = len(coefficients)
    freq1 = freq2 = total // 2
    if total % 2 == 1:
        freq2 += 1
    
    return np.array([freq1, freq2])
