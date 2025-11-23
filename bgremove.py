# from tkinter import *
# from tkinter import Tk
# from tkinter import filedialog,messagebox
# from PIL import Image, ImageTk
# from rembg import remove

# def choose_file():
#     global input_path
#     input_path=filedialog.askopenfilename(title="Select Image", filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp")])
#     if input_path:
#         preview_image(input_path)
#         status_label.config(text="Image selected. Click 'Remove Background' to proceed.")
# def remove_bg():
#     if not input_path:
#         messagebox.showwarning("No Image", "Please select an image first.")
#         return
#     try:
#         with open(input_path, "rb") as i:
#             input_image = i.read()
#         output_image = remove(input_image)
#         output_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Files", "*.png")], title="Save Image As")
#         if output_path:
#             with open(output_path, "wb") as o:
#                 o.write(output_image)
#             messagebox.showinfo("Success", "Background removed and image saved successfully.")
#     except Exception as e:
#         messagebox.showerror("Error", f"An error occurred: {e}")         
# def preview_image(path):
#     img = Image.open(path)
#     img.thumbnail((300, 300))
#     img_tk = ImageTk.PhotoImage(img)
#     image_label.config(image=img_tk)
#     image_label.image = img_tk  
# root = TK()
# root.title("Background Remover")
# root.geometry("400x500")
# input_path=""
# title_label=Label(root,text="Background Remover",font=("Arial",20))
# title_label.pack(pady=10)
# image_label=Label(root)
# image_label.pack(pady=10)
# choose_button=Button(root,text="Choose Image",command=choose_file)
# choose_button.pack(pady=10)
# remove_button=Button(root,text="Remove Background",command=remove_bg)
# remove_button.pack(pady=10)
# status_label=Label(root,text="No image selected.",font=("Arial",12))
# status_label.pack(pady=10)
# root.mainloop()
from tkinter import *
from tkinter import filedialog, messagebox, font as tkfont, ttk
from PIL import Image, ImageTk
from rembg import remove
import threading
import os
from pathlib import Path
import time
import random

def choose_file():
    global input_path
    input_path = filedialog.askopenfilename(
        title="Select Image",
        filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp")]
    )
    if input_path:
        preview_image(input_path)
        status_label.config(text="Image selected. Click 'Remove Background' to continue.")

def remove_bg():
    if not input_path:
        messagebox.showwarning("No Image", "Please select an image first.")
        return

    # Ask where to save BEFORE starting background work (file dialog must run on main thread)
    output_path = filedialog.asksaveasfilename(
        defaultextension=".png",
        filetypes=[("PNG Files", "*.png")],
        title="Save Image As"
    )
    if not output_path:
        return

    def worker(in_path, out_path):
        try:
            # Disable UI
            root.after(0, lambda: choose_button.config(state=DISABLED))
            root.after(0, lambda: remove_button.config(state=DISABLED))

            # Check for model file (rembg will download on first run)
            model_hint = Path.home() / ".u2net" / "u2net.onnx"
            if not model_hint.exists():
                root.after(0, lambda: status_label.config(text="Downloading model (first run)..."))
            else:
                root.after(0, lambda: status_label.config(text="Removing background..."))

            # Initialize determinate progress and start animator thread
            root.after(0, lambda: set_progress(0))

            done_event = threading.Event()

            def progress_animator():
                expected = 176 * 1024 * 1024
                model_path = Path.home() / ".u2net" / "u2net.onnx"
                # animator runs until done_event is set
                while not done_event.is_set():
                    if model_path.exists():
                        try:
                            size = model_path.stat().st_size
                            pct = min(30 + (size / expected) * 50, 90)
                        except Exception:
                            pct = min(progress_state['value'] + random.uniform(0.5, 2.5), 90)
                    else:
                        pct = min(progress_state['value'] + random.uniform(0.8, 2.2), 30)
                    root.after(0, lambda p=pct: set_progress(p))
                    time.sleep(0.18)
                root.after(0, lambda: set_progress(100))

            animator = threading.Thread(target=progress_animator, daemon=True)
            animator.start()

            # Read image bytes
            with open(in_path, "rb") as f:
                input_image = f.read()

            # Call rembg (blocking) - happens in thread so UI stays responsive
            output_image = remove(input_image)

            # Write result
            with open(out_path, "wb") as o:
                o.write(output_image)

            # Update UI with result on main thread
            root.after(0, lambda: preview_image(out_path))
            root.after(0, lambda: status_label.config(text="Background removed successfully!"))
            root.after(0, lambda: messagebox.showinfo("Success", "Background removed and image saved successfully."))
        except Exception as e:
            root.after(0, lambda: messagebox.showerror("Error", f"An error occurred: {e}"))
            root.after(0, lambda: status_label.config(text="Error occurred. See message."))
        finally:
            # Signal animator to finish and re-enable UI
            try:
                done_event.set()
            except Exception:
                pass
            root.after(0, lambda: choose_button.config(state=NORMAL))
            root.after(0, lambda: remove_button.config(state=NORMAL))

    threading.Thread(target=worker, args=(input_path, output_path), daemon=True).start()

def preview_image(path):
    img = Image.open(path)
    img.thumbnail((300, 300))
    img_tk = ImageTk.PhotoImage(img)
    image_label.config(image=img_tk)
    image_label.image = img_tk

# Main window
root = Tk()
root.title("Background Remover")
root.geometry("520x680")

# Cartoonish theme
BG = "#f7f3e9"  # warm paper
FG = "#2b2b2b"
ACCENT = "#ff8a65"  # playful orange
ACCENT2 = "#ffd54f"  # warm yellow for glow
root.configure(bg=BG)

style = ttk.Style()
try:
    style.theme_use('clam')
except Exception:
    pass
style.configure('TButton', background=ACCENT, foreground=FG, font=('Comic Sans MS', 11))
style.map('TButton', background=[('active', '#ffab91')])
style.configure('TLabel', background=BG, foreground=FG)
style.configure('TFrame', background=BG)

input_path = ""

title_font = tkfont.Font(family='Comic Sans MS', size=24, weight='bold')
title_label = ttk.Label(root, text="Background Remover", font=title_font, anchor='center')
title_label.pack(pady=14)

image_frame = ttk.Frame(root)
image_frame.pack(pady=8)

image_label = Label(image_frame, bg=BG)
image_label.pack()

# Cartoon figure canvas
canvas = Canvas(root, width=140, height=140, bg=BG, highlightthickness=0)
canvas.pack(pady=6)

# Draw a halo (glow) and simple cartoon character (head + body)
halo = canvas.create_oval(10, 10, 130, 130, fill='#ddd6b8', outline='')
head = canvas.create_oval(50, 20, 90, 60, fill='#fff7d6', outline='#d9c88a')
body = canvas.create_oval(36, 56, 104, 110, fill='#ffd59e', outline='#e6b58a')
eye1 = canvas.create_oval(60, 34, 66, 40, fill='#2b2b2b')
eye2 = canvas.create_oval(74, 34, 80, 40, fill='#2b2b2b')
smile = canvas.create_arc(60, 40, 80, 60, start=200, extent=140, style='arc', width=2)

# Progressbar (determinate)
progressbar = ttk.Progressbar(root, mode='determinate', length=360, maximum=100)
progressbar.pack(pady=8)

progress_state = {'value': 0}

def lerp_color(a, b, t):
    # a and b are '#rrggbb'
    ar, ag, ab = int(a[1:3], 16), int(a[3:5], 16), int(a[5:7], 16)
    br, bgc, bb = int(b[1:3], 16), int(b[3:5], 16), int(b[5:7], 16)
    r = int(ar + (br - ar) * t)
    g = int(ag + (bgc - ag) * t)
    b2 = int(ab + (bb - ab) * t)
    return '#%02x%02x%02x' % (r, g, b2)

def update_glow(pct):
    t = max(0.0, min(1.0, pct / 100.0))
    dim = '#ddd6b8'
    bright = ACCENT2
    color = lerp_color(dim, bright, t)
    # scale halo size a little with progress
    min_pad = 10
    pad = min_pad + int(t * 10)
    canvas.coords(halo, 10 - pad/2, 10 - pad/2, 130 + pad/2, 130 + pad/2)
    canvas.itemconfig(halo, fill=color)

def set_progress(pct):
    progress_state['value'] = pct
    try:
        progressbar['value'] = pct
    except Exception:
        pass
    update_glow(pct)

choose_button = ttk.Button(root, text="Choose Image", command=choose_file)
choose_button.pack(pady=6)

remove_button = ttk.Button(root, text="Remove Background", command=remove_bg)
remove_button.pack(pady=6)

status_label = ttk.Label(root, text="No image selected.", font=("Comic Sans MS", 12))
status_label.pack(pady=10)

root.mainloop()
