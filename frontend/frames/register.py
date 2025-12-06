import tkinter as tk
from tkinter import ttk, messagebox

from frontend.api import api_register


class RegisterScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        ttk.Label(self, text="Register", font=(None, 20)).pack(pady=10)

        form = ttk.Frame(self)
        form.pack(pady=10)

        ttk.Label(form, text="Username:").grid(row=0, column=0, sticky="e")
        self.username_entry = ttk.Entry(form)
        self.username_entry.grid(row=0, column=1)

        ttk.Label(form, text="Email:").grid(row=1, column=0, sticky="e")
        self.email_entry = ttk.Entry(form)
        self.email_entry.grid(row=1, column=1)

        ttk.Label(form, text="Password:").grid(row=2, column=0, sticky="e")
        self.password_entry = ttk.Entry(form, show="*")
        self.password_entry.grid(row=2, column=1)

        ttk.Label(form, text="Confirm:").grid(row=3, column=0, sticky="e")
        self.confirm_entry = ttk.Entry(form, show="*")
        self.confirm_entry.grid(row=3, column=1)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Register", command=self.on_register).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Back to Login", command=lambda: controller.show_frame("LoginScreen")).pack(side="left", padx=5)

    def on_register(self):
        username = self.username_entry.get().strip()
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        confirm = self.confirm_entry.get().strip()

        if not username or not email or not password:
            messagebox.showinfo("Missing", "Please fill in username, email and password")
            return
        if password != confirm:
            messagebox.showinfo("Mismatch", "Passwords do not match")
            return

        def worker():
            res = api_register(username, password, email)

            def ui_update():
                if res.get("success"):
                    messagebox.showinfo("Registered", "Account created — please login")
                    self.controller.show_frame("LoginScreen")
                else:
                    messagebox.showerror("Registration failed", res.get("msg", "Could not register"))

            self.controller.after(0, ui_update)

        import threading

        threading.Thread(target=worker, daemon=True).start()
