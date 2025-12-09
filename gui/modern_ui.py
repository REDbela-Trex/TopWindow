import tkinter as tk
try:
    from .window_manager import WindowManager
except ImportError:
    from window_manager import WindowManager
import ctypes
import os
import sys
from PIL import Image
import pystray
from pystray import MenuItem as item
import win32gui

# Pillow kontrolü
HAS_PILLOW = False
try:
    from PIL import Image, ImageTk, ImageDraw
    HAS_PILLOW = True
except ImportError:
    pass

# ═══════════════════════════════════════════════════════════════
# Windows 11 Yuvarlak Köşe Desteği (DWM API)
# ═══════════════════════════════════════════════════════════════
def set_rounded_corners(hwnd, radius=2):
    """Windows 11'de pencere köşelerini yuvarlar."""
    try:
        DWMWA_WINDOW_CORNER_PREFERENCE = 33
        preference = ctypes.c_int(radius)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_WINDOW_CORNER_PREFERENCE,
            ctypes.byref(preference),
            ctypes.sizeof(preference)
        )
    except:
        pass

# Dosya yolu (exe ve py için uyumlu)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Modern Renk Paleti
COLORS = {
    'bg_dark': '#0d0d0d',
    'bg_card': '#1a1a1a',
    'bg_hover': '#2a2a2a',
    'accent': '#00e676',
    'accent_dim': '#1b5e20',
    'text': '#ffffff',
    'text_muted': '#888888',
    'danger': '#ff4444',
    'border': '#333333',
}

def load_icon(filename, size=(20, 20)):
    """PNG dosyasını yükler ve boyutlandırır"""
    if not HAS_PILLOW:
        return None
    try:
        path = os.path.join(BASE_DIR, filename)
        img = Image.open(path)
        img = img.resize(size, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)
    except:
        return None

class ToolTip:
    """Modern Tooltip - Fare Takipli"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show)
        self.widget.bind("<Leave>", self.hide)
        self.widget.bind("<Motion>", self.move)

    def show(self, event=None):
        if self.tooltip or not self.text: return
        x, y = event.x_root + 12, event.y_root + 12
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.attributes('-topmost', True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        self.tooltip.update_idletasks()
        try:
            hwnd = ctypes.windll.user32.GetParent(self.tooltip.winfo_id())
            set_rounded_corners(hwnd, 3)
        except: pass
        
        frame = tk.Frame(self.tooltip, bg=COLORS['bg_card'], padx=1, pady=1)
        frame.pack()
        label = tk.Label(frame, text=self.text, bg=COLORS['bg_card'], fg=COLORS['text'],
                        font=("Segoe UI", 9), padx=10, pady=6)
        label.pack()

    def move(self, event=None):
        if self.tooltip:
            self.tooltip.wm_geometry(f"+{event.x_root + 12}+{event.y_root + 12}")

    def hide(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

class RoundedCard(tk.Canvas):
    """Canvas tabanlı yuvarlak köşeli kart"""
    def __init__(self, parent, width=54, height=54, radius=12, bg=COLORS['bg_card'], **kwargs):
        super().__init__(parent, width=width, height=height, 
                        bg=COLORS['bg_dark'], highlightthickness=0, **kwargs)
        self.radius = radius
        self.card_bg = bg
        self.w, self.h = width, height
        self._draw_rounded_rect(bg)
        
    def animate_scale(self, target_scale, steps=10, delay=10):
        """Smoothly scale the card"""
        current_scale = getattr(self, '_current_scale', 1.0)
        scale_step = (target_scale - current_scale) / steps
        
        def step(count):
            if count < steps:
                scale = current_scale + scale_step * (count + 1)
                self.scale("all", 0, 0, scale / getattr(self, '_current_scale', 1.0), scale / getattr(self, '_current_scale', 1.0))
                self._current_scale = scale
                self.after(delay, lambda: step(count + 1))
            else:
                self._current_scale = target_scale
                
        step(0)
        
    def _draw_rounded_rect(self, color):
        self.delete("card")
        r = self.radius
        w, h = self.w, self.h
        self.create_arc(0, 0, r*2, r*2, start=90, extent=90, fill=color, outline=color, tags="card")
        self.create_arc(w-r*2, 0, w, r*2, start=0, extent=90, fill=color, outline=color, tags="card")
        self.create_arc(0, h-r*2, r*2, h, start=180, extent=90, fill=color, outline=color, tags="card")
        self.create_arc(w-r*2, h-r*2, w, h, start=270, extent=90, fill=color, outline=color, tags="card")
        self.create_rectangle(r, 0, w-r, h, fill=color, outline=color, tags="card")
        self.create_rectangle(0, r, w, h-r, fill=color, outline=color, tags="card")
        
    def set_color(self, color):
        self.card_bg = color
        self._draw_rounded_rect(color)
        self.tag_raise("icon")
        
    def pulse_effect(self, duration=200):
        """Create a pulsing effect"""
        original_color = self.card_bg
        
        # Brighten effect
        def brighten():
            r, g, b = int(original_color[1:3], 16), int(original_color[3:5], 16), int(original_color[5:7], 16)
            r = min(255, r + 30)
            g = min(255, g + 30)
            b = min(255, b + 30)
            bright_color = f"#{r:02x}{g:02x}{b:02x}"
            self.set_color(bright_color)
            
        brighten()
        self.after(duration // 2, lambda: self.set_color(original_color))
        
    def transition_color(self, target_color, steps=10, delay=20):
        """Smoothly transition to a target color"""
        if not hasattr(self, '_transition_job'):
            self._transition_job = None
            
        if self._transition_job:
            self.after_cancel(self._transition_job)
            
        # Parse current and target colors
        current = self.card_bg
        if len(current) == 7:  # #RRGGBB format
            cr, cg, cb = int(current[1:3], 16), int(current[3:5], 16), int(current[5:7], 16)
        else:
            cr, cg, cb = 0, 0, 0
            
        if len(target_color) == 7:  # #RRGGBB format
            tr, tg, tb = int(target_color[1:3], 16), int(target_color[3:5], 16), int(target_color[5:7], 16)
        else:
            tr, tg, tb = 0, 0, 0
            
        # Calculate step sizes
        sr = (tr - cr) / steps
        sg = (tg - cg) / steps
        sb = (tb - cb) / steps
        
        def step(count):
            if count < steps:
                nr = int(cr + sr * (count + 1))
                ng = int(cg + sg * (count + 1))
                nb = int(cb + sb * (count + 1))
                new_color = f"#{nr:02x}{ng:02x}{nb:02x}"
                self.set_color(new_color)
                self._transition_job = self.after(delay, lambda: step(count + 1))
            else:
                self.set_color(target_color)
                self._transition_job = None
                
        step(0)

class IconCard(tk.Frame):
    """Modern Yuvarlak Köşeli İkon Kartı"""
    def __init__(self, parent, window, manager, on_update):
        super().__init__(parent, bg=COLORS['bg_dark'])
        
        self.window = window
        self.manager = manager
        self.on_update = on_update
        self.img_ref = None
        self.is_active = False
        
        # Create a container frame for shadow effect
        self.shadow_frame = tk.Frame(self, bg="#000000", bd=0)
        self.shadow_frame.pack(padx=4, pady=4)
        
        self.card = RoundedCard(self.shadow_frame, width=54, height=54, radius=12)
        self.card.pack(padx=0, pady=0)
        
        self._load_icon()
        self._setup_events()
        self._update_visual()
        
        # Check if this window was previously selected
        if window.title in manager.previous_windows:
            self.configure(bg=COLORS['accent'])
        
        ToolTip(self.card, window.title)

    def _load_icon(self):
        size = 32
        img = None
        
        if HAS_PILLOW:
            pil_img = self.manager.get_window_icon(self.window._hWnd)
            if pil_img:
                pil_img = pil_img.resize((size, size), Image.Resampling.LANCZOS)
                img = ImageTk.PhotoImage(pil_img)
        
        if img is None and HAS_PILLOW:
            fallback = Image.new('RGBA', (size, size), (37, 37, 37, 255))
            draw = ImageDraw.Draw(fallback)
            char = (self.window.title[0].upper() if self.window.title else "?")
            draw.text((size//3, size//4), char, fill=COLORS['text_muted'])
            img = ImageTk.PhotoImage(fallback)
        
        if img:
            self.img_ref = img
            self.card.create_image(27, 27, image=img, tags="icon")
            self.card.tag_raise("icon")
        else:
            self.card.create_text(27, 27, text=self.window.title[0].upper() if self.window.title else "?",
                                 fill=COLORS['text_muted'], font=("Segoe UI", 14, "bold"), tags="icon")
            self.card.tag_raise("icon")

    def _setup_events(self):
        self.card.bind("<Enter>", self._on_enter)
        self.card.bind("<Leave>", self._on_leave)
        self.card.bind("<Button-1>", self._on_click)
        self.card.bind("<Button-3>", self._minimize_window)

    def _on_enter(self, e):
        if not self.is_active:
            self.card.transition_color(COLORS['bg_hover'])
            # Smooth scale up effect
            self.card.animate_scale(1.05)
            # Shadow effect
            self.shadow_frame.configure(bg="#333333")

    def _on_leave(self, e):
        # Reset scale effect
        self.card.animate_scale(1.0)
        # Reset shadow effect
        self.shadow_frame.configure(bg="#000000")
        self._update_visual()

    def _on_click(self, e):
        # Pulse effect for click
        self.card.pulse_effect()
        
        self.manager.toggle_topmost(self.window)
        self._update_visual()
        # Update the manager's previous windows list after toggling
        self._update_previous_windows_list()

    def _minimize_window(self, e):
        """Minimize the window on right-click"""
        self.manager.minimize_window(self.window)
        # Refresh the UI to reflect any changes
        if self.on_update:
            self.on_update()

    def _update_visual(self):
        self.is_active = self.manager.is_always_on_top(self.window._hWnd)
        if self.is_active:
            self.card.transition_color(COLORS['accent_dim'])
            self.configure(bg=COLORS['accent'])
        else:
            self.card.transition_color(COLORS['bg_card'])
            self.configure(bg=COLORS['bg_dark'])

    def _update_previous_windows_list(self):
        """Update the list of previous windows in the manager"""
        # Get all currently active windows from the manager
        active_windows = []
        try:
            # We need to get the titles of all windows that are currently topmost
            # Since the manager tracks hwnds, we need to get their titles
            for hwnd in list(self.manager.topmost_hwnds):
                try:
                    window_title = win32gui.GetWindowText(hwnd)
                    if window_title:
                        active_windows.append(window_title)
                except:
                    pass
        except:
            pass
        
        # Save to manager
        self.manager.save_previous_windows(active_windows)

class TopWindowApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("TopWindow")
        self.root.configure(bg=COLORS['bg_dark'])
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        
        # Pencere boyutu ve konumu (top-left corner)
        self.width, self.height = 290, 440
        self.root.geometry(f"{self.width}x{self.height}+0+0")
        
        # Windows 11 yuvarlak köşeler
        self.root.update_idletasks()
        try:
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            set_rounded_corners(hwnd, 2)
        except: pass
        
        # Pencere ikonu (taskbar için - overrideredirect ile çalışmayabilir)
        try:
            icon_path = os.path.join(BASE_DIR, "top_window_icon.png")
            self.root.iconphoto(True, ImageTk.PhotoImage(file=icon_path))
        except: pass
        
        self.manager = WindowManager()
        self._drag = {"x": 0, "y": 0}
        self._snap_threshold = 30  # pixels
        self._snap_margin = 10     # pixels margin from edge
        self._snap_animation_steps = 20
        self._snap_animation_delay = 15  # ms
        self._is_dragging = False  # Track dragging state
        
        # İkonları yükle
        self._icons = {
            'close': load_icon("cross.png", (16, 16)),
            'refresh': load_icon("refresh.png", (16, 16)),
            'logo': load_icon("top_window_icon.png", (24, 24)),
        }
        
        # Create tray icon
        self._create_tray_icon()
        
        self._build_ui()
        self._refresh()
        
        # Start periodic edge check
        self._check_edge_position()

    def _build_ui(self):
        # ═══ BAŞLIK ÇUBUĞU ═══
        header = tk.Frame(self.root, bg=COLORS['bg_dark'], height=44)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        header.bind("<Button-1>", self._start_drag)
        header.bind("<B1-Motion>", self._do_drag)
        header.bind("<ButtonRelease-1>", self._stop_drag)
        header.bind("<Button-3>", lambda e: self._refresh())
        
        # Logo + Başlık
        if self._icons['logo']:
            logo_label = tk.Label(header, image=self._icons['logo'], bg=COLORS['bg_dark'])
            logo_label.pack(side=tk.LEFT, padx=(12, 6), pady=10)
            logo_label.bind("<Button-1>", self._start_drag)
            logo_label.bind("<B1-Motion>", self._do_drag)
            logo_label.bind("<ButtonRelease-1>", self._stop_drag)
        
        title = tk.Label(header, text="TopWindow", bg=COLORS['bg_dark'], 
                        fg=COLORS['text'], font=("Segoe UI", 11, "bold"))
        title.pack(side=tk.LEFT, pady=10)
        title.bind("<Button-1>", self._start_drag)
        title.bind("<B1-Motion>", self._do_drag)
        title.bind("<ButtonRelease-1>", self._stop_drag)
        
        # Kapat butonu (PNG)
        if self._icons['close']:
            close = tk.Label(header, image=self._icons['close'], bg=COLORS['bg_dark'], cursor="hand2")
            close.pack(side=tk.RIGHT, padx=10)
            close.bind("<Button-1>", lambda e: self._close())
            close.bind("<Enter>", lambda e: close.configure(bg=COLORS['bg_hover']))
            close.bind("<Leave>", lambda e: close.configure(bg=COLORS['bg_dark']))
        else:
            close = tk.Label(header, text="✕", bg=COLORS['bg_dark'], fg=COLORS['danger'],
                            font=("Arial", 10), cursor="hand2", padx=8)
            close.pack(side=tk.RIGHT, padx=6)
            close.bind("<Button-1>", lambda e: self._close())
        
        # Hide/Show butonu
        self.hide_show_btn = tk.Label(header, text="−", bg=COLORS['bg_dark'], fg=COLORS['text'],
                             font=("Arial", 14), cursor="hand2", padx=8)
        self.hide_show_btn.pack(side=tk.RIGHT, padx=4)
        self.hide_show_btn.bind("<Button-1>", lambda e: self._toggle_visibility())
        self.hide_show_btn.bind("<Enter>", lambda e: self.hide_show_btn.configure(bg=COLORS['bg_hover']))
        self.hide_show_btn.bind("<Leave>", lambda e: self.hide_show_btn.configure(bg=COLORS['bg_dark']))
        
        # Yenile butonu (PNG)
        if self._icons['refresh']:
            refresh = tk.Label(header, image=self._icons['refresh'], bg=COLORS['bg_dark'], cursor="hand2")
            refresh.pack(side=tk.RIGHT, padx=4)
            refresh.bind("<Button-1>", lambda e: self._refresh())
            refresh.bind("<Enter>", lambda e: refresh.configure(bg=COLORS['bg_hover']))
            refresh.bind("<Leave>", lambda e: refresh.configure(bg=COLORS['bg_dark']))
        else:
            refresh = tk.Label(header, text="↻", bg=COLORS['bg_dark'], fg=COLORS['text_muted'],
                              font=("Arial", 14), cursor="hand2", padx=4)
            refresh.pack(side=tk.RIGHT)
            refresh.bind("<Button-1>", lambda e: self._refresh())
        
        # ═══ İÇERİK ALANI ═══
        container = tk.Frame(self.root, bg=COLORS['bg_dark'])
        container.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        self.canvas = tk.Canvas(container, bg=COLORS['bg_dark'], highlightthickness=0)
        self.scroll_frame = tk.Frame(self.canvas, bg=COLORS['bg_dark'])
        
        self.scroll_frame.bind("<Configure>", 
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.canvas.bind_all("<MouseWheel>", 
            lambda e: self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

    def _start_drag(self, e):
        self._drag["x"], self._drag["y"] = e.x, e.y
        self._is_dragging = True

    def _do_drag(self, e):
        x = self.root.winfo_x() + e.x - self._drag["x"]
        y = self.root.winfo_y() + e.y - self._drag["y"]
        self.root.geometry(f"+{x}+{y}")
        
    def _stop_drag(self, e):
        """Handle drag stop with animated snapping to nearest edge"""
        self._is_dragging = False
        # Use animated snapping when drag stops
        self.root.after(10, self._snap_to_nearest_edge_animated)
        
    def _animate_snap(self, from_x, from_y, to_x, to_y):
        """Animate the snapping motion with linear interpolation"""
        dx = (to_x - from_x) / self._snap_animation_steps
        dy = (to_y - from_y) / self._snap_animation_steps
        
        def step(count):
            if count < self._snap_animation_steps:
                x = int(from_x + dx * (count + 1))
                y = int(from_y + dy * (count + 1))
                # Ensure we don't go outside screen bounds even during animation
                screen_w = self.root.winfo_screenwidth()
                screen_h = self.root.winfo_screenheight()
                x = max(-self._snap_margin, min(x, screen_w - self.width + self._snap_margin))
                y = max(-self._snap_margin, min(y, screen_h - self.height + self._snap_margin))
                self.root.geometry(f"+{x}+{y}")
                self.root.after(self._snap_animation_delay, lambda: step(count + 1))
            else:
                self.root.geometry(f"+{to_x}+{to_y}")
                
        step(0)
        
    def _animate_snap_easeInOut(self, from_x, from_y, to_x, to_y):
        """Animate the snapping motion with ease-in-out interpolation for smoother movement"""
        def easeOutQuart(t):
            """Ease-out quartic function - starts slow and accelerates"""
            return 1 - pow(1 - t, 4)
        
        dx = to_x - from_x
        dy = to_y - from_y
        
        def step(count):
            if count < self._snap_animation_steps:
                # Apply ease-out function to progress (accelerates as it approaches target)
                progress = (count + 1) / self._snap_animation_steps
                eased_progress = easeOutQuart(progress)
                
                x = int(from_x + dx * eased_progress)
                y = int(from_y + dy * eased_progress)
                
                # Ensure we don't go outside screen bounds even during animation
                screen_w = self.root.winfo_screenwidth()
                screen_h = self.root.winfo_screenheight()
                x = max(-self._snap_margin, min(x, screen_w - self.width + self._snap_margin))
                y = max(-self._snap_margin, min(y, screen_h - self.height + self._snap_margin))
                self.root.geometry(f"+{x}+{y}")
                self.root.after(self._snap_animation_delay, lambda: step(count + 1))
            else:
                self.root.geometry(f"+{to_x}+{to_y}")
                
        step(0)

    def _refresh(self):
        for w in self.scroll_frame.winfo_children():
            w.destroy()
        
        windows = self.manager.get_visible_windows()
        
        # Highlight previously selected windows
        previous_window_titles = set(self.manager.previous_windows)
        
        if not windows:
            tk.Label(self.scroll_frame, text="Açık pencere yok", 
                    bg=COLORS['bg_dark'], fg=COLORS['text_muted'],
                    font=("Segoe UI", 9)).pack(pady=30)
            return
        
        cols = 4
        for i, win in enumerate(windows):
            row, col = divmod(i, cols)
            card = IconCard(self.scroll_frame, win, self.manager, self._refresh)
            card.grid(row=row, column=col, padx=1, pady=1, sticky="nsew")
            
            # Highlight previously selected windows
            if win.title in previous_window_titles:
                card.configure(bg=COLORS['accent'])
                
    def _close(self):
        self.manager.cleanup()
        if hasattr(self, 'tray_icon'):
            self.tray_icon.stop()
        self.root.quit()
        
    def _create_tray_icon(self):
        """Create system tray icon"""
        # Create an image for the tray icon
        icon_path = os.path.join(BASE_DIR, "top_window_icon.png")
        try:
            image = Image.open(icon_path)
        except:
            # Create a simple icon if file is not found
            image = Image.new('RGB', (64, 64), color=(0, 230, 118))
        
        # Define menu items
        menu = (
            item('Show', self._show_from_tray),
            item('Exit', self._exit_from_tray)
        )
        
        # Create and run the tray icon
        self.tray_icon = pystray.Icon("TopWindow", image, "TopWindow", menu)
        
    def _show_from_tray(self, icon, item):
        """Show the application window from tray"""
        self.manager.show_app_window(self.root)
        self.hide_show_btn.config(text="−")  # Change to hide icon
        
    def _exit_from_tray(self, icon, item):
        """Exit the application from tray"""
        icon.stop()
        self._close()
        
    def _hide_to_tray(self):
        """Hide the application to system tray"""
        self.manager.hide_app_window(self.root)
        if not hasattr(self, 'tray_icon'):
            self._create_tray_icon()
        self.tray_icon.run_detached()

    def _toggle_visibility(self):
        """Toggle the visibility of the application window"""
        if self.root.state() == 'normal' or self.root.state() == 'zoomed':
            # Window is visible, so hide it to tray
            self._hide_to_tray()
            self.hide_show_btn.config(text="□")  # Change to show icon
        else:
            # Window is hidden, so show it
            self.manager.show_app_window(self.root)
            self.hide_show_btn.config(text="−")  # Change to hide icon

    def _check_edge_position(self):
        """Continuously check and snap to nearest edge"""
        self._snap_to_nearest_edge()
        # Check more frequently for immediate snapping
        self.root.after(100, self._check_edge_position)
        
    def _snap_to_nearest_edge(self):
        """Snap to nearest left or right edge immediately, but only if not dragging"""
        # Don't snap while dragging
        if self._is_dragging:
            return
            
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        width = self.width
        height = self.height
        screen_w = self.root.winfo_screenwidth()
        
        # Only calculate distances to left and right edges
        left_dist = abs(x - self._snap_margin)
        right_dist = abs(x + width - screen_w + self._snap_margin)
        
        min_dist = min(left_dist, right_dist)
        
        # Snap to nearest left or right edge (immediate snapping)
        target_x, target_y = x, y
        if min_dist == left_dist:
            target_x = self._snap_margin
        elif min_dist == right_dist:
            target_x = screen_w - width - self._snap_margin
        
        # Snap immediately if not already at target position (horizontal only)
        if target_x != x:
            # For immediate snapping, use direct positioning instead of animation
            self.root.geometry(f"+{target_x}+{target_y}")
            
    def _snap_to_nearest_edge_animated(self):
        """Animated snapping to left or right edge after drag stop"""
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        width = self.width
        height = self.height
        screen_w = self.root.winfo_screenwidth()
        
        # Only calculate distances to left and right edges
        left_dist = abs(x - self._snap_margin)
        right_dist = abs(x + width - screen_w + self._snap_margin)
        
        min_dist = min(left_dist, right_dist)
        
        # Snap to nearest left or right edge with animation
        target_x, target_y = x, y
        if min_dist == left_dist:
            target_x = self._snap_margin
        elif min_dist == right_dist:
            target_x = screen_w - width - self._snap_margin
        
        # Animate snapping if needed (horizontal only)
        if target_x != x:
            self._animate_snap_easeInOut(x, y, target_x, y)
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = TopWindowApp()
    app.run()
