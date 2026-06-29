"use client";

import { useState } from "react";
import useSWR, { useSWRConfig } from "swr";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { usePermissions, ROLE_LABELS } from "@/lib/permissions";
import { fetcher, usersAPI } from "@/lib/api";
import { createUserSchema, CreateUserFormData } from "@/lib/validations";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Select from "@/components/ui/Select";
import Modal from "@/components/ui/Modal";
import Table from "@/components/ui/Table";
import Badge from "@/components/ui/Badge";
import Spinner from "@/components/ui/Spinner";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import { useToast } from "@/components/ui/Toast";
import { UserPlus, Search, Edit2, ShieldAlert, Trash2, Key, RefreshCw, Check, X } from "lucide-react";

interface UserRecord extends Record<string, unknown> {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  role_display: string;
  is_active: boolean;
  phone?: string;
  branch?: string;
}

export default function UsersPage() {
  const { role, isAdmin } = usePermissions();
  const { mutate } = useSWRConfig();
  const toast = useToast();
  const [search, setSearch] = useState("");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<UserRecord | null>(null);
  const [deletingUser, setDeletingUser] = useState<UserRecord | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const roleOptions = Object.entries(ROLE_LABELS).map(([key, label]) => ({ value: key, label }));

  // Fetch users
  const params = search ? `?search=${search}` : "";
  const { data, error, isLoading, isValidating } = useSWR<UserRecord[]>(
    `/users/${params}`,
    fetcher
  );

  const usersList = Array.isArray(data) ? data : (data as unknown as { results?: UserRecord[] })?.results || [];

  // Create user form
  const {
    register: registerCreate,
    handleSubmit: handleSubmitCreate,
    reset: resetCreate,
    formState: { errors: errorsCreate, isSubmitting: isSubmittingCreate },
  } = useForm<CreateUserFormData>({
    resolver: zodResolver(createUserSchema),
    defaultValues: {
      username: "",
      email: "",
      first_name: "",
      last_name: "",
      role: "loan_officer",
      password: "",
      confirm_password: "",
      phone: "",
      branch: "",
    },
  });

  // Edit user form (just role and branch/phone/active)
  const [editRole, setEditRole] = useState("");
  const [editBranch, setEditBranch] = useState("");
  const [editPhone, setEditPhone] = useState("");
  const [isUpdating, setIsUpdating] = useState(false);

  if (!isAdmin) {
    return (
      <Card className="flex flex-col items-center justify-center text-center py-16 max-w-md mx-auto">
        <div className="w-12 h-12 rounded-full bg-red-100 dark:bg-red-950/30 flex items-center justify-center mb-3">
          <ShieldAlert className="h-6 w-6 text-red-600" />
        </div>
        <h3 className="text-lg font-bold text-[var(--text-primary)]">Access Denied</h3>
        <p className="text-[var(--text-muted)] text-sm mt-2">
          You do not have permission to view User Management. This module is restricted to Administrators only.
        </p>
      </Card>
    );
  }

  const handleCreateUser = async (formData: CreateUserFormData) => {
    try {
      await usersAPI.createUser(formData);
      toast.success("User account created successfully");
      setIsCreateOpen(false);
      resetCreate();
      mutate(`/users/${params}`);
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      const detail = axiosErr.response?.data?.detail || "Failed to create user account";
      toast.error(detail);
    }
  };

  const handleToggleStatus = async (userRecord: UserRecord) => {
    try {
      await usersAPI.updateUser(userRecord.id, { is_active: !userRecord.is_active });
      toast.success(`User ${userRecord.is_active ? "deactivated" : "activated"} successfully`);
      mutate(`/users/${params}`);
    } catch (err) {
      toast.error("Failed to toggle user status");
    }
  };

  const handleDeleteUser = async () => {
    if (!deletingUser) return;
    setIsDeleting(true);
    try {
      await usersAPI.deleteUser(deletingUser.id);
      toast.success("User deleted successfully");
      mutate(`/users/${params}`);
      setDeletingUser(null);
    } catch (err) {
      toast.error("Failed to delete user");
    } finally {
      setIsDeleting(false);
    }
  };

  const openEditModal = (u: UserRecord) => {
    setEditingUser(u);
    setEditRole(u.role);
    setEditBranch(u.branch || "");
    setEditPhone(u.phone || "");
  };

  const handleUpdateUser = async () => {
    if (!editingUser) return;
    setIsUpdating(true);
    try {
      await usersAPI.updateUser(editingUser.id, {
        role: editRole,
        branch: editBranch,
        phone: editPhone,
      });
      toast.success("User updated successfully");
      setEditingUser(null);
      mutate(`/users/${params}`);
    } catch (err) {
      toast.error("Failed to update user");
    } finally {
      setIsUpdating(false);
    }
  };

  const columns = [
    {
      id: "name",
      header: "Staff Member",
      cell: (r: UserRecord) => (
        <div className="flex items-center gap-2.5 min-w-0"> {/* FIX[BUG 15]: added min-w-0 */}
          <div className="w-8 h-8 rounded-full gradient-primary flex items-center justify-center text-white text-[11px] font-bold flex-shrink-0"> {/* FIX[BUG 15]: added flex-shrink-0 */}
            {r.first_name?.[0] || r.username?.[0]}{r.last_name?.[0] || ""}
          </div>
          <div className="min-w-0"> {/* FIX[BUG 15]: added min-w-0 */}
            <p className="text-[13px] font-semibold text-[var(--text-primary)] truncate"> {/* FIX[BUG 15]: added truncate */}
              {r.first_name} {r.last_name}
            </p>
            <p className="text-[11px] text-[var(--text-muted)] truncate">@{r.username}</p> {/* FIX[BUG 15]: added truncate */}
          </div>
        </div>
      ),
    },
    {
      id: "email",
      header: "Email Address",
      cell: (r: UserRecord) => <span className="text-[13px] text-[var(--text-secondary)]">{r.email}</span>,
    },
    {
      id: "role",
      header: "System Role",
      cell: (r: UserRecord) => (
        <Badge status="INFO">
          {ROLE_LABELS[r.role] || r.role_display || r.role}
        </Badge>
      ),
    },
    {
      id: "branch",
      header: "Branch",
      cell: (r: UserRecord) => <span className="text-[13px] text-[var(--text-secondary)]">{r.branch || "General HQ"}</span>,
    },
    {
      id: "status",
      header: "Status",
      cell: (r: UserRecord) => (
        <Badge status={r.is_active ? "ACTIVE" : "INACTIVE"} />
      ),
    },
    {
      id: "actions",
      header: "Actions",
      cell: (r: UserRecord) => (
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => openEditModal(r)}
            className="p-1 rounded hover:bg-gray-100 dark:hover:bg-zinc-800 text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            title="Edit details"
          >
            <Edit2 className="h-4 w-4" />
          </button>
          <button
            onClick={() => handleToggleStatus(r)}
            className={`p-1 rounded hover:bg-gray-100 dark:hover:bg-zinc-800 ${
              r.is_active ? "text-amber-600 hover:text-amber-700" : "text-emerald-600 hover:text-emerald-700"
            }`}
            title={r.is_active ? "Deactivate account" : "Activate account"}
          >
            {r.is_active ? <X className="h-4 w-4" /> : <Check className="h-4 w-4" />}
          </button>
          <button
            onClick={() => setDeletingUser(r)}
            className="p-1 rounded hover:bg-red-50 dark:hover:bg-red-950/20 text-red-500 hover:text-red-600"
            title="Delete user"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <p className="text-[var(--text-muted)] text-sm mt-0.5">Create and manage internal staff accounts and assign system roles</p>
        </div>
        <Button onClick={() => setIsCreateOpen(true)} className="flex items-center gap-1.5">
          <UserPlus className="h-5 w-5" />
          Create Staff Account
        </Button>
      </div>

      {/* Stats Counter */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card padding={false}>
          <div className="flex items-center justify-between p-4 sm:p-6">
            <div>
              <p className="text-[12px] text-[var(--text-muted)] uppercase tracking-wider font-semibold">Total Staff</p>
              <p className="text-2xl font-bold text-[var(--text-primary)] mt-1">{usersList.length}</p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-blue-50 dark:bg-blue-950/30 flex items-center justify-center text-blue-600">
              <UserPlus className="h-5 w-5" />
            </div>
          </div>
        </Card>
        <Card padding={false}>
          <div className="flex items-center justify-between p-4 sm:p-6">
            <div>
              <p className="text-[12px] text-[var(--text-muted)] uppercase tracking-wider font-semibold">Active Staff</p>
              <p className="text-2xl font-bold text-emerald-600 mt-1">
                {usersList.filter((u: UserRecord) => u.is_active).length}
              </p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-emerald-50 dark:bg-emerald-950/30 flex items-center justify-center text-emerald-600">
              <Check className="h-5 w-5" />
            </div>
          </div>
        </Card>
        <Card padding={false}>
          <div className="flex items-center justify-between p-4 sm:p-6">
            <div>
              <p className="text-[12px] text-[var(--text-muted)] uppercase tracking-wider font-semibold">Inactive Staff</p>
              <p className="text-2xl font-bold text-red-500 mt-1">
                {usersList.filter((u: UserRecord) => !u.is_active).length}
              </p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-red-50 dark:bg-red-950/30 flex items-center justify-center text-red-500">
              <X className="h-5 w-5" />
            </div>
          </div>
        </Card>
      </div>

      {/* Main List Table */}
      <Card padding={false}>
        <div className="flex items-center gap-2 p-4 border-b border-[var(--border-color)]">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-[var(--text-muted)]" />
            <input
              type="text"
              placeholder="Search by name, username or email..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 border border-[var(--border-color)] rounded-lg text-[13px] bg-transparent focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <Button
            variant="secondary"
            onClick={() => mutate(`/users/${params}`)}
            disabled={isLoading || isValidating}
            className="flex items-center gap-1.5"
          >
            <RefreshCw className={`h-4 w-4 ${isValidating ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>

        <Table
          columns={columns}
          data={usersList}
          loading={isLoading}
          error={error}
          onRetry={() => mutate(`/users/${params}`)}
          emptyMessage="No staff accounts found matching search filters."
        />
      </Card>

      {/* Create Account Modal */}
      <Modal isOpen={isCreateOpen} onClose={() => setIsCreateOpen(false)} title="Create Staff Account" size="md">
        <form onSubmit={handleSubmitCreate(handleCreateUser)} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="First Name"
              placeholder="First name"
              error={errorsCreate.first_name?.message}
              {...registerCreate("first_name")}
            />
            <Input
              label="Last Name"
              placeholder="Last name"
              error={errorsCreate.last_name?.message}
              {...registerCreate("last_name")}
            />
          </div>

          <Input
            label="Username"
            placeholder="Username (must be unique)"
            error={errorsCreate.username?.message}
            {...registerCreate("username")}
          />

          <Input
            label="Email Address"
            type="email"
            placeholder="email@company.com"
            error={errorsCreate.email?.message}
            {...registerCreate("email")}
          />

          <div className="grid grid-cols-2 gap-4">
            <Select
              label="Role Assignment"
              error={errorsCreate.role?.message}
              options={roleOptions}
              {...registerCreate("role")}
            />

            <Input
              label="Branch Office"
              placeholder="Branch or HQ"
              error={errorsCreate.branch?.message}
              {...registerCreate("branch")}
            />
          </div>

          <Input
            label="Phone Number"
            placeholder="Contact number"
            error={errorsCreate.phone?.message}
            {...registerCreate("phone")}
          />

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Initial Password"
              type="password"
              placeholder="••••••••"
              error={errorsCreate.password?.message}
              {...registerCreate("password")}
            />
            <Input
              label="Confirm Password"
              type="password"
              placeholder="••••••••"
              error={errorsCreate.confirm_password?.message}
              {...registerCreate("confirm_password")}
            />
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <Button type="button" variant="secondary" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" loading={isSubmittingCreate}>
              Create Account
            </Button>
          </div>
        </form>
      </Modal>

      {/* Edit Account Modal */}
      <Modal isOpen={!!editingUser} onClose={() => setEditingUser(null)} title="Edit Staff Details" size="sm">
        {editingUser && (
          <div className="space-y-4">
            <p className="text-[13px] text-[var(--text-muted)]">
              Modifying details for <span className="font-semibold text-[var(--text-primary)]">{editingUser.first_name} {editingUser.last_name}</span> (@{editingUser.username})
            </p>

            <Select
              label="Role Assignment"
              value={editRole}
              onChange={(e) => setEditRole(e.target.value)}
              options={roleOptions}
            />

            <Input
              label="Branch Office"
              value={editBranch}
              onChange={(e) => setEditBranch(e.target.value)}
              placeholder="General HQ"
            />

            <Input
              label="Phone Number"
              value={editPhone}
              onChange={(e) => setEditPhone(e.target.value)}
              placeholder="Contact number"
            />

            <div className="flex justify-end gap-3 pt-4">
              <Button type="button" variant="secondary" onClick={() => setEditingUser(null)}>
                Cancel
              </Button>
              <Button type="button" variant="primary" onClick={handleUpdateUser} loading={isUpdating}>
                Save Changes
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={!!deletingUser}
        onClose={() => setDeletingUser(null)}
        onConfirm={handleDeleteUser}
        title="Delete Staff Account"
        message={`Are you sure you want to delete the account for ${deletingUser?.first_name} ${deletingUser?.last_name}? This action cannot be undone.`}
        confirmLabel="Delete Account"
        isDestructive={true}
        isLoading={isDeleting}
      />
    </div>
  );
}
