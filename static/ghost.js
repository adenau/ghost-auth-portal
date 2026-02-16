(async function () {
  const config = window.GhostBridgeConfig || {};
  const sessionEndpoint = config.sessionEndpoint || "/members/api/session/";
  const signInPath = config.signInPath || "/portal/signin";
  const fallbackCallbackUrl = config.callbackUrl || "";

  const query = new URLSearchParams(window.location.search);
  const requestedReturnTarget = query.get("r");

  function pickSafeReturnTarget() {
    const fallback = fallbackCallbackUrl ? new URL(fallbackCallbackUrl) : null;
    const requested = requestedReturnTarget ? new URL(requestedReturnTarget) : null;

    if (requested && fallback && requested.origin === fallback.origin) {
      return requested.toString();
    }

    if (!requested && fallback) {
      return fallback.toString();
    }

    if (requested && !fallback && requested.origin === window.location.origin) {
      return requested.toString();
    }

    return "";
  }

  const returnTarget = pickSafeReturnTarget();

  if (!returnTarget) {
    document.body.textContent = "Missing callback URL (r query parameter).";
    return;
  }

  function redirectToSignIn() {
    const signInUrl = new URL(window.location.href);
    signInUrl.hash = signInPath.startsWith("#") ? signInPath : `#${signInPath}`;
    window.location.replace(signInUrl.toString());
  }

  async function getMemberToken() {
    const response = await fetch(sessionEndpoint, {
      credentials: "include",
      headers: {
        Accept: "application/json"
      }
    });

    if (response.status === 204) {
      return null;
    }

    if (!response.ok) {
      throw new Error("Unable to get member session");
    }

    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      const body = await response.json();
      return body.token || body.jwt || null;
    }

    const textToken = (await response.text()).trim();
    return textToken || null;
  }

  try {
    const token = await getMemberToken();
    if (!token) {
      redirectToSignIn();
      return;
    }

    const callback = new URL(returnTarget);
    callback.hash = `token=${encodeURIComponent(token)}`;
    window.location.replace(callback.toString());
  } catch (_error) {
    document.body.textContent = "Authentication bridge error.";
  }
})();
