from Crypto import Random
from Crypto.Cipher import AES, DES, DES3
from Crypto.Util.py3compat import *
from Crypto.Util.number import long_to_bytes, bytes_to_long, size, ceil_div


def get_zero_vector(numBytes):
    """
    Generates a zero vector of a given size

    :param numBytes:
    :return:
    """
    return bytearray([0] * numBytes).decode('ascii')


