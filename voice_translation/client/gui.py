import asyncio
import json
import tkinter as tk
from tkinter import scrolledtext, ttk

import websockets


class TranslationClient:
    def __init__(self):
        self.websocket = None
        self.user_id = None
        self.preferred_language = "en"
        self.languages = {
            "English": "en",
            "Arabic": "ar",
            "Turkish": "tr",
            "Chinese": "zh",
        }
        self.setup_gui()

    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("Voice Translation System")
        self.root.geometry("600x500")

        # Connection frame
        conn_frame = ttk.Frame(self.root)
        conn_frame.pack(pady=10, padx=10, fill="x")

        ttk.Label(conn_frame, text="User ID:").pack(side="left")
        self.user_id_entry = ttk.Entry(conn_frame, width=15)
        self.user_id_entry.pack(side="left", padx=5)

        ttk.Label(conn_frame, text="Language:").pack(side="left", padx=(20, 5))
        self.language_var = tk.StringVar(value="English")
        self.language_combo = ttk.Combobox(
            conn_frame,
            textvariable=self.language_var,
            values=list(self.languages.keys()),
            width=10,
        )
        self.language_combo.pack(side="left", padx=5)

        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.connect)
        self.connect_btn.pack(side="left", padx=10)

        # Status
        self.status_label = ttk.Label(self.root, text="Disconnected", foreground="red")
        self.status_label.pack(pady=5)

        # Results
        results_frame = ttk.LabelFrame(self.root, text="Results")
        results_frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.results_text = scrolledtext.ScrolledText(
            results_frame, height=20, width=70
        )
        self.results_text.pack(pady=10, padx=10, fill="both", expand=True)

        # Update button
        ttk.Button(
            self.root, text="Update Language", command=self.update_language
        ).pack(pady=5)

    async def connect_to_server(self):
        try:
            self.websocket = await websockets.connect("ws://localhost:8765")

            registration_data = {
                "type": "register",
                "user_id": self.user_id,
                "preferred_language": self.languages[self.language_var.get()],
            }

            await self.websocket.send(json.dumps(registration_data))

            async for message in self.websocket:
                data = json.loads(message)
                self.handle_server_message(data)

        except Exception as e:
            self.update_status(f"Connection error: {str(e)}", "red")

    def handle_server_message(self, data):
        if data["type"] == "registration_success":
            self.update_status("Connected", "green")
            self.preferred_language = data["preferred_language"]

        elif data["type"] == "transcription_result":
            self.display_result(data)

    def display_result(self, data):
        speaker_id = data["speaker_id"]
        original_text = data["original_text"]
        detected_lang = data["detected_language"]
        translations = data["translations"]

        result_text = f"\n--- Speaker {speaker_id} ({detected_lang}) ---\n"
        result_text += f"Original: {original_text}\n"

        if self.user_id in translations:
            result_text += f"Translation ({self.preferred_language}): {translations[self.user_id]}\n"

        self.results_text.insert(tk.END, result_text)
        self.results_text.see(tk.END)

    def update_status(self, message, color):
        self.status_label.config(text=message, foreground=color)

    def connect(self):
        self.user_id = self.user_id_entry.get().strip()
        if not self.user_id:
            self.update_status("Please enter User ID", "red")
            return

        asyncio.create_task(self.connect_to_server())

    def update_language(self):
        if self.websocket:
            new_language = self.languages[self.language_var.get()]
            update_data = {
                "type": "update_preference",
                "user_id": self.user_id,
                "preferred_language": new_language,
            }

            asyncio.create_task(self.websocket.send(json.dumps(update_data)))
            self.preferred_language = new_language
            self.update_status(f"Language updated to {self.language_var.get()}", "blue")

    def run(self):
        self.root.mainloop()
