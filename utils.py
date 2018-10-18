from os.path import join
from bs4 import BeautifulSoup as Soup
import re

FLT_RE = r"(?:|\+ ?|- ?)\d+\.?\d*(?:[eE][+-]\d+)?"

def read_cross_section(run_name, task):
    fname = join(run_name, task.job_name, 'crossx.html')
    with open(fname) as f:
        soup = Soup(f, 'html5lib')
    text_raw = soup.select("tr")[1].select("td")[3].get_text()
    crossx, stat_err = re.findall(r"({flt}) . ({flt})".format(flt=FLT_RE), text_raw, re.UNICODE)[0]
    return crossx, stat_err

def read_param(run_name, task, block_name, idx):
    fname = join(run_name, task.job_name, 'Cards', 'param_card.dat')
    with open(fname) as f:
        lines = f.readlines()
        in_block = False
        for line in lines:
            line = line.strip()
            if in_block:
                tokens = line.split()
                if int(tokens[0]) == idx:
                    return float(tokens[1])
            else:
                if 'BLOCK '+block_name in line:
                    in_block = True
    raise ValueError("Unable to lookup {} in block {} in {}".format(idx, block_name, fname))
