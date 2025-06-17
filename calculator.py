import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sympy as sp
from sympy import *
import math
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import io
import base64
import os


class SymPyCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("科学计算器")
        self.root.geometry("600x800")

        #self.root.iconbitmap('icon.ico')
        self.root.configure(bg='#f0f0f0')
        
        # 设置窗口最小安全尺寸
        self.root.minsize(400, 800)
        
        # 创建符号变量
        self.x, self.y, self.z = symbols('x y z')
        self.t = symbols('t')
        
        # 历史记录
        self.history = []
        
        # LaTeX显示设置
        self.latex_enabled = tk.BooleanVar(value=True)
        
        self.setup_ui()
        self.bind_keyboard()
        
        # 修复焦点问题：确保窗口完全加载后设置焦点
        self.root.after(100, self.set_initial_focus)
        
    def set_initial_focus(self):
        """设置初始焦点到输入框"""
        self.entry.focus_set()  # 使用focus_set而不是focus_force
        self.entry.icursor(tk.END)  # 将光标移到末尾
        
    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=0)  # 显示区
        main_frame.rowconfigure(2, weight=1)  # 按钮区和右侧区
        main_frame.columnconfigure(0, weight=1)  # 左侧按钮区
        main_frame.columnconfigure(1, weight=1)  # 右侧历史记录区
        
        # 顶部设置框架
        settings_frame = ttk.Frame(main_frame)
        settings_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        # LaTeX开关
        latex_check = ttk.Checkbutton(settings_frame, text="启用LaTeX显示", 
                                     variable=self.latex_enabled,
                                     command=self.toggle_latex)
        latex_check.grid(row=0, column=0, sticky=tk.W)
        
        # 显示区域
        display_frame = ttk.LabelFrame(main_frame, text="显示区", padding="5")
        display_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        display_frame.columnconfigure(0, weight=1)
        display_frame.columnconfigure(1, weight=1)
        
        # 输入框 - 修复鼠标控制问题
        self.entry = tk.Entry(display_frame, font=("Arial", 14), width=60)  # 原为80，缩小宽度
        self.entry.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # 移除可能干扰鼠标交互的事件绑定
        self.entry.bind("<FocusIn>", self.on_entry_focus_in)
        
        # 输入表达式显示标签（纯文本显示输入）
        self.input_display_var = tk.StringVar()
        self.input_display_label = ttk.Label(display_frame, textvariable=self.input_display_var, 
                                           font=("Arial", 12), foreground="black")
        self.input_display_label.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(2, 0))
        
        # LaTeX显示区域框架（仅用于结果）
        latex_frame = ttk.Frame(display_frame)
        latex_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # 创建matplotlib图形用于LaTeX渲染
        self.latex_fig = Figure(figsize=(7, 1), facecolor='white')  # 原为(8, 1)，缩小宽度
        self.latex_ax = self.latex_fig.add_subplot(111)
        self.latex_ax.axis('off')
        
        self.latex_canvas = FigureCanvasTkAgg(self.latex_fig, latex_frame)
        self.latex_canvas.get_tk_widget().grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # 传统文本结果显示（备用）
        self.result_var = tk.StringVar()
        self.result_label = ttk.Label(display_frame, textvariable=self.result_var, 
                                     font=("Arial", 12), foreground="blue")
        self.result_label.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # 左侧按钮面板
        # button_frame = ttk.LabelFrame(main_frame, text="功能按钮", padding="5")
        # button_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        button_frame = ttk.LabelFrame(main_frame, text="功能按钮")
        button_frame.grid(row=2, column=0, sticky=(tk.N, tk.S, tk.W, tk.E))
        button_frame.rowconfigure(0, weight=1)
        button_frame.columnconfigure(0, weight=1)
        
        # 基础运算按钮
        basic_buttons = [
            ('7', '8', '9', '/'),
            ('4', '5', '6', '*'),
            ('1', '2', '3', '-'),
            ('0', '.', '=', '+'),
            ('(', ')', 'C', '←')
        ]
        basic_frame = ttk.LabelFrame(button_frame, text="基础运算", padding="5")
        basic_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        basic_frame.columnconfigure((0,1,2,3), weight=1)  # 让按钮等宽自适应
        for i, row in enumerate(basic_buttons):
            basic_frame.rowconfigure(i, weight=1)  # 行自适应
            for j, btn_text in enumerate(row):
                btn = ttk.Button(basic_frame, text=btn_text, 
                               command=lambda t=btn_text: self.button_click(t))
                btn.grid(row=i, column=j, padx=2, pady=2, sticky=(tk.N, tk.S, tk.W, tk.E))
        
        # 科学计算按钮
        sci_buttons = [
            ('sin', 'cos', 'tan', 'π'),
            ('asin', 'acos', 'atan', 'e'),
            ('ln', 'log', 'exp', '^'),
            ('sqrt', '²', '!', 'abs'),
        ]
        sci_frame = ttk.LabelFrame(button_frame, text="科学计算", padding="5")
        sci_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        sci_frame.columnconfigure((0,1,2,3), weight=1)
        for i, row in enumerate(sci_buttons):
            sci_frame.rowconfigure(i, weight=1)
            for j, btn_text in enumerate(row):
                btn = ttk.Button(sci_frame, text=btn_text,
                               command=lambda t=btn_text: self.sci_button_click(t))
                btn.grid(row=i, column=j, padx=2, pady=2, sticky=(tk.N, tk.S, tk.W, tk.E))
        
        # 高级功能按钮
        adv_buttons = [
            ('diff', 'integrate', 'limit', 'solve'),
            ('expand', 'factor', 'simplify', 'subs'),
            ('idiff',)
        ]
        adv_frame = ttk.LabelFrame(button_frame, text="高级功能", padding="5")
        adv_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        adv_frame.columnconfigure((0,1,2,3), weight=1)
        for i, row in enumerate(adv_buttons):
            adv_frame.rowconfigure(i, weight=1)
            for j, btn_text in enumerate(row):
                btn = ttk.Button(adv_frame, text=btn_text,
                               command=lambda t=btn_text: self.adv_button_click(t))
                btn.grid(row=i, column=j, padx=2, pady=2, sticky=(tk.N, tk.S, tk.W, tk.E))

        # 右侧面板
        self.right_frame = ttk.Frame(main_frame)
        self.right_frame.grid(row=2, column=1, sticky=(tk.N, tk.S, tk.W, tk.E), padx=5)
        # 移除固定宽度和grid_propagate
        self.right_frame.rowconfigure(0, weight=1)
        self.right_frame.columnconfigure(0, weight=1)
        
        header_frame = tk.Frame(self.right_frame, height=50, width=10)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        header_frame.pack_propagate(False)

        # 历史记录按钮
        self.history_btn = tk.Button(header_frame, text="历史记录", 
                                    command=lambda: self.switch_right_panel('history'),
                                    )
        self.history_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 使用说明按钮
        self.help_btn = tk.Button(header_frame, text="使用说明",
                                 command=lambda: self.switch_right_panel('help'),
                                 )
        self.help_btn.pack(side=tk.LEFT)
        
        # 内容区域
        self.content_frame = tk.Frame(self.right_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # 历史记录面板
        self.history_panel = tk.Frame(self.content_frame)
        self.history_panel.pack(fill=tk.BOTH, expand=True)
        
        # 历史记录文本框
        self.history_text = scrolledtext.ScrolledText(
            self.history_panel, 
            wrap=tk.WORD,
            width=50,  # 控制每行显示字符数，缩小宽度
            height=26
        )
        self.history_text.pack(fill=tk.BOTH, expand=True)
        
        # 清除历史按钮
        clear_history_btn = tk.Button(self.history_panel, text="清除历史记录",
                                     command=self.clear_history,
                                     )
        clear_history_btn.pack(pady=(10, 0))
        
        # 使用说明面板
        self.help_panel = tk.Frame(self.content_frame)
        
        help_text = """基础运算：
• 数字和运算符：+, -, *, /, (), ^(幂运算)
• 快捷键：Enter计算, Esc清除

科学函数：
• 三角函数：sin, cos, tan, asin, acos, atan
• 对数函数：ln(自然对数), log10(常用对数), exp
• 其他：sqrt(平方根), abs(绝对值), factorial(阶乘)

常数：
• π(pi) - 圆周率
• e(E) - 自然常数  
• ∞(oo) - 无穷大

微积分：
• d/dx - 对x求导
• ∫ - 对x积分
• limit(f,x,a) - 求f在x→a时的极限
• idiff(F,y,x) - 隐函数y对x求导

代数运算：
• solve(eq,x) - 求解方程
• expand() - 展开表达式
• factor() - 因式分解
• simplify() - 简化表达式
• subs() - 变量替换

变量：
• 默认变量：x, y, z, t
• 可直接在表达式中使用

LaTeX显示：
• 结果以LaTeX格式美化显示
• 分数：1/2 显示为 ½
• 幂次：x^2 显示为 x²
• 根号：sqrt(x) 显示为 √x

示例：
• 基础：2+3*4, sin(pi/2)
• 微积分：diff(x^2, x), integrate(x^2, x)
          idiff(x+y^2, y, x)
• 求解：solve(x^2-4, x)
• 因式分解：factor(x^2-4)

注意：需要matplotlib库支持LaTeX渲染"""
        
        self.help_text = scrolledtext.ScrolledText(
            self.help_panel,
            wrap=tk.WORD,
            state=tk.DISABLED,
            width=50,
            height=28
        )
        self.help_text.pack(fill=tk.BOTH, expand=True)
        
        # 插入帮助文本
        self.help_text.config(state=tk.NORMAL)
        self.help_text.insert(tk.END, help_text)
        self.help_text.config(state=tk.DISABLED)
        
        # 初始显示历史记录
        self.switch_right_panel('history')

        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪 - LaTeX显示已启用")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        
    def switch_right_panel(self, mode):
        """切换右侧面板显示模式"""
        self.right_panel_mode = mode
        
        # 隐藏所有面板
        self.history_panel.pack_forget()
        self.help_panel.pack_forget()
        
        # 重置按钮样式
        self.history_btn.config()
        self.help_btn.config()
        
        # 显示对应面板并高亮按钮
        if mode == 'history':
            self.history_panel.pack(fill=tk.BOTH, expand=True)
            self.history_btn.config()
        else:
            self.help_panel.pack(fill=tk.BOTH, expand=True)
            self.help_btn.config()
        
    def toggle_latex(self):
        """切换LaTeX显示模式"""
        if self.latex_enabled.get():
            self.status_var.set("就绪 - LaTeX显示已启用")
            self.latex_canvas.get_tk_widget().grid()
            self.result_label.grid_remove()
        else:
            self.status_var.set("就绪 - LaTeX显示已禁用")
            self.latex_canvas.get_tk_widget().grid_remove()
            self.result_label.grid()
            
    def render_latex(self, result):
        """渲染LaTeX公式 - 仅渲染结果部分"""
        try:
            # 清除之前的内容
            self.latex_ax.clear()
            self.latex_ax.axis('off')
            
            # 只转换结果为LaTeX格式
            result_latex = sp.latex(result) if hasattr(result, '__class__') else sp.latex(sp.sympify(str(result)))
            
            # 构建LaTeX字符串（只显示结果）
            full_latex = f"$= {result_latex}$"
            
            # 在图形中显示LaTeX
            self.latex_ax.text(0.05, 0.5, full_latex, fontsize=16, 
                              transform=self.latex_ax.transAxes,
                              verticalalignment='center',
                              bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue"))
            
            # 调整布局并刷新
            self.latex_fig.tight_layout()
            self.latex_canvas.draw()
            
            return True
            
        except Exception as e:
            print(f"LaTeX渲染错误: {e}")
            # 如果LaTeX渲染失败，显示纯文本
            self.latex_ax.clear()
            self.latex_ax.axis('off')
            text_display = f"= {result}"
            self.latex_ax.text(0.05, 0.5, text_display, fontsize=12,
                              transform=self.latex_ax.transAxes,
                              verticalalignment='center',
                              bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
            self.latex_fig.tight_layout()
            self.latex_canvas.draw()
            return False
    
    def on_entry_focus_in(self, event):
        """处理输入框获得焦点事件"""
        status_text = "就绪 - 可以输入"
        if self.latex_enabled.get():
            status_text += " (LaTeX已启用)"
        self.status_var.set(status_text)
        
    def bind_keyboard(self):
        """绑定键盘事件 - 修复版本，减少对鼠标交互的干扰"""
        # 只绑定到entry，避免全局键盘事件干扰鼠标操作
        self.entry.bind('<Return>', lambda e: self.calculate())
        self.entry.bind('<Escape>', lambda e: self.clear())
        
        # 绑定窗口激活事件，但不强制设置焦点
        self.root.bind('<FocusIn>', self.on_window_focus)
        
    def on_window_focus(self, event):
        """窗口获得焦点时的处理 - 温和版本"""
        # 只有当当前没有其他控件有焦点时，才设置焦点到输入框
        if event.widget == self.root and self.root.focus_get() is None:
            self.root.after(10, lambda: self.entry.focus_set())
        
    def button_click(self, text):
        """处理基础按钮点击"""
        # 点击按钮后确保输入框获得焦点，但不强制
        self.entry.focus_set()
        
        if text == '=':
            self.calculate()
        elif text == 'C':
            self.clear()
        elif text == '←':
            self.backspace()
        else:
            self.insert_text(text)
            
    def sci_button_click(self, text):
        """处理科学计算按钮点击"""
        self.entry.focus_set()
        
        mappings = {
            'π': 'pi',
            'e': 'E',
            '^': '**',
            '²': '**2',
            '!': '!',
            'sqrt': 'sqrt(',
            'ln': 'log(',
            'log': 'log10(',
            'exp': 'exp(',
            'abs': 'abs('
        }
        
        if text in mappings:
            self.insert_text(mappings[text])
        elif text in ['sin', 'cos', 'tan', 'asin', 'acos', 'atan']:
            self.insert_text(f'{text}(')
        else:
            self.insert_text(text)
            
    def adv_button_click(self, text):
        """处理高级功能按钮点击"""
        self.entry.focus_set()
        
        current = self.entry.get()
        
        if text == 'diff':
            # 求导
            if 'x' not in current:
                current += 'x'
            self.entry.delete(0, tk.END)
            self.entry.insert(0, f'diff({current}, x)')
        elif text == 'integrate':
            # 积分
            if 'x' not in current:
                current += 'x'
            self.entry.delete(0, tk.END)
            self.entry.insert(0, f'integrate({current}, x)')
        elif text == 'limit':
            # 极限
            if 'x' not in current:
                current += 'x'
            self.entry.delete(0, tk.END)
            self.entry.insert(0, f'limit({current}, x, 0)')
        elif text == 'solve':
            # 求解方程
            if 'x' not in current:
                current += 'x'
            self.entry.delete(0, tk.END)
            self.entry.insert(0, f'solve({current}, x)')
        elif text == 'expand':
            # 展开
            self.entry.delete(0, tk.END)
            self.entry.insert(0, f'expand({current})')
        elif text == 'factor':
            # 因式分解
            self.entry.delete(0, tk.END)
            self.entry.insert(0, f'factor({current})')
        elif text == 'simplify':
            # 简化
            self.entry.delete(0, tk.END)
            self.entry.insert(0, f'simplify({current})')
        elif text == 'subs':
            # 替换（示例：将x替换为1）
            self.entry.delete(0, tk.END)
            self.entry.insert(0, f'({current}).subs(x, 1)')
        elif text == 'idiff':
            # 隐函数求导
            self.entry.delete(0, tk.END)
            self.entry.insert(0, f'idiff({current},y, x)')

    def insert_text(self, text):
        """在光标位置插入文本"""
        cursor_pos = self.entry.index(tk.INSERT)
        self.entry.insert(cursor_pos, text)
        
    def clear(self):
        """清除输入"""
        self.entry.delete(0, tk.END)
        self.result_var.set("")
        self.input_display_var.set("")
        
        # 清除LaTeX显示
        if self.latex_enabled.get():
            self.latex_ax.clear()
            self.latex_ax.axis('off')
            self.latex_canvas.draw()
        
        status_text = "已清除"
        if self.latex_enabled.get():
            status_text += " (LaTeX已启用)"
        self.status_var.set(status_text)
        
        # 清除后确保焦点仍在输入框
        self.entry.focus_set()
        
    def backspace(self):
        """删除一个字符"""
        cursor_pos = self.entry.index(tk.INSERT)
        if cursor_pos > 0:
            self.entry.delete(cursor_pos-1, cursor_pos)
            
    def calculate(self):
        """执行计算"""
        expression = self.entry.get().strip()
        if not expression:
            return
            
        try:
            self.status_var.set("计算中...")
            
            # 显示输入表达式（纯文本）
            self.input_display_var.set(f"输入: {expression}")
            
            # 预处理表达式
            processed_expr = self.preprocess_expression(expression)
            
            # 使用SymPy计算
            result = self.evaluate_expression(processed_expr)
            
            # 显示结果
            result_str = str(result)
            
            if self.latex_enabled.get():
                # 使用LaTeX显示结果
                success = self.render_latex(result)
                if not success:
                    self.result_var.set(f"{result_str}")
                else:
                    self.result_var.set("")  # 清除文本显示
            else:
                # 使用传统文本显示
                self.result_var.set(f"= {result_str}")
                # 清除LaTeX显示区域
                self.latex_ax.clear()
                self.latex_ax.axis('off')
                self.latex_canvas.draw()
            
            # 添加到历史记录
            self.add_to_history(expression, result_str)
            
            status_text = "计算完成"
            if self.latex_enabled.get():
                status_text += " (LaTeX显示)"
            self.status_var.set(status_text)
            
        except Exception as e:
            error_msg = f"错误: {str(e)}"
            self.result_var.set(error_msg)
            self.status_var.set("计算出错")
            self.input_display_var.set(f"输入: {expression}")
            
            # 清除LaTeX显示区域的错误内容
            if self.latex_enabled.get():
                self.latex_ax.clear()
                self.latex_ax.axis('off')
                self.latex_ax.text(0.05, 0.5, f"计算错误: {str(e)}", fontsize=12,
                                  transform=self.latex_ax.transAxes,
                                  verticalalignment='center',
                                  bbox=dict(boxstyle="round,pad=0.3", facecolor="lightcoral"))
                self.latex_canvas.draw()
            
            messagebox.showerror("计算错误", error_msg)
        
        # 计算后确保焦点回到输入框
        self.entry.focus_set()
            
    def preprocess_expression(self, expr):
        """预处理表达式"""
        # 替换常用数学符号
        replacements = [
            ('π', 'pi'),
            ('∞', 'oo'),
            ('×', '*'),
            ('÷', '/'),
            ('log10', 'log10'),
            ('!', '!'),  # 阶乘会在evaluate中处理
        ]
        
        for old, new in replacements:
            expr = expr.replace(old, new)
            
        return expr
        
    def evaluate_expression(self, expr):
        """使用SymPy计算表达式"""
        # 创建安全的命名空间
        namespace = {
            # 基本符号
            'x': self.x, 'y': self.y, 'z': self.z, 't': self.t,
            # 常数
            'pi': sp.pi, 'e': sp.E, 'I': sp.I, 'oo': sp.oo,
            # 基本函数
            'sin': sp.sin, 'cos': sp.cos, 'tan': sp.tan,
            'asin': sp.asin, 'acos': sp.acos, 'atan': sp.atan,
            'sinh': sp.sinh, 'cosh': sp.cosh, 'tanh': sp.tanh,
            'log': sp.log, 'log10': lambda x: sp.log(x, 10),
            'ln': sp.log, 'exp': sp.exp,
            'sqrt': sp.sqrt, 'abs': sp.Abs,
            'factorial': sp.factorial,
            # 微积分函数
            'diff': sp.diff, 'integrate': sp.integrate,
            'limit': sp.limit, 'series': sp.series,
            'idiff': sp.idiff,
            # 代数函数
            'solve': sp.solve, 'expand': sp.expand,
            'factor': sp.factor, 'simplify': sp.simplify,
            'cancel': sp.cancel, 'apart': sp.apart,
            # 矩阵函数
            'Matrix': sp.Matrix, 'det': lambda m: m.det(),
            # 其他有用函数
            'summation': sp.summation, 'product': sp.product,
        }
        
        # 处理阶乘
        if '!' in expr:
            # 简单处理阶乘
            import re
            expr = re.sub(r'(\d+)!', r'factorial(\1)', expr)
            expr = re.sub(r'([a-zA-Z_][a-zA-Z0-9_]*)!', r'factorial(\1)', expr)
        
        # 计算表达式
        try:
            result = eval(expr, {"__builtins__": {}}, namespace)
            
            # 如果结果是SymPy表达式，尝试数值化
            if hasattr(result, 'evalf'):
                try:
                    numeric_result = result.evalf()
                    # 如果数值结果比符号结果更简单，返回数值结果
                    if len(str(numeric_result)) < len(str(result)) and numeric_result.is_real:
                        return numeric_result
                except:
                    pass
            
            return result
            
        except Exception as e:
            # 如果直接计算失败，尝试作为SymPy表达式解析
            try:
                parsed = sp.sympify(expr, locals=namespace)
                return parsed.evalf() if parsed.is_number else parsed
            except:
                raise e
                
    def add_to_history(self, expression, result):
        """添加到历史记录"""
        history_entry = f"{expression} = {result}\n"
        self.history.append(history_entry)
        self.history_text.insert(tk.END, history_entry)
        self.history_text.see(tk.END)
        
        # 限制历史记录数量
        if len(self.history) > 100:
            self.history.pop(0)
            
    def clear_history(self):
        """清除历史记录"""
        self.history.clear()
        self.history_text.delete(1.0, tk.END)
        status_text = "历史记录已清除"
        if self.latex_enabled.get():
            status_text += " (LaTeX已启用)"
        self.status_var.set(status_text)
        # 清除历史后确保焦点回到输入框
        self.entry.focus_set()

def main():
    root = tk.Tk()
    app = SymPyCalculator(root)
    root.mainloop()

if __name__ == "__main__":
    main()