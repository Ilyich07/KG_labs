"""Лабораторная работа №3 — визуализатор растеризации. Python 3.10+, Tkinter."""
import tkinter as tk
from tkinter import ttk, messagebox
from time import perf_counter_ns
from statistics import median
from algorithms import step_by_step, dda, bresenham, bresenham_circle, unique_pixels

BG='#0b1220'; PANEL='#131e30'; INK='#e5edf7'; MUTED='#94a3b8'; ACCENT='#38bdf8'; PIXEL='#fb923c'; GRID='#26354a'
ALGORITHMS = ['Пошаговый', 'ЦДА', 'Брезенхем (отрезок)', 'Брезенхем (окружность)']

class App:
    def __init__(self, root):
        self.root = root
        root.title('Лабораторная №3 · Базовые растровые алгоритмы')
        root.geometry('1250x800'); root.minsize(920,600); root.configure(bg=BG)
        self.scale=26; self.pan_x=0; self.pan_y=0; self.steps=[]; self.index=0
        self.algorithm=tk.StringVar(value=ALGORITHMS[2]); self.vars={k:tk.StringVar(value=v) for k,v in {'x1':'-12','y1':'-7','x2':'12','y2':'7','R':'12'}.items()}
        self.status=tk.StringVar(value='Выберите алгоритм и нажмите «Построить».')
        self.coords=tk.StringVar(value='')
        self.make_ui(); self.compute()
        root.bind('<Configure>', self.on_resize)
        root.bind('<Left>', lambda e:self.move_step(-1)); root.bind('<Right>', lambda e:self.move_step(1))

    def make_ui(self):
        top=tk.Frame(self.root,bg=BG); top.pack(fill='x',padx=22,pady=(18,10))
        tk.Label(top,text='РАСТЕРИЗАЦИЯ',font=('Segoe UI',22,'bold'),fg=INK,bg=BG).pack(side='left')
        tk.Label(top,text='Лабораторная работа №3 · 4 базовых алгоритма',font=('Segoe UI',11),fg=MUTED,bg=BG).pack(side='left',padx=20)
        main=tk.Frame(self.root,bg=BG); main.pack(fill='both',expand=True,padx=18,pady=(0,15))
        side=tk.Frame(main,bg=PANEL,width=310); side.pack(side='left',fill='y',padx=(0,13)); side.pack_propagate(False)
        canvas_frame=tk.Frame(main,bg=PANEL); canvas_frame.pack(side='left',fill='both',expand=True)
        def lbl(text, bold=False):
            tk.Label(side,text=text,anchor='w',bg=PANEL,fg=INK if bold else MUTED,font=('Segoe UI',11,'bold' if bold else 'normal')).pack(fill='x',padx=18,pady=(14 if bold else 7,4))
        lbl('АЛГОРИТМ',True)
        style=ttk.Style(); style.theme_use('clam'); style.configure('App.TCombobox',fieldbackground='#243248',background='#243248',foreground=INK,arrowcolor=INK,padding=7)
        style.map('App.TCombobox',fieldbackground=[('readonly','#243248')],foreground=[('readonly','#111827')])
        self.combo=ttk.Combobox(side,values=ALGORITHMS,textvariable=self.algorithm,state='readonly',style='App.TCombobox',font=('Segoe UI',10))
        self.combo.pack(fill='x',padx=18); self.combo.bind('<<ComboboxSelected>>',lambda e:self.update_fields())
        lbl('ПАРАМЕТРЫ',True)
        self.fields=tk.Frame(side,bg=PANEL); self.fields.pack(fill='x',padx=18)
        self.update_fields()
        self.action=tk.Button(side,text='▶  Построить',command=self.compute,bg=ACCENT,fg='#052339',font=('Segoe UI',12,'bold'),relief='flat',cursor='hand2',pady=10)
        self.action.pack(fill='x',padx=18,pady=(16,7))
        tk.Button(side,text='Измерить время (1000 запусков)',command=self.benchmark,bg='#273950',fg=INK,font=('Segoe UI',10),relief='flat',pady=9).pack(fill='x',padx=18)
        lbl('ПОШАГОВАЯ ВИЗУАЛИЗАЦИЯ',True)
        nav=tk.Frame(side,bg=PANEL);nav.pack(fill='x',padx=18)
        for text,step in [('◀',-1),('▶',1)]:
            tk.Button(nav,text=text,command=lambda v=step:self.move_step(v),font=('Segoe UI',13),bg='#273950',fg=INK,relief='flat',width=5).pack(side='left',padx=(0,8))
        tk.Button(nav,text='Показать всё',command=self.show_all,font=('Segoe UI',10),bg='#273950',fg=INK,relief='flat').pack(side='left',fill='x',expand=True)
        self.step_slider=tk.Scale(side,from_=0,to=0,orient='horizontal',command=self.slider_changed,showvalue=False,bg=PANEL,fg=INK,troughcolor='#273950',highlightthickness=0,activebackground=ACCENT)
        self.step_slider.pack(fill='x',padx=17)
        self.step_info=tk.Label(side,text='',wraplength=275,justify='left',bg=PANEL,fg=INK,font=('Consolas',9),anchor='nw')
        self.step_info.pack(fill='x',padx=18,pady=8)
        lbl('РЕЗУЛЬТАТ',True)
        self.stats=tk.Label(side,text='',justify='left',anchor='nw',wraplength=275,bg=PANEL,fg=MUTED,font=('Segoe UI',10))
        self.stats.pack(fill='x',padx=18,pady=(3,5))
        tk.Label(side,text='Прокрутка мыши — масштаб\nЛКМ + перетаскивание — панорама\n←/→ — предыдущий/следующий шаг',justify='left',bg=PANEL,fg=MUTED,font=('Segoe UI',9)).pack(side='bottom',anchor='w',padx=18,pady=20)
        bar=tk.Frame(canvas_frame,bg=PANEL);bar.pack(fill='x',padx=14,pady=(12,4))
        tk.Label(bar,text='Координатная плоскость',font=('Segoe UI',12,'bold'),bg=PANEL,fg=INK).pack(side='left')
        for text,cmd in [('−',lambda:self.zoom(1/1.2)),('+',lambda:self.zoom(1.2)),('Центр',self.reset_view)]:
            tk.Button(bar,text=text,command=cmd,bg='#273950',fg=INK,relief='flat',padx=11).pack(side='right',padx=3)
        self.canvas=tk.Canvas(canvas_frame,bg='#0c1626',highlightthickness=0)
        self.canvas.pack(fill='both',expand=True,padx=10,pady=(3,9))
        self.canvas.bind('<MouseWheel>',lambda e:self.zoom(1.2 if e.delta>0 else 1/1.2))
        self.canvas.bind('<Button-4>',lambda e:self.zoom(1.2));self.canvas.bind('<Button-5>',lambda e:self.zoom(1/1.2))
        self.canvas.bind('<ButtonPress-1>',lambda e:setattr(self,'drag',(e.x,e.y,self.pan_x,self.pan_y)))
        self.canvas.bind('<B1-Motion>',self.drag_view)
        self.canvas.bind('<Configure>',lambda e:self.redraw())
        footer=tk.Label(canvas_frame,textvariable=self.status,font=('Segoe UI',9),fg=MUTED,bg=PANEL,anchor='w')
        footer.pack(fill='x',padx=15,pady=(0,9))

    def update_fields(self):
        for child in self.fields.winfo_children():child.destroy()
        circ=self.algorithm.get()==ALGORITHMS[3]
        for name in (['x1','y1','R'] if circ else ['x1','y1','x2','y2']):
            row=tk.Frame(self.fields,bg=PANEL); row.pack(fill='x',pady=3)
            label=('Центр X' if name=='x1' else 'Центр Y' if name=='y1' else 'Радиус' if name=='R' else name.upper()) if circ else name.upper()
            tk.Label(row,text=label,width=12,anchor='w',bg=PANEL,fg=MUTED,font=('Segoe UI',10)).pack(side='left')
            ent=tk.Entry(row,textvariable=self.vars[name],bg='#243248',fg=INK,insertbackground=INK,relief='flat',font=('Consolas',11),width=12)
            ent.pack(side='right',ipady=5,fill='x',expand=True)
            ent.bind('<Return>',lambda e:self.compute())

    def get_data(self):
        is_circle=self.algorithm.get()==ALGORITHMS[3]
        names=['x1','y1','R'] if is_circle else ['x1','y1','x2','y2']
        values=[int(self.vars[n].get().strip()) for n in names]
        if any(abs(v)>100000 for v in values):raise ValueError('Координаты и радиус по модулю не более 100000')
        if is_circle and values[2]<0:raise ValueError('Радиус должен быть неотрицательным')
        return values

    def compute(self):
        try:
            values=self.get_data()
            fun=[step_by_step,dda,bresenham,bresenham_circle][ALGORITHMS.index(self.algorithm.get())]
            self.steps=fun(*values)
            self.index=len(self.steps)
            self.step_slider.configure(to=len(self.steps));self.step_slider.set(self.index)
            self.stats.config(text=f'Шагов: {len(self.steps)}\nУникальных пикселей: {len(unique_pixels(self.steps))}\nВсе концы включены; координаты целые.')
            self.status.set('Масштабируйте изображение колёсиком, перемещайте холст мышью.')
            self.update_step();self.redraw()
        except (ValueError,OverflowError) as exc:
            messagebox.showerror('Ошибка параметров',str(exc))

    def benchmark(self):
        try:
            fun=[step_by_step,dda,bresenham,bresenham_circle][ALGORITHMS.index(self.algorithm.get())]
            values=self.get_data()
            times=[]
            for _ in range(7):
                start=perf_counter_ns()
                for i in range(1000):fun(*values)
                times.append((perf_counter_ns()-start)/1000)
            value=median(times)/1000
            self.status.set(f'Медиана из 7 серий по 1000 запусков: {value:.2f} мкс/запуск (включая создание списка шагов).')
        except ValueError as exc: messagebox.showerror('Ошибка',str(exc))

    def slider_changed(self,v):
        self.index=int(float(v));self.update_step();self.redraw()
    def move_step(self,delta):self.step_slider.set(max(0,min(len(self.steps),self.index+delta)))
    def show_all(self):self.step_slider.set(len(self.steps))
    def update_step(self):
        if self.steps and self.index:
            self.step_info.config(text=self.steps[self.index-1].note)
        else:self.step_info.config(text=f'Шаг 0 / {len(self.steps)}\nПеред построением')

    def xy(self,x,y):
        w,h=self.canvas.winfo_width(),self.canvas.winfo_height()
        return w/2+self.pan_x+x*self.scale,h/2+self.pan_y-y*self.scale
    def zoom(self,factor):self.scale=max(7,min(95,self.scale*factor));self.redraw()
    def reset_view(self):self.pan_x=0;self.pan_y=0;self.scale=26;self.redraw()
    def drag_view(self,e):
        if hasattr(self,'drag'):
            px,py,ox,oy=self.drag;self.pan_x=ox+e.x-px;self.pan_y=oy+e.y-py;self.redraw()
    def on_resize(self,e):pass
    def redraw(self):
        c=self.canvas
        if not c.winfo_exists():return
        w,h=c.winfo_width(),c.winfo_height()
        if w<4 or h<4:return
        c.delete('all');s=self.scale
        import math
        xmin=math.floor((-w/2-self.pan_x)/s)-1;xmax=math.ceil((w/2-self.pan_x)/s)+1
        ymin=math.floor((-h/2+self.pan_y)/s)-1;ymax=math.ceil((h/2+self.pan_y)/s)+1
        # Границы дискретных ячеек лежат на полуцелых координатах.
        for x in range(xmin,xmax+1):
            sx,_=self.xy(x+0.5,0);c.create_line(sx,0,sx,h,fill=GRID)
        for y in range(ymin,ymax+1):
            _,sy=self.xy(0,y+0.5);c.create_line(0,sy,w,sy,fill=GRID)
        ox,oy=self.xy(0,0)
        c.create_line(ox,0,ox,h,fill='#60a5fa',width=2)
        c.create_line(0,oy,w,oy,fill='#60a5fa',width=2)
        every=1 if s>=22 else 2 if s>=12 else 5
        for x in range(xmin,xmax+1):
            if x%every==0:
                sx,_=self.xy(x,0)
                if 0<=sx<=w:
                    if x:c.create_text(sx,min(max(oy+13,12),h-8),text=str(x),fill=MUTED,font=('Consolas',8))
        for y in range(ymin,ymax+1):
            if y%every==0 and y:
                _,sy=self.xy(0,y)
                if 0<=sy<=h:c.create_text(min(max(ox-15,15),w-17),sy,text=str(y),fill=MUTED,font=('Consolas',8))
        c.create_text(min(w-12,ox+20),min(h-10,max(12,oy+13)),text='0',fill='#60a5fa',font=('Consolas',9))
        c.create_text(w-14,min(h-15,max(15,oy-15)),text='X',fill='#60a5fa',font=('Segoe UI',10,'bold'))
        c.create_text(min(w-16,max(16,ox+16)),12,text='Y',fill='#60a5fa',font=('Segoe UI',10,'bold'))
        if self.steps:
            current=set()
            for st in self.steps[:self.index]:current.update(st.pixels)
            latest=set(self.steps[self.index-1].pixels) if self.index else set()
            for x,y in current:
                sx,sy=self.xy(x,y)
                if -s<=sx<=w+s and -s<=sy<=h+s:
                    color=ACCENT if (x,y) in latest else PIXEL
                    c.create_rectangle(sx-s/2+0.8,sy-s/2+0.8,sx+s/2-0.8,sy+s/2-0.8,fill=color,outline='')
        c.create_text(13,h-13,anchor='sw',text=f'1 клетка = 1 × 1  ·  масштаб: {s:.1f} px/ед.',fill=MUTED,font=('Segoe UI',9))

if __name__=='__main__':
    root=tk.Tk();App(root);root.mainloop()
