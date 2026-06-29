import Cookies from "js-cookie";

export function setTokens(access: string, refresh: string, role: string) {
  Cookies.set("access_token", access, { sameSite: "Strict" });
  Cookies.set("refresh_token", refresh, {
    sameSite: "Strict",
    expires: 7,
  });
  Cookies.set("user_role", role, { sameSite: "Strict" });
}

export function clearTokens() {
  Cookies.remove("access_token");
  Cookies.remove("refresh_token");
  Cookies.remove("user_role");
}

export function getAccessToken(): string | undefined {
  return Cookies.get("access_token");
}

export function getRefreshToken(): string | undefined {
  return Cookies.get("refresh_token");
}

export function getUserRole(): string | undefined {
  return Cookies.get("user_role");
}

export function parseJwt(token: string): Record<string, unknown> | null {
  try {
    const base64Url = token.split(".")[1];
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join("")
    );
    return JSON.parse(jsonPayload);
  } catch {
    return null;
  }
}

export function isTokenExpired(token: string): boolean {
  const payload = parseJwt(token);
  if (!payload || !payload.exp) return true;
  const exp = (payload.exp as number) * 1000;
  return Date.now() >= exp;
}
