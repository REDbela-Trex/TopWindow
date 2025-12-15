import pygetwindow as gw
import time
import sys
import win32gui
import win32con
import json
import os

# ANSI color codes for terminal coloring
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Store references to windows that are kept on top
topmost_windows = {}

# JSON file for persisting window data
WINDOW_DATA_FILE = "top_window_data.json"

MENU_OPTIONS = {
    '1': 'Keep window(s) on top',
    '2': 'Restore window(s) from top',
    '3': 'Launch GUI version',
    '4': 'Exit program'
}

def load_window_data():
    """Load previously selected windows from JSON file"""
    try:
        if os.path.exists(WINDOW_DATA_FILE):
            with open(WINDOW_DATA_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading window data: {e}")
    return {"previous_windows": []}

def save_window_data(window_titles):
    """Save selected window titles to JSON file"""
    try:
        data = {"previous_windows": window_titles}
        with open(WINDOW_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving window data: {e}")

def display_menu():
    """Display the main menu options"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== TopWindow Menu ==={Colors.ENDC}")
    for key, value in MENU_OPTIONS.items():
        if key == '1':
            print(f"{Colors.OKGREEN}{key}. {value}{Colors.ENDC}")
        elif key == '2':
            print(f"{Colors.WARNING}{key}. {value}{Colors.ENDC}")
        elif key == '3':
            print(f"{Colors.OKCYAN}{key}. {value}{Colors.ENDC}")
        elif key == '4':
            print(f"{Colors.FAIL}{key}. {value}{Colors.ENDC}")
        else:
            print(f"{key}. {value}")
    print(f"{Colors.HEADER}{Colors.BOLD}======================={Colors.ENDC}")

def list_windows():
    """List all available windows"""
    windows = gw.getAllWindows()
    print(f"\n{Colors.OKBLUE}{Colors.BOLD}Available Windows:{Colors.ENDC}")
    print(f"{Colors.OKCYAN}{'-' * 50}{Colors.ENDC}")
    valid_windows = []
    count = 1
    for window in windows:
        # Only show windows with titles that are not empty and not the current console
        if window.title.strip() and not window.title.startswith("TopWindow"):
            status = f"{Colors.WARNING}[ON TOP]{Colors.ENDC}" if window._hWnd in topmost_windows else ""
            print(f"{Colors.OKGREEN}{count}.{Colors.ENDC} {window.title} {status}")
            valid_windows.append(window)
            count += 1
    return valid_windows

def select_multiple_windows(windows):
    """Allow user to select multiple windows"""
    print("\nEnter window numbers separated by commas (e.g., 1,3,5) or 'all' for all windows:")
    print("Press Enter to return to menu.")
    
    user_input = input(">>> ").strip()
    
    if not user_input:
        return []
        
    if user_input.lower() == 'all':
        return windows
    
    try:
        indices = [int(x.strip()) - 1 for x in user_input.split(',')]
        selected_windows = []
        for idx in indices:
            if 0 <= idx < len(windows):
                selected_windows.append(windows[idx])
            else:
                print(f"Invalid window number: {idx + 1}")
        return selected_windows
    except ValueError:
        print("Please enter valid numbers separated by commas!")
        return []

def set_window_always_on_top(window):
    """Set a window to always stay on top using Windows API"""
    try:
        hwnd = window._hWnd
        if hwnd:
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, 
                                 win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            topmost_windows[hwnd] = window  # Keep reference
            return True
    except Exception as e:
        print(f"Error setting window to topmost: {e}")
        return False

def unset_window_always_on_top(window):
    """Remove the always on top setting"""
    try:
        hwnd = window._hWnd
        if hwnd and hwnd in topmost_windows:
            win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, 
                                 win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            del topmost_windows[hwnd]  # Remove reference
            return True
    except Exception as e:
        print(f"Error unsetting window from topmost: {e}")
        return False

def keep_selected_windows_on_top(windows):
    """Keep selected windows on top"""
    if not windows:
        print(f"{Colors.WARNING}No windows selected.{Colors.ENDC}")
        return
        
    success_count = 0
    selected_titles = []
    for window in windows:
        if set_window_always_on_top(window):
            print(f"{Colors.OKGREEN}Window '{window.title}' is now on top.{Colors.ENDC}")
            selected_titles.append(window.title)
            success_count += 1
        else:
            print(f"{Colors.FAIL}Failed to set window '{window.title}' on top.{Colors.ENDC}")
    
    if success_count > 0:
        # Save the selected window titles for persistence
        save_window_data(selected_titles)
        print(f"\n{Colors.OKGREEN}Successfully set {success_count} window(s) on top.{Colors.ENDC}")
    else:
        print(f"\n{Colors.FAIL}No windows were successfully set on top.{Colors.ENDC}")

def restore_selected_windows(windows):
    """Restore selected windows from top"""
    if not windows:
        print(f"{Colors.WARNING}No windows selected.{Colors.ENDC}")
        return
        
    success_count = 0
    for window in windows:
        if unset_window_always_on_top(window):
            print(f"{Colors.OKGREEN}Window '{window.title}' restored to normal.{Colors.ENDC}")
            success_count += 1
        else:
            print(f"{Colors.FAIL}Failed to restore window '{window.title}'.{Colors.ENDC}")
    
    if success_count > 0:
        print(f"\n{Colors.OKGREEN}Successfully restored {success_count} window(s).{Colors.ENDC}")
    else:
        print(f"\n{Colors.FAIL}No windows were successfully restored.{Colors.ENDC}")

def launch_gui_version():
    """Launch the GUI version of the application"""
    print(f"\n{Colors.OKBLUE}Launching GUI version...{Colors.ENDC}")
    try:
        restore_all_windows()  # Clean up before switching to GUI
        
        import subprocess
        import sys
        import os
        import ctypes
        
        # Get console window handle
        kernel32 = ctypes.WinDLL('kernel32')
        user32 = ctypes.WinDLL('user32')
        hwnd = kernel32.GetConsoleWindow()
        
        cmd = []
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            cmd = [sys.executable, '--gui']
        else:
            # Running as script
            gui_script = os.path.join(os.path.dirname(__file__), 'gui', 'modern_ui.py')
            cmd = [sys.executable, gui_script]

        # Launch GUI process (removed DETACHED_PROCESS to allow waiting)
        # We pass the current environment to ensure it inherits necessary context
        process = subprocess.Popen(cmd)
        
        if hwnd:
            # Hide the console window
            # SW_HIDE = 0
            user32.ShowWindow(hwnd, 0)
            
        # Wait for the GUI process to finish
        exit_code = process.wait()
        
        # If exit code indicates error, show console again
        if exit_code != 0 and hwnd:
            # SW_SHOW = 5
            user32.ShowWindow(hwnd, 5)
            print(f"\n{Colors.FAIL}GUI Process exited with error code: {exit_code}{Colors.ENDC}")
            print(f"{Colors.WARNING}Check 'gui_error_log.txt' in the 'gui' folder for details.{Colors.ENDC}")
            input("Press Enter to exit...")
            
        sys.exit(exit_code)
        
    except Exception as e:
        print(f"{Colors.FAIL}Error launching GUI version: {e}{Colors.ENDC}")
        # Ensure console is visible if we crashed here
        try:
            kernel32 = ctypes.WinDLL('kernel32')
            user32 = ctypes.WinDLL('user32')
            hwnd = kernel32.GetConsoleWindow()
            if hwnd: user32.ShowWindow(hwnd, 5)
        except: pass
        input("Press Enter to exit...")

def restore_all_windows():
    """Restore all windows when exiting"""
    if topmost_windows:
        print("\nRestoring all windows...")
        # Create a copy of the dictionary items to avoid modification during iteration
        windows_to_restore = list(topmost_windows.values())
        for window in windows_to_restore:
            unset_window_always_on_top(window)
        print("All windows restored to normal behavior.")

def main():
    """Main application loop"""
    print(f"{Colors.OKBLUE}{Colors.BOLD}TopWindow - Keep Any Window On Top{Colors.ENDC}")
    print(f"{Colors.OKCYAN}{'=' * 40}{Colors.ENDC}")
    
    try:
        while True:
            display_menu()
            choice = input(f"\n{Colors.OKBLUE}Select an option: {Colors.ENDC}").strip()
            
            if choice == '1':
                # Keep windows on top
                windows = list_windows()
                if not windows:
                    print(f"{Colors.WARNING}No suitable windows found!{Colors.ENDC}")
                    continue
                    
                selected_windows = select_multiple_windows(windows)
                keep_selected_windows_on_top(selected_windows)
                
            elif choice == '2':
                # Restore windows from top
                if not topmost_windows:
                    print(f"{Colors.WARNING}No windows are currently kept on top.{Colors.ENDC}")
                    continue
                    
                # Create list of topmost windows for selection
                topmost_list = list(topmost_windows.values())
                print(f"\n{Colors.OKBLUE}{Colors.BOLD}Currently Topmost Windows:{Colors.ENDC}")
                print(f"{Colors.OKCYAN}{'-' * 30}{Colors.ENDC}")
                for i, window in enumerate(topmost_list, 1):
                    print(f"{Colors.OKGREEN}{i}.{Colors.ENDC} {window.title}")
                    
                selected_windows = select_multiple_windows(topmost_list)
                restore_selected_windows(selected_windows)
                
            elif choice == '3':
                # Launch GUI version
                launch_gui_version()
                break
                
            elif choice == '4':
                # Exit program
                print(f"\n{Colors.OKGREEN}Exiting program...{Colors.ENDC}")
                restore_all_windows()
                print(f"{Colors.OKGREEN}Goodbye!{Colors.ENDC}")
                break
                
            else:
                print(f"{Colors.FAIL}Invalid option. Please select 1, 2, 3, or 4.{Colors.ENDC}")
                
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Program interrupted by user.{Colors.ENDC}")
        restore_all_windows()
    except Exception as e:
        print(f"{Colors.FAIL}An unexpected error occurred: {e}{Colors.ENDC}")
        restore_all_windows()

if __name__ == "__main__":
    # Check if we should launch the GUI directly
    if len(sys.argv) > 1 and sys.argv[1] == '--gui':
        # Launch GUI directly
        try:
            # Setup logging for startup
            import datetime
            log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui_startup_log.txt")
            
            with open(log_path, "w") as f:
                f.write(f"Startup initiated at {datetime.datetime.now()}\n")
            
            from gui import modern_ui
            app = modern_ui.TopWindowApp()
            app.run()
        except Exception as e:
            import traceback
            log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui_startup_log.txt")
            with open(log_path, "a") as f:
                f.write(f"Error launching GUI: {e}\n")
                traceback.print_exc(file=f)
            print(f"Error launching GUI: {e}")
            sys.exit(1)
    else:
        # Launch CLI version
        main()