import re
from os.path import join
from bs4 import BeautifulSoup as Soup
from dill import loads
import requests
from ft_tools.utils import FLT_RE


class Run(object):
    def __init__(self, run_name, remote=None):
        self.name = run_name
        self.remote = remote
        self._tasks = None

    def _read(self, path, binary=False):
        path = join(self.name, path)
        if self.remote is None:
            return open(path, 'rb' if binary else 'r')
        else:
            web_path = self.remote + '/' + path
            r = requests.get(web_path)
            if r.status_code != 200:  # Success
                raise IOError('failed to fetch resource at ' + web_path)
            if binary:
                return r.content
            else:
                return r.text

    @property
    def tasks(self):
        if self._tasks is None:
            self._tasks = loads(self._read('batch.dill', binary=True))
        return self._tasks

    def read_cross_section(self, task):
        fname = join(task.job_name, 'crossx.html')
        raw = self._read(fname)
        soup = Soup(raw, 'html5lib')
        text_raw = soup.select("tr")[1].select("td")[3].get_text()
        crossx, stat_err = re.findall(r"({flt}) . ({flt})".format(flt=FLT_RE), text_raw, re.UNICODE)[0]
        return float(crossx), float(stat_err)

    def read_param(self, task, block_name, idx):
        fname = join(task.job_name, 'Cards', 'param_card.dat')
        raw = self._read(fname)
        in_block = False
        for line in raw.split('\n'):
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


if __name__ == '__main__':
    run = Run('DM', remote='http://t3.unl.edu/~cfangmeier/runs')
    print(run.tasks)
    for task_name, task in run.tasks.items():
        xs = ('NaN', 'NaN')
        m_chi = 0
        try:
            xs = run.read_cross_section(task)
            m_chi = run.read_param(task, 'MASS', 9100022)
        except Exception as e:
            print(e)
        print(task_name, m_chi, xs)
