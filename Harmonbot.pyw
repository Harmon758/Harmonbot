
import atexit
from queue import Queue
from subprocess import Popen, PIPE
import sys
from threading import Thread
from tkinter import END, Frame, Text, Tk

import psutil

class HarmonbotGUI:
	
	def __init__(self, master):
		self.master = master
		master.title("Harmonbot")
		
		self.discord_frame = Frame(self.master)
		self.discord_frame.grid(row = 1, column = 1)
		self.discord_text = Text(self.discord_frame)
		self.discord_text.pack()
		
		self.discord_listener_frame = Frame(self.master)
		self.discord_listener_frame.grid(row = 2, column = 1)
		self.discord_listener_text = Text(self.discord_listener_frame)
		self.discord_listener_text.pack()
		
		self.twitch_frame = Frame(self.master)
		self.twitch_frame.grid(row = 1, column = 2)
		self.twitch_text = Text(self.twitch_frame)
		self.twitch_text.pack()
		
		self.telegram_frame = Frame(self.master)
		self.telegram_frame.grid(row = 2, column = 2)
		self.telegram_text = Text(self.telegram_frame)
		self.telegram_text.pack()

if __name__ == "__main__":
	root = Tk()
	root.wm_state("zoomed")  # Maximized window
	harmonbot_gui = HarmonbotGUI(root)
	
	discord_process = Popen([sys.executable, "-u", "Harmonbot.py"], cwd = "Discord", stdout = PIPE, stderr = PIPE, bufsize = 1, universal_newlines = True)
	discord_listener_process = Popen(["go", "run", "Harmonbot_Listener.go"], cwd = "Discord", stdout = PIPE, stderr = PIPE, bufsize = 1, universal_newlines = True, shell = True)
	twitch_process = Popen(["pyw", "-3.6", "-u", "Twitch_Harmonbot.py"], cwd = "Twitch", stdout = PIPE, stderr = PIPE, bufsize = 1, universal_newlines = True)
	# TODO: Update to use Python 3.7 executable
	telegram_process = Popen([sys.executable, "-u", "Telegram_Harmonbot.py"], cwd = "Telegram", stdout = PIPE, stderr = PIPE, bufsize = 1, universal_newlines = True)
	
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
	
	def process_outputs():
		while not discord_queue.empty():
			line = discord_queue.get_nowait()
			harmonbot_gui.discord_text.insert(END, line)
		while not discord_listener_queue.empty():
			line = discord_listener_queue.get_nowait()
			harmonbot_gui.discord_listener_text.insert(END, line)
		while not twitch_queue.empty():
			line = twitch_queue.get_nowait()
			harmonbot_gui.twitch_text.insert(END, line)
		while not telegram_queue.empty():
			line = telegram_queue.get_nowait()
			harmonbot_gui.telegram_text.insert(END, line)
		root.after(1, process_outputs)
	
	root.after(0, process_outputs)
	
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

