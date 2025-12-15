import pygetwindow as gw
import win32gui
import win32con
import win32ui
import win32process
import win32api
from PIL import Image
import ctypes
import json
import os

class WindowManager:
    def __init__(self):
        # Üstte tutulan pencerelerin HWND'lerini sakla
        self.topmost_hwnds = set()
        self.icon_cache = {} # hwnd -> Image cache
        self.previous_windows = self.load_previous_windows()
        
    def load_previous_windows(self):
        """Load previously selected windows from JSON file"""
        try:
            window_data_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "top_window_data.json")
            if os.path.exists(window_data_file):
                with open(window_data_file, 'r') as f:
                    data = json.load(f)
                    return data.get("previous_windows", [])
        except Exception as e:
            pass
        return []
        
    def save_previous_windows(self, window_titles):
        """Save selected window titles to JSON file"""
        try:
            window_data_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "top_window_data.json")
            data = {"previous_windows": window_titles}
            with open(window_data_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            pass

    def get_window_exe_path(self, hwnd):
        """Pencerenin ait olduğu exe dosyasının yolunu bulur."""
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            # PROCESS_QUERY_INFORMATION (0x0400) | PROCESS_VM_READ (0x0010)
            h_process = win32api.OpenProcess(0x0410, False, pid)
            try:
                path = win32process.GetModuleFileNameEx(h_process, 0)
            finally:
                win32api.CloseHandle(h_process)
            return path
        except:
            return None

    def hicon_to_image(self, hicon):
        """HICON handle'ını PIL Image'a dönüştürür."""
        try:
            hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
            hbmp = win32ui.CreateBitmap()
            hbmp.CreateCompatibleBitmap(hdc, 32, 32)
            hdc = hdc.CreateCompatibleDC()
            hdc.SelectObject(hbmp)
            
            # DrawIconEx ile çiz
            win32gui.DrawIconEx(hdc.GetSafeHdc(), 0, 0, hicon, 32, 32, 0, 0, win32con.DI_NORMAL)

            bmpinfo = hbmp.GetInfo()
            bmpstr = hbmp.GetBitmapBits(True)
            img = Image.frombuffer(
                'RGB',
                (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                bmpstr, 'raw', 'BGRX', 0, 1)
            
            # Kaynakları serbest bırak (önemli)
            hdc.DeleteDC()
            win32gui.DeleteObject(hbmp.GetHandle())

            return img
        except Exception as e:
            return None

    def get_window_icon(self, hwnd):
        """Pencere ikonunu alır ve PIL Image olarak döndürür."""
        if hwnd in self.icon_cache:
            return self.icon_cache[hwnd]

        img = None
        
        # YÖNTEM 1: Exe yolundan Orijinal İkonu Çek (En Kaliteli)
        try:
            exe_path = self.get_window_exe_path(hwnd)
            # ApplicationFrameHost.exe (UWP kaplaması) ise atla, çünkü kendi ikonu boştur.
            is_uwp = exe_path and "ApplicationFrameHost.exe" in exe_path
            
            if exe_path and not is_uwp:
                # ExtractIconEx büyük ikonları döner
                large_icons, small_icons = win32gui.ExtractIconEx(exe_path, 0)
                if large_icons:
                    hicon = large_icons[0]
                    img = self.hicon_to_image(hicon)
                    for h in large_icons: win32gui.DestroyIcon(h)
                    for h in small_icons: win32gui.DestroyIcon(h)
        except Exception:
            pass

        # YÖNTEM 2: WM_GETICON / GetClassLong (Fallback & UWP)
        if img is None:
            try:
                hicon = 0
                # 2.1 WM_GETICON (SendMessageTimeout güvenlidir)
                # Timeout süresini 100ms'ye indirdik (daha hızlı yanıt için)
                try:
                    res, hicon = win32gui.SendMessageTimeout(hwnd, win32con.WM_GETICON, win32con.ICON_BIG, 0, 0x0002, 100)
                    if hicon == 0:
                        res, hicon = win32gui.SendMessageTimeout(hwnd, win32con.WM_GETICON, win32con.ICON_SMALL, 0, 0x0002, 100)
                except: pass

                # 2.2 GetClassLong (Mesaj döngüsü cevap vermezse)
                if hicon == 0:
                    try:
                        hicon = win32gui.GetClassLong(hwnd, win32con.GCL_HICON)
                    except: pass
                
                if hicon == 0:
                    try:
                        # GCL_HICONSM = -34
                        hicon = win32gui.GetClassLong(hwnd, -34)
                    except: pass
                
                if hicon != 0:
                    img = self.hicon_to_image(hicon)
            except:
                pass

        if img:
            self.icon_cache[hwnd] = img
            return img
        
        return None

    def get_visible_windows(self):
        """Görünür ve geçerli pencereleri listeler."""
        windows = gw.getAllWindows()
        valid_windows = []
        for win in windows:
            if win.title.strip() and win.visible and not win.title.startswith("TopWindow"):
                valid_windows.append(win)
        return valid_windows

    def is_always_on_top(self, hwnd):
        """Bir pencerenin zaten topmost olup olmadığını kontrol eder (win32 API)."""
        try:
            ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            return (ex_style & win32con.WS_EX_TOPMOST) != 0
        except:
            return False

    def toggle_topmost(self, window):
        hwnd = window._hWnd
        if self.is_always_on_top(hwnd):
            self.unset_topmost(window)
        else:
            self.set_topmost(window)

    def set_topmost(self, window):
        try:
            hwnd = window._hWnd
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                                 win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            self.topmost_hwnds.add(hwnd)
            # Add window title to previous windows list
            if window.title not in self.previous_windows:
                self.previous_windows.append(window.title)
            return True
        except:
            return False

    def unset_topmost(self, window):
        try:
            hwnd = window._hWnd
            win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                                 win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            if hwnd in self.topmost_hwnds:
                self.topmost_hwnds.remove(hwnd)
            # Remove window title from previous windows list
            if window.title in self.previous_windows:
                self.previous_windows.remove(window.title)
            return True
        except:
            return False

    def minimize_window(self, window):
        """Minimize the specified window"""
        try:
            hwnd = window._hWnd
            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
            return True
        except:
            return False

    def cleanup(self):
        """Çıkışta tüm pencereleri eski haline getirir."""
        for hwnd in list(self.topmost_hwnds):
            try:
                win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                                     win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            except:
                pass
        self.topmost_hwnds.clear()

    def hide_app_window(self, root):
        """Hide the application window"""
        try:
            root.withdraw()
            return True
        except:
            return False

    def show_app_window(self, root):
        """Show the application window"""
        try:
            root.deiconify()
            root.lift()
            root.focus_force()
            return True
        except:
            return False