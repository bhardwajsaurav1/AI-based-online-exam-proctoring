/* WebAuthn / FIDO2 browser client - no dependencies, no API keys.
 * Works with Face ID / Touch ID, Android fingerprint/face, Windows Hello,
 * and phone-via-QR or USB security keys on Linux. */
(function () {
  "use strict";

  function b64uToBuf(s) {
    s = s.replace(/-/g, "+").replace(/_/g, "/");
    s += "=".repeat((4 - (s.length % 4)) % 4);
    const bin = atob(s);
    const out = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
    return out.buffer;
  }

  function bufToB64u(buf) {
    const bytes = new Uint8Array(buf);
    let s = "";
    for (let i = 0; i < bytes.length; i++) s += String.fromCharCode(bytes[i]);
    return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  }

  async function postJSON(url, data) {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify(data || {}),
    });
    let body = {};
    try { body = await res.json(); } catch (e) { /* non-JSON error page */ }
    if (!res.ok) throw new Error(body.error || "Request failed (" + res.status + ")");
    return body;
  }

  function supported() {
    return window.isSecureContext && !!window.PublicKeyCredential && !!navigator.credentials;
  }

  function friendly(err) {
    if (err && err.name === "NotAllowedError") return "Cancelled or timed out. Please try again.";
    if (err && err.name === "InvalidStateError") return "This device is already enrolled.";
    if (err && err.name === "SecurityError") return "Biometrics need HTTPS (or localhost).";
    return (err && err.message) || "Something went wrong.";
  }

  async function register(label) {
    const opts = await postJSON("/webauthn/register/options");
    opts.challenge = b64uToBuf(opts.challenge);
    opts.user.id = b64uToBuf(opts.user.id);
    (opts.excludeCredentials || []).forEach(function (c) { c.id = b64uToBuf(c.id); });

    const cred = await navigator.credentials.create({ publicKey: opts });
    const payload = {
      id: cred.id,
      rawId: bufToB64u(cred.rawId),
      type: cred.type,
      clientExtensionResults: cred.getClientExtensionResults(),
      response: {
        clientDataJSON: bufToB64u(cred.response.clientDataJSON),
        attestationObject: bufToB64u(cred.response.attestationObject),
      },
    };
    return postJSON("/webauthn/register/verify", { credential: payload, label: label });
  }

  async function authenticate(nextUrl) {
    const opts = await postJSON("/webauthn/auth/options");
    opts.challenge = b64uToBuf(opts.challenge);
    (opts.allowCredentials || []).forEach(function (c) { c.id = b64uToBuf(c.id); });

    const cred = await navigator.credentials.get({ publicKey: opts });
    const r = cred.response;
    const payload = {
      id: cred.id,
      rawId: bufToB64u(cred.rawId),
      type: cred.type,
      clientExtensionResults: cred.getClientExtensionResults(),
      response: {
        clientDataJSON: bufToB64u(r.clientDataJSON),
        authenticatorData: bufToB64u(r.authenticatorData),
        signature: bufToB64u(r.signature),
      },
    };
    if (r.userHandle) payload.response.userHandle = bufToB64u(r.userHandle);
    return postJSON("/webauthn/auth/verify", { credential: payload, next: nextUrl });
  }

  function setStatus(el, msg, isError) {
    if (!el) return;
    el.textContent = msg;
    el.style.color = isError ? "#d93025" : "#188038";
  }

  document.addEventListener("DOMContentLoaded", async function () {
    const status = document.getElementById("wa-status");
    const hint = document.getElementById("wa-hint");
    const regBtn = document.getElementById("wa-register-btn");
    const authBtn = document.getElementById("wa-auth-btn");

    if (!supported()) {
      setStatus(status, "This browser/connection does not support biometric sign-in. Use HTTPS (or localhost) and a current browser.", true);
      if (regBtn) regBtn.disabled = true;
      if (authBtn) authBtn.disabled = true;
      return;
    }

    if (hint && PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable) {
      try {
        const platform = await PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable();
        hint.textContent = platform
          ? "This device has a built-in biometric / screen-lock authenticator."
          : "No built-in biometric found. You can still use your phone (scan the QR code your browser shows) or a USB security key.";
      } catch (e) { /* hint only */ }
    }

    if (regBtn) {
      regBtn.addEventListener("click", async function () {
        const label = (document.getElementById("wa-label") || {}).value || "My device";
        regBtn.disabled = true;
        try {
          await register(label);
          setStatus(status, "Device enrolled.", false);
          setTimeout(function () { window.location.reload(); }, 600);
        } catch (e) {
          setStatus(status, friendly(e), true);
          regBtn.disabled = false;
        }
      });
    }

    if (authBtn) {
      authBtn.addEventListener("click", async function () {
        authBtn.disabled = true;
        try {
          const res = await authenticate(authBtn.dataset.next);
          setStatus(status, "Verified. Redirecting...", false);
          window.location.href = res.redirect;
        } catch (e) {
          setStatus(status, friendly(e), true);
          authBtn.disabled = false;
        }
      });
    }

    document.querySelectorAll("[data-wa-delete]").forEach(function (btn) {
      btn.addEventListener("click", async function () {
        if (!confirm("Remove this device?")) return;
        try {
          await postJSON("/webauthn/credentials/delete", { credential_id: btn.dataset.waDelete });
          window.location.reload();
        } catch (e) {
          setStatus(status, friendly(e), true);
        }
      });
    });
  });
})();
