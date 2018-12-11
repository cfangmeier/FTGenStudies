from __future__ import print_function
from os.path import join
from bs4 import BeautifulSoup as Soup
import re
from six.moves import (input)

FLT_RE = r"(?:|\+ ?|- ?)\d+\.?\d*(?:[eE][+-]\d+)?"


def sh(cmd, args, output=None):
    from subprocess import call, STDOUT
    if output is not None:
        retval = call([cmd] + list(args), stdout=output, stderr=STDOUT)
    else:
        retval = call([cmd] + list(args))
    if retval:
        raise RuntimeError('command failed to run(' + str(retval) + '): ' + str(cmd) + ' ' + str(args))


def read_cross_section(run_name, task):
    fname = join(run_name, task.job_name, 'crossx.html')
    with open(fname) as f:
        soup = Soup(f, 'html5lib')
    text_raw = soup.select("tr")[1].select("td")[3].get_text()
    crossx, stat_err = re.findall(r"({flt}) . ({flt})".format(flt=FLT_RE), text_raw, re.UNICODE)[0]
    return float(crossx), float(stat_err)


def read_param(run_name, task, block_name, idx):
    fname = join(run_name, task.job_name, 'Cards', 'param_card.dat')
    with open(fname) as f:
        lines = f.readlines()
        in_block = False
        for line in lines:
            line = line.strip()
            if in_block:
                try:
                    tokens = line.split()
                    if int(tokens[0]) == idx:
                        return float(tokens[1])
                except ValueError:  # reached end of block
                    break
            else:
                if 'BLOCK '+block_name in line:
                    in_block = True
    raise ValueError("Unable to lookup {} in block {} in {}".format(idx, block_name, fname))


pdgIds = {
    'd ':  1,
    'u ':  2,
    's ':  3,
    'c ':  4,
    'b':   5,
    't':   6,
    'e':   11,
    've ': 12,
    'mu':  13,
    'vm ': 14,
    'ta':  15,
    'vt ': 16,
    'g':   21,
    'a':   22,
    'z':   23,
    'w':   24,
    'h':   25,
    'h1':  25,
    'h2':  35,
    'a2':  36,
    'h3':  36,
    'hc':  37,
    'zp':  9000005,
    'phi': 9100000,  # DM like
    'chi': 9100022,  # DM like
}


class C:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def info(text, **kwargs):
    print(C.HEADER+text+C.ENDC, **kwargs)


def info2(text, **kwargs):
    print(C.OKGREEN+text+C.ENDC, **kwargs)


def get_yes_no(prompt, default=False, no_prompt=False):
    if no_prompt:
        return default
    if default:
        while True:
            info(prompt + ' (Y/n)')
            x = input().strip().lower()
            if x == 'n':
                return False
            elif x in ('', 'y'):
                return True
    else:
        while True:
            info(prompt + ' (y/N)')
            x = input().strip().lower()
            if x == 'y':
                return True
            elif x in ('', 'n'):
                return False

