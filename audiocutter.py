import os
import datetime
from tkinter import Tk, Label, Button, Entry, filedialog, Text, Scrollbar  
from moviepy.editor import *

class AudiocutterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Audiocutter")

        # Browse MP3 file
        self.browse_button = Button(root, text="Browse MP3", command=self.browse_mp3)
        self.browse_button.grid(row=0, column=0)

        # Display the MP3 file name
        self.mp3_label = Label(root, text="")
        self.mp3_label.grid(row=0, column=1, padx=(10, 0))

        # Browse destination folder
        self.browse_folder_button = Button(root, text="Browse Folder", command=self.browse_folder)
        self.browse_folder_button.grid(row=1, column=0)

        # Display the destination folder path
        self.folder_label = Label(root, text="")
        self.folder_label.grid(row=1, column=1, padx=(7, 0))  

        # RecordingTimes input 
        self.recording_times_label = Label(root, text="RecordingTimes")
        self.recording_times_label.grid(row=2, column=0)
        self.recording_times_input = Text(root, width=30, height=10, wrap="none")
        self.recording_times_input.grid(row=2, column=1)
        self.scrollbar = Scrollbar(root, command=self.recording_times_input.yview)
        self.scrollbar.grid(row=2, column=2, sticky="NS")
        self.recording_times_input.config(yscrollcommand=self.scrollbar.set)

        # Cut button
        self.cut_button = Button(root, text="Cut Audio", command=self.cut_audio) 
        self.cut_button.grid(row=3, column=0)

        # Set FFMPEG Windows path   
        self.set_ffmpeg_path()
        
    def browse_mp3(self):
        self.mp3_path = filedialog.askopenfilename(filetypes=[("MP3 files", "*.mp3")])
        self.timecodes_path = self.mp3_path.replace(".mp3", "_timecodes.txt")

        # Step 1: Display the MP3 file name
        self.mp3_label.config(text=os.path.basename(self.mp3_path))

        # Step 2: Set the initial destination folder to the root folder of the MP3 file
        self.destination_folder = os.path.dirname(self.mp3_path)
        self.folder_label.config(text=self.destination_folder)

    def browse_folder(self):
        self.destination_folder = filedialog.askdirectory()

        # Step 3 and 4: Display the selected destination folder path
        self.folder_label.config(text=self.destination_folder)  
        
    def browse_folder(self):
        self.destination_folder = filedialog.askdirectory()   
        
    def cut_audio(self):
        audio = AudioFileClip(self.mp3_path)
        timecodes = self.parse_timecodes(self.timecodes_path)
        recording_times = self.recording_times_input.get("1.0", "end-1c").splitlines()

        # Extract the first two parts of the original MP3 filename
        filename_parts = os.path.basename(self.mp3_path).split(" - ")[:2]
        filename_prefix = " - ".join(filename_parts)

        for i, recording_time in enumerate(recording_times):
            start_time_str, duration_str = recording_time.split("(")
            duration_str = duration_str.replace(")", "")

            start_time = self.time_to_seconds(start_time_str, timecodes)
            duration = self.time_to_seconds(duration_str)

            audio_part = audio.subclip(start_time, start_time + duration)

            # Step 1: Format the part number with 2 digits
            part_number = i + 1
            part_str = f"part_{part_number:02d}"

            # Step 2: Find the next available part number if the file already exists
            output_filename = f"{filename_prefix} - {part_str}.mp3"
            while os.path.exists(os.path.join(self.destination_folder, output_filename)):
                part_number += 1
                part_str = f"part_{part_number:02d}"
                output_filename = f"{filename_prefix} - {part_str}.mp3"

            audio_part.write_audiofile(os.path.join(self.destination_folder, output_filename))



    def parse_timecodes(self, timecodes_path):
        with open(timecodes_path, "r") as file:
            timecodes = [line.strip().split(" > ") for line in file.readlines()]
        return timecodes

    def time_to_seconds(self, time_str, timecodes=None):
        if timecodes:
            input_time = datetime.datetime.strptime(time_str, "%H:%M:%S")

            for i, tc in enumerate(timecodes):
                # Convert the HH:MM:SS time to datetime objects
                recorded_time = datetime.datetime.strptime(tc[1], "%Y-%m-%d %H:%M:%S")

                if i < len(timecodes) - 1:
                    next_recorded_time = datetime.datetime.strptime(timecodes[i + 1][1], "%Y-%m-%d %H:%M:%S")
                else:
                    next_recorded_time = None

                # Compare the input_time with the recorded_time (ignoring the date part)
                if input_time.time() >= recorded_time.time() and (next_recorded_time is None or input_time.time() < next_recorded_time.time()):
                    time_str = tc[0]
                    break

        time_parts = list(map(int, time_str.split(":")))
        if len(time_parts) == 3:
            h, m, s = time_parts
        elif len(time_parts) == 2:
            m, s = time_parts
            h = 0
        else:
            raise ValueError("Invalid time format")

        return h * 3600 + m * 60 + s




    def set_ffmpeg_path(self):
        ffmpeg_path = r"C:\ffmpeg\ffmpeg.exe"
        os.environ['IMAGEIO_FFMPEG_EXE'] = ffmpeg_path

if __name__ == "__main__":
    root = Tk()
    app = AudiocutterApp(root)
    root.mainloop()
