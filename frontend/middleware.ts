import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PROTECTED_PATHS = [
  "/dashboard",
  "/clients",
  "/loans",
  "/approvals",
  "/repayments",
  "/collections",
  "/fraud",
  "/reports",
  "/audit",
  "/notifications",
  "/users",
  "/profile",
];

const PUBLIC_PATHS = ["/login"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const accessToken = request.cookies.get("access_token")?.value;
  const userRole = request.cookies.get("user_role")?.value;

  const isProtected = PROTECTED_PATHS.some(
    (p) => pathname === p || pathname.startsWith(p + "/")
  );
  const isPublic = PUBLIC_PATHS.some(
    (p) => pathname === p || pathname.startsWith(p + "/")
  );

  if (isPublic && accessToken) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  if (isProtected && !accessToken) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }

  if (isProtected && userRole) {
    const headers = new Headers(request.headers);
    headers.set("x-user-role", userRole);
    return NextResponse.next({ request: { headers } });
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/clients/:path*",
    "/loans/:path*",
    "/approvals/:path*",
    "/repayments/:path*",
    "/collections/:path*",
    "/fraud/:path*",
    "/reports/:path*",
    "/audit/:path*",
    "/notifications/:path*",
    "/users/:path*",
    "/profile/:path*",
    "/login",
  ],
};
