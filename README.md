<<<<<<< HEAD
# QuantumSafe

A beginner-friendly web application for quantum-safe digital signatures using **NIST FIPS 204 ML-DSA-65**. Flask exposes the API and invokes the maintained `@noble/post-quantum` ML-DSA implementation in a small Node.js worker. It does not use RSA, Rainbow, or an invented signature scheme.

## Features

- Generate and download ML-DSA-65 keys (PEM files in a ZIP archive).
- Sign any file and download a detached `.sig` signature.
- Verify an original file, signature, and public key. A changed file fails verification.
- Create a `.qsafe` share package with the original document and signature; recipients verify with a trusted public key before downloading the document.
- Browser-local operation history; it stores filenames, timestamps, operation, and result only.
- 25 MB request limit. Backend handles files in memory and does not write uploads or keys to disk.

## Requirements

- Python 3.10 or newer
- Node.js 20 or newer and npm

## Run locally

### Backend

```powershell
cd backend
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
npm install
python app.py
```

The API listens on `http://127.0.0.1:5000`. Set `FRONTEND_ORIGIN` to the frontend origin (or a comma-separated list of origins) if it differs from the defaults `http://localhost:5173` and `http://127.0.0.1:5173`.

### Frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Visit the Vite URL (normally `http://127.0.0.1:5173`). Optionally set `VITE_API_URL` before starting Vite to change the API base URL (default `http://127.0.0.1:5000/api`).

## Use the application

1. Select **Generate Keys**, then download the ZIP and safely store the private key. Do not share it.
2. Select **Sign Document**, choose the document and private key. Save the downloaded `.sig` beside the original.
3. Select **Verify Signature**, choose the document, `.sig`, and corresponding public key. A valid signature shows SUCCESS. A mismatch shows FAILED; authenticity could not be established.
4. To check tampering, change the document and verify it against the original `.sig`. Verification must fail.
5. To share a signed file, use **Share Package** to create a `.qsafe` bundle. Send the bundle and the public key separately. The recipient opens the bundle with **Share Package**, supplies the public key obtained through a trusted channel, and downloads the document only after successful verification.

Key files use QuantumSafe's PEM-style Base64 wrapper around the raw ML-DSA-65 key bytes; they are generated and consumed by this app and are not PKCS#8/X.509 files. No private key is retained by the backend. The private key is sent over the local HTTP connection during signing; use HTTPS and an authenticated deployment before exposing this app beyond a trusted local environment.

## API

- `GET /api/health` — service and algorithm status.
- `POST /api/keys/generate` — downloads a ZIP containing public and private PEM keys.
- `POST /api/sign` — multipart fields `document`, `private_key`; downloads `<filename>.sig`.
- `POST /api/verify` — multipart fields `document`, `signature`, `public_key`; JSON `valid`, `status`, and `message`.
- `POST /api/share/package` — multipart fields `document`, `signature`, `public_key`; verifies and downloads a `.qsafe` package containing the document and detached signature.
- `POST /api/share/open` — multipart fields `bundle`, `public_key`; verifies the package and returns the document only when the signature is valid.

Uploaded content is handled in memory. Flask's multipart parser may use its own bounded temporary buffering for larger requests; the app itself does not explicitly persist upload files. Signatures use ML-DSA with the application context `QuantumSafe file signature v1`; use this app's verification endpoint or the same context when verifying independently. A `.qsafe` package is a ZIP bundle, not encryption: it contains the readable original file and `.sig`. Verification proves the document matches the signature for the supplied public key; recipients must authenticate that public key separately. The Noble JavaScript implementation is tested against public ACVP/Wycheproof vectors, but it does not claim constant-time execution and has not been independently audited. This local demo is not appropriate where an attacker can closely measure signing operations; production use should choose a reviewed constant-time native implementation.

## Project layout

```text
quantum-safe-signature/
├── backend/
│   ├── app.py
│   ├── crypto_service.py
│   ├── mldsa_worker.mjs
│   ├── package.json
│   ├── package-lock.json
│   └── requirements.txt
├── frontend/
│   ├── src/App.jsx
│   ├── src/services/api.js
│   └── package.json
└── README.md
```

## Sample test files

`samples/original.txt` and `samples/modified.txt` demonstrate tamper detection. The attached `samples/rainbow.pdf` is also included with its ML-DSA-65 signature (`samples/rainbow.pdf.sig`) and matching demo public key (`samples/rainbow_public_key.pem`). The signature was generated and verified with this project's ML-DSA workflow; “Rainbow” is the PDF's filename, not the Rainbow cryptographic algorithm. Choose these three files in **Verify Signature** to check the sample, or use them to create a share package.

## Security notes

- A signature provides integrity and proof of signing-key possession; it does **not** encrypt the document or establish a real-world identity by itself.
- A public key must be authenticated through a trusted channel to prevent key substitution.
- Keep private keys protected. The generated private PEM is unencrypted to keep this beginner demo simple; the downloaded archive must be stored securely.
- This app is intended for local learning and evaluation, not as a hardened multi-user production service.
=======
# Quantum-safe-using-digital-signature
>>>>>>> ba02a29dffe9f3f78ce2f534a474b3a2349eb515
