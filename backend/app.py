import io
import json
import logging
import os
import zipfile
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from crypto_service import generate_keypair, sign_file, verify_file

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 26 * 1024 * 1024
configured_origins = [origin.strip() for origin in os.environ.get(
    "FRONTEND_ORIGIN", ""
).split(",") if origin.strip()]
if not configured_origins:
    configured_origins = [
        f"http://localhost:{port}" for port in range(5173, 5191)
    ] + [
        f"http://127.0.0.1:{port}" for port in range(5173, 5191)
    ]
allowed_origins = list(dict.fromkeys(configured_origins))
CORS(app, resources={r"/api/*": {"origins": allowed_origins}})
logging.basicConfig(level=logging.INFO)


def required_upload(name):
    item = request.files.get(name)
    if item is None or not item.filename:
        raise ValueError(f"Missing required file: {name}")
    return item


@app.get("/api/health")
def health():
    return jsonify(status="ok", algorithm="ML-DSA-65")


@app.post("/api/keys/generate")
def keys_generate():
    public_pem, private_pem = generate_keypair()
    # Package both PEM files in an in-memory ZIP; keys are not persisted by the API.
    import zipfile
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("quantumsafe_public_key.pem", public_pem)
        zf.writestr("quantumsafe_private_key.pem", private_pem)
    archive.seek(0)
    return send_file(archive, mimetype="application/zip", as_attachment=True,
                     download_name="quantumsafe-ml-dsa-65-keys.zip")


@app.post("/api/sign")
def sign():
    document = required_upload("document")
    private_key = required_upload("private_key")
    signature = sign_file(document.stream, private_key.read())
    return send_file(io.BytesIO(signature), mimetype="application/octet-stream", as_attachment=True,
                     download_name=f"{os.path.basename(document.filename)}.sig")


@app.post("/api/verify")
def verify():
    document = required_upload("document")
    signature = required_upload("signature")
    public_key = required_upload("public_key")
    try:
        valid = verify_file(document.stream, signature.read(), public_key.read())
        if valid:
            return jsonify(valid=True, status="SUCCESS", message="Signature is valid. The signed file matches.")
        return jsonify(valid=False, status="FAILED", message="Verification failed. Authenticity could not be established; the file may have changed or the key/signature may not match."), 200
    except ValueError:
        # Signature mismatch and malformed signature are normal invalid results.
        return jsonify(valid=False, status="FAILED", message="Verification failed. Authenticity could not be established; the file may have changed or the key/signature may not match."), 200


@app.post("/api/share/package")
def create_share_package():
    document = required_upload("document")
    signature = required_upload("signature")
    public_key = required_upload("public_key")
    document_bytes = document.stream.read()
    signature_bytes = signature.read()
    public_key_bytes = public_key.read()
    valid = verify_file(io.BytesIO(document_bytes), signature_bytes, public_key_bytes)
    if not valid:
        return jsonify(valid=False, status="FAILED", message="The file and signature do not match. A share package was not created."), 422

    filename = secure_filename(os.path.basename(document.filename)) or "signed-document.pdf"
    archive = io.BytesIO()
    manifest = {"format": "quantumsafe-signed-document", "version": 1,
                "algorithm": "ML-DSA-65", "document_name": filename}
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest))
        zf.writestr(f"document/{filename}", document_bytes)
        zf.writestr("signature/document.sig", signature_bytes)
    archive.seek(0)
    return send_file(archive, mimetype="application/vnd.quantumsafe.signed-document+zip",
                     as_attachment=True, download_name=f"{filename}.qsafe")


@app.post("/api/share/open")
def open_share_package():
    package = required_upload("bundle")
    public_key = required_upload("public_key")
    try:
        archive = zipfile.ZipFile(package.stream)
        entries = archive.infolist()
        if len(entries) != 3 or len({entry.filename for entry in entries}) != 3:
            raise ValueError("Unexpected package contents.")
        if any(entry.file_size < 0 for entry in entries) or sum(entry.file_size for entry in entries) > 25 * 1024 * 1024:
            raise ValueError("Package contents exceed the 25 MB limit.")
        required = {"manifest.json", "signature/document.sig"}
        if not required.issubset({entry.filename for entry in entries}):
            raise ValueError("Package is missing required contents.")
        manifest = json.loads(archive.read("manifest.json"))
        filename = manifest.get("document_name", "")
        document_path = f"document/{filename}"
        if (manifest.get("format") != "quantumsafe-signed-document" or manifest.get("version") != 1
                or manifest.get("algorithm") != "ML-DSA-65" or not filename
                or secure_filename(filename) != filename or document_path not in {entry.filename for entry in entries}):
            raise ValueError("Package manifest is invalid.")
        document_bytes = archive.read(document_path)
        signature_bytes = archive.read("signature/document.sig")
    except (zipfile.BadZipFile, KeyError, json.JSONDecodeError, UnicodeDecodeError, ValueError):
        return jsonify(valid=False, status="FAILED", message="This share package is invalid or damaged."), 400

    try:
        valid = verify_file(io.BytesIO(document_bytes), signature_bytes, public_key.read())
    except ValueError:
        valid = False
    if not valid:
        return jsonify(valid=False, status="FAILED", message="Verification failed. Authenticity could not be established; the package, document, signature, or public key may not match."), 422
    response = send_file(io.BytesIO(document_bytes), mimetype="application/octet-stream", as_attachment=True,
                         download_name=filename)
    response.headers["X-QuantumSafe-Verification"] = "SUCCESS"
    return response
@app.errorhandler(ValueError)
def bad_request(error):
    return jsonify(error=str(error)), 400


@app.errorhandler(413)
def too_large(_error):
    return jsonify(error="Upload exceeds the 25 MB per-request limit."), 413


@app.errorhandler(Exception)
def internal_error(error):
    app.logger.error("Request failed (%s)", type(error).__name__)
    return jsonify(error="The request could not be processed. Check the supplied files and try again."), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False)
