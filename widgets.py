"""Canvas-based rounded panel and button widgets.

ttk.Button on macOS Aqua silently ignores style foreground/background colors
for some Tk builds (native chrome wins), which is why the Calculate/Export
buttons rendered with invisible text. Drawing buttons (and panel borders)
directly on a tk.Canvas sidesteps native theming entirely and also makes
rounded corners possible, which ttk.Frame can't do.
"""

import tkinter as tk


def _rounded_rect_points(x1, y1, x2, y2, radius):
    return [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1,
        x1 + radius, y1,
    ]


class RoundedPanel(tk.Canvas):
    """A panel with a rounded, colored border and an embedded content frame.

    Use `.inner` (a tk.Frame) to add content, exactly like a regular Frame.
    """

    def __init__(self, parent, bg_outer, bg_inner, border_color, radius=14, border_width=2, **kwargs):
        super().__init__(parent, bg=bg_outer, highlightthickness=0, **kwargs)
        self._border_color = border_color
        self._bg_inner = bg_inner
        self._radius = radius
        self._border_width = border_width
        self._requested_size = (0, 0)

        self.inner = tk.Frame(self, bg=bg_inner)
        self._window_id = self.create_window(0, 0, window=self.inner, anchor="nw")

        # Only the canvas's own <Configure> (its parent resizing it) drives a
        # redraw. The inner frame's <Configure> only adjusts the canvas's
        # *requested* size, and only when it actually changes -- without that
        # guard, canvas<->inner resize events feed into each other forever.
        self.bind("<Configure>", self._redraw)
        self.inner.bind("<Configure>", self._on_inner_configure)

    def _on_inner_configure(self, event=None):
        bw = self._border_width
        w = self.inner.winfo_reqwidth() + bw * 2 + 4
        h = self.inner.winfo_reqheight() + bw * 2 + 4
        if (w, h) == self._requested_size:
            return
        self._requested_size = (w, h)
        self.configure(width=w, height=h)

    def _redraw(self, event=None):
        self.delete("border")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 4 or h < 4:
            return
        bw = self._border_width
        self.create_polygon(
            _rounded_rect_points(1, 1, w - 1, h - 1, self._radius),
            smooth=True, fill=self._border_color, outline=self._border_color, tags="border",
        )
        self.create_polygon(
            _rounded_rect_points(1 + bw, 1 + bw, w - 1 - bw, h - 1 - bw, max(self._radius - bw, 0)),
            smooth=True, fill=self._bg_inner, outline=self._bg_inner, tags="border",
        )
        self.coords(self._window_id, bw + 2, bw + 2)
        self.itemconfigure(self._window_id, width=w - 2 * bw - 4, height=h - 2 * bw - 4)
        self.tag_lower("border")


class RoundedButton(tk.Canvas):
    """A rounded, click-able button with guaranteed text/color rendering
    (no dependency on native ttk button theming)."""

    def __init__(self, parent, text, command, bg, fg, active_bg, radius=10,
                 font=("Helvetica", 10), padx=14, pady=8, **kwargs):
        super().__init__(parent, highlightthickness=0, bg=parent["bg"] if "bg" in parent.keys() else bg, **kwargs)
        self._command = command
        self._bg = bg
        self._fg = fg
        self._active_bg = active_bg
        self._radius = radius
        self._font = font
        self._padx = padx
        self._pady = pady
        self._text = text

        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self._render()

    def _render(self, hover=False):
        self.delete("all")
        text_id = self.create_text(0, 0, text=self._text, font=self._font, fill=self._fg, anchor="nw")
        bbox = self.bbox(text_id)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        self.delete("all")

        w = text_w + 2 * self._padx
        h = text_h + 2 * self._pady
        self.configure(width=w, height=h)

        fill = self._active_bg if hover else self._bg
        self.create_polygon(
            _rounded_rect_points(1, 1, w - 1, h - 1, self._radius),
            smooth=True, fill=fill, outline=fill,
        )
        self.create_text(w / 2, h / 2, text=self._text, font=self._font, fill=self._fg, anchor="center")

    def set_text(self, text):
        self._text = text
        self._render()

    def _on_click(self, event=None):
        if self._command:
            self._command()

    def _on_enter(self, event=None):
        self._render(hover=True)

    def _on_leave(self, event=None):
        self._render(hover=False)
