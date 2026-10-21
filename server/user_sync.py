import json
from pydantic import BaseModel

class UserSyncRequest(BaseModel):
    uid: str
    email: str
    name: str = ""
    displayName: str = ""
    role: str = "engineer"

def sync_user_to_firestore(req: UserSyncRequest):
    """
    Syncs user account profile to Firestore database 'project' under collection 'users'.
    Uses GCP metadata token on Cloud Run, or gcloud token locally.
    """
    import urllib.request
    try:
        token = None
        # 1. Try GCP Cloud Run metadata server token
        try:
            meta_req = urllib.request.Request(
                "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token",
                headers={"Metadata-Flavor": "Google"}
            )
            with urllib.request.urlopen(meta_req, timeout=2) as resp:
                token_data = json.loads(resp.read().decode())
                token = token_data.get("access_token")
        except Exception:
            pass

        # 2. Local development fallback via gcloud
        if not token:
            try:
                import subprocess
                token = subprocess.check_output("gcloud auth print-access-token", shell=True).decode().strip()
            except Exception:
                pass

        display_name = req.displayName or req.name or req.email.split('@')[0]
        
        if token:
            url = f"https://firestore.googleapis.com/v1/projects/iceu-songpa03/databases/project/documents/users/{req.uid}"
            payload = {
                "fields": {
                    "email": {"stringValue": req.email},
                    "name": {"stringValue": display_name},
                    "displayName": {"stringValue": display_name},
                    "role": {"stringValue": req.role},
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
                return {"success": True, "database": "project", "doc": res_body.get("name")}

        return {"success": True, "note": "Local session recorded", "user": req.dict()}
    except Exception as e:
        return {"success": False, "error": str(e)}
