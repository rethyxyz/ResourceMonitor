import psutil
import tkinter as tk
from colorsys import hsv_to_rgb
import platform

PROGRAM_TITLE = "ResourceMonitor"

class ResourceUsageApp:
    def __init__(self, master):
        self.master = master
        self.master.title(PROGRAM_TITLE)
        self.master.configure(background='black')

        self.frame = tk.Frame(master, background='black')
        self.frame.pack()

        # CPU.
        self.cpu_label = tk.Label(self.frame, text="CPU Usage", fg='white', bg='black')
        self.cpu_label.grid(row=0, column=0, sticky="w")
        self.cpu_canvas = tk.Canvas(self.frame, width=300, height=20, bd=1, relief='solid', bg='black')
        self.cpu_canvas.grid(row=0, column=1)
        self.cpu_usage_bar = self.cpu_canvas.create_rectangle(0, 0, 0, 20, fill='grey')

        # RAM.
        self.ram_label = tk.Label(self.frame, text="RAM Usage", fg='white', bg='black')
        self.ram_label.grid(row=1, column=0, sticky="w")
        self.ram_canvas = tk.Canvas(self.frame, width=300, height=20, bd=1, relief='solid', bg='black')
        self.ram_canvas.grid(row=1, column=1)
        self.ram_usage_bar = self.ram_canvas.create_rectangle(0, 0, 0, 20, fill='grey')

        # Disk.
        self.disks = self.get_usable_disks()
        self.disk_labels = []
        self.disk_canvases = []
        self.disk_usage_bars = []
        self.init_disk_visualization(start_row=2)

        self.update_loop()

    def get_usable_disks(self):
        # Filter for usable disks only
        disks = []
        for disk in psutil.disk_partitions():
            if disk.fstype and ('cdrom' not in disk.opts) and (platform.system() != 'Windows' or 'removable' not in disk.opts):
                try:
                    # Check if we can access disk usage data
                    psutil.disk_usage(disk.mountpoint)
                    disks.append(disk)
                except (PermissionError, FileNotFoundError):
                    continue  # Skip inaccessible disks
        return disks

    def calculate_color(self, percentage):
        hue = (1 - percentage / 100) * 0.33  # Green to red
        r, g, b = hsv_to_rgb(hue, 1, 1)
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

    def init_disk_visualization(self, start_row=0):
        for i, disk in enumerate(self.disks):
            label = tk.Label(self.frame, text="", fg='white', bg='black')
            label.grid(row=start_row + i, column=0, sticky="w")
            self.disk_labels.append(label)

            canvas = tk.Canvas(self.frame, width=300, height=20, bd=1, relief='solid', bg='black')
            canvas.grid(row=start_row + i, column=1)
            usage_bar = canvas.create_rectangle(0, 0, 0, 20, fill='grey')
            self.disk_canvases.append(canvas)
            self.disk_usage_bars.append(usage_bar)

    def update_cpu_visualization(self):
        cpu_percent = psutil.cpu_percent(interval=None)
        color = self.calculate_color(cpu_percent)
        label_text = f"CPU Usage: {cpu_percent:.2f}%"
        self.cpu_label.config(text=label_text)
        self.cpu_canvas.coords(self.cpu_usage_bar, 0, 0, cpu_percent * 3, 20)
        self.cpu_canvas.itemconfig(self.cpu_usage_bar, fill=color)

    def update_ram_visualization(self):
        mem = psutil.virtual_memory()
        ram_percent = mem.percent
        total_gb = mem.total / (1024 ** 3)
        available_gb = mem.available / (1024 ** 3)
        used_gb = mem.used / (1024 ** 3)
        color = self.calculate_color(ram_percent)
        label_text = f"RAM Usage: {ram_percent:.2f}% | Total: {total_gb:.1f}GB, Used: {used_gb:.1f}GB, Available: {available_gb:.1f}GB"
        self.ram_label.config(text=label_text)
        self.ram_canvas.coords(self.ram_usage_bar, 0, 0, ram_percent * 3, 20)
        self.ram_canvas.itemconfig(self.ram_usage_bar, fill=color)

    def update_disk_visualization(self):
        for i, disk in enumerate(self.disks):
            try:
                usage = psutil.disk_usage(disk.mountpoint)
            except (PermissionError, FileNotFoundError):
                continue  # Skip if we don't have permission or the disk is unavailable

            total_gb = usage.total / (1024 ** 3)
            free_gb = usage.free / (1024 ** 3)
            used_percent = (usage.used / usage.total) * 100
            free_percent = (usage.free / usage.total) * 100
            color = self.calculate_color(used_percent)

            label_text = f"{disk.device} ({disk.mountpoint}) - Used: {used_percent:.2f}%, Free: {free_percent:.2f}% | Total: {total_gb:.1f}GB, Free: {free_gb:.1f}GB"
            self.disk_labels[i].config(text=label_text)
            self.disk_canvases[i].coords(self.disk_usage_bars[i], 0, 0, used_percent * 3, 20)
            self.disk_canvases[i].itemconfig(self.disk_usage_bars[i], fill=color)

    def update_loop(self):
        self.update_cpu_visualization()
        self.update_ram_visualization()
        self.update_disk_visualization()
        self.master.after(1000, self.update_loop)  # Update every second

def main():
    root = tk.Tk()
    app = ResourceUsageApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
