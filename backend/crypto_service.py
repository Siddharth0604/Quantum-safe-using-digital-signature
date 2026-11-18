"""Flask-side adapter for the maintained Noble ML-DSA-65 implementation."""
import base64
import json
import shutil
import subprocess
from pathlib import Path

WORKER = Path(__file__).with_name("mldsa_worker.mjs")
NODE = shutil.which("node") or "node"


def _call_worker(payload):
    try:
        result = subprocess.run(
            [NODE, str(WORKER)], input=json.dumps(payload), text=True,
            capture_output=True, check=False, timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError("The ML-DSA worker could not be started.") from exc
    if result.returncode != 0:
        # Never include worker output: it could contain user-controlled key material.
        raise RuntimeError("The ML-DSA operation failed.")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("The ML-DSA worker returned an invalid response.") from exc


def _pem(label, raw):
    encoded = base64.b64encode(raw).decode("ascii")
    lines = [encoded[i:i + 64] for i in range(0, len(encoded), 64)]
    return f"-----BEGIN QUANTUMSAFE ML-DSA-65 {label} KEY-----\n" + "\n".join(lines) + f"\n-----END QUANTUMSAFE ML-DSA-65 {label} KEY-----\n"


def _unpem(data, label):
    try:
        text = data.decode("ascii") if isinstance(data, bytes) else data
        begin = f"-----BEGIN QUANTUMSAFE ML-DSA-65 {label} KEY-----"
        end = f"-----END QUANTUMSAFE ML-DSA-65 {label} KEY-----"
        if not text.startswith(begin) or not text.rstrip().endswith(end):
            raise ValueError
        encoded = text[len(begin):text.rfind(end)].strip()
        return base64.b64decode("".join(encoded.split()), validate=True)
    except (UnicodeDecodeError, ValueError, TypeError) as exc:
        raise ValueError(f"Invalid QuantumSafe ML-DSA-65 {label.lower()} key file.") from exc


def generate_keypair():
    keys = _call_worker({"operation": "generate"})
    return _pem("PUBLIC", base64.b64decode(keys["publicKey"])), _pem("PRIVATE", base64.b64decode(keys["secretKey"]))


def sign_file(file_obj, private_key_data):
    secret_key = _unpem(private_key_data, "PRIVATE")
    message = file_obj.read()
    result = _call_worker({
        "operation": "sign",
        "secretKey": base64.b64encode(secret_key).decode("ascii"),
        "message": base64.b64encode(message).decode("ascii"),
    })
    return base64.b64decode(result["signature"])


def verify_file(file_obj, signature, public_key_data):
    public_key = _unpem(public_key_data, "PUBLIC")
    message = file_obj.read()
    result = _call_worker({
        "operation": "verify",
        "publicKey": base64.b64encode(public_key).decode("ascii"),
        "signature": base64.b64encode(signature).decode("ascii"),
        "message": base64.b64encode(message).decode("ascii"),
    })
    return result["valid"] is True
