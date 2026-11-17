"""Воспроизводимые замеры вычисления шагов без GUI и отрисовки."""
from statistics import median
from time import perf_counter_ns
from platform import python_version, platform
from algorithms import step_by_step, dda, bresenham, bresenham_circle

CASES=[('Пошаговый',step_by_step,(-12,-7,17,10)),('ЦДА',dda,(-12,-7,17,10)),('Брезенхем / отрезок',bresenham,(-12,-7,17,10)),('Брезенхем / окружность',bresenham_circle,(0,0,12))]
REPEATS=1000
SERIES=7

def run():
    print('Platform:',platform(),'Python:',python_version())
    print('Includes: algorithm and list of steps; excludes GUI drawing.')
    for name,fn,args in CASES:
        fn(*args)
        measures=[]
        for _ in range(SERIES):
            t0=perf_counter_ns()
            for k in range(REPEATS):fn(*args)
            measures.append((perf_counter_ns()-t0)/REPEATS/1000)
        print(f'{name}: {median(measures):.3f} us/call; runs={REPEATS} x {SERIES}; steps={len(fn(*args))}')

if __name__=='__main__':run()
