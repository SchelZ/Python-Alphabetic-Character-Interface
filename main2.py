import tkinter as tk, matplotlib.colors as mcolors, os, threading, heapq
from tkinter import filedialog, LEFT, RIGHT
from collections import Counter
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class TreeCanvas(tk.Frame):
    def __init__(self, parent, root, title="Arbore"):
        super().__init__(parent)
        self.root = root

        # Canvas + Scrollbars
        self.canvas = tk.Canvas(self, bg="white", width=1200, height=600)
        self.hbar = tk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.vbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.config(xscrollcommand=self.hbar.set, yscrollcommand=self.vbar.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.hbar.grid(row=1, column=0, sticky="we")
        self.vbar.grid(row=0, column=1, sticky="ns")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.canvas.bind("<MouseWheel>", self.zoom)  # scroll zoom
        self.scale = 1.0

        self.draw_tree()

    def zoom(self, event):
        factor = 1.1 if event.delta > 0 else 0.9
        self.scale *= factor
        self.canvas.scale("all", 0, 0, factor, factor)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def draw_tree(self):
        canvas = self.canvas
        canvas.delete("all")

        root = self.root
        if not root: return

        # 1. Count leaves
        def count_leaves(node):
            if node is None: return 0
            if node.left is None and node.right is None: return 1
            return count_leaves(node.left) + count_leaves(node.right)

        # 2. Assign positions
        positions = {}
        x_step = 60
        y_step = 80
        def assign_x(node, depth, next_x):
            if node is None: return next_x
            if node.left is None and node.right is None:
                positions[node] = (next_x * x_step, depth * y_step)
                return next_x + 1
            next_x = assign_x(node.left, depth + 1, next_x)
            next_x = assign_x(node.right, depth + 1, next_x)
            lx, _ = positions[node.left]
            rx, _ = positions[node.right]
            positions[node] = ((lx + rx)/2, depth * y_step)
            return next_x

        assign_x(root, 0, 1)

        # Normalize margin
        min_x = min(pos[0] for pos in positions.values())
        for node in positions:
            x, y = positions[node]
            positions[node] = (x - min_x + 50, y + 30)

        # Draw edges (curved)
        for node, (x, y) in positions.items():
            if node.left:
                x2, y2 = positions[node.left]
                canvas.create_line(x, y, x2, y2, smooth=True)
            if node.right:
                x2, y2 = positions[node.right]
                canvas.create_line(x, y, x2, y2, smooth=True)

        # Draw nodes
        for node, (x, y) in positions.items():
            r = 20
            color = "#cfe6ff" if node.symbol else "#ffddb3"
            canvas.create_oval(x-r, y-r, x+r, y+r, fill=color, outline="#4a6fa5", width=2)
            text = f"{node.symbol}\n{node.freq}" if node.symbol else f"{node.freq}"
            canvas.create_text(x, y, text=text, font=("Arial", 9), justify="center")

class Node:
    def __init__(self, symbol=None, freq=0, left=None, right=None):
        self.symbol = symbol
        self.freq = freq
        self.left = left
        self.right = right

    def __lt__(self, other):
        return self.freq < other.freq
    
class BuildCompression:
    def __init__(self, letters: dict, symbols):
        self.symbols = symbols
        self.huffman_root = None
        self.shannon_root = None
        self.results_huffman, self.huffman_root = self.build_huffman()
        self.results_shannon, self.shannon_root = self.build_shannon_fano()

    def build_huffman(self):
        heap = [Node(c, f) for c, f in self.symbols]
        heapq.heapify(heap)
        while len(heap) > 1:
            left = heapq.heappop(heap)
            right = heapq.heappop(heap)
            heapq.heappush(heap, Node(None, left.freq + right.freq, left, right))
        root = heap[0] if heap else None
        codes = {}
        self._build_huffman_codes(root, "", codes)
        return codes, root

    def _build_huffman_codes(self, node, prefix, codes):
        if node is None: return
        if node.symbol is not None:
            codes[node.symbol] = int(prefix or "0")
            return
        self._build_huffman_codes(node.left, prefix + "0", codes)
        self._build_huffman_codes(node.right, prefix + "1", codes)

    def build_shannon_fano(self):
        total = sum(f for _, f in self.symbols)
        probs = [(c, f/total) for c, f in self.symbols]
        codes = {}
        self.shannon_root = self._recursive_shannon(probs, codes)
        return codes, self.shannon_root

    def _recursive_shannon(self, symbols, codes, prefix=""):
        if len(symbols) == 1:
            codes[symbols[0][0]] = prefix or "0"
            return Node(symbols[0][0], round(symbols[0][1], 2))
        total = sum(p for _, p in symbols)
        acc, split = 0, 0
        for i, (_, p) in enumerate(symbols):
            acc += p
            if acc >= total/2:
                split = i+1
                break
        left_node = self._recursive_shannon(symbols[:split], codes, prefix+"0")
        right_node = self._recursive_shannon(symbols[split:], codes, prefix+"1")
        return Node(None, round(total, 2), left_node, right_node)

    # ================= SHOW WINDOWS =====================
    def show_huffman_window(self):
        win = tk.Toplevel()
        win.title("Arbore Huffman")
        TreeCanvas(win, self.huffman_root).pack(fill="both", expand=True)
        txt = tk.Text(win, height=5)
        txt.pack(fill="x")
        for k, v in self.results_huffman.items():
            txt.insert("end", f"{k}: {v}\n")

    def show_shannon_window(self):
        win = tk.Toplevel()
        win.title("Arbore Shannon–Fano")
        TreeCanvas(win, self.shannon_root).pack(fill="both", expand=True)
        txt = tk.Text(win, height=5)
        txt.pack(fill="x")
        for k, v in self.results_shannon.items():
            txt.insert("end", f"{k}: {v}\n")


class InteractiveChart:
    """Chart with smooth height animation and hover tooltip."""

    def __init__(self, parent):
        self.parent = parent
        self.figure = Figure(figsize=(8, 3), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.parent)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.tooltip = tk.Label(parent, bg="#333", fg="white", padx=5, pady=2, font=("Segoe UI", 10))
        self.tooltip.place_forget()

        self.bars = []
        self.data = []
        self.animating = False

        self.canvas.mpl_connect("motion_notify_event", self.on_hover)

    def draw_chart(self, sorted_counts):
        """Initial chart draw."""
        self.ax.clear()
        letters = [l for l, _ in sorted_counts]
        counts = [c for _, c in sorted_counts]

        self.bars = self.ax.bar(letters, counts, color="#3a7bd5")
        self.data = sorted_counts

        self.ax.set_xlabel("Litere")
        self.ax.set_ylabel("Total")
        self.ax.set_title("Frecventa de aparitie")
        self.ax.grid(True, linestyle="--", alpha=0.5)
        self.canvas.draw()

    def update_chart_smooth(self, sorted_counts, steps=10, delay=30, on_complete=None):
        if self.animating: return 

        if not self.bars or len(self.bars) != len(sorted_counts):
            self.draw_chart(sorted_counts)
            if on_complete:
                on_complete()
            return

        current_heights = [bar.get_height() for bar in self.bars]
        new_heights = [c for _, c in sorted_counts]
        letters = [l for l, _ in sorted_counts]

        self.animating = True

        def step(i):
            factor = (i + 1) / steps
            for bar, h_old, h_new in zip(self.bars, current_heights, new_heights):
                bar.set_height(h_old + (h_new - h_old) * factor)

            self.ax.set_xticks(range(len(letters)))
            self.ax.set_xticklabels(letters)
            self.canvas.draw_idle()

            if i + 1 < steps:
                self.parent.after(delay, lambda: step(i + 1))
            else:
                self.animating = False
                self.data = sorted_counts
                if on_complete:
                    on_complete()
        step(0)

    def on_hover(self, event):
        if event.inaxes != self.ax:
            self.tooltip.place_forget()
            return

        hovered = None
        for bar, (letter, count) in zip(self.bars, self.data):
            if bar.contains(event)[0]:
                hovered = bar
                self.show_tooltip(event, f"{letter}: {count}")
                self.animate_color(bar, "#5ab4ff")
            else:
                self.animate_color(bar, "#3a7bd5")

        if hovered is None:
            self.tooltip.place_forget()

    def show_tooltip(self, event, text):
        self.tooltip.config(text=text)
        x = int(self.parent.winfo_pointerx() - self.parent.winfo_rootx() + 10)
        y = int(self.parent.winfo_pointery() - self.parent.winfo_rooty() - 10)
        self.tooltip.place(x=x, y=y)

    def animate_color(self, bar, target_color):
        start_color = mcolors.to_rgb(bar.get_facecolor())
        end_color = mcolors.to_rgb(target_color)
        new_color = tuple(start_color[i] + (end_color[i] - start_color[i]) * 0.5 for i in range(3))
        bar.set_facecolor(new_color)
        self.canvas.draw_idle()


class LetterCounterApp(tk.Tk):
    def __init__(self, debug=False):
        super().__init__()
        self.debug = debug
        self.title("BSI Lp 1")
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        
        self.sort_mode = tk.IntVar(value=0)
        self.counts = {}
        self.sorted_counts = []

        # Initialize both frames
        self.init_select_frame()
        self.init_results_frame()

        if debug:
            self.geometry("1200x700")
            self.process_file(f"{self.dir_path}/text.txt")
            self.show_results()
        else:
            self.geometry("600x400")
            self.show_select()

    def init_select_frame(self):
        """Frame for file selection"""
        self.frame_select = tk.Frame(self)
        tk.Label(self.frame_select, text="Select a text file", font=("Arial", 16)).pack(pady=20)
        tk.Button(self.frame_select, text="Select File", command=self.select_file, width=20, height=2).pack()
        self.file_label = tk.Label(self.frame_select, text="", wraplength=500)
        self.file_label.pack(pady=10)

    def init_results_frame(self):
        """Frame for results and chart"""
        self.frame_results = tk.Frame(self)

        top_bar = tk.Frame(self.frame_results)
        top_bar.pack(fill="x", pady=5)

        # Back button on the left
        self.back_button = tk.Button(top_bar, text="Back", command=self.go_back, width=10, height=1)
        self.back_button.pack(side="left", padx=5)

        # Character count in the center
        self.char_count_label = tk.Label(top_bar, text="Litere: 0", font=("Segoe UI", 10))
        self.char_count_label.pack(side="left", expand=True)

        # Missing letters on the right
        self.missing_letters_label = tk.Label(top_bar, text="", fg="red", font=("Segoe UI", 10))
        self.missing_letters_label.pack(side="right", padx=15)
        
        text_row = tk.Frame(self.frame_results)
        text_row.pack(fill="x", padx=10, pady=5)
        self.results_text = tk.Text(text_row, wrap="word", height=10, width=60)
        self.results_text.pack(side="left", fill="both", expand=True, padx=(0,5))

        self.shanon_text = tk.Text(text_row, wrap="word", height=10, width=60)
        self.shanon_text.pack(side="left", fill="both", expand=True, padx=(5,0))

        self.chart_frame = tk.Frame(self.frame_results)
        self.chart_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.chart_widget = InteractiveChart(self.chart_frame)

        self.create_sort_buttons(self.frame_results)

    def show_select(self):
        """Show select frame"""
        self.frame_results.pack_forget()
        self.geometry("600x400")
        self.frame_select.pack(fill="both", expand=True)

    def show_results(self):
        """Show results frame"""
        self.frame_select.pack_forget()
        self.geometry("1200x700")
        self.frame_results.pack(fill="both", expand=True)
        total_chars = sum(self.counts.values())


        def update_text():
            self.results_text.delete("1.0", tk.END)
            for letter, count in self.sorted_counts:
                prob = count / total_chars
                self.results_text.insert(tk.END, f"{letter}: {prob:.4f}\n")

        self.chart_widget.update_chart_smooth(self.sorted_counts, on_complete=update_text)

    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="Selecteaza un fisier",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
        )
        if file_path:
            self.file_label.config(text=f"Fisierul selectat este:\n{file_path}")
            self.process_file(file_path)
            
            self.show_results()

    def process_file(self, file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            text = file.read()
            clean_text = [c.lower() for c in text if c.lower() in "abcdefghijklmnopqrstuvwxyzăâîșț"]
            self.counts = Counter(clean_text)
            self.sorted_counts = sorted(self.counts.items(), key=lambda x: x[1], reverse=True)

            # Litere lipsă din alfabetul român
            self.missing_letters_label.config(
                text="Litere lipsă: " + ", ".join(
                    sorted(set("aăâbcdefghiîjklmnopqrsștțuvwxyz") - self.counts.keys())
                )
            )

            self.char_count_label.config(text=f"Litere: {self.counts.total()}")
            self.compression = BuildCompression(self.counts, self.sorted_counts)
            self.create_compression_buttons()
            
    def create_sort_buttons(self, parent):
        sort_frame = tk.Frame(parent)
        sort_frame.pack(pady=10)

        tk.Label(sort_frame, text="Sortare:").pack(side=LEFT, padx=5)
        tk.Radiobutton(sort_frame, text="Descrescator ↓", variable=self.sort_mode, value=0, command=self.update_sort).pack(side=LEFT)
        tk.Radiobutton(sort_frame, text="Crescator ↑", variable=self.sort_mode, value=1, command=self.update_sort).pack(side=LEFT)
        tk.Radiobutton(sort_frame, text="Litera A–Z", variable=self.sort_mode, value=2, command=self.update_sort).pack(side=LEFT)
        tk.Radiobutton(sort_frame, text="Litera Z–A", variable=self.sort_mode, value=3, command=self.update_sort).pack(side=LEFT)


    def create_compression_buttons(self):
        # Verificăm dacă butoanele există deja ca să nu le creăm de două ori
        if hasattr(self, "compression_btn_frame"):
            return

        self.compression_btn_frame = tk.Frame(self.frame_results)
        self.compression_btn_frame.pack(pady=10)

        tk.Button(self.compression_btn_frame, text="Arbore Huffman", width=20, height=2,
                  command=self.compression.show_huffman_window).pack(side=tk.LEFT, padx=10)

        tk.Button(self.compression_btn_frame, text="Arbore Shannon–Fano", width=20, height=2,
                  command=self.compression.show_shannon_window).pack(side=tk.LEFT, padx=10)

    def update_sort(self):
        match self.sort_mode.get():
            case 0:
                self.sorted_counts = sorted(self.counts.items(), key=lambda x: x[1], reverse=True)
            case 1:
                self.sorted_counts = sorted(self.counts.items(), key=lambda x: x[1])
            case 2:
                self.sorted_counts = sorted(self.counts.items(), key=lambda x: x[0])
            case 3:
                self.sorted_counts = sorted(self.counts.items(), key=lambda x: x[0], reverse=True)
            case _: pass

        self.show_results()

    def go_back(self):
        self.show_select()


if __name__ == "__main__":
    app = LetterCounterApp(debug=True)
    app.mainloop()
