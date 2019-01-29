from __future__ import print_function
import re
from os.path import join, isfile, isdir
from os import remove
from bs4 import BeautifulSoup as Soup
from dill import loads
import tarfile
import requests
import pandas as pd
from lhe2sqlite import convert
from ft_tools.utils import FLT_RE


class Run(object):
    def __init__(self, run_name, job_dir='runs', remote=None):
        self.name = run_name
        self.job_dir = job_dir
        self.remote = remote
        self._tasks = None

    def _read(self, path, binary=False):
        path = join(self.job_dir, self.name, path)
        if self.remote is None:
            return open(path, 'rb' if binary else 'r').read()
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

    def unpack_tasks(self):
        dest = join(self.job_dir, self.name)
        for task_name in self.tasks:
            dir_ = join(self.job_dir, self.name, task_name)
            archive = dir_ + '.tar.gz'
            if isfile(archive) and not isdir(dir_):
                with tarfile.open(archive, 'r:gz') as f:
                    print('unpacking:', archive)
                    f.extractall(dest)
                remove(archive)

    def convert_lhe(self, task):
        self.unpack_tasks()
        lhe_filename = join(self.job_dir, self.name, task.job_name, 'Events', 'run_01', 'unweighted_events.lhe.gz')
        sql_filename = join(self.job_dir, self.name, task.job_name, 'Events', 'run_01', 'unweighted_events.sqlite3')
        if not isfile(sql_filename):
            print('converting', lhe_filename, '->', sql_filename)
            try:
                convert(lhe_filename, sql_filename)
            except Exception as e:
                print(e)
        return sql_filename

    def query_events(self, task, sql):
        sql_filename = self.convert_lhe(task)
        return pd.read_sql_query(sql, 'sqlite:///'+sql_filename)

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


# if __name__ == '__main__':
#     run = Run('DM', remote='http://t3.unl.edu/~cfangmeier/runs')
#     print(run.tasks)
#     for task_name, task in run.tasks.items():
#         xs = ('NaN', 'NaN')
#         m_chi = 0
#         try:
#             xs = run.read_cross_section(task)
#             m_chi = run.read_param(task, 'MASS', 9100022)
#         except Exception as e:
#             print(e)
#         print(task_name, m_chi, xs)
