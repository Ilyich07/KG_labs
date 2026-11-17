"""
Лабораторная работа 2, вариант 3.
1) Построение и эквализация гистограммы + линейное контрастирование
2) Высокочастотные фильтры (повышение резкости)
"""
import numpy as np
from matplotlib.figure import Figure
from PIL import Image

def load(path, mode):
    img = Image.open(path).convert(mode)
    img.thumbnail((1000, 1000))
    return np.array(img)


def load_gray(path):
    return load(path, "L")


def load_rgb(path):
    return load(path, "RGB")


def histogram(gray):
    """h(i) - число пикселей с яркостью i, i = 0..255"""
    return np.bincount(gray.ravel(), minlength=256)


def linear_contrast(gray):
    """f' = 255 * (f - fmin) / (fmax - fmin)"""
    fmin, fmax = int(gray.min()), int(gray.max())
    if fmax == fmin:
        return gray.copy()
    res = 255.0 * (gray.astype(float) - fmin) / (fmax - fmin)
    return np.round(res).astype(np.uint8)


def equalize(gray):
    """Эквализация: f' = 255 * Sh(f), Sh - кумулятивная гистограмма"""
    h = histogram(gray)               
    h = h / gray.size                 
    sh = np.cumsum(h)                 
    lut = np.round(255 * sh).astype(np.uint8)  
    return lut[gray]


def equalize_rgb(rgb):
    out = np.zeros_like(rgb)
    for c in range(3):
        out[:, :, c] = equalize(rgb[:, :, c])
    return out


def equalize_hsv(rgb):
    hsv = np.array(Image.fromarray(rgb).convert("HSV"))
    hsv[:, :, 2] = equalize(hsv[:, :, 2])
    return np.array(Image.fromarray(hsv, "HSV").convert("RGB"))


MASKS = {
    "Маска 5 (центр 5)": np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]]),
    "Маска 9 (центр 9)": np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]]),
    "Маска 1-2-1 (центр 5)": np.array([[1, -2, 1], [-2, 5, -2], [1, -2, 1]]),
    "Маска (центр 20)": np.array([[0, -1, 0], [-1, 20, -1], [0, -1, 0]]),
}


def convolve(ch, mask):
    """Дискретная свёртка с маской и делением на сумму весов W.
    Границы: изображение расширяется повторением крайних пикселей."""
    k = mask.shape[0] // 2
    h, w = ch.shape
    p = np.pad(ch.astype(float), k, mode="edge")
    out = np.zeros((h, w))
    for i in range(mask.shape[0]):
        for j in range(mask.shape[1]):
            out += mask[i, j] * p[i:i + h, j:j + w]
    W = mask.sum()
    if W != 0:
        out /= W
    return out


def sharpen_mask(img, mask):
    if img.ndim == 2:
        return np.clip(convolve(img, mask), 0, 255).astype(np.uint8)
    out = np.zeros_like(img)
    for c in range(img.shape[2]):
        out[:, :, c] = np.clip(convolve(img[:, :, c], mask), 0, 255)
    return out


def unsharp(img, k=1.5):
    avg = np.ones((3, 3))             # размытие усредняющим фильтром 3x3
    if img.ndim == 2:
        b = convolve(img, avg)
        return np.clip(img + k * (img - b), 0, 255).astype(np.uint8)
    out = np.zeros_like(img)
    for c in range(img.shape[2]):
        f = img[:, :, c].astype(float)
        out[:, :, c] = np.clip(f + k * (f - convolve(f, avg)), 0, 255)
    return out


def laplacian(gray):
    m = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]])
    return convolve(gray, m)


# ---------------------------------------------------------------
# Построение окон с результатами
# ---------------------------------------------------------------
def show(ax, img, title):
    if img.ndim == 2:
        ax.imshow(img, cmap="gray", vmin=0, vmax=255)
    else:
        ax.imshow(img)
    ax.set_title(title, fontsize=9)
    ax.axis("off")


def show_hist(ax, gray, title):
    ax.bar(range(256), histogram(gray), width=1.0, color="gray")
    ax.set_title(title, fontsize=9)
    ax.set_xlim(0, 255)


def fig_contrast(path):
    g = load_gray(path)
    lin, eq = linear_contrast(g), equalize(g)
    fig = Figure(figsize=(11, 6), layout="constrained")
    ax = fig.subplots(2, 3)
    show(ax[0, 0], g, "Исходное")
    show(ax[0, 1], lin, "Линейное контрастирование")
    show(ax[0, 2], eq, "Эквализация гистограммы")
    show_hist(ax[1, 0], g, "Гистограмма исходного")
    show_hist(ax[1, 1], lin, "Гистограмма (линейное)")
    show_hist(ax[1, 2], eq, "Гистограмма (эквализация)")
    return fig


def fig_color(path):
    rgb = load_rgb(path)
    r, h = equalize_rgb(rgb), equalize_hsv(rgb)
    gray = lambda a: np.array(Image.fromarray(a).convert("L"))
    fig = Figure(figsize=(11, 6), layout="constrained")
    ax = fig.subplots(2, 3)
    show(ax[0, 0], rgb, "Исходное")
    show(ax[0, 1], r, "Эквализация в RGB (3 канала)")
    show(ax[0, 2], h, "Эквализация V в HSV")
    show_hist(ax[1, 0], gray(rgb), "Гистограмма яркости (исходное)")
    show_hist(ax[1, 1], gray(r), "Гистограмма яркости (RGB)")
    show_hist(ax[1, 2], gray(h), "Гистограмма яркости (HSV)")
    return fig


def fig_sharp(path):
    g = load_rgb(path)
    fig = Figure(figsize=(11, 7), layout="constrained")
    ax = fig.subplots(2, 3)
    ax = ax.ravel()
    show(ax[0], g, "Исходное")
    i = 1
    for name, m in MASKS.items():
        show(ax[i], sharpen_mask(g, m), name)
        i += 1
    show(ax[5], unsharp(g), "Unsharp masking (k=1.5)")
    return fig


# ---------------------------------------------------------------
# Графический интерфейс
# ---------------------------------------------------------------
MODES = {
    "Контраст: линейное + эквализация (серое)": fig_contrast,
    "Эквализация цветного: RGB и HSV": fig_color,
    "Повышение резкости (ВЧ-фильтры)": fig_sharp,
}


def main():
    import os
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

    # --- цвета и шрифт
    BG, DARK, WHITE = "#f5f3ee", "#35463d", "#fffefa"
    BLUE, BLUE_H = "#64856f", "#4d7059"
    FONT = "Segoe UI"

    root = tk.Tk()
    root.title("Лабораторная работа 2 (вариант 3): обработка изображений")
    root.geometry("1150x740")
    root.minsize(800, 500)
    root.configure(bg=BG)

    # --- стили элементов
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("Main.TButton", font=(FONT, 10, "bold"), foreground="white",
                    background=BLUE, padding=(15, 9), borderwidth=0, focuscolor=BLUE)
    style.map("Main.TButton", background=[("active", BLUE_H)])
    style.configure("TCombobox", padding=6, font=(FONT, 10),
                    fieldbackground=WHITE, background="#e8ece5", foreground="#28382e",
                    bordercolor="#cbd4c9", arrowcolor="#35463d")
    root.option_add("*TCombobox*Listbox.font", (FONT, 10))
    style.configure("Bar.TFrame", background=WHITE)
    style.configure("Bar.TLabel", background=WHITE, foreground="#35463d", font=(FONT, 10))

    state = {"path": None, "fig": None, "canvas": None}
    status = tk.StringVar(value="1. Откройте изображение     2. Выберите метод обработки")
    mode = tk.StringVar(value=list(MODES)[0])

    # --- заголовок
    header = tk.Frame(root, bg=DARK)
    header.pack(fill="x")
    tk.Label(header, text="Обработка цифровых изображений", bg=DARK, fg="white",
             font=(FONT, 17, "bold")).pack(anchor="w", padx=18, pady=(12, 0))
    tk.Label(header, text="Лабораторная работа 2, вариант 3: контраст и повышение резкости",
             bg=DARK, fg="#d9e2d7", font=(FONT, 10)).pack(anchor="w", padx=18, pady=(0, 12))

    # --- панель управления
    bar = ttk.Frame(root, style="Bar.TFrame", padding=(14, 10))
    bar.pack(fill="x")
    ttk.Button(bar, text="Открыть изображение", style="Main.TButton",
               command=lambda: open_file()).pack(side="left")
    ttk.Label(bar, text="Метод:", style="Bar.TLabel").pack(side="left", padx=(18, 6))
    box = ttk.Combobox(bar, textvariable=mode, values=list(MODES), state="readonly", width=44)
    box.pack(side="left")

    # --- строка состояния (внизу)
    tk.Label(root, textvariable=status, anchor="w", bg="#e9ede6", fg="#44554a",
             font=(FONT, 9), padx=14, pady=6).pack(side="bottom", fill="x")

    # --- область результата
    outer = tk.Frame(root, bg=BG)
    outer.pack(fill="both", expand=True, padx=14, pady=12)
    area = tk.Frame(outer, bg=WHITE, highlightthickness=1, highlightbackground="#d6ded3")
    area.pack(fill="both", expand=True)
    hint = tk.Label(area, text="Нажмите «Открыть изображение», чтобы начать",
                    bg=WHITE, fg="#819084", font=(FONT, 13))
    hint.pack(expand=True)

    def update(*_):
        if state["path"] is None:
            return
        try:
            fig = MODES[mode.get()](state["path"])
        except Exception as e:
            messagebox.showerror("Ошибка", "Не удалось обработать файл:\n" + str(e))
            return
        hint.pack_forget()
        if state["canvas"] is not None:
            state["canvas"].get_tk_widget().destroy()
        canvas = FigureCanvasTkAgg(fig, master=area)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        canvas.draw()
        state["fig"], state["canvas"] = fig, canvas
        status.set("Файл: " + os.path.basename(state["path"]) + "     |     " + mode.get())

    def open_file():
        p = filedialog.askopenfilename(
            initialdir="test_images" if os.path.isdir("test_images") else ".",
            filetypes=[("Изображения", "*.png *.jpg *.jpeg *.bmp")])
        if p:
            state["path"] = p
            update()

    box.bind("<<ComboboxSelected>>", update)   # метод сменился - сразу пересчитать
    root.mainloop()


if __name__ == "__main__":
    main()
