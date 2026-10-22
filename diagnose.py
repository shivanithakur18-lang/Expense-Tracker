"""
Expense Tracker - environment and chart diagnostics.

Run this if the charts do not appear on screen:

    python diagnose.py

Or in VS Code: open this file and press F5 (Run).

It prints everything needed to find out why the chart window does not
show up, and writes the same report to diagnose_report.txt
"""

import os
import sys
import time
import traceback
import tkinter as tk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import app as appmod

LINES = []


def say(text=""):
    print(text)
    LINES.append(str(text))


def pump(root, seconds=0.5):
    end = time.time() + seconds
    while time.time() < end:
        try:
            root.update()
        except tk.TclError:
            break
        time.sleep(0.01)


def dpi_awareness():
    try:
        import ctypes

        value = ctypes.windll.shcore.GetProcessDpiAwareness(None)
        names = {
            0: "0 = UNAWARE (Windows scales the window bitmap)",
            1: "1 = SYSTEM DPI AWARE",
            2: "2 = PER-MONITOR DPI AWARE"
        }
        return names.get(value, str(value))
    except Exception as error:
        return f"not available ({error})"


def main():

    say("=" * 62)
    say(" EXPENSE TRACKER DIAGNOSTICS")
    say("=" * 62)
    say()

    say("--- ENVIRONMENT ---")
    say(f"python          : {sys.version.split()[0]}")
    say(f"executable      : {sys.executable}")
    say(f"tkinter version : {tk.TkVersion}")
    say(f"platform        : {sys.platform}")
    say(f"dpi awareness   : {dpi_awareness()}")
    say(f"script folder   : {appmod.BASE_DIR}")
    say()

    say("--- DATABASE ---")
    say(f"database path   : {appmod.DATABASE}")
    say(f"database exists : {os.path.exists(appmod.DATABASE)}")

    try:
        appmod.create_database()
        records = appmod.get_all_expenses()
        say(f"expense rows    : {len(records)}")
        if records:
            say(f"sample row      : {records[0]}")
    except Exception as error:
        say(f"database FAILED : {error}")
        records = []
    say()

    say("--- MAIN WINDOW ---")
    root = tk.Tk()
    tracker = appmod.ExpenseTracker(root)
    pump(root, 0.8)

    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    win_w = root.winfo_width()
    win_h = root.winfo_height()
    win_x = root.winfo_rootx()
    win_y = root.winfo_rooty()

    say(f"screen          : {screen_w} x {screen_h}")
    say(f"tk scaling      : {root.tk.call('tk', 'scaling')}")
    say(f"window          : {win_w} x {win_h} at +{win_x}+{win_y}")
    say(f"window bottom   : {win_y + win_h} (screen {screen_h})")
    say(
        "window fits     : "
        + ("YES" if win_y + win_h <= screen_h else "NO  <-- TOO TALL")
    )

    say()
    say("--- TOOLBAR BUTTONS ---")
    button_ok = True

    def walk(node):
        yield node
        for child in node.winfo_children():
            yield from walk(child)

    for node in walk(root):
        if node.winfo_class() in ("TButton", "Button"):
            try:
                text = node.cget("text")
            except Exception:
                continue
            if not text:
                continue
            bottom = node.winfo_rooty() + node.winfo_height()
            ok = bottom <= screen_h
            if not ok:
                button_ok = False
            say(f"  [{'OK ' if ok else 'CUT'}] {text}")

    say()

    say("--- CHART WINDOW ---")
    chart_ok = False
    try:
        tracker.show_chart()
        pump(root, 1.0)

        window = tracker.chart_window

        if window is None:
            say("chart window    : NOT CREATED  <-- PROBLEM")
        else:
            cw = window.winfo_width()
            ch = window.winfo_height()
            cx = window.winfo_rootx()
            cy = window.winfo_rooty()
            say(f"chart window    : {cw} x {ch} at +{cx}+{cy}")
            say(f"chart bottom    : {cy + ch} (screen {screen_h})")
            fits = cy + ch <= screen_h and cx + cw <= screen_w and cx >= 0 and cy >= 0
            say(f"chart on screen : {'YES' if fits else 'NO  <-- OFF SCREEN'}")

            say()
            say("--- CHART TABS ---")

            notebook = None
            for node in walk(window):
                if node.winfo_class() == "TNotebook":
                    notebook = node
                    break

            if notebook is None:
                say("notebook        : NOT FOUND  <-- PROBLEM")
            else:
                for tab, name in zip(notebook.tabs(), ["bar", "pie", "trend"]):
                    notebook.select(tab)
                    pump(root, 0.5)
                    canvas = tracker.chart_canvases.get(name)
                    if canvas is None:
                        say(f"  {name:6s}: canvas MISSING  <-- PROBLEM")
                        continue
                    items = len(canvas.find_all())
                    kinds = {}
                    for item in canvas.find_all():
                        kind = canvas.type(item)
                        kinds[kind] = kinds.get(kind, 0) + 1
                    say(
                        f"  {name:6s}: canvas {canvas.winfo_width()}x{canvas.winfo_height()} "
                        f"items={items} {kinds}"
                    )
                    if items == 0:
                        say(f"           ^ EMPTY CANVAS  <-- PROBLEM")

            chart_ok = fits

            # Screenshot for visual proof
            try:
                from PIL import ImageGrab

                if notebook is not None:
                    notebook.select(notebook.tabs()[0])
                    pump(root, 0.6)
                    window.lift()
                    pump(root, 0.3)
                shot = ImageGrab.grab(
                    bbox=(cx, cy, cx + cw, cy + ch)
                )
                out = os.path.join(appmod.BASE_DIR, "diagnose_chart.png")
                shot.save(out)
                say()
                say(f"screenshot saved: {out}")
            except Exception as error:
                say(f"screenshot skipped: {error}")

    except Exception as error:
        say(f"chart FAILED    : {error}")
        say(traceback.format_exc())

    say()
    say("=" * 62)
    if chart_ok and button_ok:
        say(" RESULT: everything looks correct on this machine.")
        say(" If you still cannot see the chart, check that the")
        say(" 'Expense Analytics' window is not behind VS Code.")
    else:
        say(" RESULT: problems found above (marked <-- ).")
        say(" Send diagnose_report.txt back for a fix.")
    say("=" * 62)

    try:
        root.destroy()
    except Exception:
        pass

    report = os.path.join(appmod.BASE_DIR, "diagnose_report.txt")
    with open(report, "w", encoding="utf-8") as handle:
        handle.write("\n".join(LINES))
    print()
    print(f"Report written to: {report}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
    input("\nPress Enter to close...")
