## Digital Steganography for Image Watermarking
### General Description
The core of the project consists of the `steganography` package, which supports both embedding, extraction and detection of information hidden in PNG and JPEG images. 

The technique used for PNG images is LSBR (Least Significant Bit Replacement), while the technique used for JPEG images is JSTEG. In terms of detection, the `steganalysis` module supports the chi-squared test on both image formats. It might be worth mentioning that there is also a rudimentary visual attack implemented in the `helpers` module. Although the package can be used individually, CLI functionality is also provided in the `steg.py` script.

This project was developed as the final assignment in a Signal Processing University Course, and a detailed report outlining the methods we have used and showcasing relevant results can be found under `docs/`, in both English and Romanian. 

### Requirements and Installation
Only python 3.11 is absolutely guaranteed to work, but older or newer versions of python might also run the project without issues. The operating systems on which both development and testing took place are Linux and macOS, so no guarantees can be made about Windows.

In order to install the project, clone this repository:
```shell
git clone https://github.com/tnadu/Digital-Steganography-For-Image-Watermarking.git && cd Digital-Steganography-For-Image-Watermarking 
```

For convenience, a virtual environment is the recommended method of installation. We will use `venv`:
```shell
python3 -m venv venv && source venv/bin/activate
```

Next, install the required packages using pip:
```shell
pip install -r src/requirements.txt
```

Finally, run the CLI script, to verify that the installation was successful:
```shell
python src/steg.py -h
```

Just to be safe, one should also run the following:
```shell
python -c "import bitarray; assert bitarray.test().wasSuccessful()"
```