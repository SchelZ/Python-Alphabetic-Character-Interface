# 🇷🇴 Romanian Letter Frequency Analyzer

A modern Tkinter application that analyzes a `.txt` file and displays the **frequency of each Romanian alphabet letter** in an **interactive animated bar chart**.

## 🚀 Features

* File picker to load any `.txt` file
* Counts Romanian-specific letters (ă â î ș ț)
* Animated Matplotlib bar chart
* Hover tooltip with live count
* Smooth color transition on bar hover
* Shows total letters + missing letters
* Sorting options:

  * 🔽 Frequency Descending
  * 🔼 Frequency Ascending
  * 🔤 Alphabetical A–Z
  * 🔡 Alphabetical Z–A

## 🖥️ UI Overview

| Section     | Purpose                                       |
| ----------- | --------------------------------------------- |
| **Top Bar** | Back button · Total letters · Missing letters |
| **Middle**  | Probability list (`count / total`)            |
| **Bottom**  | Interactive animated chart                    |

## 📦 Installation

```bash
pip install matplotlib
```

(Requires Python 3 + Tkinter and collections comes preinstalled)

## 📦For Linux You Have To Install Tkinter Library
```bash
sudo apt install python3-tk
```

## ▶️ Run

```bash
python main.py
```

## 🧠 Code Structure

* `InteractiveChart` → handles chart, hover, animation
* `LetterCounterApp` → UI, file selection, processing, sorting

---
