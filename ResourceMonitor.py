import psutil
import tkinter as tk
from colorsys import hsv_to_rgb
import platform
from time import time
import os
from typing import Dict, Optional

PROGRAM_TITLE = "ResourceMonitor"
UPDATE_INTERVAL = 500

class ResourceUsageApp:
    def __init__(self, master):
        self.master = master
        self.master.title(PROGRAM_TITLE)
        self.master.configure(background='black')
        
        self.master.resizable(True, True)
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(0, weight=1)
        
        self.frame = tk.Frame(master, background='black', padx=5, pady=5)
        self.frame.grid(row=0, column=0, sticky='nsew')
        
        self.frame.grid_columnconfigure(1, weight=2)
        self.frame.grid_columnconfigure(2, weight=1)
        
        current_row = self.init_header_row()
        current_row = self.init_system_resources(current_row)
        current_row = self.init_disk_sections(current_row)
        
        self.update_loop()

    def init_header_row(self):
        """Initialize the header row with column labels."""
        headers = [
            ("Resource", 20),
            ("Usage", 30),
            ("Statistics", 50)
        ]
        
        for col, (text, width) in enumerate(headers):
            cell = tk.Label(
                self.frame,
                text=text,
                fg='white',
                bg='#1a1a1a',
                padx=10,
                pady=5,
                font=('TkDefaultFont', 10, 'bold'),
                width=width
            )
            cell.grid(row=0, column=col, sticky='ew', padx=1)
        
        return 1

    def create_table_row(self, row, label_text, show_bars=True):
        """Create a standardized table row."""
        widgets = {}
        
        name_label = tk.Label(
            self.frame,
            text=label_text,
            fg='white',
            bg='#262626',
            padx=10,
            pady=5,
            anchor='w'
        )
        name_label.grid(row=row, column=0, sticky='ew', padx=1)
        widgets['name'] = name_label
        
        if show_bars:
            canvas = tk.Canvas(
                self.frame,
                height=25,
                bd=0,
                highlightthickness=0,
                bg='#262626'
            )
            canvas.grid(row=row, column=1, sticky='ew', padx=1)
            bar = canvas.create_rectangle(0, 0, 0, 25, fill='grey')
            widgets['canvas'] = canvas
            widgets['bar'] = bar
        
        stats_label = tk.Label(
            self.frame,
            text="",
            fg='white',
            bg='#262626',
            padx=10,
            pady=5,
            anchor='w'
        )
        stats_label.grid(row=row, column=2, sticky='ew', padx=1)
        widgets['stats'] = stats_label
        
        return widgets

    def init_system_resources(self, start_row):
        """Initialize CPU and RAM resource rows."""
        current_row = start_row
        
        header = tk.Label(
            self.frame,
            text="System Resources",
            fg='white',
            bg='black',
            font=('TkDefaultFont', 10, 'bold'),
            pady=10
        )
        header.grid(row=current_row, column=0, columnspan=3, sticky='w')
        current_row += 1
        
        self.cpu_widgets = self.create_table_row(current_row, "CPU")
        current_row += 1
        
        self.ram_widgets = self.create_table_row(current_row, "RAM")
        current_row += 2
        
        return current_row

    def get_dm_name(self, device_path):
        """Get the dm-X name for a /dev/mapper device or Windows disk name."""
        try:
            if platform.system() == 'Windows':
                return device_path
            elif device_path.startswith('/dev/mapper/'):
                real_path = os.path.realpath(device_path)
                if 'dm-' in real_path:
                    return os.path.basename(real_path)
            return None
        except Exception:
            return None

    def get_windows_drive_label(self, device_path):
        """Get the label of a Windows drive."""
        try:
            if platform.system() == 'Windows':
                import ctypes
                kernel32 = ctypes.windll.kernel32
                volume_name_buffer = ctypes.create_unicode_buffer(1024)
                file_system_name_buffer = ctypes.create_unicode_buffer(1024)
                
                if not device_path.endswith('\\'):
                    device_path += '\\'
                
                success = kernel32.GetVolumeInformationW(
                    device_path,
                    volume_name_buffer,
                    ctypes.sizeof(volume_name_buffer),
                    None,
                    None,
                    None,
                    file_system_name_buffer,
                    ctypes.sizeof(file_system_name_buffer)
                )
                
                if success and volume_name_buffer.value:
                    return volume_name_buffer.value
            return None
        except Exception:
            return None

    def get_friendly_name(self, device_path, mountpoint):
        """Get a user-friendly name for the device."""
        if platform.system() == 'Windows':
            label = self.get_windows_drive_label(mountpoint)
            if label:
                return f"{mountpoint} ({label})"
            return mountpoint
        else:
            return os.path.basename(device_path)

    def init_disk_sections(self, start_row):
        """Initialize disk section rows."""
        current_row = start_row
        
        header = tk.Label(
            self.frame,
            text="Storage Devices",
            fg='white',
            bg='black',
            font=('TkDefaultFont', 10, 'bold'),
            pady=10
        )
        header.grid(row=current_row, column=0, columnspan=3, sticky='w')
        current_row += 1
        
        self.disk_widgets = []
        self.last_io_stats = {}
        self.last_io_time = time()
        
        for disk in psutil.disk_partitions(all=False):
            try:
                if (not disk.fstype or 
                    (platform.system() == 'Windows' and 'cdrom' in disk.opts.lower()) or
                    (platform.system() != 'Windows' and 'cdrom' in disk.opts.lower())):
                    continue
                
                if platform.system() == 'Windows':
                    if disk.mountpoint.startswith('C:\\System Volume Information'):
                        continue
                
                psutil.disk_usage(disk.mountpoint)
                
                dm_name = self.get_dm_name(disk.device)
                friendly_name = self.get_friendly_name(disk.device, disk.mountpoint)
                
                usage_widgets = self.create_table_row(
                    current_row,
                    friendly_name
                )
                current_row += 1
                
                io_widgets = self.create_table_row(
                    current_row,
                    "└ I/O"
                )
                current_row += 2
                
                disk_info = {
                    'device': disk.device,
                    'mountpoint': disk.mountpoint,
                    'dm_name': dm_name,
                    'usage_widgets': usage_widgets,
                    'io_widgets': io_widgets
                }
                self.disk_widgets.append(disk_info)
                
                if platform.system() == 'Windows':
                    self.last_io_stats[disk.device] = None
                else:
                    if dm_name:
                        self.last_io_stats[dm_name] = None
                    else:
                        self.last_io_stats[os.path.basename(disk.device)] = None
                
            except (PermissionError, FileNotFoundError):
                continue
            except Exception as e:
                print(f"Error initializing disk {disk.device}: {str(e)}")
                continue
        
        return current_row

    def calculate_color(self, percentage):
        """Calculate color based on percentage (green to red)."""
        hue = (1 - percentage / 100) * 0.33
        r, g, b = hsv_to_rgb(hue, 1, 1)
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

    def update_cpu_visualization(self):
        cpu_percent = psutil.cpu_percent(interval=None)
        color = self.calculate_color(cpu_percent)
        
        canvas = self.cpu_widgets['canvas']
        bar = self.cpu_widgets['bar']
        canvas_width = canvas.winfo_width()
        bar_width = (cpu_percent / 100) * canvas_width
        canvas.coords(bar, 0, 0, bar_width, 25)
        canvas.itemconfig(bar, fill=color)
        
        self.cpu_widgets['stats'].config(
            text=f"Usage: {cpu_percent:.1f}%"
        )

    def update_ram_visualization(self):
        mem = psutil.virtual_memory()
        ram_percent = mem.percent
        total_gb = mem.total / (1024 ** 3)
        used_gb = mem.used / (1024 ** 3)
        available_gb = mem.available / (1024 ** 3)
        
        color = self.calculate_color(ram_percent)
        
        canvas = self.ram_widgets['canvas']
        bar = self.ram_widgets['bar']
        canvas_width = canvas.winfo_width()
        bar_width = (ram_percent / 100) * canvas_width
        canvas.coords(bar, 0, 0, bar_width, 25)
        canvas.itemconfig(bar, fill=color)
        
        stats_text = (
            f"Total: {total_gb:.1f}GB | "
            f"Used: {used_gb:.1f}GB | "
            f"Available: {available_gb:.1f}GB"
        )
        self.ram_widgets['stats'].config(text=stats_text)

    def update_disk_visualizations(self):
        current_time = time()
        time_delta = current_time - self.last_io_time
        disk_io_all = psutil.disk_io_counters(perdisk=True)
        
        for disk_info in self.disk_widgets:
            try:
                device = disk_info['device']
                mountpoint = disk_info['mountpoint']
                usage_widgets = disk_info['usage_widgets']
                io_widgets = disk_info['io_widgets']
                
                usage = psutil.disk_usage(mountpoint)
                used_percent = usage.percent
                total_gb = usage.total / (1024 ** 3)
                free_gb = usage.free / (1024 ** 3)
                
                color = self.calculate_color(used_percent)
                canvas = usage_widgets['canvas']
                bar = usage_widgets['bar']
                canvas_width = canvas.winfo_width()
                bar_width = (used_percent / 100) * canvas_width
                canvas.coords(bar, 0, 0, bar_width, 25)
                canvas.itemconfig(bar, fill=color)
                
                usage_stats = (
                    f"Total: {total_gb:.1f}GB | "
                    f"Used: {used_percent:.1f}% | "
                    f"Free: {free_gb:.1f}GB"
                )
                usage_widgets['stats'].config(text=usage_stats)
                
                if platform.system() == 'Windows':
                    io_name = disk_info['device']
                else:
                    io_name = disk_info['dm_name'] if disk_info['dm_name'] else os.path.basename(device)
                
                current_io = disk_io_all.get(io_name.lower() if platform.system() == 'Windows' else io_name)
                last_io = self.last_io_stats.get(io_name)
                
                if current_io and last_io:
                    io_util = min(100, (current_io.busy_time - last_io.busy_time) / (time_delta * 1000) * 100)
                    read_bytes = current_io.read_bytes - last_io.read_bytes
                    write_bytes = current_io.write_bytes - last_io.write_bytes
                    read_mb_sec = read_bytes / time_delta / (1024 * 1024)
                    write_mb_sec = write_bytes / time_delta / (1024 * 1024)
                    
                    color = self.calculate_color(io_util)
                    canvas = io_widgets['canvas']
                    bar = io_widgets['bar']
                    canvas_width = canvas.winfo_width()
                    bar_width = (io_util / 100) * canvas_width
                    canvas.coords(bar, 0, 0, bar_width, 25)
                    canvas.itemconfig(bar, fill=color)
                    
                    io_stats = (
                        f"Utilization: {io_util:.1f}% | "
                        f"Read: {read_mb_sec:.1f}MB/s | "
                        f"Write: {write_mb_sec:.1f}MB/s"
                    )
                    io_widgets['stats'].config(text=io_stats)
                
                self.last_io_stats[io_name] = current_io
                
            except Exception as e:
                print(f"Error updating disk {device}: {str(e)}")
                continue
        
        self.last_io_time = current_time

    def update_loop(self):
        """Main update loop for refreshing all visualizations."""
        self.update_cpu_visualization()
        self.update_ram_visualization()
        self.update_disk_visualizations()
        self.master.after(UPDATE_INTERVAL, self.update_loop)

def main():
    root = tk.Tk()
    root.minsize(800, 400)
    app = ResourceUsageApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()