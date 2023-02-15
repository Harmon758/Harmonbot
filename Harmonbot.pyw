#! /usr/bin/env python3.10

import atexit
from queue import Queue
from subprocess import CREATE_NO_WINDOW, Popen, PIPE
import sys
from threading import Thread
from tkinter import BOTH, BooleanVar, Checkbutton, END, Frame, NONE, Text, Tk, ttk
from tkinter.font import Font

import psutil

class HarmonbotGUI:
	
	def __init__(self, master):
		self.master = master
		master.title("Harmonbot")
		self.bots = ["discord", "discord_listener", "twitch", "telegram"]
		self.text_background_color = "Silver"
		self.text_font = Font(family = "TkDefaultFont", size = "11")  # Other?
		
		self.notebook = ttk.Notebook(master)
		for tab in ["overview"] + self.bots:
			frame = Frame(self.notebook)
			setattr(self, f"{tab}_tab", frame)
			self.notebook.add(frame, text = tab.replace('_', ' ').title())
		self.notebook.pack()
		
		for bot in self.bots:
			frame = Frame(self.overview_tab)
			setattr(self, f"overview_{bot}_frame", frame)
			text = Text(frame, wrap = NONE, background = self.text_background_color, font = self.text_font)
			setattr(self, f"overview_{bot}_text", text)
			text.pack()
		self.overview_discord_frame.grid(row = 1, column = 1)
		self.overview_discord_listener_frame.grid(row = 2, column = 1)
		self.overview_twitch_frame.grid(row = 1, column = 2)
		self.overview_telegram_frame.grid(row = 2, column = 2)
		self.overview_tab.grid_columnconfigure(1, weight = 1)
		self.overview_tab.grid_columnconfigure(2, weight = 1)
		self.overview_tab.grid_rowconfigure(1, weight = 1)
		self.overview_tab.grid_rowconfigure(2, weight = 1)
		
		self.overview_controls_frame = Frame(self.overview_tab)
		self.overview_controls_frame.grid(row = 1, column = 3, rowspan = 2, ipadx = 30)
		self.overview_tab.grid_columnconfigure(3, weight = 1)
		
		for bot in self.bots:
			setattr(self, f"autorestart_{bot}", BooleanVar())
			checkbutton = Checkbutton(self.overview_controls_frame, 
										text = f"Auto-Restart {bot.replace('_', ' ').title()}", 
										variable = getattr(self, f"autorestart_{bot}"))
			setattr(self, f"autorestart_{bot}_checkbutton", checkbutton)
			checkbutton.pack()
			checkbutton.select()
			
			notebook_tab = getattr(self, f"{bot}_tab")
			frame = Frame(notebook_tab)
			setattr(self, f"{bot}_frame", frame)
			frame.pack(expand = True, fill = BOTH)
			text = Text(frame, background = self.text_background_color, font = self.text_font)
			setattr(self, f"{bot}_text", text)
			text.pack(expand = True, fill = BOTH)

if __name__ == "__main__":
	root = Tk()
	root.wm_state("zoomed")  # Maximized window
	harmonbot_gui = HarmonbotGUI(root)
	
	processes = {}
	process_args = {}
	process_args["discord"] = [sys.executable, "-u", "Harmonbot.py"]
	process_args["discord_listener"] = ["go", "run", "Harmonbot_Listener.go"]
	process_args["twitch"] = [sys.executable, "-u", "Twitch_Harmonbot.py"]
	process_args["telegram"] = [sys.executable, "-u", "Telegram_Harmonbot.py"]
	
	def start_process(process):
		process_kwargs = {"stdout": PIPE, "stderr": PIPE, "bufsize": 1, "encoding": "UTF-8"}
		# "errors": "backslashreplace" necessary?
		if process == "discord_listener":
			process_kwargs["creationflags"] = CREATE_NO_WINDOW
		processes[process] = Popen(process_args[process], cwd = process.split('_')[0].capitalize(), **process_kwargs)
	
	def enqueue_output(out, queue):
		with out:
			for line in iter(out.readline, ""):
				queue.put(line)
	
	output_queues = {}
	output_threads = {"stdout": {}, "stderr": {}}
	
	def output_thread(process):
		output_queue = Queue()
		output_queues[process] = output_queue
		for output_type in ("stdout", "stderr"):
			process_output = getattr(processes[process], output_type)
			output_thread = Thread(target = enqueue_output, args = (process_output, output_queue))
			output_threads[output_type][process] = output_thread
			output_thread.daemon = True
			output_thread.start()
	
	for bot in harmonbot_gui.bots:
		start_process(bot)
		output_thread(bot)
	
	# TODO: Check stdout and stderr order
	
	def process_output(name):
		output_queue = output_queues[name]
		while not output_queue.empty():
			line = output_queue.get_nowait()
			for text_name in (f"overview_{name}_text", f"{name}_text"):
				text = getattr(harmonbot_gui, text_name)
				text.insert(END, line)
		root.after(100, process_output, name)  # Every 1/10 sec.
	
	def check_process_ended(name):
		if processes[name].poll() is None:
			root.after(100, check_process_ended, name)  # Every 1/10 sec.
		elif getattr(harmonbot_gui, f"autorestart_{name}").get():
			line = f"Restarting {name.replace('_', ' ').title()} process\n"
			for text_name in (f"overview_{name}_text", f"{name}_text"):
				text = getattr(harmonbot_gui, text_name)
				text.insert(END, line)
			start_process(name)
			output_thread(name)
			root.after(100, check_process_ended, name)  # Every 1/10 sec.
		else:
			line = f"{name.replace('_', ' ').title()} process ended"
			for text_name in (f"overview_{name}_text", f"{name}_text"):
				text = getattr(harmonbot_gui, text_name)
				text.insert(END, line)
	
	for process in processes:
		root.after(0, process_output, process)
		root.after(0, check_process_ended, process)
	
	def cleanup():
		go_process = psutil.Process(processes["discord_listener"].pid)
		for process in go_process.children(recursive = True):
			process.terminate()
		for process in processes.values():
			process.terminate()
		## root.destroy()
	
	atexit.register(cleanup)
	
	## root.protocol("WM_DELETE_WINDOW", cleanup)
	root.mainloop()

