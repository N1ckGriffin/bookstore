import tkinter as tk
from tkinter import ttk

from frontend.api import api_login


class LoginScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        ttk.Label(self, text="Login", font=(None, 20)).pack(pady=10)

        form = ttk.Frame(self)
        form.pack(pady=10)

        ttk.Label(form, text="Username:").grid(row=0, column=0, sticky="e")
        self.username_entry = ttk.Entry(form)
        self.username_entry.grid(row=0, column=1)

        ttk.Label(form, text="Password:").grid(row=1, column=0, sticky="e")
        self.password_entry = ttk.Entry(form, show="*")
        self.password_entry.grid(row=1, column=1)

        self.role_var = tk.StringVar(value="customer")
        ttk.Radiobutton(form, text="Customer", variable=self.role_var, value="customer").grid(row=2, column=0)
        ttk.Radiobutton(form, text="Manager", variable=self.role_var, value="manager").grid(row=2, column=1)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Login", command=self.on_login).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Register", command=lambda: self.controller.show_frame("RegisterScreen")).grid(row=0, column=1, padx=5)

    def on_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        role = self.role_var.get()

        def worker():
            res = api_login(username, password)

            def ui_update():
                if res.get("success"):
                    token = res.get("token")
                    self.controller.jwt_token = token
                    self.controller.current_user = username
                    self.controller.current_role = role
                    if role == "customer":
                        self.controller.show_frame("CustomerHome")
                    else:
                        self.controller.show_frame("ManagerDashboard")
                else:
                    from tkinter import messagebox

                    messagebox.showerror("Login failed", res.get("msg", "Login failed"))

            self.controller.after(0, ui_update)

        import threading

        threading.Thread(target=worker, daemon=True).start()
