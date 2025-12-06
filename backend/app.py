import os
from flask import Flask, jsonify, request
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
)
from backend.password import hash_password, verify_password

from backend.config import Config
from backend.models import db, User, Book, Order, OrderItem
from backend.email_utils import send_order_email


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    jwt = JWTManager(app)

    @app.route("/register", methods=["POST"])
    def register():
        try:
            data = request.get_json() or {}
            username = data.get("username")
            password = data.get("password")
            email = data.get("email")
            if not username or not password or not email:
                return jsonify({"msg": "username, password, email required"}), 400

            if User.query.filter_by(username=username).first():
                return jsonify({"msg": "username already exists"}), 400
            if User.query.filter_by(email=email).first():
                return jsonify({"msg": "email already used"}), 400

            pw_hash = hash_password(password)
            user = User(username=username, password_hash=pw_hash, email=email, role="customer")
            db.session.add(user)
            db.session.commit()
            return jsonify({"msg": "registered"}), 201
        except Exception:
            app.logger.exception("Error in register endpoint")
            return jsonify({"msg": "internal error"}), 500

    @app.route("/login", methods=["POST"])
    def login():
        data = request.get_json() or {}
        username = data.get("username")
        password = data.get("password")
        if not username or not password:
            return jsonify({"msg": "username and password required"}), 400
        user = User.query.filter_by(username=username).first()
        if not user or not verify_password(password, user.password_hash):
            return jsonify({"msg": "bad credentials"}), 401
        additional = {"id": user.id, "role": user.role, "username": user.username}
        access = create_access_token(identity=str(user.id), additional_claims=additional)
        return jsonify({"access_token": access}), 200

    def role_required(role):
        def wrapper(fn):
            @jwt_required()
            def decorated(*args, **kwargs):
                claims = get_jwt()
                if not claims or claims.get("role") != role:
                    return jsonify({"msg": "forbidden"}), 403
                return fn(*args, **kwargs)

            decorated.__name__ = fn.__name__
            return decorated

        return wrapper

    @app.route("/books", methods=["GET"])
    @jwt_required()
    def search_books():
        """Search books — requires authentication.

        The UI is expected to call this endpoint after login. Returns a list
        of books with id, title, author, buy_price, and rent_price.
        """
        q = request.args.get("keyword", "").strip()
        if not q:
            books = Book.query.limit(50).all()
        else:
            like = f"%{q}%"
            books = Book.query.filter((Book.title.ilike(like)) | (Book.author.ilike(like))).all()
        out = [
            {
                "id": b.id,
                "title": b.title,
                "author": b.author,
                "buy_price": b.buy_price,
                "rent_price": b.rent_price,
                "available_copies": b.available_copies,
            }
            for b in books
        ]
        return jsonify(out)

    @app.route("/orders", methods=["POST"])
    @jwt_required()
    def create_order():
        ident = get_jwt_identity()
        user_id = int(ident)
        user = User.query.get(user_id)
        if not user:
            return jsonify({"msg": "user not found"}), 404

        data = request.get_json() or {}
        items = data.get("items") or []
        if not items:
            return jsonify({"msg": "no items"}), 400

        order = Order(user_id=user.id, total=0.0)
        db.session.add(order)
        total = 0.0
        for it in items:
            book_id = it.get("book_id")
            typ = it.get("type")
            if typ not in ("buy", "rent"):
                db.session.rollback()
                return jsonify({"msg": "invalid item type"}), 400
            book = Book.query.get(book_id)
            if not book:
                db.session.rollback()
                return jsonify({"msg": f"book {book_id} not found"}), 404
            if book.available_copies < 1:
                db.session.rollback()
                return jsonify({"msg": f"not enough copies for book {book_id}"}), 400
            book.available_copies -= 1
            price = book.buy_price if typ == "buy" else book.rent_price
            oi = OrderItem(order=order, book=book, is_buy=(typ == "buy"), price=price)
            db.session.add(oi)
            total += price

        order.total = total
        db.session.commit()

        order_data = {
            "customer": user.username,
            "items": [{"book": oi.book.title, "type": ("buy" if oi.is_buy else "rent"), "price": oi.price} for oi in order.items],
            "total": order.total,
            "payment_status": order.payment_status,
        }

        try:
            body = f"Your Order\nTotal: {order.total}\nItems:\n"
            for oi in order.items:
                body += f" - {oi.book.title}: {oi.price} ({'buy' if oi.is_buy else 'rent'})\n"
            send_order_email(user.email, f"Your Order", body)
        except Exception:
            pass

        return jsonify(order_data), 201

    @app.route("/manager/orders", methods=["GET"])
    @role_required("manager")
    def list_orders():
        orders = Order.query.all()
        out = []
        for o in orders:
            out.append({
                "id": o.id,
                "customer": o.user.username,
                "items": [{"book": it.book.title, "type": ("buy" if it.is_buy else "rent")} for it in o.items],
                "total": o.total,
                "payment_status": o.payment_status,
            })
        return jsonify(out)

    @app.route("/manager/books", methods=["GET"])
    @role_required("manager")
    def list_books_manager():
        """Return a minimal list of books for manager UIs so they can select
        a book without having to type an ID manually."""
        books = Book.query.all()
        out = [
            {
                "id": b.id,
                "title": b.title,
                "author": b.author,
                "buy_price": b.buy_price,
                "rent_price": b.rent_price,
                "available_copies": b.available_copies,
            }
            for b in books
        ]
        return jsonify(out)

    @app.route("/manager/orders/<int:id>/payment", methods=["PUT"])
    @role_required("manager")
    def update_payment(id):
        o = Order.query.get(id)
        if not o:
            return jsonify({"msg": "order not found"}), 404
        data = request.get_json() or {}
        status = data.get("payment_status")
        if status not in ("pending", "paid"):
            return jsonify({"msg": "invalid status"}), 400
        o.payment_status = status
        db.session.commit()
        return jsonify({"msg": "updated"})

    @app.route("/manager/books", methods=["POST"])
    @role_required("manager")
    def create_book():
        data = request.get_json() or {}
        title = data.get("title")
        author = data.get("author")
        buy_price = data.get("buy_price")
        rent_price = data.get("rent_price")

        if not title or not author or buy_price is None or rent_price is None:
            return jsonify({"msg": "missing fields"}), 400
        b = Book(
            title=title,
            author=author,
            buy_price=float(buy_price),
            rent_price=float(rent_price),
            available_copies=1,
        )
        db.session.add(b)
        db.session.commit()
        return jsonify({"id": b.id}), 201

    @app.route("/manager/books/<int:book_id>", methods=["PUT"])
    @role_required("manager")
    def update_book(book_id):
        b = Book.query.get(book_id)
        if not b:
            return jsonify({"msg": "not found"}), 404
        data = request.get_json() or {}
        for fld in ("title", "author", "buy_price", "rent_price", "available_copies"):
            if fld in data:
                setattr(b, fld, data[fld])
        db.session.commit()
        return jsonify({"msg": "updated"})

    return app


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
