import tkinter as tk
from tkinter import ttk, messagebox

from frontend.api import api_search_books, api_place_order


class CustomerHome(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        ttk.Label(self, text="Customer Home", font=(None, 18)).pack(pady=10)

        ttk.Button(self, text="Search for Books", command=lambda: controller.show_frame("BookSearchScreen")).pack(pady=5)
        ttk.Button(self, text="View Order Draft / Cart", command=lambda: controller.show_frame("OrderFinalizationScreen")).pack(pady=5)
        ttk.Button(self, text="Log Out", command=self.logout).pack(pady=5)

    def logout(self):
        self.controller.reset_state()
        self.controller.show_frame("LoginScreen")


class BookSearchScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        ttk.Label(self, text="Book Search", font=(None, 18)).pack(pady=10)

        search_frame = ttk.Frame(self)
        search_frame.pack(pady=5)
        ttk.Label(search_frame, text="Keyword:").grid(row=0, column=0)
        self.keyword_entry = ttk.Entry(search_frame, width=40)
        self.keyword_entry.grid(row=0, column=1, padx=5)
        ttk.Button(search_frame, text="Search", command=self.on_search).grid(row=0, column=2)

        self.results_tree = ttk.Treeview(self, columns=("title", "author", "buy", "rent"), show="headings")
        self.results_tree.heading("title", text="Title")
        self.results_tree.heading("author", text="Author")
        self.results_tree.heading("buy", text="Buy Price")
        self.results_tree.heading("rent", text="Rent Price")
        self.results_tree.pack(fill="both", expand=True, pady=10)

        control_frame = ttk.Frame(self)
        control_frame.pack(pady=5)
        ttk.Button(control_frame, text="Add Selected as Buy", command=lambda: self.add_selected("buy")).grid(row=0, column=0, padx=5)
        ttk.Button(control_frame, text="Add Selected as Rent", command=lambda: self.add_selected("rent")).grid(row=0, column=1, padx=5)
        ttk.Button(control_frame, text="Finalize Order", command=lambda: controller.show_frame("OrderFinalizationScreen")).grid(row=0, column=2, padx=5)
        ttk.Button(control_frame, text="Back", command=lambda: controller.show_frame("CustomerHome")).grid(row=0, column=3, padx=5)

        self.last_results = []

    def on_search(self):
        keyword = self.keyword_entry.get().strip()
        def worker():
            token = getattr(self.controller, 'jwt_token', None)
            res = api_search_books(keyword, token)

            def ui_update():
                if not res.get("success"):
                    from tkinter import messagebox

                    messagebox.showerror("Search failed", res.get("msg", "Search error"))
                    return

                results = res.get("books", [])
                self.last_results = results

                for r in self.results_tree.get_children():
                    self.results_tree.delete(r)

                for book in results:
                    bid = str(book.get("id"))
                    self.results_tree.insert("", "end", iid=bid, values=(book.get("title"), book.get("author"), f"${book.get('buy_price')}", f"${book.get('rent_price')}"))

            self.controller.after(0, ui_update)

        import threading

        threading.Thread(target=worker, daemon=True).start()

    def add_selected(self, typ):
        sel = self.results_tree.selection()
        if not sel:
            messagebox.showinfo("No selection", "Please select a book from the results")
            return
        for iid in sel:
            book = next((b for b in self.last_results if str(b.get("id")) == iid), None)
            if book:
                price = book.get("buy_price") if typ == "buy" else book.get("rent_price")
                self.controller.order_draft.append({"book": book, "type": typ, "price": price})
        messagebox.showinfo("Added", "Selected items added to order draft")


class OrderFinalizationScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        ttk.Label(self, text="Finalize Order", font=(None, 18)).pack(pady=10)

        self.order_tree = ttk.Treeview(self, columns=("title", "type", "price"), show="headings")
        self.order_tree.heading("title", text="Title")
        self.order_tree.heading("type", text="Type")
        self.order_tree.heading("price", text="Price")
        self.order_tree.pack(fill="both", expand=True, pady=10)

        bottom = ttk.Frame(self)
        bottom.pack(pady=5)
        self.total_var = tk.StringVar(value="$0.00")
        ttk.Label(bottom, text="Total:").grid(row=0, column=0)
        ttk.Label(bottom, textvariable=self.total_var).grid(row=0, column=1)

        ttk.Button(bottom, text="Place Order", command=self.place_order).grid(row=0, column=2, padx=5)
        ttk.Button(bottom, text="Back to Search", command=lambda: controller.show_frame("BookSearchScreen")).grid(row=0, column=3, padx=5)
        ttk.Button(bottom, text="Back to Home", command=lambda: controller.show_frame("CustomerHome")).grid(row=0, column=4, padx=5)


    def on_show(self):
        self.refresh()

    def refresh(self):
        for r in self.order_tree.get_children():
            self.order_tree.delete(r)
        total = 0.0
        for idx, item in enumerate(self.controller.order_draft):
            title = item["book"]["title"]
            typ = item["type"]
            price = item["price"]
            total += price
            self.order_tree.insert("", "end", iid=str(idx), values=(title, typ, f"${price:.2f}"))
        self.total_var.set(f"${total:.2f}")

    def place_order(self):
        items = []
        for it in self.controller.order_draft:
            b = it["book"]
            items.append({"book_id": int(b.get("id")), "quantity": int(it.get("quantity", 1)), "type": it.get("type")})

        token = getattr(self.controller, "jwt_token", None)

        def worker():
            res = api_place_order(items, token)

            def ui_update():
                from tkinter import messagebox

                if not res.get("success"):
                    messagebox.showerror("Order failed", res.get("msg", "Order error"))
                    return
                messagebox.showinfo("Order Placed", "Order has been placed")
                self.controller.order_draft = []
                self.refresh()
                self.controller.show_frame("CustomerHome")

            self.controller.after(0, ui_update)

        import threading

        threading.Thread(target=worker, daemon=True).start()
