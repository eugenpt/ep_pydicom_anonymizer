# anonymize.py
from __future__ import annotations

import argparse
import configparser
import multiprocessing
import os
import sys
import threading
import tkinter as tk
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Dict

import pydicom
import tqdm
from pydicom.tag import Tag
from tkinter import filedialog, messagebox, ttk

# Import worker
from anonymizer import anonymize_one

import time
import subprocess

import ctypes
from ctypes import wintypes

from io import StringIO
import traceback

import multiprocessing
if __name__ == '__main__':
    multiprocessing.freeze_support()

IS_GUI = len(sys.argv) == 1

# Hide console if GUI mode
def hide_console():
    if IS_GUI:
        try:
            # Get console window handle
            kernel32 = ctypes.windll.kernel32
            user32 = ctypes.windll.user32
            handle = kernel32.GetConsoleWindow()
            if handle:
                # SW_HIDE = 0
                user32.ShowWindow(handle, 0)
        except Exception:
            traceback.print_exc()
            pass  # Silently fail on non-Windows

if __name__ == "__main__":
    hide_console()

# --------------------------------------------------------------------------- #
# Logger
# --------------------------------------------------------------------------- #

def info(msg: str):
    if IS_GUI: messagebox.showinfo("Info", msg)
    else: print(f"[INFO] {msg}")

def warn(msg: str):
    if IS_GUI: messagebox.showwarning("Warning", msg)
    else: print(f"[WARN] {msg}", file=sys.stderr)

def error(msg: str):
    if IS_GUI: messagebox.showerror("Error", msg)
    else: print(f"[ERROR] {msg}", file=sys.stderr); sys.exit(1)


# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #
def load_config(path: str | None) -> Dict[Tag, str]:
    cfg: Dict[Tag, str] = {}
    if not path or not Path(path).is_file():
        return cfg
    parser = configparser.ConfigParser()
    parser.optionxform = str
    try:
        parser.read(path, encoding="utf-8")
    except Exception as e:
        warn(f"Config error: {e}")
        return cfg
    for sec in parser.sections():
        for k, v in parser.items(sec):
            try:
                tag = Tag(int(k.replace(",", ""), 16))
            except:
                try:
                    tag = Tag(k)
                except:
                    continue
            cfg[tag] = v.strip(' "\'')
    return cfg


# --------------------------------------------------------------------------- #
# Parallel
# --------------------------------------------------------------------------- #
def anonymize_parallel(
    input_dir: str,
    output_dir: str,
    config_path: str | None = None,
    cli_fields: Dict[Tag, str] | None = None,
    max_workers: int | None = None,
    *,
    progress_cb=None,
    status_cb=None,
):
    in_p = Path(input_dir).resolve()
    out_p = Path(output_dir).resolve()
    if not in_p.is_dir():
        error(f"Input not found: {in_p}")
    out_p.mkdir(parents=True, exist_ok=True)

    fields = {**load_config(config_path), **(cli_fields or {})}

    files = [
        p for p in in_p.rglob("*")
        if p.is_file() and p.stat().st_size > 1024
        and p.suffix.lower() in {".dcm", ".dicom", ""}
    ]
    if not files:
        info("No DICOM files.")
        return

    total = len(files)
    args = [(f, in_p, out_p, fields, i + 1) for i, f in enumerate(files)]

    errors = []
    done = 0

    with ProcessPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(anonymize_one, a): a[0] for a in args}
        for future in tqdm.tqdm(
            as_completed(futures),
            total=total,
            desc="Anonymizing",
            unit="file",
            ncols=100,
            disable=IS_GUI
        ):
            res = future.result()
            if res:
                errors.append(res)
            done += 1
            if progress_cb:
                progress_cb(done, total)
            if status_cb:
                status_cb(f"{done}/{total}")

    if errors:
        msg = f"{len(errors)} errors (first 3):\n"
        for f, tb in errors[:3]:
            msg += f"\n{f}\n{tb}\n{'-'*50}"
        if len(errors) > 3:
            msg += f"\n… and {len(errors)-3} more."
        warn(msg)
    else:
        if not IS_GUI:
            info(f"Done: {total} files → {out_p}")


# --------------------------------------------------------------------------- #
# GUI – smart dialog chain + independent browsing
# --------------------------------------------------------------------------- #
def run_gui():
    root = tk.Tk()
    root.title("DICOM Anonymizer")
    root.geometry("620x320")
    root.resizable(False, False)

    tk.Label(root, text="DICOM Batch Anonymizer", font=("Helvetica", 16, "bold")).pack(pady=12)

    input_var  = tk.StringVar()
    output_var = tk.StringVar()
    config_var = tk.StringVar()

    # Track if this is the first launch
    # Shared flag — must be modified with `nonlocal`
    first_launch = [True]  # Use list to allow mutation in closures

    def make_row(label, var, browse_cmd):
        frame = tk.Frame(root)
        frame.pack(fill="x", padx=20, pady=4)
        tk.Label(frame, text=label, width=14, anchor="w").pack(side="left")
        entry = tk.Entry(frame, textvariable=var, width=50, state="readonly")
        entry.pack(side="left", padx=(0, 5), expand=True, fill="x")
        tk.Button(frame, text="Browse...", command=browse_cmd, width=10).pack(side="right")
        return frame

    # Browse functions
    def browse_input():
        path = filedialog.askdirectory(title="Select Input Folder")
        if path:
            input_var.set(path)
            if first_launch[0]:
                root.after(100, browse_output)

    def browse_output():
        init = str(Path(input_var.get()).parent) if input_var.get() else os.getcwd()
        path = filedialog.askdirectory(title="Select Output Folder", initialdir=init)
        if path:
            output_var.set(path)
            if first_launch[0]:
                root.after(100, browse_config)

    def browse_config():
        exe_dir = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
        path = filedialog.askopenfilename(
            title="Select Config File (optional)",
            initialdir=str(exe_dir),
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if path:
            config_var.set(path)
        # Only on first launch do we chain
        if first_launch[0]:
            first_launch[0] = False

    # Build UI
    make_row("Input Folder:",  input_var,  browse_input)
    make_row("Output Folder:", output_var, browse_output)
    make_row("Config (opt):",  config_var, browse_config)

    # Progress
    prog_frame = tk.Frame(root)
    prog_frame.pack(fill="x", padx=20, pady=12)
    prog_var = tk.DoubleVar()
    prog_bar = ttk.Progressbar(prog_frame, variable=prog_var, maximum=100, length=560)
    prog_bar.pack()
    status_lbl = tk.Label(prog_frame, text="Ready", fg="gray")
    status_lbl.pack(pady=2)

    # --- Checkbox ---
    open_folder_var = tk.BooleanVar(value=False)
    chk = tk.Checkbutton(root, text="Open output folder when finished", variable=open_folder_var)
    chk.pack(pady=5)

# --- Start button ---
    start_btn = tk.Button(
        root, text="Start Anonymization", bg="#2ecc71", fg="white",
        font=("Helvetica", 11, "bold"), height=2,
        command=lambda: start_anonymization(
            input_var.get(), output_var.get(), config_var.get() or None,
            prog_var, status_lbl, start_btn, root, open_folder_var
        )
    )
    start_btn.pack(pady=10)

    # Auto-start chain
    root.after(100, browse_input)

    root.mainloop()


# --------------------------------------------------------------------------- #
# Start anonymization with timer + taskbar flash + open folder
# --------------------------------------------------------------------------- #
def start_anonymization(in_dir, out_dir, cfg, prog_var, status_lbl, btn, root, open_var):
    if not in_dir or not out_dir:
        status_lbl.config(text="Error: Select input and output", fg="red")
        return

    btn.config(state="disabled")
    prog_var.set(0)
    start_time = time.time()

    def progress(done, total):
        prog_var.set(done / total * 100)
        elapsed = time.time() - start_time
        status_lbl.config(text=f"Processing {done}/{total} | {elapsed:.1f}s")

    def status(txt):
        elapsed = time.time() - start_time
        status_lbl.config(text=f"{txt} | {elapsed:.1f}s")

    def on_done():
        elapsed = time.time() - start_time
        status_lbl.config(text=f"Done in {elapsed:.1f}s", fg="green")
        btn.config(state="normal")
        root.update_idletasks()

        # Flash taskbar (Windows only)
        if sys.platform.startswith("win"):
            try:
                import ctypes
                ctypes.windll.user32.FlashWindow(ctypes.windll.kernel32.GetConsoleWindow(), True)
            except:
                pass  # ignore if no console or fails

        # Open folder if checked
        if open_var.get() and out_dir:
            try:
                os.startfile(out_dir)  # Windows
            except:
                try:
                    subprocess.Popen(["explorer", out_dir])  # fallback
                except:
                    pass

    def run_and_finish(i, o, c, prog_cb, stat_cb, done_cb):
        try:
            anonymize_parallel(i, o, c, progress_cb=prog_cb, status_cb=stat_cb)
        except Exception as e:
            status_lbl.config(text=f"Error: {e}", fg="red")
        finally:
            root.after(0, done_cb)

    thread = threading.Thread(
        target=lambda: run_and_finish(
            in_dir, out_dir, cfg, progress, status, on_done
        ),
        daemon=True
    )
    thread.start()



# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def run_cli():
    p = argparse.ArgumentParser()
    p.add_argument("input", nargs="?")
    p.add_argument("output", nargs="?")
    p.add_argument("-c", "--config")
    a, e = p.parse_known_args()

    cf: Dict[Tag, str] = {}
    for x in e:
        if "=" not in x: continue
        k, v = x.split("=", 1)
        try: tag = Tag(k.strip('"'))
        except:
            try: tag = Tag(int(k.replace(",", ""), 16))
            except: continue
        cf[tag] = v.strip('"')

    if a.input and a.output:
        anonymize_parallel(a.input, a.output, a.config, cf)
    else:
        run_gui()


# --------------------------------------------------------------------------- #
# Entry
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    multiprocessing.freeze_support()
    if len(sys.argv) > 1:
        run_cli()
    else:
        run_gui()