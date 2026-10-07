/* WebAuthn / FIDO2 browser client - no dependencies, no API keys.
 *
 * Supports three modes:
 *   1. Platform   -> Windows Hello / Touch ID / Face ID (built-in chip)
 *   2. Cross-platform -> Phone via QR code / USB security key
 *   3. Any (default)  -> Browser shows all available options
 *
 * Works with Face ID / Touch ID, Android fingerprint/face, Windows Hello,
 * and phone-via-QR or USB security keys on any OS. */
(function () {
  "use strict";

  /* ── Base64url helpers ── */
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

  /* ── HTTP helper ── */
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

  /* ── Feature detection ── */
  function supported() {
    return window.isSecureContext && !!window.PublicKeyCredential && !!navigator.credentials;
  }

  /* ── User-friendly error messages ── */
  function friendly(err) {
    if (!err) return "Something went wrong.";
    if (err.name === "NotAllowedError")
      return "Cancelled or timed out. Please try again.";
    if (err.name === "InvalidStateError")
      return "This device is already enrolled. Try a different device.";
    if (err.name === "SecurityError")
      return "Biometrics require HTTPS (or localhost).";
    if (err.name === "NotSupportedError")
      return "This authenticator type is not supported by your browser/OS.";
    if (err.name === "AbortError")
      return "The request was aborted. Please try again.";
    return err.message || "Something went wrong.";
  }

  /* ── Core: register a new credential ──
   *  authenticatorType: "platform" | "cross-platform" | undefined
   *    platform       = this device's built-in biometric (Windows Hello, Touch ID)
   *    cross-platform = phone QR code / USB security key
   *    undefined      = browser picks (shows all options)
   */
  async function register(label, authenticatorType) {
    const opts = await postJSON("/webauthn/register/options", {
      authenticator_type: authenticatorType || null,
    });
    opts.challenge = b64uToBuf(opts.challenge);
    opts.user.id   = b64uToBuf(opts.user.id);
    (opts.excludeCredentials || []).forEach(function (c) { c.id = b64uToBuf(c.id); });

    const cred = await navigator.credentials.create({ publicKey: opts });
    const payload = {
      id:                    cred.id,
      rawId:                 bufToB64u(cred.rawId),
      type:                  cred.type,
      clientExtensionResults: cred.getClientExtensionResults(),
      response: {
        clientDataJSON:    bufToB64u(cred.response.clientDataJSON),
        attestationObject: bufToB64u(cred.response.attestationObject),
      },
    };
    return postJSON("/webauthn/register/verify", { credential: payload, label: label });
  }

  /* ── Core: authenticate with an existing credential ── */
  async function authenticate(nextUrl) {
    const opts = await postJSON("/webauthn/auth/options");
    opts.challenge = b64uToBuf(opts.challenge);
    (opts.allowCredentials || []).forEach(function (c) { c.id = b64uToBuf(c.id); });

    const cred = await navigator.credentials.get({ publicKey: opts });
    const r = cred.response;
    const payload = {
      id:                    cred.id,
      rawId:                 bufToB64u(cred.rawId),
      type:                  cred.type,
      clientExtensionResults: cred.getClientExtensionResults(),
      response: {
        clientDataJSON:    bufToB64u(r.clientDataJSON),
        authenticatorData: bufToB64u(r.authenticatorData),
        signature:         bufToB64u(r.signature),
      },
    };
    if (r.userHandle) payload.response.userHandle = bufToB64u(r.userHandle);
    return postJSON("/webauthn/auth/verify", { credential: payload, next: nextUrl });
  }

  /* ── UI helpers ── */
  function setStatus(el, msg, isError) {
    if (!el) return;
    el.textContent = msg;
    el.style.color = isError ? "#dc2626" : "#16a34a";
  }

  function setButtonLoading(btn, loading, originalText) {
    if (!btn) return;
    btn.disabled = loading;
    if (loading) {
      btn.dataset.origText = btn.innerHTML;
      btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Please wait...';
    } else {
      btn.innerHTML = btn.dataset.origText || originalText || btn.innerHTML;
    }
  }

  /* ── Validates label field before enrolling ── */
  function getLabel(labelEl, statusEl) {
    if (!labelEl) return "My Device";
    const val = labelEl.value.trim();
    if (!val) {
      labelEl.focus();
      labelEl.style.borderColor = "#dc2626";
      setStatus(statusEl, "Please enter a name for this device first.", true);
      return null;
    }
    labelEl.style.borderColor = "";
    return val;
  }

  /* ── Wire up a single enroll button ──
   *    btn              : the <button> element
   *    authenticatorType: "platform" | "cross-platform" | undefined
   *    statusEl / hintEl: display elements
   */
  function wireEnrollBtn(btn, authenticatorType, statusEl, hintEl) {
    if (!btn) return;
    btn.addEventListener("click", async function () {
      const labelEl = document.getElementById("wa-label");
      const label = getLabel(labelEl, statusEl);
      if (label === null) return;

      setButtonLoading(btn, true);
      if (hintEl) hintEl.textContent = "";
      setStatus(statusEl, "Waiting for authenticator prompt...", false);

      try {
        await register(label, authenticatorType);
        const urlParams = new URLSearchParams(window.location.search);
        const nextUrl = urlParams.get("next") || (document.querySelector(".setup-hero") ? "/" : null);
        if (nextUrl) {
          setStatus(statusEl, "\u2713 Biometrics enrolled successfully! Redirecting to Exam Dashboard...", false);
          setTimeout(function () { window.location.href = nextUrl; }, 800);
        } else {
          setStatus(statusEl, "\u2713 Device enrolled successfully! Reloading...", false);
          setTimeout(function () { window.location.reload(); }, 900);
        }
      } catch (e) {
        setStatus(statusEl, friendly(e), true);
        setButtonLoading(btn, false);
      }
    });
  }

  /* ══════════════════════════════════════════════
     DOMContentLoaded – wire up all elements
  ══════════════════════════════════════════════ */
  document.addEventListener("DOMContentLoaded", async function () {
    const statusEl    = document.getElementById("wa-status");
    const hintEl      = document.getElementById("wa-hint");

    /* Enrollment buttons */
    const regBtnAny      = document.getElementById("wa-register-btn");          // any / default
    const regBtnPlatform = document.getElementById("wa-register-platform-btn"); // this device
    const regBtnPhone    = document.getElementById("wa-register-phone-btn");    // phone / cross-platform

    /* Authentication button (MFA page) */
    const authBtn = document.getElementById("wa-auth-btn");

    /* ── Browser / security check ── */
    if (!supported()) {
      const msg = "This browser/connection does not support biometric sign-in. Use HTTPS (or localhost) with a modern browser.";
      setStatus(statusEl, msg, true);
      [regBtnAny, regBtnPlatform, regBtnPhone, authBtn].forEach(function (b) {
        if (b) b.disabled = true;
      });
      return;
    }

    /* ── Detect built-in biometric availability and update hint ── */
    if (hintEl && window.PublicKeyCredential &&
        PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable) {
      try {
        const hasPlatform = await PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable();
        if (hasPlatform) {
          hintEl.textContent =
            "This device has a built-in biometric authenticator (Windows Hello / Touch ID / Fingerprint).";
        } else {
          hintEl.textContent =
            "No built-in biometric found on this device. Use \"Use Phone / QR Code\" to enroll your phone.";
          /* Auto-disable the platform button if no platform authenticator */
          if (regBtnPlatform) {
            regBtnPlatform.disabled  = true;
            regBtnPlatform.title     = "No built-in biometric detected on this device.";
            regBtnPlatform.style.opacity = "0.45";
          }
        }
      } catch (e) { /* hint only — ignore */ }
    }

    /* ── Wire enroll buttons ── */
    wireEnrollBtn(regBtnAny,      undefined,        statusEl, hintEl);
    wireEnrollBtn(regBtnPlatform, "platform",       statusEl, hintEl);
    wireEnrollBtn(regBtnPhone,    "cross-platform", statusEl, hintEl);

    /* ── Wire auth button (MFA page) ── */
    if (authBtn) {
      authBtn.addEventListener("click", async function () {
        setButtonLoading(authBtn, true);
        setStatus(statusEl, "Waiting for biometric verification...", false);
        try {
          const res = await authenticate(authBtn.dataset.next);
          setStatus(statusEl, "\u2713 Verified! Redirecting...", false);
          window.location.href = res.redirect;
        } catch (e) {
          setStatus(statusEl, friendly(e), true);
          setButtonLoading(authBtn, false);
        }
      });
    }

    /* ── Wire delete buttons ── */
    document.querySelectorAll("[data-wa-delete]").forEach(function (btn) {
      btn.addEventListener("click", async function () {
        if (!confirm("Remove this device? You will no longer be able to use it to log in.")) return;
        try {
          await postJSON("/webauthn/credentials/delete", { credential_id: btn.dataset.waDelete });
          window.location.reload();
        } catch (e) {
          setStatus(statusEl, friendly(e), true);
        }
      });
    });
  });
})();
