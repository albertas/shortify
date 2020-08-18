from random import choices
from string import ascii_letters, digits


def gen_short_path(length=6):
    symbols = ascii_letters + digits
    return "".join(choices(symbols, k=length))
