"""Frontend package entrypoint.

Run with: python -m frontend
This launches the Tkinter GUI by importing the frontend controller and starting
the mainloop.
"""
from frontend.controller import BookstoreApp


def main():
    app = BookstoreApp()
    app.mainloop()


if __name__ == "__main__":
    main()
