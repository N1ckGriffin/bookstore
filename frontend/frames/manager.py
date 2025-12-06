import tkinter as tk
from tkinter import ttk, messagebox

from frontend.api import (
    api_list_orders,
    api_update_payment_status,
    api_create_book,
    api_update_book,
    api_list_manager_books,
)


class ManagerDashboard(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        ttk.Label(self, text="Manager Dashboard", font=(None, 18)).pack(pady=10)

        ttk.Button(self, text="View All Orders", command=lambda: controller.show_frame("OrdersScreen")).pack(pady=5)
        ttk.Button(self, text="Create Book", command=lambda: (setattr(controller, 'book_maintenance_mode', 'create'), controller.show_frame("BookMaintenanceScreen"))).pack(pady=5)
        ttk.Button(self, text="Update Book", command=lambda: (setattr(controller, 'book_maintenance_mode', 'update'), controller.show_frame("BookMaintenanceScreen"))).pack(pady=5)
        ttk.Button(self, text="Log Out", command=self.logout).pack(pady=5)

    def logout(self):
        self.controller.reset_state()
        self.controller.show_frame("LoginScreen")


class OrdersScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        ttk.Label(self, text="Orders", font=(None, 18)).pack(pady=10)

        self.tree = ttk.Treeview(self, columns=("customer", "items", "total", "status"), show="headings")
        self.tree.heading("customer", text="Customer")
        self.tree.heading("items", text="Items")
        self.tree.heading("total", text="Total")
        self.tree.heading("status", text="Payment Status")
        self.tree.pack(fill="both", expand=True, pady=10)

        update_frame = ttk.Frame(self)
        update_frame.pack(pady=5)
        ttk.Label(update_frame, text="Update Payment Status:").grid(row=0, column=0, padx=5)
        self.status_var = tk.StringVar(value="pending")
        self.status_combo = ttk.Combobox(update_frame, textvariable=self.status_var, values=("pending", "paid"), state="readonly", width=10)
        self.status_combo.grid(row=0, column=1, padx=5)
        ttk.Button(update_frame, text="Update Selected Order", command=self.update_selected_status).grid(row=0, column=2, padx=5)

        btn = ttk.Frame(self)
        btn.pack(pady=5)
        ttk.Button(btn, text="Refresh", command=self.load_orders).grid(row=0, column=0, padx=5)
        ttk.Button(btn, text="Back", command=lambda: controller.show_frame("ManagerDashboard")).grid(row=0, column=1, padx=5)

    def on_show(self):
        """Called by controller when this frame becomes visible - load orders lazily."""
        self.load_orders()

    def load_orders(self):
        def worker():
            token = getattr(self.controller, "jwt_token", None)

            res = api_list_orders(token)

            def ui_update():
                from tkinter import messagebox

                for r in self.tree.get_children():
                    self.tree.delete(r)
                if not res.get("success"):
                    messagebox.showerror("Load failed", res.get("msg", "Could not load orders"))
                    return
                for o in res.get("orders", []):
                    items = o.get("items", [])
                    items_str = ", ".join([f"{it.get('book')}({it.get('type')})" for it in items])
                    self.tree.insert("", "end", iid=o.get("id"), values=(o.get("customer"), items_str, f"${o.get('total')}", o.get("payment_status")))

            self.controller.after(0, ui_update)

        import threading

        threading.Thread(target=worker, daemon=True).start()

    def update_selected_status(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("No selection", "Please select an order to update")
            return
        order_id = sel[0]  # iid is id
        new_status = self.status_var.get()

        def worker():
            token = getattr(self.controller, "jwt_token", None)
            res = api_update_payment_status(order_id, new_status, token)

            def ui_update():
                from tkinter import messagebox

                if not res.get("success"):
                    messagebox.showerror("Update failed", res.get("msg", "Could not update status"))
                    return
                messagebox.showinfo("Updated", f"Order status updated to {new_status}")
                self.load_orders()

            self.controller.after(0, ui_update)

        import threading

        threading.Thread(target=worker, daemon=True).start()


class BookMaintenanceScreen(ttk.Frame):
    """Book maintenance screen with separate Create vs Update modes.

    - Create mode: simple form to create a book (title, author, buy/rent). No selector.
    - Update mode: shows a selector to pick an existing book and allows update/delete, including total copies.
    """

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        ttk.Label(self, text="Book Maintenance", font=(None, 18)).pack(pady=10)

        form = ttk.Frame(self)
        form.pack(pady=10)

        self.book_label = ttk.Label(form, text="Select Book (for update):")
        self.book_label.grid(row=0, column=0)
        self.book_var = tk.StringVar()
        self.book_select = ttk.Combobox(form, textvariable=self.book_var, state="readonly", width=47)
        self.book_select.grid(row=0, column=1)
        self._books_cache = []

        ttk.Label(form, text="Title:").grid(row=1, column=0)
        self.title_entry = ttk.Entry(form, width=50)
        self.title_entry.grid(row=1, column=1)

        ttk.Label(form, text="Author:").grid(row=2, column=0)
        self.author_entry = ttk.Entry(form, width=50)
        self.author_entry.grid(row=2, column=1)

        ttk.Label(form, text="Buy Price:").grid(row=3, column=0)
        self.buy_entry = ttk.Entry(form)
        self.buy_entry.grid(row=3, column=1)

        ttk.Label(form, text="Rent Price:").grid(row=4, column=0)
        self.rent_entry = ttk.Entry(form)
        self.rent_entry.grid(row=4, column=1)

        self.available_label = ttk.Label(form, text="Available Copies:")
        self.available_label.grid(row=5, column=0)
        self.available_entry = ttk.Entry(form)
        self.available_entry.grid(row=5, column=1)
        btns = ttk.Frame(form)
        btns.grid(row=6, column=0, columnspan=2, pady=5)
        self.create_btn = ttk.Button(btns, text="Create New Book", command=self.create_book)
        self.create_btn.grid(row=0, column=0, padx=5)

        self.update_btn = ttk.Button(btns, text="Update Existing Book", command=self.update_book)
        self.update_btn.grid(row=0, column=1, padx=5)

        self.back_btn = ttk.Button(btns, text="Back", command=lambda: controller.show_frame("ManagerDashboard"))
        self.back_btn.grid(row=0, column=2, padx=5)

        try:
            self.book_select.unbind('<<ComboboxSelected>>')
        except Exception:
            pass
        self.book_select.bind('<<ComboboxSelected>>', lambda e: self._on_book_selected())

    def create_book(self):
        title = self.title_entry.get().strip()
        author = self.author_entry.get().strip()
        buy = self.buy_entry.get().strip()
        rent = self.rent_entry.get().strip()
        available = self.available_entry.get().strip()

        if not title or not author:
            messagebox.showinfo("Missing", "Title and Author required")
            return

        def worker():
            token = getattr(self.controller, "jwt_token", None)
            data = {
                "title": title,
                "author": author,
                "buy_price": float(buy) if buy else 0.0,
                "rent_price": float(rent) if rent else 0.0,
                "available_copies": int(available) if available else 1,
            }
            res = api_create_book(data, token)

            def ui_update():
                if not res.get("success"):
                    messagebox.showerror("Create failed", res.get("msg", "Could not create book"))
                    return
                messagebox.showinfo("Created", "Book created")
                self.title_entry.delete(0, 'end')
                self.author_entry.delete(0, 'end')
                self.buy_entry.delete(0, 'end')
                self.rent_entry.delete(0, 'end')
                self.available_entry.delete(0, 'end')

            self.controller.after(0, ui_update)

        import threading

        threading.Thread(target=worker, daemon=True).start()

    def on_show(self):
        mode = getattr(self.controller, 'book_maintenance_mode', 'create')

        def worker():
            token = getattr(self.controller, "jwt_token", None)
            res = api_list_manager_books(token)

            def ui_update():
                if not res.get("success"):
                    books = []
                else:
                    books = res.get("books", [])
                self._books_cache = books
                values = [b.get('title') for b in books]
                self.book_select['values'] = values

                self.title_entry.delete(0, 'end')
                self.author_entry.delete(0, 'end')
                self.buy_entry.delete(0, 'end')
                self.rent_entry.delete(0, 'end')
                self.available_entry.delete(0, 'end')
                self.book_var.set('')  # clear selection

                if mode == 'create':
                    try:
                        self.book_label.grid_remove()
                    except Exception:
                        pass
                    try:
                        self.book_select.grid_remove()
                    except Exception:
                        pass

                    try:
                        self.create_btn.grid()
                    except Exception:
                        pass
                    try:
                        self.update_btn.grid_remove()
                    except Exception:
                        pass
                    try:
                        self.delete_btn.grid_remove()
                    except Exception:
                        pass
                else:
                    try:
                        self.book_label.grid()
                    except Exception:
                        pass
                    try:
                        self.book_select.grid()
                    except Exception:
                        pass
                    try:
                        self.available_label.grid()
                    except Exception:
                        pass
                    try:
                        self.available_entry.grid()
                    except Exception:
                        pass

                    try:
                        self.create_btn.grid_remove()
                    except Exception:
                        pass
                    try:
                        self.update_btn.grid()
                    except Exception:
                        pass

            self.controller.after(0, ui_update)

        import threading

        threading.Thread(target=worker, daemon=True).start()

    def _on_book_selected(self):
        sel = self.book_var.get().strip()
        if not sel:
            return
        book = next((b for b in self._books_cache if b.get('title') == sel), None)
        if not book:
            return
        self.title_entry.delete(0, 'end')
        self.title_entry.insert(0, book.get('title') or '')
        self.author_entry.delete(0, 'end')
        self.author_entry.insert(0, book.get('author') or '')
        self.buy_entry.delete(0, 'end')
        self.buy_entry.insert(0, str(book.get('buy_price') or ''))
        self.rent_entry.delete(0, 'end')
        self.rent_entry.insert(0, str(book.get('rent_price') or ''))
        try:
            self.available_entry.delete(0, 'end')
            self.available_entry.insert(0, str(book.get('available_copies') or ''))
        except Exception:
            pass

    def update_book(self):
        sel = self.book_var.get().strip()
        if not sel:
            messagebox.showinfo("Missing", "Please select a book to update")
            return
        book = next((b for b in self._books_cache if b.get('title') == sel), None)
        if not book:
            messagebox.showerror("Error", "Invalid Book selection")
            return
        bid = book.get('id')

        title = self.title_entry.get().strip()
        author = self.author_entry.get().strip()
        buy = self.buy_entry.get().strip()
        rent = self.rent_entry.get().strip()
        available = self.available_entry.get().strip()

        data = {}
        if title:
            data['title'] = title
        if author:
            data['author'] = author
        if buy:
            try:
                data['buy_price'] = float(buy)
            except Exception:
                pass
        if rent:
            try:
                data['rent_price'] = float(rent)
            except Exception:
                pass
        if available:
            try:
                data['available_copies'] = int(available)
            except Exception:
                pass

        def worker():
            token = getattr(self.controller, 'jwt_token', None)
            res = api_update_book(bid, data, token)

            def ui_update():
                if not res.get('success'):
                    messagebox.showerror('Update failed', res.get('msg', 'Could not update book'))
                    return
                messagebox.showinfo('Updated', 'Book updated')

            self.controller.after(0, ui_update)

        import threading

        threading.Thread(target=worker, daemon=True).start()
