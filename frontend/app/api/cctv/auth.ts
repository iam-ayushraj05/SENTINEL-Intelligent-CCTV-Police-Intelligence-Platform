/**
 * CDN Session Manager — server-only module for cctv.corp8.cloud authentication.
 *
 * NEVER import this from client components.
 * NEVER expose credentials to the browser.
 * NEVER log the password.
 */

const CDN_BASE = process.env.SENTINEL_CCTV_HLS_BASE || "https://cctv.corp8.cloud";
const CDN_EMAIL = process.env.CCTV_CDN_EMAIL || process.env.SENTINEL_CCTV_EMAIL || "";
const CDN_PASSWORD = process.env.CCTV_CDN_PASSWORD || process.env.SENTINEL_CCTV_PASSWORD || "";

let cachedCookie: string | null = null;
let cookieExpiry: number = 0;
let authInProgress: Promise<string | null> | null = null;

/**
 * Authenticate with the CDN and cache the session cookie.
 * Re-authenticates when the session expires.
 */
export async function getCDNSessionCookie(): Promise<string | null> {
  // Return cached if still valid
  if (cachedCookie && Date.now() < cookieExpiry) {
    return cachedCookie;
  }

  // Prevent parallel auth requests
  if (authInProgress) {
    return authInProgress;
  }

  authInProgress = performAuth();
  try {
    return await authInProgress;
  } finally {
    authInProgress = null;
  }
}

async function performAuth(): Promise<string | null> {
  if (!CDN_EMAIL || !CDN_PASSWORD) {
    console.warn("[CCTV Auth] Credentials not configured (CCTV_CDN_EMAIL / CCTV_CDN_PASSWORD)");
    return null;
  }

  try {
    const loginUrl = `${CDN_BASE}/auth/login`;
    const formData = new URLSearchParams();
    formData.append("email", CDN_EMAIL);
    formData.append("password", CDN_PASSWORD);

    const response = await fetch(loginUrl, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: formData.toString(),
      redirect: "manual",
    });

    // Extract Set-Cookie headers
    const setCookies = response.headers.getSetCookie?.() || [];
    const cookieParts: string[] = [];

    for (const cookie of setCookies) {
      const nameValue = cookie.split(";")[0];
      if (nameValue) {
        cookieParts.push(nameValue);
      }
    }

    // Also try the raw set-cookie header
    const rawCookie = response.headers.get("set-cookie");
    if (rawCookie && cookieParts.length === 0) {
      const nameValue = rawCookie.split(";")[0];
      if (nameValue) {
        cookieParts.push(nameValue);
      }
    }

    if (cookieParts.length > 0) {
      cachedCookie = cookieParts.join("; ");
      // Cache for 50 minutes (assuming 1-hour session)
      cookieExpiry = Date.now() + 50 * 60 * 1000;
      console.log("[CCTV Auth] Session authenticated successfully");
      return cachedCookie;
    }

    // If redirect (302), the session might be in the response
    if (response.status >= 200 && response.status < 400) {
      // Some auth systems set cookies even on 200
      console.warn("[CCTV Auth] Auth response received but no cookies found");
    } else {
      console.warn("[CCTV Auth] Auth failed with status:", response.status);
    }

    return null;
  } catch (error) {
    console.error("[CCTV Auth] Authentication error:", (error as Error).message);
    return null;
  }
}

/**
 * Make an authenticated fetch to the CDN.
 * Retries once if session expired (401).
 */
export async function cdnFetch(path: string, init?: RequestInit): Promise<Response> {
  const url = path.startsWith("http") ? path : `${CDN_BASE}${path.startsWith("/") ? "" : "/"}${path}`;

  const doFetch = async (cookie: string | null) => {
    const headers: Record<string, string> = {
      ...(init?.headers as Record<string, string> || {}),
    };
    if (cookie) {
      headers["Cookie"] = cookie;
    }
    return fetch(url, { ...init, headers, redirect: "follow" });
  };

  let cookie = await getCDNSessionCookie();
  let response = await doFetch(cookie);

  // Retry on 401 — session may have expired
  if (response.status === 401 || isLoginPage(response)) {
    cachedCookie = null;
    cookieExpiry = 0;
    cookie = await getCDNSessionCookie();
    if (cookie) {
      response = await doFetch(cookie);
    }
  }

  return response;
}

/**
 * Check if the response is the CDN login page (HTML form).
 */
function isLoginPage(response: Response): boolean {
  const ct = response.headers.get("content-type") || "";
  return ct.includes("text/html") && response.status === 200;
}

/**
 * Clear cached session — for testing or forced re-auth.
 */
export function clearCDNSession(): void {
  cachedCookie = null;
  cookieExpiry = 0;
}

export function hasCredentials(): boolean {
  return !!(CDN_EMAIL && CDN_PASSWORD);
}

export { CDN_BASE };
