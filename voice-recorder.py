#!/usr/bin/env python3
import pyaudio, datetime, threading, time, wave, numpy as np, os, signal, subprocess, datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk
import sys
import ctypes

class RecordThread(threading.Thread):

    def __init__(self, use_mic, use_speaker, filename, stop_event):
        threading.Thread.__init__(self)
        self.use_mic = use_mic
        self.use_speaker = use_speaker
        self.stop_event = stop_event
        self.filename = filename

    def run(self):
        temp_wav = self.filename.replace(".mp3", "_temp.wav")

        self.start_time = datetime.datetime.now().replace(microsecond=0)  # Store the start time as an attribute
        total_frames = 0
        last_written_elapsed_time = -10

        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=48000,
                        input=True,
                        frames_per_buffer=2048,
                        input_device_index=self.use_mic)

        with wave.open(temp_wav, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(p.get_sample_size(pyaudio.paInt16))
            wav_file.setframerate(48000)

            timecodes_file = self.filename.replace(".mp3", "_timecodes.txt")
            with open(timecodes_file, "w") as f:

                start_time = datetime.datetime.now().replace(microsecond=0)
                total_frames = 0
                last_written_elapsed_time = -10

                while not self.stop_event.is_set():
                    data = stream.read(2048)
                    wav_file.writeframes(data)
                    total_frames += 2048

                    recorded_seconds = total_frames // 48000

                    # Write the timecode every 10 seconds
                    if recorded_seconds % 10 == 0 and recorded_seconds > last_written_elapsed_time:
                        current_time = datetime.datetime.now().replace(microsecond=0)
                        recording_timecode = datetime.timedelta(seconds=recorded_seconds)
                        f.write(f"{recording_timecode} > {current_time}\n")
                        last_written_elapsed_time = recorded_seconds

        stream.stop_stream()
        stream.close()
        p.terminate()

        self.convert_to_mp3(temp_wav)
        os.remove(temp_wav)


    #When testing the file without pyinstaller
    # def convert_to_mp3(self, temp_wav):
    #     ffmpeg_path = os.path.join(os.path.dirname(__file__), "lib", "ffmpeg.exe")
    #     command = f'"{ffmpeg_path}" -i "{temp_wav}" "{self.filename}"'
    #     subprocess.run(command, shell=True, check=True)

    #When using pyinstaller
    def convert_to_mp3(self, temp_wav):
        if getattr(sys, 'frozen', False):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        ffmpeg_path = os.path.join(base_dir, "lib", "ffmpeg.exe")
        command = f'"{ffmpeg_path}" -i "{temp_wav}" "{self.filename}"'
        subprocess.run(command, shell=True, check=True)

    def join(self, *args):
        threading.Thread.join(self, *args)




class RecorderApp(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("Lamassu Voice Recorder")
        self.geometry("300x200")

        self.stop_event = threading.Event()
        self.recording_thread = None
        self.office_hours_only = tk.BooleanVar(value=True)

        self.init_ui()

        self.start_recording()

        # Hide console window
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

        # Start the app minimized
        self.iconify()

        # Bind the window close button to a custom method
        self.protocol("WM_DELETE_WINDOW", self.on_close)        

    def init_ui(self):
        self.create_widgets()
        self.place_widgets()

    def create_widgets(self):
        self.start_button = ttk.Button(self, text="REC", command=lambda: self.start_recording(user_initiated=True))
        self.stop_button = ttk.Button(self, text="STOP", command=self.stop_recording, state=tk.DISABLED)
        self.progress_label = ttk.Label(self, text="Stopped")
        self.elapsed_time_label = ttk.Label(self, text="00:00:00")  # New elapsed time label
        self.office_hours_checkbox = ttk.Checkbutton(self, text="Office Hours Only", variable=self.office_hours_only)

    def place_widgets(self):
        self.start_button.pack(pady=10)
        self.stop_button.pack(pady=10)
        self.progress_label.pack(pady=5)
        self.elapsed_time_label.pack(pady=5)
        self.office_hours_checkbox.pack(pady=5)

    def start_recording(self, user_initiated=False):
        if user_initiated:
            self.office_hours_only.set(False)
        if self.office_hours_only.get():
            self.schedule_office_hours_recording()
        else:
            self.start_recording_now()

    def start_recording_now(self):
        self.progress_label.config(text="Recording")
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        p = pyaudio.PyAudio()
        default_mic = p.get_default_input_device_info()['index']

        filename = self.generate_filename()
        self.recording_thread = RecordThread(default_mic, None, filename, self.stop_event)
        self.recording_thread.start()
        self.update_elapsed_time()

    def stop_recording(self):
        self.progress_label.config(text="Stopped")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

        self.stop_event.set()
        self.recording_thread.join()
        self.stop_event.clear()

        if not self.office_hours_only.get():
            return
        self.schedule_office_hours_recording()

    def schedule_office_hours_recording(self):
        now = datetime.datetime.now()
        weekday = now.weekday()

        if weekday < 4:  # Monday to Thursday
            start_time1 = now.replace(hour=8, minute=30, second=0, microsecond=0)
            stop_time1 = now.replace(hour=13, minute=0, second=0, microsecond=0)
            start_time2 = now.replace(hour=14, minute=0, second=0, microsecond=0)
            stop_time2 = now.replace(hour=17, minute=52, second=0, microsecond=0) if weekday < 3 else now.replace(hour=17, minute=25, second=0, microsecond=0)

            if start_time1 <= now < stop_time1:
                self.start_recording_now()
                time_to_stop = (stop_time1 - now).total_seconds() * 1000
                self.after(int(time_to_stop), self.stop_recording)
                time_to_start2 = (start_time2 - now).total_seconds() * 1000
                self.after(int(time_to_start2), self.start_recording)
            elif start_time2 <= now < stop_time2:
                self.start_recording_now()
                time_to_stop = (stop_time2 - now).total_seconds() * 1000
                self.after(int(time_to_stop), self.stop_recording)
            elif stop_time1 <= now < start_time2:
                time_to_start = (start_time2 - now).total_seconds() * 1000
                self.after(int(time_to_start), self.start_recording)
            elif now < start_time1:
                time_to_start = (start_time1 - now).total_seconds() * 1000
                self.after(int(time_to_start), self.start_recording)
            else:  # now >= stop_time2
                next_day = now + datetime.timedelta(days=1)
                next_weekday = (next_day.weekday() + 1) % 7  # Get the next weekday (Monday to Thursday)
                next_start_time = next_day.replace(hour=8, minute=30, second=0, microsecond=0)
                time_to_start = (next_start_time - now).total_seconds() * 1000
                self.after(int(time_to_start), self.start_recording)
        elif weekday == 4:  # Friday
            start_time = now.replace(hour=8, minute=30, second=0, microsecond=0)
            stop_time = now.replace(hour=13, minute=0, second=0, microsecond=0)
            if start_time <= now < stop_time:
                self.start_recording_now()
                time_to_stop = (stop_time - now).total_seconds() * 1000
                self.after(int(time_to_stop), self.stop_recording)
            else:
                next_day = now + datetime.timedelta(days=3)  # Jump to next Monday
                next_start_time = next_day.replace(hour=8, minute=30, second=0, microsecond=0)
                time_to_start = (next_start_time - now).total_seconds() * 1000
                self.after(int(time_to_start), self.start_recording)
        else:  # Saturday or Sunday
            next_day = now + datetime.timedelta(days=(7 - weekday))
            next_weekday = (next_day.weekday() + 1) % 7  # Get the next weekday (Monday to Thursday)
            next_start_time = next_day.replace(hour=8, minute=30, second=0, microsecond=0)

            time_to_start = (next_start_time - now).total_seconds() * 1000
            self.after(int(time_to_start), self.start_recording)


        



    def update_elapsed_time(self):
        if self.recording_thread and self.recording_thread.is_alive():
            start_time = self.recording_thread.start_time
            if start_time:
                elapsed_time = datetime.datetime.now().replace(microsecond=0) - start_time
                self.elapsed_time_label.config(text=str(elapsed_time))
        self.after(1000, self.update_elapsed_time)  # Schedule the next update in 1 second


    def generate_filename(self):
        username = os.getlogin()
        date_time = time.strftime("%Y-%m-%d - %H_%M_%S")
        music_folder = os.path.expanduser("~\\Music")
        filename = os.path.join(music_folder, f"{username} - {date_time}.mp3")
        return filename

    def join(self, *args):
        threading.Thread.join(self, *args)

    def on_close(self):
        from tkinter import messagebox
        result = messagebox.askyesno("Close Voice Recorder", "Do you really want to close the Voice Recorder?")
        if result:
            self.destroy()

if __name__ == "__main__":
    app = RecorderApp()
    app.mainloop()
    