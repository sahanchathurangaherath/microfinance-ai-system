/* eslint-disable react-hooks/set-state-in-effect */
"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { AlertCircle, ArrowLeft, CheckCircle2, Eye, EyeOff, Lock } from "lucide-react";
import { authAPI } from "@/lib/api";
import { resetPasswordSchema, type ResetPasswordFormData } from "@/lib/validations";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";

function ResetPasswordContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const uid = searchParams.get("uid") || "";
  const token = searchParams.get("token") || "";

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordSchema),
  });

  useEffect(() => {
    if (!uid || !token) {
      setServerError("This password reset link is missing required information. Please request a new one.");
    }
  }, [uid, token]);

  const onSubmit = async (data: ResetPasswordFormData) => {
    setServerError(null);
    try {
      await authAPI.resetPassword({
        uid,
        token,
        new_password: data.new_password,
        confirm_password: data.confirm_password,
      });
      setSuccess(true);
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { [key: string]: unknown } } };
      const firstError = axiosErr?.response?.data ? Object.values(axiosErr.response.data)[0] : null;
      const message = typeof firstError === "string" ? firstError : "We could not reset your password. Please request a new link.";
      setServerError(message);
    }
  };

  return (
    <div className="animate-fade-in bg-white/95 rounded-[20px] border border-[var(--border-color)] shadow-[0_20px_50px_-24px_rgba(15,23,42,0.28)] p-7 sm:p-9 flex flex-col gap-6"> {/* FIX[BUG 17]: padding and gap-based spacing */}
      <div>
        <Link href="/login" className="flex items-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-700 mb-4 w-fit">
          <ArrowLeft className="h-4 w-4 flex-shrink-0" /> {/* FIX[BUG 17]: flex-shrink-0 */}
          Back to sign in
        </Link>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Reset your password</h1> {/* FIX[BUG 17]: text-2xl and removed mb-2 */}
        <p className="text-[var(--text-secondary)] text-sm mt-1"> {/* FIX[BUG 17]: text-sm mt-1 */}
          Choose a new password for your MicroFinance AI account.
        </p>
      </div>

      {serverError && (
        <div className="flex items-start gap-3 p-4 rounded-xl bg-red-50 border border-red-200"> {/* FIX[BUG 17]: removed mb-5 */}
          <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
          <p className="text-[13px] text-red-700 font-medium">{serverError}</p>
        </div>
      )}

      {success ? (
        <div className="space-y-4">
          <div className="flex items-start gap-3 p-4 rounded-xl bg-green-50 border border-green-200">
            <CheckCircle2 className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
            <p className="text-[13px] text-green-700 font-medium">Your password has been reset successfully.</p>
          </div>
          <Button type="button" variant="primary" className="w-full h-12 rounded-[16px] text-base font-semibold mt-2" onClick={() => router.push("/login")}>
            Go to sign in
          </Button>
        </div>
      ) : (
        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-1" noValidate> {/* Reduced gap to account for Input error space */}
          <Input
            label="New password"
            id="new_password"
            type={showPassword ? "text" : "password"}
            placeholder="Enter a new password"
            autoComplete="new-password"
            autoFocus
            leftIcon={<Lock className="h-4 w-4" />}
            rightIcon={
              <button type="button" onClick={() => setShowPassword((v) => !v)} tabIndex={-1} aria-label={showPassword ? "Hide password" : "Show password"}>
                {showPassword ? <EyeOff className="h-4 w-4 cursor-pointer" /> : <Eye className="h-4 w-4 cursor-pointer" />}
              </button>
            }
            error={errors.new_password?.message}
            {...register("new_password")}
          />

          <Input
            label="Confirm new password"
            id="confirm_password"
            type={showConfirmPassword ? "text" : "password"}
            placeholder="Repeat your new password"
            autoComplete="new-password"
            leftIcon={<Lock className="h-4 w-4" />}
            rightIcon={
              <button type="button" onClick={() => setShowConfirmPassword((v) => !v)} tabIndex={-1} aria-label={showConfirmPassword ? "Hide password" : "Show password"}>
                {showConfirmPassword ? <EyeOff className="h-4 w-4 cursor-pointer" /> : <Eye className="h-4 w-4 cursor-pointer" />}
              </button>
            }
            error={errors.confirm_password?.message}
            {...register("confirm_password")}
          />

          <Button type="submit" variant="primary" loading={isSubmitting} className="w-full h-12 rounded-[16px] text-base font-semibold mt-2" disabled={!uid || !token}>
            {isSubmitting ? "Resetting password..." : "Reset password"}
          </Button>
        </form>
      )}
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div className="animate-fade-in bg-white/95 rounded-[20px] border border-[var(--border-color)] shadow-[0_20px_50px_-24px_rgba(15,23,42,0.28)] p-7 sm:p-9 flex flex-col gap-6"> {/* FIX[BUG 17]: padding and gap-based spacing */}Loading...</div>}>
      <ResetPasswordContent />
    </Suspense>
  );
}
