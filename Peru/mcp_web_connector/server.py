#!/usr/bin/env python3
"""MCP server for read-only access to the Media Commerce Peru web hosting."""

from __future__ import annotations

import base64
import contextlib
import datetime as dt
import decimal
import inspect
import json
import os
import posixpath
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import paramiko
import pymysql
from sshtunnel import SSHTunnelForwarder


APP_DIR = Path(__file__).resolve().parent
READ_ONLY_FIRST_WORDS = {"select", "show", "describe", "desc", "explain"}
DANGEROUS_SQL = re.compile(
    r"\b("
    r"insert|update|delete|drop|alter|create|truncate|replace|grant|revoke|"
    r"set|load|outfile|infile|call|do|handler|lock|unlock|rename|flush"
    r")\b",
    re.IGNORECASE,
)
IDENTIFIER = re.compile(r"^[A-Za-z0-9_$]+$")


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_dotenv(APP_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    ssh_host: str
    ssh_port: int
    ssh_user: str
    ssh_password: Optional[str]
    ssh_key_file: Optional[str]
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: Optional[str]
    allowed_roots: Tuple[str, ...]
    max_read_bytes: int

    @classmethod
    def from_env(cls) -> "Settings":
        ssh_password = os.getenv("MCP_WEB_SSH_PASSWORD") or None
        db_password = os.getenv("MCP_WEB_DB_PASSWORD") or ssh_password
        allowed_roots = tuple(
            posixpath.normpath(item.strip())
            for item in os.getenv(
                "MCP_WEB_ALLOWED_ROOTS",
                "/var/www,/home,/usr/local/apache/htdocs,/usr/share/nginx/html,/opt",
            ).split(",")
            if item.strip()
        )
        return cls(
            ssh_host=os.getenv("MCP_WEB_SSH_HOST", "179.43.82.54"),
            ssh_port=int(os.getenv("MCP_WEB_SSH_PORT", "22")),
            ssh_user=os.getenv("MCP_WEB_SSH_USER", "root"),
            ssh_password=ssh_password,
            ssh_key_file=os.getenv("MCP_WEB_SSH_KEY_FILE") or None,
            db_host=os.getenv("MCP_WEB_DB_HOST", "127.0.0.1"),
            db_port=int(os.getenv("MCP_WEB_DB_PORT", "3306")),
            db_name=os.getenv("MCP_WEB_DB_NAME", "bdmcperu"),
            db_user=os.getenv("MCP_WEB_DB_USER", "root"),
            db_password=db_password,
            allowed_roots=allowed_roots,
            max_read_bytes=int(os.getenv("MCP_WEB_MAX_READ_BYTES", "50000")),
        )


def settings() -> Settings:
    return Settings.from_env()


def public_settings() -> Dict[str, Any]:
    cfg = settings()
    return {
        "ssh_host": cfg.ssh_host,
        "ssh_port": cfg.ssh_port,
        "ssh_user": cfg.ssh_user,
        "db_host": cfg.db_host,
        "db_port": cfg.db_port,
        "db_name": cfg.db_name,
        "db_user": cfg.db_user,
        "allowed_roots": list(cfg.allowed_roots),
        "max_read_bytes": cfg.max_read_bytes,
        "has_ssh_password": bool(cfg.ssh_password),
        "has_ssh_key_file": bool(cfg.ssh_key_file),
        "has_db_password": bool(cfg.db_password),
    }


def connect_ssh() -> paramiko.SSHClient:
    cfg = settings()
    if not cfg.ssh_password and not cfg.ssh_key_file:
        raise RuntimeError("Configura MCP_WEB_SSH_PASSWORD o MCP_WEB_SSH_KEY_FILE.")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=cfg.ssh_host,
        port=cfg.ssh_port,
        username=cfg.ssh_user,
        password=cfg.ssh_password,
        key_filename=cfg.ssh_key_file,
        look_for_keys=False,
        allow_agent=False,
        timeout=15,
        banner_timeout=20,
        auth_timeout=20,
    )
    return client


@contextlib.contextmanager
def ssh_client() -> Iterable[paramiko.SSHClient]:
    client = connect_ssh()
    try:
        yield client
    finally:
        client.close()


@contextlib.contextmanager
def db_connection(database: Optional[str] = None) -> Iterable[pymysql.connections.Connection]:
    cfg = settings()
    if not cfg.db_password:
        raise RuntimeError("Configura MCP_WEB_DB_PASSWORD o MCP_WEB_SSH_PASSWORD.")

    tunnel = SSHTunnelForwarder(
        (cfg.ssh_host, cfg.ssh_port),
        ssh_username=cfg.ssh_user,
        ssh_password=cfg.ssh_password,
        ssh_pkey=cfg.ssh_key_file,
        remote_bind_address=(cfg.db_host, cfg.db_port),
    )
    tunnel.start()
    try:
        connection = pymysql.connect(
            host="127.0.0.1",
            port=tunnel.local_bind_port,
            user=cfg.db_user,
            password=cfg.db_password,
            database=database or cfg.db_name,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=12,
            read_timeout=30,
            write_timeout=30,
        )
        try:
            yield connection
        finally:
            connection.close()
    finally:
        tunnel.stop()


def normalize_remote_path(path: str) -> str:
    if not path:
        raise ValueError("La ruta remota no puede estar vacia.")
    normalized = posixpath.normpath(path if path.startswith("/") else f"/{path}")
    roots = settings().allowed_roots
    if not any(normalized == root or normalized.startswith(f"{root}/") for root in roots):
        raise ValueError(
            "Ruta fuera de MCP_WEB_ALLOWED_ROOTS. "
            f"Ruta: {normalized}. Permitidas: {', '.join(roots)}"
        )
    return normalized


def serialize_value(value: Any) -> Any:
    if isinstance(value, (dt.date, dt.datetime, dt.time)):
        return value.isoformat()
    if isinstance(value, decimal.Decimal):
        return float(value)
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError:
            return {"base64": base64.b64encode(value).decode("ascii")}
    return value


def serialize_rows(rows: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [{key: serialize_value(value) for key, value in row.items()} for row in rows]


def strip_sql_comments(sql: str) -> str:
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    lines = []
    for line in sql.splitlines():
        cleaned = line.split("--", 1)[0].split("#", 1)[0]
        if cleaned.strip():
            lines.append(cleaned)
    return "\n".join(lines).strip()


def validate_readonly_sql(sql: str) -> str:
    cleaned = strip_sql_comments(sql)
    if not cleaned:
        raise ValueError("La consulta SQL esta vacia.")
    without_trailing = cleaned[:-1].strip() if cleaned.endswith(";") else cleaned
    if ";" in without_trailing:
        raise ValueError("No se permiten multiples sentencias SQL.")
    first_word = without_trailing.split(None, 1)[0].lower()
    if first_word not in READ_ONLY_FIRST_WORDS:
        raise ValueError(
            "Solo se permiten consultas de lectura: SELECT, SHOW, DESCRIBE, DESC o EXPLAIN."
        )
    if DANGEROUS_SQL.search(without_trailing):
        raise ValueError("La consulta contiene una palabra SQL bloqueada para este MCP.")
    return without_trailing


def validate_identifier(name: str, label: str) -> str:
    if not IDENTIFIER.match(name or ""):
        raise ValueError(f"{label} invalido: {name!r}")
    return name


def fetch_rows(
    sql: str,
    params: Optional[Sequence[Any]] = None,
    database: Optional[str] = None,
    max_rows: int = 100,
) -> Dict[str, Any]:
    max_rows = max(1, min(int(max_rows or 100), 500))
    with db_connection(database) as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, params or ())
            rows = cursor.fetchmany(max_rows + 1)
            truncated = len(rows) > max_rows
            rows = rows[:max_rows]
            columns = [item[0] for item in cursor.description or []]
    return {
        "columns": columns,
        "rows": serialize_rows(rows),
        "row_count": len(rows),
        "truncated": truncated,
        "max_rows": max_rows,
    }


TOOLS: Dict[str, Dict[str, Any]] = {}


def annotation_to_schema(annotation: Any) -> Dict[str, Any]:
    text = str(annotation)
    if "int" in text:
        return {"type": "integer"}
    if "float" in text or "decimal" in text:
        return {"type": "number"}
    if "bool" in text:
        return {"type": "boolean"}
    return {"type": "string"}


def schema_for_function(func: Any) -> Dict[str, Any]:
    signature = inspect.signature(func)
    properties: Dict[str, Any] = {}
    required: List[str] = []
    for name, parameter in signature.parameters.items():
        properties[name] = annotation_to_schema(parameter.annotation)
        if parameter.default is inspect.Parameter.empty:
            required.append(name)
    schema: Dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return schema


def tool() -> Any:
    def decorator(func: Any) -> Any:
        TOOLS[func.__name__] = {
            "name": func.__name__,
            "description": inspect.getdoc(func) or "",
            "inputSchema": schema_for_function(func),
            "handler": func,
        }
        return func

    return decorator


@tool()
def config_summary() -> Dict[str, Any]:
    """Return non-secret connection settings currently loaded by the MCP server."""
    return public_settings()


@tool()
def ssh_health() -> Dict[str, Any]:
    """Check SSH access and return basic remote server information."""
    command = (
        "printf 'host='; hostname; "
        "printf 'user='; whoami; "
        "printf 'kernel='; uname -sr; "
        "printf 'pwd='; pwd; "
        "printf 'mysql='; mysql --version 2>/dev/null | head -n 1 || true; "
        "printf 'php='; php -v 2>/dev/null | head -n 1 || true"
    )
    with ssh_client() as client:
        stdin, stdout, stderr = client.exec_command(command, timeout=20)
        exit_status = stdout.channel.recv_exit_status()
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")
    return {"exit_status": exit_status, "stdout": out, "stderr": err}


@tool()
def remote_list(path: str = "/var/www", max_entries: int = 100) -> Dict[str, Any]:
    """List files from an allowed remote directory using SFTP."""
    remote_path = normalize_remote_path(path)
    max_entries = max(1, min(int(max_entries or 100), 500))
    with ssh_client() as client:
        sftp = client.open_sftp()
        try:
            entries = []
            for item in sftp.listdir_attr(remote_path)[:max_entries]:
                entries.append(
                    {
                        "name": item.filename,
                        "size": item.st_size,
                        "mode": oct(item.st_mode),
                        "mtime": dt.datetime.fromtimestamp(item.st_mtime).isoformat()
                        if item.st_mtime
                        else None,
                    }
                )
        finally:
            sftp.close()
    return {"path": remote_path, "entries": entries, "entry_count": len(entries)}


@tool()
def remote_read_text(path: str, max_bytes: Optional[int] = None) -> Dict[str, Any]:
    """Read a remote text file from an allowed path."""
    remote_path = normalize_remote_path(path)
    byte_limit = max(1, min(int(max_bytes or settings().max_read_bytes), settings().max_read_bytes))
    with ssh_client() as client:
        sftp = client.open_sftp()
        try:
            stat = sftp.stat(remote_path)
            with sftp.open(remote_path, "rb") as handle:
                data = handle.read(byte_limit + 1)
        finally:
            sftp.close()
    truncated = len(data) > byte_limit
    data = data[:byte_limit]
    return {
        "path": remote_path,
        "size": stat.st_size,
        "truncated": truncated,
        "content": data.decode("utf-8", errors="replace"),
    }


@tool()
def mysql_query_readonly(sql: str, database: Optional[str] = None, max_rows: int = 100) -> Dict[str, Any]:
    """Run a safe read-only MariaDB query over SSH tunnel."""
    safe_sql = validate_readonly_sql(sql)
    return fetch_rows(safe_sql, database=database or settings().db_name, max_rows=max_rows)


@tool()
def mysql_list_tables(database: Optional[str] = None, max_rows: int = 300) -> Dict[str, Any]:
    """List tables in the configured database."""
    db_name = database or settings().db_name
    return fetch_rows("SHOW TABLES", database=db_name, max_rows=max_rows)


@tool()
def mysql_describe_table(table: str, database: Optional[str] = None) -> Dict[str, Any]:
    """Describe columns for one table in MariaDB."""
    table_name = validate_identifier(table, "table")
    db_name = database or settings().db_name
    return fetch_rows(f"DESCRIBE `{table_name}`", database=db_name, max_rows=300)


@tool()
def wordpress_users(search: str = "", max_rows: int = 50, database: Optional[str] = None) -> Dict[str, Any]:
    """Search WordPress users from wp_users."""
    db_name = database or settings().db_name
    like = f"%{search.strip()}%"
    sql = (
        "SELECT ID, user_login, user_nicename, user_email, user_registered, display_name "
        "FROM wp_users "
        "WHERE %s = '' OR user_login LIKE %s OR user_email LIKE %s OR display_name LIKE %s "
        "ORDER BY ID DESC"
    )
    return fetch_rows(sql, (search.strip(), like, like, like), database=db_name, max_rows=max_rows)


@tool()
def wordpress_options(search: str = "", max_rows: int = 50, database: Optional[str] = None) -> Dict[str, Any]:
    """Search WordPress wp_options without returning very large option values."""
    db_name = database or settings().db_name
    like = f"%{search.strip()}%"
    sql = (
        "SELECT option_id, option_name, LEFT(option_value, 300) AS option_value_preview, autoload "
        "FROM wp_options "
        "WHERE %s = '' OR option_name LIKE %s "
        "ORDER BY option_id ASC"
    )
    return fetch_rows(sql, (search.strip(), like), database=db_name, max_rows=max_rows)


@tool()
def find_client_columns(database: Optional[str] = None, max_rows: int = 200) -> Dict[str, Any]:
    """Find columns that look related to clients, documents, contacts, phones or emails."""
    db_name = database or settings().db_name
    terms = ["client", "cliente", "customer", "razon", "ruc", "dni", "contact", "telefono", "email", "correo"]
    predicates = " OR ".join(["LOWER(COLUMN_NAME) LIKE %s" for _ in terms])
    params = [db_name] + [f"%{term}%" for term in terms]
    sql = (
        "SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY "
        "FROM information_schema.COLUMNS "
        f"WHERE TABLE_SCHEMA = %s AND ({predicates}) "
        "ORDER BY TABLE_NAME, ORDINAL_POSITION"
    )
    return fetch_rows(sql, params, database=db_name, max_rows=max_rows)


@tool()
def export_result_json(sql: str, database: Optional[str] = None, max_rows: int = 100) -> str:
    """Run a read-only query and return a JSON string."""
    result = mysql_query_readonly(sql=sql, database=database, max_rows=max_rows)
    return json.dumps(result, ensure_ascii=False, indent=2)


def tool_result(value: Any) -> Dict[str, Any]:
    if isinstance(value, str):
        text = value
    else:
        text = json.dumps(value, ensure_ascii=False, indent=2)
    return {"content": [{"type": "text", "text": text}]}


def tool_error(exc: BaseException) -> Dict[str, Any]:
    return {
        "isError": True,
        "content": [{"type": "text", "text": f"{type(exc).__name__}: {exc}"}],
    }


def response(message_id: Any, result: Optional[Dict[str, Any]] = None, error: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"jsonrpc": "2.0", "id": message_id}
    if error is not None:
        payload["error"] = error
    else:
        payload["result"] = result or {}
    return payload


def handle_request(message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    method = message.get("method")
    message_id = message.get("id")
    params = message.get("params") or {}

    if method is None:
        return response(message_id, error={"code": -32600, "message": "Invalid Request"})

    if message_id is None and method.startswith("notifications/"):
        return None

    if method == "initialize":
        requested_version = params.get("protocolVersion") or "2024-11-05"
        return response(
            message_id,
            {
                "protocolVersion": requested_version,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "mcperu-web", "version": "0.1.0"},
            },
        )

    if method == "ping":
        return response(message_id, {})

    if method == "tools/list":
        tools = [
            {
                "name": item["name"],
                "description": item["description"],
                "inputSchema": item["inputSchema"],
            }
            for item in TOOLS.values()
        ]
        return response(message_id, {"tools": tools})

    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments") or {}
        item = TOOLS.get(name)
        if item is None:
            return response(message_id, error={"code": -32602, "message": f"Unknown tool: {name}"})
        try:
            value = item["handler"](**arguments)
            return response(message_id, tool_result(value))
        except Exception as exc:  # noqa: BLE001 - return MCP tool errors as content.
            return response(message_id, tool_error(exc))

    return response(message_id, error={"code": -32601, "message": f"Method not found: {method}"})


def run_stdio() -> None:
    for line in sys.stdin:
        raw = line.strip()
        if not raw:
            continue
        try:
            message = json.loads(raw)
            payload = handle_request(message)
        except Exception as exc:  # noqa: BLE001 - protect the stdio loop.
            payload = response(None, error={"code": -32603, "message": f"Internal error: {exc}"})
        if payload is not None:
            sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    run_stdio()
