"use client";

import { useState } from "react";
import useSWR, { useSWRConfig } from "swr";
import { Bell, Check, CheckSquare, RefreshCw, AlertTriangle, Info, CheckCircle, ShieldAlert } from "lucide-react";
import { fetcher, notificationsAPI } from "@/lib/api";
import { formatRelativeTime } from "@/lib/utils";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Spinner from "@/components/ui/Spinner";
import { useToast } from "@/components/ui/Toast";

interface Notification {
  id: number;
  title: string;
  message: string;
  notification_type: string;
  is_read: boolean;
  created_at: string;
}

export default function NotificationsPage() {
  const toast = useToast();
  const { mutate } = useSWRConfig();
  const [filter, setFilter] = useState<"all" | "unread">("all");
  const params = filter === "unread" ? "?is_read=false" : "";
  const { data, error, isLoading, isValidating } = useSWR<{ results: Notification[] }>(
    `/notifications${params}`,
    fetcher,
    { refreshInterval: 15000 }
  );

  const notifications = data?.results || (Array.isArray(data) ? data : []);

  const handleMarkAsRead = async (id: number) => {
    try {
      await notificationsAPI.markRead(id);
      toast.success("Notification marked as read");
      mutate(`/notifications${params}`);
      mutate("/notifications");
    } catch (err) {
      toast.error("Failed to mark notification as read");
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationsAPI.markAllRead();
      toast.success("All notifications marked as read");
      mutate(`/notifications${params}`);
      mutate("/notifications");
    } catch (err) {
      toast.error("Failed to mark all as read");
    }
  };

  const getIcon = (type: string) => {
    switch (type) {
      case "FRAUD_ALERT":
      case "ERROR":
        return <ShieldAlert className="h-5 w-5 text-red-600" />;
      case "LOAN_STATUS":
      case "WARNING":
        return <AlertTriangle className="h-5 w-5 text-amber-600" />;
      case "APPROVAL_REQUIRED":
      case "SUCCESS":
        return <CheckCircle className="h-5 w-5 text-emerald-600" />;
      case "INFO":
      default:
        return <Info className="h-5 w-5 text-blue-600" />;
    }
  };

  const getTypeStyle = (type: string) => {
    switch (type) {
      case "FRAUD_ALERT":
      case "ERROR":
        return "bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-900/30";
      case "LOAN_STATUS":
      case "WARNING":
        return "bg-amber-50 dark:bg-amber-950/20 border-amber-200 dark:border-amber-900/30";
      case "APPROVAL_REQUIRED":
      case "SUCCESS":
        return "bg-emerald-50 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-900/30";
      case "INFO":
      default:
        return "bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-900/30";
    }
  };

  return (
    <div className="flex flex-col gap-4 pb-6"> {/* FIX[BUG 1]: removed h-full p-6 added pb-6 */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"> {/* FIX[BUG 1]: removed flex-shrink-0 */}
        <div>
          <p className="text-[var(--text-muted)] text-sm mt-0.5">Stay updated on system activities, loan approvals, and compliance alerts</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="secondary"
            onClick={() => mutate(`/notifications${params}`)}
            className="flex items-center gap-1.5"
            disabled={isLoading || isValidating}
          >
            <RefreshCw className={`h-4 w-4 ${isValidating ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Button
            variant="primary"
            onClick={handleMarkAllRead}
            disabled={notifications.length === 0 || !notifications.some(n => !n.is_read)}
            className="flex items-center gap-1.5"
          >
            <CheckSquare className="h-4 w-4" />
            Mark All Read
          </Button>
        </div>
      </div>

      <div className="flex border-b border-gray-200 px-4 gap-4"> {/* FIX[BUG 1]: removed flex-shrink-0 */}
        <button
          onClick={() => setFilter("all")}
          className={`text-sm font-medium py-2.5 px-1 border-b-2 transition-all ${
            filter === "all" ? "border-blue-500 text-blue-600 animate-fade-in" : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
        >
          All
        </button>
        <button
          onClick={() => setFilter("unread")}
          className={`text-sm font-medium py-2.5 px-1 border-b-2 transition-all ${
            filter === "unread" ? "border-blue-500 text-blue-600 animate-fade-in" : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
        >
          Unread
        </button>
      </div>

      <div> {/* FIX[BUG 9]: removed flex-1 overflow-y-auto */}
        {isLoading ? (
          <div className="flex justify-center py-12">
            <Spinner size="lg" />
          </div>
        ) : notifications.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-3 text-center py-20">
            <div className="w-14 h-14 rounded-full bg-gray-100 flex items-center justify-center text-gray-400">
              <Bell className="h-6 w-6" />
            </div>
            <h3 className="text-base font-semibold text-[var(--text-primary)]">All caught up!</h3>
            <p className="text-[var(--text-muted)] text-sm max-w-sm mt-1">
              You don&apos;t have any {filter === "unread" ? "unread " : ""}notifications at this moment.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {notifications.map((notification) => (
              <Card
                key={notification.id}
                className={`border-l-4 transition-all duration-200 ${
                  notification.is_read
                    ? "border-gray-200 dark:border-zinc-700 bg-white dark:bg-zinc-950 opacity-75"
                    : `${getTypeStyle(notification.notification_type)}`
                }`}
              >
                <div className="flex gap-4">
                  <div className="mt-0.5 flex-shrink-0">{getIcon(notification.notification_type)}</div> {/* FIX[BUG 15]: added flex-shrink-0 */}
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1">
                      <p className={`text-[14px] font-semibold ${
                        notification.is_read ? "text-[var(--text-primary)]" : "text-[var(--text-primary)] font-bold"
                      }`}>
                        {notification.title}
                      </p>
                      <span className="text-[12px] text-[var(--text-muted)]">
                        {formatRelativeTime(notification.created_at)}
                      </span>
                    </div>
                    <p className="text-[13px] text-[var(--text-secondary)] mt-1 break-words">
                      {notification.message}
                    </p>
                  </div>
                  {!notification.is_read && (
                    <button
                      onClick={() => handleMarkAsRead(notification.id)}
                      className="p-1 rounded-md hover:bg-black/5 dark:hover:bg-white/5 text-[var(--text-secondary)] transition-all flex-shrink-0 self-center"
                      title="Mark as read"
                    >
                      <Check className="h-4 w-4" />
                    </button>
                  )}
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
