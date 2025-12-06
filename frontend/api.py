"""HTTP client helpers used by the GUI to call the backend.

These use the `requests` library. Network calls are synchronous here; the GUI
frames are responsible for running them on background threads and updating the
UI on the main thread.
"""
import os
from typing import Optional, Any, Dict, List

import requests

BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:5000")


def _auth_header(token: Optional[str]) -> Dict[str, str]:
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def api_login(username: str, password: str) -> Dict[str, Any]:
    """POST /login — returns dict {success: bool, token?: str, msg?: str}"""
    url = f"{BASE_URL}/login"
    try:
        r = requests.post(url, json={"username": username, "password": password}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            return {"success": True, "token": data.get("access_token")}
        else:
            try:
                msg = r.json().get("msg")
            except Exception:
                msg = r.text
            return {"success": False, "msg": msg or f"HTTP {r.status_code}"}
    except requests.RequestException as e:
        return {"success": False, "msg": str(e)}


def api_register(username: str, password: str, email: str) -> Dict[str, Any]:
    """POST /register — create a new customer account.

    Returns {success: bool, msg?: str}
    """
    url = f"{BASE_URL}/register"
    try:
        r = requests.post(url, json={"username": username, "password": password, "email": email}, timeout=10)
        if r.status_code in (200, 201):
            return {"success": True}
        else:
            try:
                msg = r.json().get("msg")
            except Exception:
                msg = r.text
            return {"success": False, "msg": msg or f"HTTP {r.status_code}"}
    except requests.RequestException as e:
        return {"success": False, "msg": str(e)}


def api_search_books(keyword: Optional[str] = None, token: Optional[str] = None) -> Dict[str, Any]:
    """GET /books?keyword=... — requires auth; returns {success: bool, books: [...]}"""
    url = f"{BASE_URL}/books"
    params = {}
    if keyword:
        params["keyword"] = keyword
    headers = _auth_header(token)
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        if r.status_code == 200:
            return {"success": True, "books": r.json()}
        else:
            try:
                msg = r.json().get("msg")
            except Exception:
                msg = r.text
            return {"success": False, "msg": msg or f"HTTP {r.status_code}"}
    except requests.RequestException as e:
        return {"success": False, "msg": str(e)}


def api_place_order(items: List[Dict[str, Any]], token: Optional[str]) -> Dict[str, Any]:
    """POST /orders — items is list of {book_id, quantity, type}

    Returns {success: bool, order?: {...}, msg?: str}
    """
    url = f"{BASE_URL}/orders"
    headers = _auth_header(token)
    try:
        r = requests.post(url, json={"items": items}, headers=headers, timeout=10)
        if r.status_code in (200, 201):
            return {"success": True, "order": r.json()}
        else:
            try:
                msg = r.json().get("msg")
            except Exception:
                msg = r.text
            return {"success": False, "msg": msg or f"HTTP {r.status_code}"}
    except requests.RequestException as e:
        return {"success": False, "msg": str(e)}


def api_list_orders(token: Optional[str]) -> Dict[str, Any]:
    url = f"{BASE_URL}/manager/orders"
    headers = _auth_header(token)
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            return {"success": True, "orders": r.json()}
        else:
            return {"success": False, "msg": r.text}
    except requests.RequestException as e:
        return {"success": False, "msg": str(e)}


def api_update_payment_status(order_id: str, new_status: str, token: Optional[str]) -> Dict[str, Any]:
    url = f"{BASE_URL}/manager/orders/{order_id}/payment"
    headers = _auth_header(token)
    try:
        r = requests.put(url, json={"payment_status": new_status}, headers=headers, timeout=10)
        if r.status_code == 200:
            return {"success": True}
        else:
            return {"success": False, "msg": r.text}
    except requests.RequestException as e:
        return {"success": False, "msg": str(e)}


def api_list_manager_books(token: Optional[str]) -> Dict[str, Any]:
    """GET /manager/books — returns {success: bool, books: [...]}"""
    url = f"{BASE_URL}/manager/books"
    headers = _auth_header(token)
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            return {"success": True, "books": r.json()}
        else:
            return {"success": False, "msg": r.text}
    except requests.RequestException as e:
        return {"success": False, "msg": str(e)}


def api_create_book(data: Dict[str, Any], token: Optional[str]) -> Dict[str, Any]:
    url = f"{BASE_URL}/manager/books"
    headers = _auth_header(token)
    try:
        r = requests.post(url, json=data, headers=headers, timeout=10)
        if r.status_code in (200, 201):
            return {"success": True, "book": r.json()}
        else:
            return {"success": False, "msg": r.text}
    except requests.RequestException as e:
        return {"success": False, "msg": str(e)}


def api_update_book(book_id: int, data: Dict[str, Any], token: Optional[str]) -> Dict[str, Any]:
    url = f"{BASE_URL}/manager/books/{book_id}"
    headers = _auth_header(token)
    try:
        r = requests.put(url, json=data, headers=headers, timeout=10)
        if r.status_code == 200:
            return {"success": True}
        else:
            return {"success": False, "msg": r.text}
    except requests.RequestException as e:
        return {"success": False, "msg": str(e)}