"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Eye, EyeOff, Lock, User, AlertCircle, Clock, ShieldAlert } from "lucide-react";
import { authAPI } from "@/lib/api";
import { setTokens } from "@/lib/auth";
import { useAuthStore } from "@/lib/store";
import { ROLE_HOME_PAGES } from "@/lib/permissions";
import { loginSchema, type LoginFormData } from "@/lib/validations";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";

export default function LoginPage() {
  const router = useRouter();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rateLimited, setRateLimited] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormData) => {
    setError(null);
    try {
      const response = await authAPI.login(data.username, data.password);
      const { access, refresh, user } = response.data;

      setTokens(access, refresh, user.role);
      setAuth(user);

      const homePage = ROLE_HOME_PAGES[user.role] || "/dashboard";
      router.replace(homePage);
    } catch (err: unknown) {
      const axiosErr = err as { response?: { status?: number; data?: { error?: string } } };
      const status = axiosErr?.response?.status;
      const msg = axiosErr?.response?.data?.error;

      if (status === 429) {
        setRateLimited(true);
        setError("Too many login attempts. Please wait a moment and try again.");
      } else if (status === 403) {
        setError("Your account has been disabled. Please contact your administrator.");
      } else if (status === 401) {
        setError("Invalid username or password. Please try again.");
      } else {
        setError(msg || "An unexpected error occurred. Please try again.");
      }
    }
  };

  return (
    <div className="w-full max-w-[440px] flex flex-col gap-5 bg-white/95 border border-[#E2E8F0] rounded-[24px] p-7 sm:p-9 shadow-[0_24px_60px_-26px_rgba(15,23,42,0.24)] animate-fade-in"> {/* FIX[BUG 7]: gap-5 and p-7 sm:p-9 instead of p-6 sm:p-8 lg:p-10 */}
      <div className="space-y-4">
        <p className="text-sm font-semibold uppercase tracking-[0.24em] text-blue-600">
          MicroFinance AI
        </p>
        <div className="space-y-2">
          <h1 className="text-3xl font-semibold tracking-tight text-slate-950">
            Welcome back
          </h1>
          <p className="text-sm text-slate-500">
            Sign in to your MicroFinance AI account
          </p>
        </div>
      </div>

      {error && (
        <div className="flex items-start gap-3 p-4 rounded-2xl bg-red-50 border border-red-200 animate-scale-in"> {/* FIX[BUG 7]: removed mt-5, parent gap handles it */}
          {rateLimited ? (
            <Clock className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
          ) : (
            <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
          )}
          <p className="text-sm text-red-700 font-medium">{error}</p>
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4" noValidate> {/* FIX[BUG 8]: flex flex-col gap-4 instead of space-y-5 mt-6 */}
        <Input
          id="username"
          label="Username"
          type="text"
          placeholder="Enter your username"
          autoComplete="username"
          autoFocus
          leftIcon={<User className="h-4 w-4" />}
          className="rounded-[16px]"
          error={errors.username?.message}
          {...register("username")}
        />

        <Input
          id="password"
          label="Password"
          type={showPassword ? "text" : "password"}
          placeholder="Enter your password"
          autoComplete="current-password"
          leftIcon={<Lock className="h-4 w-4" />}
          rightIcon={
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              className="text-slate-400 hover:text-slate-600 transition-colors focus:outline-none flex items-center justify-center p-1"
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          }
          className="rounded-[16px]"
          error={errors.password?.message}
          {...register("password")}
        />

        <div className="flex justify-end text-sm">
          <Link href="/forgot-password" className="font-medium text-blue-600 hover:text-blue-700 transition-colors">
            Forgot password?
          </Link>
        </div>

        <Button
          type="submit"
          variant="primary"
          loading={isSubmitting}
          disabled={rateLimited}
          className="w-full h-12 rounded-[16px] text-base font-semibold"
        >
          {isSubmitting ? "Signing in..." : "Sign In"}
        </Button>
      </form>

      <div className="text-center text-xs text-slate-500"> {/* FIX[BUG 7]: removed mt-5, parent gap handles it */}
        Having trouble signing in?{' '}
        <a href="mailto:support@microfinance.ai" className="font-semibold text-blue-600 hover:text-blue-700 transition-colors">
          Contact administrator
        </a>
      </div>

      <div className="rounded-[20px] border border-[#E2E8F0] bg-slate-50 px-4 py-4 text-sm text-slate-600"> {/* FIX[BUG 7]: removed mt-4, parent gap handles it */}
        <div className="flex items-start gap-3">
          <ShieldAlert className="h-5 w-5 flex-shrink-0 mt-0.5 text-slate-400" />
          <div className="space-y-1">
            <p className="font-semibold text-slate-900">Authorized Access Only</p>
            <p className="leading-relaxed">
              This system is for authorized personnel only. Access attempts are logged and monitored for security purposes.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
