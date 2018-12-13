from __future__ import print_function

from functools32 import lru_cache

from ft_tools.results import Run
from ft_tools.utils import pdgIds

# Scalar
PAPER_XS = {  # (mChi, mPhi)    : xs[pb],
    'DMScalar': {
        (1, 10)    : 21.36,
        (1, 20)    : 10.95,
        (1, 40)    : 3.088,
        (1, 100)   : 7.205e-1,
        (1, 200)   : 1.016e-1,
        (1, 300)   : 3.045e-2,
        (1, 500)   : 4.947e-3,
        # (1, 10000) : 3.342e-9,

        (10, 10)   : 0.1011,
        # (10, 15)   : 0.1279,
        # (10, 50)   : 3.097,
        (10, 100)  : 0.7417,

        (50, 10)   : 0.002078,
        # (50, 50)   : 0.002567,
        # (50, 95)   : 0.007202,
        (50, 200)  : 0.1003,
        (50, 300)  : 0.03046,
    },
    'DMPseudo': {
        (1, 10)    : 0.4517,
        (1, 20)    : 0.4117,
        (1, 40)    : 0.3080,
        (1, 100)   : 0.1932,
        (1, 200)   : 0.08786,
        (1, 300)   : 0.03950,
        (1, 500)   : 0.005163,
        # (1, 10000) : 3.814e-9,

        (10, 10)   : 0.01522,
        # (10, 15)   : 0.01950,
        # (10, 50)   : 0.3091,
        (10, 100)  : 0.1976,

        (50, 10)   : 0.002405,
        # (50, 50)   : 0.002928,
        # (50, 95)   : 0.01072,
        (50, 200)  : 0.08476,
        (50, 300)  : 0.03845,
    }
}


@lru_cache()
def mchi(t):
    try:
        return int(run.read_param(t, 'MASS', pdgIds['chi']))
    except:
        return 0


@lru_cache()
def mphi(t):
    try:
        return int(run.read_param(t, 'MASS', pdgIds['phi']))
    except:
        return 0


if __name__ == '__main__':
    run = Run('DM', remote='http://t3.unl.edu/~cfangmeier/runs')

    tasks = list(run.tasks.values())
    tasks.sort(key=lambda x: mphi(x))
    tasks.sort(key=lambda x: mchi(x))
    tasks.sort(key=lambda x: x.proc_name)
    tasks.sort(key=lambda x: x.model)

    fmt_title = '{:10s} {:8s} {:8s} {:12s} {:12s} {:8s} {:8s}'
    print(fmt_title.format('Model', 'm_{chi}', 'm_{phi}', 'xs_paper', 'xs_mine', 'pap/me', 'me/pap'))
    for task in tasks:
        t_mchi = mchi(task)
        t_mphi = mphi(task)
        if task.proc_name != 'ttchichiJets':
            continue
        try:
            paper_xs = PAPER_XS[task.model][(t_mchi, t_mphi)]
        except KeyError:
            continue
        xs, xs_err = run.read_cross_section(task)
        fmt = '{:10s} {:8d} {:8d} {:12.8f} {:12.8f} {:8.4f} {:8.4f}'
        print(fmt.format(task.model, t_mchi, t_mphi, paper_xs, xs, paper_xs / xs, xs / paper_xs))
