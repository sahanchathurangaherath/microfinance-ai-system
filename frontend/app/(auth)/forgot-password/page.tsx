"use client";

import Link from "next/link";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowLeft, Mail, CheckCircle2, AlertCircle } from "lucide-react";
import { authAPI } from "@/lib/api";
import { forgotPasswordSchema, type ForgotPasswordFormData } from "@/lib/validations";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";

export default function ForgotPasswordPage() {
  const [submitted, setSubmitted] = useState(false);
  const [serverMessage, setServerMessage] = useState<string | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ForgotPasswordFormData>({
    resolver: zodResolver(forgotPasswordSchema),
  });

  const onSubmit = async (data: ForgotPasswordFormData) => {
    setServerMessage(null);
    setServerError(null);
    try {
      await authAPI.forgotPassword(data.email);
      setSubmitted(true);
      setServerMessage("If an account exists for that email, a password reset link has been sent.");
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string; message?: string } } };
      const message = axiosErr?.response?.data?.detail || axiosErr?.response?.data?.message || "Unable to send reset instructions right now.";
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
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Forgot password?</h1> {/* FIX[BUG 17]: text-2xl and removed mb-2 */}
        <p className="text-[var(--text-secondary)] text-sm mt-1"> {/* FIX[BUG 17]: text-sm mt-1 */}
          Enter your email and we will send you a secure link to reset your password.
        </p>
      </div>

      {serverError && (
        <div className="flex items-start gap-3 p-4 rounded-xl bg-red-50 border border-red-200"> {/* FIX[BUG 17]: removed mb-5 */}
          <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
          <p className="text-[13px] text-red-700 font-medium">{serverError}</p>
        </div>
      )}

      {serverMessage && !serverError && (
        <div className="flex items-start gap-3 p-4 rounded-xl bg-green-50 border border-green-200"> {/* FIX[BUG 17]: removed mb-5 */}
          <CheckCircle2 className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
          <p className="text-[13px] text-green-700 font-medium">{serverMessage}</p>
        </div>
      )}

      {!submitted ? (
        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-1" noValidate> {/* Reduced gap-4 to gap-1 because Input reserves error space */}
          <Input
            label="Email address"
            id="email"
            type="email"
            placeholder="Enter your email address"
            autoComplete="email"
            autoFocus
            leftIcon={<Mail className="h-4 w-4" />}
            error={errors.email?.message}
            {...register("email")}
          />

          <Button type="submit" variant="primary" loading={isSubmitting} className="w-full h-12 rounded-[16px] text-base font-semibold mt-2">
            {isSubmitting ? "Sending link..." : "Send reset link"}
          </Button>
        </form>
      ) : (
        <div className="rounded-xl border border-[var(--border-color)] bg-slate-50 p-5 text-sm text-[var(--text-secondary)]">
          <p>If you do not see the email shortly, please check your spam folder or contact support.</p>
        </div>
      )}
    </div>
  );
}
