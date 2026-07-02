"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useAuthStore } from "@/lib/store";
import { authAPI } from "@/lib/api";
import { changePasswordSchema, ChangePasswordFormData } from "@/lib/validations";
import { usePermissions, ROLE_PERMISSIONS } from "@/lib/permissions";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Badge from "@/components/ui/Badge";
import { useToast } from "@/components/ui/Toast";
import { User, Shield, Key, CheckCircle, Mail, Phone, MapPin, BadgeCheck } from "lucide-react";
import { getInitials, cn } from "@/lib/utils";

function getPermissionBadgeClass(perm: string): string {
  const parts = perm.split(":");
  const prefix = parts[0];
  
  const map: Record<string, string> = {
    clients: "bg-emerald-50 text-emerald-700 border-emerald-200/60 dark:bg-emerald-950/20 dark:text-emerald-400 dark:border-emerald-900/30",
    loans: "bg-blue-50 text-blue-700 border-blue-200/60 dark:bg-blue-950/20 dark:text-blue-400 dark:border-blue-900/30",
    repayments: "bg-indigo-50 text-indigo-700 border-indigo-200/60 dark:bg-indigo-950/20 dark:text-indigo-400 dark:border-indigo-900/30",
    notifications: "bg-amber-50 text-amber-700 border-amber-200/60 dark:bg-amber-950/20 dark:text-amber-400 dark:border-amber-900/30",
    reports: "bg-cyan-50 text-cyan-700 border-cyan-200/60 dark:bg-cyan-950/20 dark:text-cyan-400 dark:border-cyan-900/30",
    profile: "bg-purple-50 text-purple-700 border-purple-200/60 dark:bg-purple-950/20 dark:text-purple-400 dark:border-purple-900/30",
    fraud: "bg-rose-50 text-rose-700 border-rose-200/60 dark:bg-rose-950/20 dark:text-rose-400 dark:border-rose-900/30",
    audit: "bg-zinc-50 text-zinc-600 border-zinc-200 dark:bg-zinc-950/20 dark:text-zinc-400 dark:border-zinc-900/30",
    risk: "bg-orange-50 text-orange-700 border-orange-200/60 dark:bg-orange-950/20 dark:text-orange-400 dark:border-orange-900/30",
    approvals: "bg-teal-50 text-teal-700 border-teal-200/60 dark:bg-teal-950/20 dark:text-teal-400 dark:border-teal-900/30",
  };
  
  return map[prefix] || "bg-gray-50 text-gray-700 border-gray-200 dark:bg-gray-950/20 dark:text-gray-400 dark:border-gray-900/30";
}

function getDotColor(perm: string): string {
  const parts = perm.split(":");
  const prefix = parts[0];
  const map: Record<string, string> = {
    clients: "bg-emerald-500",
    loans: "bg-blue-500",
    repayments: "bg-indigo-500",
    notifications: "bg-amber-500",
    reports: "bg-cyan-500",
    profile: "bg-purple-500",
    fraud: "bg-rose-500",
    audit: "bg-zinc-400",
    risk: "bg-orange-500",
    approvals: "bg-teal-500",
  };
  return map[prefix] || "bg-gray-400";
}

export default function ProfilePage() {
  const user = useAuthStore((s) => s.user);
  const { role } = usePermissions();
  const toast = useToast();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ChangePasswordFormData>({
    resolver: zodResolver(changePasswordSchema),
    defaultValues: {
      old_password: "",
      new_password: "",
      confirm_password: "",
    },
  });

  const onSubmit = async (data: ChangePasswordFormData) => {
    try {
      await authAPI.changePassword({
        old_password: data.old_password,
        new_password: data.new_password,
      });
      toast.success("Password updated successfully");
      reset();
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string; message?: string } } };
      const message = axiosErr.response?.data?.detail || axiosErr.response?.data?.message || "Failed to update password";
      toast.error(message);
    }
  };

  const userPermissions = ROLE_PERMISSIONS[user?.role || ""] || [];

  return (
    <div className="flex flex-col gap-4 pb-6"> {/* FIX[BUG 1]: removed h-full p-6 added pb-6 */}
      <div> {/* FIX[BUG 1]: removed flex-shrink-0 */}
        <p className="text-[var(--text-muted)] text-sm mt-0.5">Manage your account information and security settings</p>
      </div>

      <div className="flex flex-col lg:flex-row gap-6"> {/* FIX[BUG 1]: removed flex-1 min-h-0 */}
        {/* User Card & Info */}
        <div className="w-80 flex-shrink-0 flex flex-col gap-4">
          <Card className="p-5 flex flex-col gap-4 text-center" padding={false}>
            <div className="w-20 h-20 rounded-full bg-blue-100 text-blue-700 mx-auto flex items-center justify-center text-2xl font-bold mb-4 shadow-md flex-shrink-0">
              {getInitials(user?.first_name, user?.last_name, user?.username)}
            </div>
            <h2 className="text-lg font-bold text-[var(--text-primary)] truncate"> {/* FIX[BUG 15]: added truncate */}
              {user?.first_name || user?.username} {user?.last_name || ""}
            </h2>
            <div className="mt-2 self-center">
              <Badge status="INFO" className="inline-flex items-center gap-1.5">
                <BadgeCheck className="h-3.5 w-3.5" />
                {user?.role_display || user?.role}
              </Badge>
            </div>

            <hr className="my-6 border-[var(--border-color)]" />

            <div className="space-y-4 text-left px-2">
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-full bg-gray-100 flex items-center justify-center flex-shrink-0">
                  <User className="h-4 w-4 flex-shrink-0 text-muted-foreground" />
                </div>
                <div className="min-w-0">
                  <p className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider font-medium">Username</p>
                  <p className="text-[13px] font-semibold text-[var(--text-primary)] truncate">{user?.username}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-full bg-gray-100 flex items-center justify-center flex-shrink-0">
                  <Mail className="h-4 w-4 flex-shrink-0 text-muted-foreground" />
                </div>
                <div className="min-w-0">
                  <p className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider font-medium">Email Address</p>
                  <p className="text-[13px] font-semibold text-[var(--text-primary)] truncate">{user?.email || "—"}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-full bg-gray-100 flex items-center justify-center flex-shrink-0">
                  <Phone className="h-4 w-4 flex-shrink-0 text-muted-foreground" />
                </div>
                <div className="min-w-0">
                  <p className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider font-medium">Phone Number</p>
                  <p className="text-[13px] font-semibold text-[var(--text-primary)] truncate">{user?.phone || "—"}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-full bg-gray-100 flex items-center justify-center flex-shrink-0">
                  <MapPin className="h-4 w-4 flex-shrink-0 text-muted-foreground" />
                </div>
                <div className="min-w-0">
                  <p className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider font-medium">Branch Location</p>
                  <p className="text-[13px] font-semibold text-[var(--text-primary)] truncate">{user?.branch || "General HQ"}</p>
                </div>
              </div>
            </div>
          </Card>

          {/* Permissions Info */}
          <Card className="p-5 flex flex-col gap-4" padding={false}>
            <div className="flex items-center gap-2 mb-2 flex-shrink-0">
              <Shield className="h-5 w-5 text-blue-600" />
              <h3 className="text-[14px] font-bold text-[var(--text-primary)]">My System Permissions</h3>
            </div>
            {userPermissions.length === 0 ? (
              <p className="text-[12px] text-[var(--text-muted)] text-center py-2">No permissions assigned.</p>
            ) : userPermissions.includes("*") ? (
              <div className="flex flex-wrap gap-2 mt-2">
                <span className="inline-flex text-[11px] px-2.5 py-1 rounded bg-blue-50 text-blue-700 border border-blue-200 font-medium cursor-default select-none">
                  Full System Access
                </span>
              </div>
            ) : (
              <div className="flex flex-wrap gap-2 mt-2">
                {userPermissions.map((perm) => (
                  <span
                    key={perm}
                    className="inline-flex items-center text-[11px] px-2 py-0.5 rounded border bg-blue-50/50 text-blue-700 border-blue-200/60 font-mono shadow-[0_1px_2px_rgba(0,0,0,0.02)] transition-colors hover:bg-blue-100/60 hover:text-blue-800 hover:border-blue-300 cursor-default select-none"
                  >
                    {perm}
                  </span>
                ))}
              </div>
            )}
          </Card>
        </div>

        {/* Change Password Card */}
        <div className="flex-1 min-w-0"> {/* FIX[BUG 15]: changed min-h-0 to min-w-0 */}
          <Card className="p-6 flex flex-col gap-5" padding={false}>
            <div className="flex items-center gap-2 mb-2 flex-shrink-0">
              <Key className="h-5 w-5 text-amber-500" />
              <h3 className="text-base font-bold text-[var(--text-primary)]">Change Password</h3>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4 max-w-md">
              <Input
                label="Current Password"
                type="password"
                placeholder="Enter current password"
                error={errors.old_password?.message}
                {...register("old_password")}
              />

              <Input
                label="New Password"
                type="password"
                placeholder="Enter new password (min. 8 characters)"
                error={errors.new_password?.message}
                {...register("new_password")}
              />

              <Input
                label="Confirm New Password"
                type="password"
                placeholder="Repeat new password"
                error={errors.confirm_password?.message}
                {...register("confirm_password")}
              />

              <div className="pt-2">
                <Button type="submit" variant="primary" loading={isSubmitting} className="w-fit px-5 h-10 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700">
                  Update Password
                </Button>
              </div>
            </form>
          </Card>
        </div>
      </div>
    </div>
  );
}
