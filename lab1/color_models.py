import tkinter as tk
from tkinter import ttk

def rgb_to_cmyk(r, g, b):
    """RGB (0..255) -> CMYK (0..1), формулы из лекции."""
    r, g, b = r / 255, g / 255, b / 255
    k = min(1 - r, 1 - g, 1 - b)
    if k == 1:                       # чистый чёрный, делить на (1 - K) нельзя
        return 0, 0, 0, 1
    c = (1 - r - k) / (1 - k)
    m = (1 - g - k) / (1 - k)
    y = (1 - b - k) / (1 - k)
    return c, m, y, k


def cmyk_to_rgb(c, m, y, k):
    """CMYK (0..1) -> RGB (0..255), формулы из лекции."""
    return (255 * (1 - c) * (1 - k),
            255 * (1 - m) * (1 - k),
            255 * (1 - y) * (1 - k))


def rgb_to_hls(r, g, b):
    """RGB (0..255) -> H (0..360), L (0..1), S (0..1)."""
    r, g, b = r / 255, g / 255, b / 255
    mx, mn = max(r, g, b), min(r, g, b)
    d = mx - mn
    l = (mx + mn) / 2
    if d == 0:                       # серый цвет: оттенок не определён
        return 0, l, 0
    s = d / (1 - abs(2 * l - 1))
    if mx == r:
        h = ((g - b) / d) % 6
    elif mx == g:
        h = (b - r) / d + 2
    else:
        h = (r - g) / d + 4
    return h * 60, l, s


def hls_to_rgb(h, l, s):
    """H (0..360), L (0..1), S (0..1) -> RGB (0..255)."""
    c = (1 - abs(2 * l - 1)) * s     # "размах" цвета (chroma)
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = l - c / 2
    r, g, b = [(c, x, 0), (x, c, 0), (0, c, x),
               (0, x, c), (x, 0, c), (c, 0, x)][int(h // 60) % 6]
    return (r + m) * 255, (g + m) * 255, (b + m) * 255


MODELS = [
    ("CMYK", [("C", 0, 100, 0.1), ("M", 0, 100, 0.1),
              ("Y", 0, 100, 0.1), ("K", 0, 100, 0.1)]),
    ("RGB",  [("R", 0, 255, 1), ("G", 0, 255, 1), ("B", 0, 255, 1)]),
    ("HLS",  [("H", 0, 360, 0.1), ("L", 0, 100, 0.1), ("S", 0, 100, 0.1)]),
]

TO_RGB = {
    "CMYK": lambda v: cmyk_to_rgb(*[x / 100 for x in v]),
    "RGB":  lambda v: tuple(v),
    "HLS":  lambda v: hls_to_rgb(v[0], v[1] / 100, v[2] / 100),
}

# RGB -> значения ползунков модели
FROM_RGB = {
    "CMYK": lambda r, g, b: [x * 100 for x in rgb_to_cmyk(r, g, b)],
    "RGB":  lambda r, g, b: [r, g, b],
    "HLS":  lambda r, g, b: (lambda h, l, s: [h, l * 100, s * 100])(
        *rgb_to_hls(r, g, b)),
}


class Row:
    """Одна компонента цвета: подпись + ползунок + поле ввода."""

    def __init__(self, parent, row, name, lo, hi, step, on_change):
        self.lo, self.hi, self.step = lo, hi, step
        self.on_change = on_change
        self.var = tk.DoubleVar(value=lo)
        self.text = tk.StringVar()

        ttk.Label(parent, text=name, width=2).grid(row=row, column=0, padx=4)
        tk.Scale(parent, from_=lo, to=hi, resolution=step, orient="horizontal",
                 variable=self.var, showvalue=False, length=300,
                 command=self._on_slider).grid(row=row, column=1, padx=4)
        entry = ttk.Entry(parent, textvariable=self.text, width=7)
        entry.grid(row=row, column=2, padx=4, pady=2)
        entry.bind("<Return>", self._on_entry)
        entry.bind("<FocusOut>", self._on_entry)

    def get(self):
        return self.var.get()

    def set(self, value):
        """Задать значение (без вызова on_change)."""
        value = min(max(value, self.lo), self.hi)
        self.var.set(value)
        self.text.set(f"{value:.0f}" if self.step == 1 else f"{value:.1f}")

    def _on_slider(self, _):
        self.set(self.var.get())
        self.on_change()

    def _on_entry(self, _):
        try:
            value = float(self.text.get().replace(",", "."))
        except ValueError:
            value = self.var.get()          # ввели ерунду - вернём старое
        self.set(round(value) if self.step == 1 else value)
        self.on_change()


class App:
    PAL_W, PAL_H = 360, 200                 # размер палитры

    def __init__(self, root):
        root.title("Цветовые модели: CMYK - RGB - HLS")
        self.busy = False                   # защита от лишних пересчётов
        self.rows = {}                      # имя модели -> список Row

        left = ttk.Frame(root)
        left.grid(row=0, column=0, padx=10, pady=10)
        right = ttk.Frame(root)
        right.grid(row=0, column=1, padx=10, pady=10, sticky="n")

        for name, comps in MODELS:
            box = ttk.LabelFrame(left, text=name)
            box.pack(fill="x", pady=5)
            self.rows[name] = [
                Row(box, i, n, lo, hi, st, lambda m=name: self.update_from(m))
                for i, (n, lo, hi, st) in enumerate(comps)
            ]

        # палитра: по горизонтали H, по вертикали L (насыщенность 100%)
        ttk.Label(right, text="Палитра (H - L)").pack(anchor="w")
        self.palette = tk.Canvas(right, width=self.PAL_W, height=self.PAL_H,
                                 cursor="crosshair", highlightthickness=1)
        self.palette.pack()
        self.draw_palette()
        self.marker = self.palette.create_oval(0, 0, 0, 0, outline="black",
                                               width=2)
        self.palette.bind("<Button-1>", self.on_palette)
        self.palette.bind("<B1-Motion>", self.on_palette)

        # предпросмотр
        ttk.Label(right, text="Выбранный цвет").pack(anchor="w", pady=(15, 0))
        self.preview = tk.Canvas(right, width=self.PAL_W, height=90,
                                 highlightthickness=1)
        self.preview.pack()
        self.hex_label = ttk.Label(right, font=("Consolas", 14))
        self.hex_label.pack(pady=5)

        # начальный цвет
        for row, v in zip(self.rows["RGB"], (51, 153, 255)):
            row.set(v)
        self.update_from("RGB")

    # --- пересчёт -------------------------------------------------------

    def update_from(self, source):
        """Пользователь изменил модель source -> обновляем остальные."""
        if self.busy:
            return
        self.busy = True
        values = [row.get() for row in self.rows[source]]
        r, g, b = [min(max(round(x), 0), 255) for x in TO_RGB[source](values)]

        for name, rows in self.rows.items():
            if name != source:              # источник не трогаем - ползунок
                for row, v in zip(rows, FROM_RGB[name](r, g, b)):  # не прыгает
                    row.set(v)

        color = f"#{r:02x}{g:02x}{b:02x}"
        self.preview.configure(bg=color)
        self.hex_label.configure(text=color.upper())
        self.move_marker()
        self.busy = False

    # --- палитра --------------------------------------------------------

    def draw_palette(self):
        self.img = tk.PhotoImage(width=self.PAL_W, height=self.PAL_H)
        for y in range(self.PAL_H):
            l = 1 - y / (self.PAL_H - 1)
            colors = []
            for x in range(self.PAL_W):
                r, g, b = hls_to_rgb(x, l, 1)
                colors.append(f"#{round(r):02x}{round(g):02x}{round(b):02x}")
            self.img.put("{" + " ".join(colors) + "}", to=(0, y))
        self.palette.create_image(0, 0, image=self.img, anchor="nw")

    def on_palette(self, event):
        x = min(max(event.x, 0), self.PAL_W - 1)
        y = min(max(event.y, 0), self.PAL_H - 1)
        h_row, l_row, s_row = self.rows["HLS"]
        h_row.set(x)
        l_row.set(100 * (1 - y / (self.PAL_H - 1)))
        s_row.set(100)
        self.update_from("HLS")

    def move_marker(self):
        h_row, l_row, _ = self.rows["HLS"]
        x = h_row.get() * (self.PAL_W - 1) / 360
        y = (1 - l_row.get() / 100) * (self.PAL_H - 1)
        self.palette.coords(self.marker, x - 5, y - 5, x + 5, y + 5)


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
