import tkinter as tk, os
from tkinter import filedialog, LEFT
from collections import Counter
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.colors as mcolors


class InteractiveChart:
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
        
        self.results_text = tk.Text(self.frame_results, wrap="word", height=10)
        self.results_text.pack(fill="x", padx=10, pady=5)

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


    def create_sort_buttons(self, parent):
        sort_frame = tk.Frame(parent)
        sort_frame.pack(pady=10)

        tk.Label(sort_frame, text="Sortare:").pack(side=LEFT, padx=5)
        tk.Radiobutton(sort_frame, text="Descrescator ↓", variable=self.sort_mode, value=0, command=self.update_sort).pack(side=LEFT)
        tk.Radiobutton(sort_frame, text="Crescator ↑", variable=self.sort_mode, value=1, command=self.update_sort).pack(side=LEFT)
        tk.Radiobutton(sort_frame, text="Litera A–Z", variable=self.sort_mode, value=2, command=self.update_sort).pack(side=LEFT)
        tk.Radiobutton(sort_frame, text="Litera Z–A", variable=self.sort_mode, value=3, command=self.update_sort).pack(side=LEFT)

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

