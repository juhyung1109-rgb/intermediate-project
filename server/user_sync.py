import json
import sqlite3
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "runtime" / "analysis.sqlite3"


class UserSyncRequest(BaseModel):
    uid: str
    email: str
    name: str = ""
    displayName: str = ""
    role: str = "engineer"
    status: str = "pending"
    isApproved: bool = False


class ApproveUserRequest(BaseModel):
    uid: str
    status: str = Field(description="'approved' 또는 'rejected'")
    adminEmail: str = "admin@semiguard.fab"


def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=15)
    conn.row_factory = sqlite3.Row
    return conn


def init_user_db():
    try:
        with get_db() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_accounts (
                    uid TEXT PRIMARY KEY,
                    email TEXT NOT NULL,
                    name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    status TEXT NOT NULL,
                    is_approved INTEGER NOT NULL DEFAULT 0,
                    requested_at TEXT,
                    approved_at TEXT,
                    approved_by TEXT
                )
            """)
            # Pre-seed default system admin if empty
            conn.execute("""
                INSERT OR IGNORE INTO user_accounts (uid, email, name, role, status, is_approved, requested_at, approved_at, approved_by)
                VALUES ('admin_default', 'admin@semiguard.fab', '시스템 공정 관리자', 'admin', 'approved', 1, datetime('now'), datetime('now'), 'system')
            """)
    except Exception as e:
        print("[UserDB Init notice]:", e)

init_user_db()


import os
_cached_token = None
_token_expire_time = 0

def get_gcp_access_token():
    global _cached_token, _token_expire_time
    import time
    now = time.time()
    if _cached_token and now < _token_expire_time:
        return _cached_token

    token = None
    # Only query GCP metadata server on Cloud Run (identified by K_SERVICE environment variable)
    if os.getenv("K_SERVICE"):
        try:
            meta_req = urllib.request.Request(
                "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token",
                headers={"Metadata-Flavor": "Google"}
            )
            with urllib.request.urlopen(meta_req, timeout=1.0) as resp:
                token_data = json.loads(resp.read().decode())
                token = token_data.get("access_token")
        except Exception:
            pass

    if token:
        _cached_token = token
        _token_expire_time = now + 1800  # 30 min cache
    return token


def sync_user_to_firestore(req: UserSyncRequest):
    """
    Syncs user account profile to local SQLite DB and Firestore database 'project' under collection 'users'.
    Default status for regular signup is 'pending' (requires admin approval).
    """
    display_name = req.displayName or req.name or req.email.split('@')[0]
    now_iso = datetime.now(timezone.utc).isoformat()
    
    # Pre-approve system admins
    status = req.status
    is_approved = req.isApproved
    if req.email.lower() == "admin@semiguard.fab" or req.email.lower().startswith("admin@"):
        status = "approved"
        is_approved = True

    # 1. Store in local SQLite
    try:
        with get_db() as conn:
            existing = conn.execute("SELECT status, is_approved FROM user_accounts WHERE uid=?", (req.uid,)).fetchone()
            if existing:
                # If already approved by admin, retain approved status
                if existing["status"] == "approved":
                    status = "approved"
                    is_approved = True
                conn.execute("""
                    UPDATE user_accounts 
                    SET email=?, name=?, role=?, status=?, is_approved=?
                    WHERE uid=?
                """, (req.email, display_name, req.role, status, 1 if is_approved else 0, req.uid))
            else:
                conn.execute("""
                    INSERT INTO user_accounts (uid, email, name, role, status, is_approved, requested_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (req.uid, req.email, display_name, req.role, status, 1 if is_approved else 0, now_iso))
    except Exception as db_err:
        print("[UserDB SQLite save notice]:", db_err)

    # 2. Sync to Cloud Firestore if token is available
    try:
        token = get_gcp_access_token()
        if token:
            url = f"https://firestore.googleapis.com/v1/projects/iceu-songpa03/databases/project/documents/users/{req.uid}"
            payload = {
                "fields": {
                    "email": {"stringValue": req.email},
                    "name": {"stringValue": display_name},
                    "displayName": {"stringValue": display_name},
                    "role": {"stringValue": req.role},
                    "status": {"stringValue": status},
                    "isApproved": {"booleanValue": is_approved},
                    "updatedAt": {"stringValue": now_iso},
                    "source": {"stringValue": "SEMI-GUARD Sync"}
                }
            }
            post_req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                method="PATCH"
            )
            with urllib.request.urlopen(post_req, timeout=5) as post_resp:
                res_body = json.loads(post_resp.read().decode())
                return {"success": True, "database": "project", "doc": res_body.get("name"), "status": status, "isApproved": is_approved}
    except Exception as fs_err:
        print("[UserDB Firestore sync notice]:", fs_err)

    return {"success": True, "note": "Local session recorded", "status": status, "isApproved": is_approved, "user": req.dict()}


def get_user_status(uid: str):
    """Retrieve user approval status by UID."""
    try:
        with get_db() as conn:
            row = conn.execute("SELECT uid, email, name, role, status, is_approved, requested_at, approved_at FROM user_accounts WHERE uid=?", (uid,)).fetchone()
            if row:
                return {
                    "found": True,
                    "uid": row["uid"],
                    "email": row["email"],
                    "name": row["name"],
                    "role": row["role"],
                    "status": row["status"],
                    "isApproved": bool(row["is_approved"]),
                    "requestedAt": row["requested_at"],
                    "approvedAt": row["approved_at"]
                }
    except Exception as e:
        print("[UserStatus query notice]:", e)
    return {"found": False, "status": "pending", "isApproved": False}


def list_all_users():
    """List all registered users and their approval statuses for Admin view."""
    users = []
    try:
        with get_db() as conn:
            rows = conn.execute("SELECT uid, email, name, role, status, is_approved, requested_at, approved_at, approved_by FROM user_accounts ORDER BY is_approved ASC, requested_at DESC").fetchall()
            for r in rows:
                users.append({
                    "uid": r["uid"],
                    "email": r["email"],
                    "name": r["name"],
                    "role": r["role"],
                    "status": r["status"],
                    "isApproved": bool(r["is_approved"]),
                    "requestedAt": r["requested_at"] or "",
                    "approvedAt": r["approved_at"] or "",
                    "approvedBy": r["approved_by"] or ""
                })
    except Exception as e:
        print("[UserList query notice]:", e)
    
    pending_count = sum(1 for u in users if u["status"] == "pending")
    return {"users": users, "total": len(users), "pendingCount": pending_count}


def approve_user_status(req: ApproveUserRequest):
    """Admin endpoint to approve or reject a user."""
    new_status = "approved" if req.status.lower() in ["approved", "approve", "true"] else "rejected"
    is_approved = 1 if new_status == "approved" else 0
    now_iso = datetime.now(timezone.utc).isoformat()
    
    # 1. Update SQLite
    try:
        with get_db() as conn:
            conn.execute("""
                UPDATE user_accounts
                SET status=?, is_approved=?, approved_at=?, approved_by=?
                WHERE uid=?
            """, (new_status, is_approved, now_iso, req.adminEmail, req.uid))
    except Exception as e:
        print("[Approve SQLite notice]:", e)

    # 2. Update Firestore if connected
    try:
        token = get_gcp_access_token()
        if token:
            url = f"https://firestore.googleapis.com/v1/projects/iceu-songpa03/databases/project/documents/users/{req.uid}?updateMask.fieldPaths=status&updateMask.fieldPaths=isApproved&updateMask.fieldPaths=approvedAt&updateMask.fieldPaths=approvedBy"
            payload = {
                "fields": {
                    "status": {"stringValue": new_status},
                    "isApproved": {"booleanValue": bool(is_approved)},
                    "approvedAt": {"stringValue": now_iso},
                    "approvedBy": {"stringValue": req.adminEmail}
                }
            }
            post_req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                method="PATCH"
            )
            with urllib.request.urlopen(post_req, timeout=5) as resp:
                pass
    except Exception as fs_err:
        print("[Approve Firestore sync notice]:", fs_err)

    return {"success": True, "uid": req.uid, "status": new_status, "isApproved": bool(is_approved)}

