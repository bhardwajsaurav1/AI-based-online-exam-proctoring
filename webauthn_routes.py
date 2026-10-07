"""
WebAuthn / FIDO2 biometric second factor (Flask blueprint).

One code path covers every device that has a browser:
  Android (fingerprint/face), iPhone/iPad (Face ID/Touch ID),
  Windows (Windows Hello), macOS (Touch ID),
  Linux (phone-via-QR or USB security key).

Library: py_webauthn (`pip install webauthn`) - free, open source, no API key.
"""
import hashlib
import os
import time

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, session, url_for
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url
from webauthn.helpers.structs import (
    AuthenticatorAttachment,
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from backend import webauthn_store as store

bp = Blueprint("webauthn", __name__, url_prefix="/webauthn")
store.init_db()

RP_NAME = os.environ.get("WEBAUTHN_RP_NAME", "AI Exam Proctoring")
CHALLENGE_TTL = 120   # seconds a challenge stays valid
MFA_TTL = 300         # seconds the password step stays valid before biometric step


# ----------------------------------------------------------------- helpers
def username_of(user):
    """
    Turn whatever db.authenticate_user() returns into a stable string id.
    ADJUST THIS if your Database class returns something different
    (it is used for both enrolment and login, so it only has to be consistent).
    """
    if isinstance(user, dict):
        for key in ("username", "email", "id"):
            if user.get(key):
                return str(user[key])
    elif hasattr(user, "keys"):  # sqlite3.Row
        for key in ("username", "email", "id"):
            if key in user.keys() and user[key]:
                return str(user[key])
    return str(user)


def _get_host():
    raw_host = request.headers.get("X-Forwarded-Host") or request.headers.get("Host") or request.host
    return raw_host.split(",")[0].strip()


def _rp_id():
    if os.environ.get("WEBAUTHN_RP_ID"):
        return os.environ["WEBAUTHN_RP_ID"]
    host = _get_host()
    return host.split(":")[0]


def _origin():
    if os.environ.get("WEBAUTHN_ORIGIN"):
        return os.environ["WEBAUTHN_ORIGIN"]
    proto = request.headers.get("X-Forwarded-Proto", request.scheme).split(",")[0].strip()
    host = _get_host()
    return f"{proto}://{host}"


def _user_handle(username):
    # Opaque, stable, non-PII handle (WebAuthn forbids using the raw username here).
    return hashlib.sha256(("exam-proctor:" + username).encode()).digest()


def _put_challenge(kind, challenge):
    session[f"wa_{kind}"] = {"c": bytes_to_base64url(challenge), "t": time.time()}


def _take_challenge(kind):
    data = session.pop(f"wa_{kind}", None)  # single use
    if not data or time.time() - data["t"] > CHALLENGE_TTL:
        return None
    return base64url_to_bytes(data["c"])


def _safe_next(target):
    if target and target.startswith("/") and not target.startswith("//") and "\\" not in target:
        return target
    return url_for("index")


def _session_username():
    user = session.get("user")
    return username_of(user) if user else None


def _auth_target():
    """Who is proving their identity right now? -> (username, user_obj, is_login_step)"""
    pending = session.get("pending_mfa")
    if pending and time.time() - pending["t"] <= MFA_TTL:
        return username_of(pending["user"]), pending["user"], True
    if session.get("user"):
        return _session_username(), session["user"], False  # re-verification
    return None, None, False


def _json_options(opts):
    return current_app.response_class(options_to_json(opts), mimetype="application/json")


# ------------------------------------------------------------------- pages
@bp.get("/security")
def security_page():
    username = _session_username()
    if not username:
        return redirect(url_for("login"))
    next_url = _safe_next(request.args.get("next"))
    return render_template("security.html", username=username,
                           credentials=store.list_credentials(username),
                           next_url=next_url)


@bp.get("/mfa")
def mfa_page():
    username, _, _ = _auth_target()
    if not username:
        return redirect(url_for("login"))
    return render_template("mfa.html", next_url=_safe_next(request.args.get("next")))


# ------------------------------------------------------------ registration
@bp.post("/register/options")
def register_options():
    username = _session_username()
    if not username:
        return jsonify(error="Please log in first."), 401

    body = request.get_json(silent=True) or {}
    # "platform"       -> this device only (Windows Hello, Touch ID)
    # "cross-platform" -> phone via QR / USB security key
    # None/omitted     -> browser decides (shows all options)
    auth_type = body.get("authenticator_type")
    attachment = None
    if auth_type == "cross-platform":
        attachment = AuthenticatorAttachment.CROSS_PLATFORM
    elif auth_type == "platform":
        attachment = AuthenticatorAttachment.PLATFORM

    existing = store.list_credentials(username)
    opts = generate_registration_options(
        rp_id=_rp_id(),
        rp_name=RP_NAME,
        user_id=_user_handle(username),
        user_name=username,
        user_display_name=username,
        authenticator_selection=AuthenticatorSelectionCriteria(
            authenticator_attachment=attachment,
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.REQUIRED,
        ),
        exclude_credentials=[
            PublicKeyCredentialDescriptor(id=base64url_to_bytes(c["credential_id"]))
            for c in existing
        ],
    )
    _put_challenge("reg", opts.challenge)
    return _json_options(opts)


@bp.post("/register/verify")
def register_verify():
    username = _session_username()
    if not username:
        return jsonify(error="Please log in first."), 401

    challenge = _take_challenge("reg")
    if challenge is None:
        return jsonify(error="Challenge expired. Please try again."), 400

    body = request.get_json(silent=True) or {}
    label = (body.get("label") or "My device").strip()[:60] or "My device"
    try:
        verified = verify_registration_response(
            credential=body.get("credential"),
            expected_challenge=challenge,
            expected_rp_id=_rp_id(),
            expected_origin=_origin(),
            require_user_verification=True,
        )
    except Exception as exc:  # parsing / signature / origin / UV failures
        current_app.logger.warning("WebAuthn registration failed: %s", exc)
        return jsonify(error=f"Registration failed: {exc}"), 400

    store.add_credential(
        username=username,
        credential_id=bytes_to_base64url(verified.credential_id),
        public_key=verified.credential_public_key,
        sign_count=verified.sign_count,
        label=label,
    )
    return jsonify(ok=True)


# ---------------------------------------------------------- authentication
@bp.post("/auth/options")
def auth_options():
    username, _, _ = _auth_target()
    if not username:
        return jsonify(error="Session expired. Please log in again."), 401

    creds = store.list_credentials(username)
    if not creds:
        return jsonify(error="No biometric device enrolled."), 400

    opts = generate_authentication_options(
        rp_id=_rp_id(),
        allow_credentials=[
            PublicKeyCredentialDescriptor(id=base64url_to_bytes(c["credential_id"]))
            for c in creds
        ],
        user_verification=UserVerificationRequirement.REQUIRED,
    )
    _put_challenge("auth", opts.challenge)
    return _json_options(opts)


@bp.post("/auth/verify")
def auth_verify():
    username, user_obj, is_login_step = _auth_target()
    if not username:
        return jsonify(error="Session expired. Please log in again."), 401

    challenge = _take_challenge("auth")
    if challenge is None:
        return jsonify(error="Challenge expired. Please try again."), 400

    body = request.get_json(silent=True) or {}
    credential = body.get("credential") or {}
    row = store.get_credential(credential.get("id", ""))
    if not row or row["username"] != username:
        return jsonify(error="Unknown credential for this account."), 400

    try:
        verified = verify_authentication_response(
            credential=credential,
            expected_challenge=challenge,
            expected_rp_id=_rp_id(),
            expected_origin=_origin(),
            credential_public_key=bytes(row["public_key"]),
            credential_current_sign_count=row["sign_count"],
            require_user_verification=True,
        )
    except Exception as exc:
        current_app.logger.warning("WebAuthn authentication failed: %s", exc)
        return jsonify(error="Biometric verification failed."), 400

    store.update_usage(row["credential_id"], verified.new_sign_count)

    if is_login_step:  # password + biometric both done -> real login
        session.pop("pending_mfa", None)
        session["user"] = user_obj
    session["identity_verified_at"] = time.time()
    session["auth_method"] = "password+webauthn"
    return jsonify(ok=True, redirect=_safe_next(body.get("next")))


# ------------------------------------------------------ credential manage
@bp.post("/credentials/delete")
def credentials_delete():
    username = _session_username()
    if not username:
        return jsonify(error="Please log in first."), 401
    cid = (request.get_json(silent=True) or {}).get("credential_id", "")
    return jsonify(ok=store.delete_credential(username, cid))
