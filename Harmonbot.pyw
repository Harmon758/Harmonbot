
import atexit
from queue import Queue
from subprocess import Popen, PIPE
import sys
from threading import Thread
from tkinter import BOTH, END, Frame, Text, Tk, ttk

import psutil

class HarmonbotGUI:
	
	def __init__(self, master):
		self.master = master
		master.title("Harmonbot")
		
		self.notebook = ttk.Notebook(master)
		for tab in ("overview", "discord", "discord_listener", "twitch", "telegram"):
			frame = Frame(self.notebook)
			setattr(self, f"{tab}_tab", frame)
			self.notebook.add(frame, text = tab.replace('_', ' ').title())
		self.notebook.pack()
		
		for overview_frame in ("discord", "discord_listener", "twitch", "telegram"):
			frame = Frame(self.overview_tab)
			setattr(self, f"overview_{overview_frame}_frame", frame)
			text = Text(frame)
			setattr(self, f"overview_{overview_frame}_text", text)
			text.pack()
		self.overview_discord_frame.grid(row = 1, column = 1)
		self.overview_discord_listener_frame.grid(row = 2, column = 1)
		self.overview_twitch_frame.grid(row = 1, column = 2)
		self.overview_telegram_frame.grid(row = 2, column = 2)
		
		self.discord_frame = Frame(self.discord_tab)
		self.discord_frame.pack(expand = True, fill = BOTH)
		self.discord_text = Text(self.discord_frame)
		self.discord_text.pack(expand = True, fill = BOTH)
		
		self.discord_listener_frame = Frame(self.discord_listener_tab)
		self.discord_listener_frame.pack(expand = True, fill = BOTH)
		self.discord_listener_text = Text(self.discord_listener_frame)
		self.discord_listener_text.pack(expand = True, fill = BOTH)
		
		self.twitch_frame = Frame(self.twitch_tab)
		self.twitch_frame.pack(expand = True, fill = BOTH)
		self.twitch_text = Text(self.twitch_frame)
		self.twitch_text.pack(expand = True, fill = BOTH)
		
		self.telegram_frame = Frame(self.telegram_tab)
		self.telegram_frame.pack(expand = True, fill = BOTH)
		self.telegram_text = Text(self.telegram_frame)
		self.telegram_text.pack(expand = True, fill = BOTH)

if __name__ == "__main__":
	root = Tk()
	root.wm_state("zoomed")  # Maximized window
	harmonbot_gui = HarmonbotGUI(root)
	
	process_kwargs = {"stdout": PIPE, "stderr": PIPE, "bufsize": 1, "universal_newlines": True}
	discord_process = Popen([sys.executable, "-u", "Harmonbot.py"], cwd = "Discord", **process_kwargs)
	discord_listener_process = Popen(["go", "run", "Harmonbot_Listener.go"], cwd = "Discord", shell = True, **process_kwargs)
	twitch_process = Popen(["pyw", "-3.6", "-u", "Twitch_Harmonbot.py"], cwd = "Twitch", **process_kwargs)
	# TODO: Update to use Python 3.7 executable
	telegram_process = Popen([sys.executable, "-u", "Telegram_Harmonbot.py"], cwd = "Telegram", **process_kwargs)
	
	def enqueue_output(out, queue):
		for line in iter(out.readline, ""):
			queue.put(line)
		out.close()
	
	discord_queue = Queue()
	discord_thread = Thread(target = enqueue_output, args = (discord_process.stdout, discord_queue))
	discord_thread.daemon = True
	discord_thread.start()
	
	discord_listener_queue = Queue()
	discord_listener_thread = Thread(target = enqueue_output, args = (discord_listener_process.stdout, discord_listener_queue))
	discord_listener_thread.daemon = True
	discord_listener_thread.start()
	
	twitch_queue = Queue()
	twitch_thread = Thread(target = enqueue_output, args = (twitch_process.stdout, twitch_queue))
	twitch_thread.daemon = True
	twitch_thread.start()
	
	telegram_queue = Queue()
	telegram_thread = Thread(target = enqueue_output, args = (telegram_process.stdout, telegram_queue))
	telegram_thread.daemon = True
	telegram_thread.start()
	
	discord_err_queue = Queue()
	discord_err_thread = Thread(target = enqueue_output, args = (discord_process.stderr, discord_err_queue))
	discord_err_thread.daemon = True
	discord_err_thread.start()
	
	discord_listener_err_queue = Queue()
	discord_listener_err_thread = Thread(target = enqueue_output, args = (discord_listener_process.stderr, discord_listener_err_queue))
	discord_listener_err_thread.daemon = True
	discord_listener_err_thread.start()
	
	twitch_err_queue = Queue()
	twitch_err_thread = Thread(target = enqueue_output, args = (twitch_process.stderr, twitch_err_queue))
	twitch_err_thread.daemon = True
	twitch_err_thread.start()
	
	telegram_err_queue = Queue()
	telegram_err_thread = Thread(target = enqueue_output, args = (telegram_process.stderr, telegram_err_queue))
	telegram_err_thread.daemon = True
	telegram_err_thread.start()
	
	def process_outputs():
		while not discord_queue.empty():
			line = discord_queue.get_nowait()
			harmonbot_gui.overview_discord_text.insert(END, line)
			harmonbot_gui.discord_text.insert(END, line)
		while not discord_listener_queue.empty():
			line = discord_listener_queue.get_nowait()
			harmonbot_gui.overview_discord_listener_text.insert(END, line)
			harmonbot_gui.discord_listener_text.insert(END, line)
		while not twitch_queue.empty():
			line = twitch_queue.get_nowait()
			harmonbot_gui.overview_twitch_text.insert(END, line)
			harmonbot_gui.twitch_text.insert(END, line)
		while not telegram_queue.empty():
			line = telegram_queue.get_nowait()
			harmonbot_gui.overview_telegram_text.insert(END, line)
			harmonbot_gui.telegram_text.insert(END, line)
		root.after(1, process_outputs)
	
	def process_error_outputs():
		while not discord_err_queue.empty():
			line = discord_err_queue.get_nowait()
			harmonbot_gui.overview_discord_text.insert(END, line)
			harmonbot_gui.discord_text.insert(END, line)
		while not discord_listener_err_queue.empty():
			line = discord_listener_err_queue.get_nowait()
			harmonbot_gui.overview_discord_listener_text.insert(END, line)
			harmonbot_gui.discord_listener_text.insert(END, line)
		while not twitch_err_queue.empty():
			line = twitch_err_queue.get_nowait()
			harmonbot_gui.overview_twitch_text.insert(END, line)
			harmonbot_gui.twitch_text.insert(END, line)
		while not telegram_err_queue.empty():
			line = telegram_err_queue.get_nowait()
			harmonbot_gui.overview_telegram_text.insert(END, line)
			harmonbot_gui.telegram_text.insert(END, line)
		root.after(1, process_error_outputs)
		# TODO: Check order with stdout
	
	def check_discord_process_ended():
		if discord_process.poll() is None:
			root.after(1, check_discord_process_ended)
		else:
			line = "Discord process ended"
			harmonbot_gui.overview_discord_text.insert(END, line)
			harmonbot_gui.discord_text.insert(END, line)
	
	def check_discord_listener_process_ended():
		if discord_listener_process.poll() is None:
			root.after(1, check_discord_listener_process_ended)
		else:
			line = "Discord listener process ended"
			harmonbot_gui.overview_discord_listener_text.insert(END, line)
			harmonbot_gui.discord_listener_text.insert(END, line)
	
	def check_twitch_process_ended():
		if twitch_process.poll() is None:
			root.after(1, check_twitch_process_ended)
		else:
			line = "Twitch process ended"
			harmonbot_gui.overview_twitch_text.insert(END, line)
			harmonbot_gui.twitch_text.insert(END, line)
	
	def check_telegram_process_ended():
		if telegram_process.poll() is None:
			root.after(1, check_telegram_process_ended)
		else:
			line = "Telegram process ended"
			harmonbot_gui.overview_telegram_text.insert(END, line)
			harmonbot_gui.telegram_text.insert(END, line)
	
	for function in (process_outputs, process_error_outputs, check_discord_process_ended, 
						check_discord_listener_process_ended, check_twitch_process_ended, 
						check_telegram_process_ended):
		root.after(0, function)
	
	def cleanup():
		discord_process.terminate()
		go_process = psutil.Process(discord_listener_process.pid)
		for process in go_process.children(recursive = True):
			process.terminate()
		go_process.terminate()
		twitch_process.terminate()
		telegram_process.terminate()
		## root.destroy()
	
	atexit.register(cleanup)
	
	## root.protocol("WM_DELETE_WINDOW", cleanup)
	root.mainloop()

