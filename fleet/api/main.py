"""
GéoClic Fleet Manager - API Backend
Tourne dans un conteneur Docker sur le serveur maître.
Exécute les commandes fleet via subprocess et retourne les résultats en JSON.
"""

import asyncio
import json
import os
import subprocess
import uuid
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from jose import JWTError, jwt
from pydantic import BaseModel

# ─── Configuration ───────────────────────────────────────────────────────────

JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "")
JWT_ALGORITHM = "HS256"
FLEET_SCRIPT = "/opt/geoclic/fleet/geoclic-fleet.sh"

app = FastAPI(title="GéoClic Fleet Manager", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Auth ────────────────────────────────────────────────────────────────────

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_admin(token: str = Depends(oauth2_scheme)) -> dict:
    """Vérifie le JWT et s'assure que c'est un super_admin."""
    if not JWT_SECRET_KEY:
        raise HTTPException(500, "JWT_SECRET_KEY non configurée")

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        if not payload.get("is_super_admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès réservé au super administrateur",
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
        )


# ─── Schemas ─────────────────────────────────────────────────────────────────

class ServerAdd(BaseModel):
    name: str
    domain: str
    ip: str
    ssh_user: str = "ubuntu"
    ssh_port: int = 22


class ProvisionRequest(BaseModel):
    name: str
    domain: str
    ip: str
    email: str
    ssh_user: str = "ubuntu"
    ssh_port: int = 22


class InitRequest(BaseModel):
    email: str
    password: str
    collectivite: str
    with_demo: bool = False


class UpdateRequest(BaseModel):
    services: Optional[str] = None
    migration: Optional[str] = None


# ─── Stockage tâches en mémoire ─────────────────────────────────────────────

_running_tasks: dict[str, dict] = {}


# ─── Helpers ─────────────────────────────────────────────────────────────────

def run_fleet_cmd(args: list[str], timeout: int = 30) -> dict:
    """Exécute une commande fleet et retourne le résultat."""
    cmd = ["bash", FLEET_SCRIPT] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": "Timeout", "returncode": -1}
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e), "returncode": -1}


async def run_fleet_cmd_async(args: list[str], task_id: str):
    """Exécute une commande fleet longue en arrière-plan."""
    cmd = ["bash", FLEET_SCRIPT] + args
    _running_tasks[task_id] = {
        "status": "running",
        "started_at": datetime.utcnow().isoformat(),
        "output": "",
    }

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )

        output_lines = []
        while True:
            line = await proc.stdout.readline()
            if not line:
                break
            decoded = line.decode("utf-8", errors="replace")
            output_lines.append(decoded)
            _running_tasks[task_id]["output"] = "".join(output_lines)

        await proc.wait()

        _running_tasks[task_id]["status"] = "completed" if proc.returncode == 0 else "failed"
        _running_tasks[task_id]["returncode"] = proc.returncode
        _running_tasks[task_id]["finished_at"] = datetime.utcnow().isoformat()
        _running_tasks[task_id]["output"] = "".join(output_lines)

    except Exception as e:
        _running_tasks[task_id]["status"] = "failed"
        _running_tasks[task_id]["error"] = str(e)
        _running_tasks[task_id]["finished_at"] = datetime.utcnow().isoformat()


# ─── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/api/fleet/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}


@app.get("/api/fleet/servers")
async def list_servers(admin: dict = Depends(get_current_admin)):
    """Liste tous les serveurs enregistrés."""
    result = run_fleet_cmd(["list", "--json"])
    if result["success"]:
        try:
            servers = json.loads(result["stdout"].strip())
            return {"servers": servers}
        except json.JSONDecodeError:
            return {"servers": [], "raw": result["stdout"]}
    raise HTTPException(500, result["stderr"])


@app.get("/api/fleet/servers/status")
async def servers_status(admin: dict = Depends(get_current_admin)):
    """État de santé de tous les serveurs (peut être lent)."""
    result = run_fleet_cmd(["status", "--json"], timeout=120)
    if result["success"]:
        try:
            statuses = json.loads(result["stdout"].strip())
            return {"servers": statuses}
        except json.JSONDecodeError:
            return {"servers": [], "raw": result["stdout"]}
    raise HTTPException(500, result["stderr"])


@app.get("/api/fleet/servers/{name}/status")
async def server_status(name: str, admin: dict = Depends(get_current_admin)):
    """État détaillé d'un serveur."""
    result = run_fleet_cmd(["status", "--client", name, "--json"], timeout=60)
    if result["success"]:
        try:
            return json.loads(result["stdout"].strip())
        except json.JSONDecodeError:
            return {"raw": result["stdout"]}
    raise HTTPException(500, result["stderr"])


@app.post("/api/fleet/servers")
async def add_server(data: ServerAdd, admin: dict = Depends(get_current_admin)):
    """Ajoute un serveur au registre."""
    result = run_fleet_cmd([
        "add",
        "--name", data.name,
        "--domain", data.domain,
        "--ip", data.ip,
        "--ssh-user", data.ssh_user,
        "--ssh-port", str(data.ssh_port),
    ])
    if result["success"]:
        return {"message": f"Serveur '{data.name}' ajouté", "name": data.name}
    raise HTTPException(400, result["stderr"] or result["stdout"])


@app.delete("/api/fleet/servers/{name}")
async def remove_server(name: str, admin: dict = Depends(get_current_admin)):
    """Retire un serveur du registre."""
    result = run_fleet_cmd(["remove", "--name", name])
    if result["success"]:
        return {"message": f"Serveur '{name}' retiré"}
    raise HTTPException(400, result["stderr"] or result["stdout"])


@app.post("/api/fleet/servers/{name}/provision")
async def provision_server(
    name: str,
    data: ProvisionRequest,
    admin: dict = Depends(get_current_admin),
):
    """Lance le provisioning d'un nouveau serveur (opération longue)."""
    task_id = f"provision_{name}_{uuid.uuid4().hex[:8]}"

    args = [
        "provision",
        "--name", data.name,
        "--domain", data.domain,
        "--ip", data.ip,
        "--email", data.email,
        "--ssh-user", data.ssh_user,
        "--ssh-port", str(data.ssh_port),
    ]

    asyncio.create_task(run_fleet_cmd_async(args, task_id))
    return {"task_id": task_id, "message": "Provisioning démarré"}


@app.post("/api/fleet/servers/{name}/init")
async def init_server(
    name: str,
    data: InitRequest,
    admin: dict = Depends(get_current_admin),
):
    """Initialise la base de données d'un serveur (migrations + super admin + branding)."""
    task_id = f"init_{name}_{uuid.uuid4().hex[:8]}"

    args = [
        "init",
        "--client", name,
        "--email", data.email,
        "--password", data.password,
        "--collectivite", data.collectivite,
    ]
    if data.with_demo:
        args.append("--with-demo")

    asyncio.create_task(run_fleet_cmd_async(args, task_id))
    return {"task_id": task_id, "message": "Initialisation de la base de données démarrée"}


@app.post("/api/fleet/servers/{name}/update")
async def update_server(
    name: str,
    data: UpdateRequest = UpdateRequest(),
    admin: dict = Depends(get_current_admin),
):
    """Lance la mise à jour d'un serveur (opération longue)."""
    task_id = f"update_{name}_{uuid.uuid4().hex[:8]}"

    args = ["update", "--client", name]
    if data.services:
        args += ["--services", data.services]
    if data.migration:
        args += ["--migration", data.migration]

    asyncio.create_task(run_fleet_cmd_async(args, task_id))
    return {"task_id": task_id, "message": "Mise à jour démarrée"}


@app.post("/api/fleet/servers/update-all")
async def update_all_servers(
    data: UpdateRequest = UpdateRequest(),
    admin: dict = Depends(get_current_admin),
):
    """Lance la mise à jour de TOUS les serveurs."""
    task_id = f"update_all_{uuid.uuid4().hex[:8]}"

    args = ["update", "--all"]
    if data.services:
        args += ["--services", data.services]
    if data.migration:
        args += ["--migration", data.migration]

    asyncio.create_task(run_fleet_cmd_async(args, task_id))
    return {"task_id": task_id, "message": "Mise à jour globale démarrée"}


@app.post("/api/fleet/servers/{name}/backup")
async def backup_server(name: str, admin: dict = Depends(get_current_admin)):
    """Lance une sauvegarde sur un serveur."""
    task_id = f"backup_{name}_{uuid.uuid4().hex[:8]}"
    asyncio.create_task(run_fleet_cmd_async(["backup", "--client", name], task_id))
    return {"task_id": task_id, "message": "Sauvegarde démarrée"}


@app.get("/api/fleet/servers/{name}/logs")
async def server_logs(
    name: str,
    service: str = "api",
    lines: int = 100,
    admin: dict = Depends(get_current_admin),
):
    """Récupère les logs Docker d'un serveur."""
    result = run_fleet_cmd(
        ["logs", name, "--service", service, "--lines", str(lines)],
        timeout=30,
    )
    return {"logs": result["stdout"], "success": result["success"]}


@app.post("/api/fleet/test-ssh")
async def test_ssh(
    ip: str,
    user: str = "ubuntu",
    port: int = 22,
    admin: dict = Depends(get_current_admin),
):
    """Teste la connexion SSH vers un serveur."""
    result = run_fleet_cmd(["test-ssh", ip, user, str(port)], timeout=15)
    try:
        return json.loads(result["stdout"].strip())
    except (json.JSONDecodeError, ValueError):
        return {"status": "failed", "error": result["stderr"]}


@app.get("/api/fleet/ssh-key")
async def get_ssh_key(admin: dict = Depends(get_current_admin)):
    """Retourne la clé publique SSH fleet."""
    result = run_fleet_cmd(["ssh-key", "show"])
    if result["success"]:
        return {"public_key": result["stdout"].strip()}
    raise HTTPException(404, "Clé SSH non trouvée. Lancez setup-master.sh.")


@app.post("/api/fleet/ssh-key/generate")
async def generate_ssh_key(admin: dict = Depends(get_current_admin)):
    """Génère une nouvelle clé SSH fleet."""
    result = run_fleet_cmd(["ssh-key", "generate"])
    if result["success"]:
        # Relire la clé publique
        key_result = run_fleet_cmd(["ssh-key", "show"])
        return {"public_key": key_result["stdout"].strip(), "message": "Clé générée"}
    raise HTTPException(500, result["stderr"])


# ─── Tâches longues ─────────────────────────────────────────────────────────

@app.get("/api/fleet/tasks/{task_id}")
async def get_task(task_id: str, admin: dict = Depends(get_current_admin)):
    """Récupère le statut d'une tâche en cours."""
    # D'abord vérifier en mémoire
    if task_id in _running_tasks:
        return _running_tasks[task_id]

    # Sinon vérifier dans le fichier de tâche du script bash
    result = run_fleet_cmd(["task-status", task_id])
    if result["success"]:
        try:
            return json.loads(result["stdout"].strip())
        except json.JSONDecodeError:
            pass

    raise HTTPException(404, "Tâche non trouvée")


@app.get("/api/fleet/tasks/{task_id}/log")
async def get_task_log(
    task_id: str,
    lines: int = 100,
    admin: dict = Depends(get_current_admin),
):
    """Récupère les logs d'une tâche."""
    # D'abord vérifier en mémoire
    if task_id in _running_tasks:
        output = _running_tasks[task_id].get("output", "")
        output_lines = output.split("\n")
        return {"log": "\n".join(output_lines[-lines:])}

    result = run_fleet_cmd(["task-log", task_id, str(lines)])
    return {"log": result["stdout"]}


# ─── Fichiers statiques (frontend) ──────────────────────────────────────────

# Le frontend build sera dans /app/web/dist
STATIC_DIR = "/app/web/dist"
if os.path.isdir(STATIC_DIR):
    app.mount("/assets", StaticFiles(directory=f"{STATIC_DIR}/assets"), name="assets")

    @app.get("/fleet/{path:path}")
    async def serve_spa(path: str = ""):
        """Sert l'application Vue.js (SPA)."""
        file_path = os.path.join(STATIC_DIR, path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))

    @app.get("/fleet")
    async def serve_fleet_root():
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
