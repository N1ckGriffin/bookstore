import tkinter as tk
from tkinter import ttk

from frontend.frames.login import LoginScreen
from frontend.frames.register import RegisterScreen
from frontend.frames.customer import CustomerHome, BookSearchScreen, OrderFinalizationScreen
from frontend.frames.manager import (
    ManagerDashboard,
    OrdersScreen,
    BookMaintenanceScreen,
)


class BookstoreApp(tk.Tk):
    """Main application controller that manages frames and shared state."""

    def __init__(self):
        super().__init__()
        self.title("Online Bookstore")
        self.geometry("800x600")

        self.current_user = None
        self.current_role = None  # 'customer' or 'manager'
        self.jwt_token = None
        self.order_draft = []  # list of dicts: {book, type: 'buy'|'rent', price}
        self.book_maintenance_mode = 'create'  # 'create' or 'update'

        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)

        self.frames = {}
        for F in (
            LoginScreen,
            RegisterScreen,
            CustomerHome,
            BookSearchScreen,
            OrderFinalizationScreen,
            ManagerDashboard,
            OrdersScreen,
            BookMaintenanceScreen,
        ):
            frame = F(container, self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("LoginScreen")

    def show_frame(self, name):
        frame = self.frames[name]
        frame.tkraise()
        try:
            on_show = getattr(frame, "on_show", None)
            if callable(on_show):
                on_show()
        except Exception:
            pass

    def reset_state(self):
        self.current_user = None
        self.current_role = None
        self.jwt_token = None
        self.order_draft = []
