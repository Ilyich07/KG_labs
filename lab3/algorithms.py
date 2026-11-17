"""Базовые алгоритмы растеризации. Все вычисления отделены от интерфейса."""
from dataclasses import dataclass
from math import floor


@dataclass(frozen=True)
class Step:
    pixels: tuple[tuple[int, int], ...]
    note: str


def nearest(v: float) -> int:
    """Округление половин от нуля (в отличие от банковского round)."""
    return floor(v + 0.5) if v >= 0 else -floor(-v + 0.5)


def step_by_step(x1: int, y1: int, x2: int, y2: int) -> list[Step]:
    """Пошаговый алгоритм: координата по уравнению прямой + округление."""
    dx, dy = x2 - x1, y2 - y1
    n = max(abs(dx), abs(dy))
    if n == 0:
        return [Step(((x1, y1),), 'Единственная точка: вычисления не требуются.')]

    steep = abs(dy) > abs(dx)
    out = []
    for i in range(n + 1):
        if steep:
            y = y1 + (1 if dy > 0 else -1) * i
            x_real = x1 + (y - y1) * dx / dy
            x = nearest(x_real)
            note = (f'Пошаговый · шаг {i} из {n}\n'
                    f'Ведущая координата: y = {y}\n'
                    f'x = {x1} + ({y} - {y1})·({dx})/({dy})\n'
                    f'x (до округления) = {x_real:.6f}\n'
                    f'Округление x → {x}\n'
                    f'Пиксель: ({x}, {y})')
        else:
            x = x1 + (1 if dx > 0 else -1) * i
            y_real = y1 + (x - x1) * dy / dx
            y = nearest(y_real)
            note = (f'Пошаговый · шаг {i} из {n}\n'
                    f'Ведущая координата: x = {x}\n'
                    f'y = {y1} + ({x} - {x1})·({dy})/({dx})\n'
                    f'y (до округления) = {y_real:.6f}\n'
                    f'Округление y → {y}\n'
                    f'Пиксель: ({x}, {y})')
        out.append(Step(((x, y),), note))
    return out


def dda(x1: int, y1: int, x2: int, y2: int) -> list[Step]:
    """Симметричный ЦДА: координаты получаются накоплением приращений."""
    dx, dy = x2 - x1, y2 - y1
    n = max(abs(dx), abs(dy))
    if n == 0:
        return [Step(((x1, y1),), 'Единственная точка: вычисления не требуются.')]

    inc_x, inc_y = dx / n, dy / n
    x, y = float(x1), float(y1)
    out = []
    for i in range(n + 1):
        px, py = nearest(x), nearest(y)
        if i == 0:
            transition = f'Старт: x = {x1}; y = {y1}'
        else:
            transition = (f'Из предыдущих: x += {inc_x:.6f}; '
                          f'y += {inc_y:.6f}')
        note = (f'ЦДА · шаг {i} из {n}\n'
                f'L = max(|{dx}|, |{dy}|) = {n}\n'
                f'Приращения: Δx/L = {inc_x:.6f}; Δy/L = {inc_y:.6f}\n'
                f'{transition}\n'
                f'Накоплено: x = {x:.6f}; y = {y:.6f}\n'
                f'Округление → ({px}, {py})')
        out.append(Step(((px, py),), note))
        if i < n:
            x += inc_x
            y += inc_y
    return out


def bresenham(x1: int, y1: int, x2: int, y2: int) -> list[Step]:
    """Целочисленный Брезенхем, все октанты, tie => диагональный шаг."""
    dx, dy = abs(x2-x1), abs(y2-y1)
    sx = 1 if x2 >= x1 else -1
    sy = 1 if y2 >= y1 else -1
    steep = dy > dx
    major, minor = (dy, dx) if steep else (dx, dy)
    x, y = x1, y1
    error = 2*minor-major
    out = []
    for i in range(major+1):
        out.append(Step(((x, y),), f'i={i}; E={error}; след. шаг: '+('диагональный' if error >= 0 else 'основной')))
        if i == major:
            break
        if steep:
            y += sy
            if error >= 0:
                x += sx
        else:
            x += sx
            if error >= 0:
                y += sy
        error += 2*(minor-major) if error >= 0 else 2*minor
    return out


def bresenham_circle(cx: int, cy: int, radius: int) -> list[Step]:
    """Окружность: E=3-2R, восемь симметричных точек из одной дуги."""
    if radius < 0:
        raise ValueError('Радиус не может быть отрицательным')
    x, y = 0, radius
    error = 3-2*radius
    out = []
    while x <= y:
        pts = {(cx+u, cy+v) for u, v in (
            (x,y), (x,-y), (-x,y), (-x,-y),
            (y,x), (y,-x), (-y,x), (-y,-x))}
        out.append(Step(tuple(sorted(pts)), f'x={x}, y={y}, E={error}; '+('диагональный ход' if error >= 0 else 'горизонтальный ход')))
        if error >= 0:
            error += 4*(x-y)+10
            y -= 1
        else:
            error += 4*x+6
        x += 1
    return out


def unique_pixels(steps: list[Step]) -> set[tuple[int, int]]:
    return {p for s in steps for p in s.pixels}
