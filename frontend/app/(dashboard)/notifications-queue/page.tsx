"use client";

import { useState } from "react";
import useSWR, { useSWRConfig } from "swr";
import { 
  MessageSquare, Check, X, Send, Eye, RefreshCw, AlertTriangle, 
  Mail, MessageSquare as SmsIcon, CheckCircle2, ShieldAlert, Clock
} from "lucide-react";
import { fetcher, notificationsAPI } from "@/lib/api";
import { formatRelativeTime } from "@/lib/utils";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Spinner from "@/components/ui/Spinner";
import Badge from "@/components/ui/Badge";
import Table from "@/components/ui/Table";
import { useToast } from "@/components/ui/Toast";

interface DraftMessage {
  id: number;
  client: number;
  recipient_phone: string;
  recipient_email: string;
  channel: "SMS" | "EMAIL";
  comm_type: string;
  subject: string;
  body: string;
  ai_drafted: boolean;
  ai_rationale: string;
  status: "PENDING_APPROVAL" | "APPROVED" | "REJECTED" | "SENT" | "FAILED";
  rejection_reason?: string;
  approved_by_name?: string;
  created_at: string;
}

export default function NotificationsQueuePage() {
  const toast = useToast();
  const { mutate } = useSWRConfig();
  const [activeTab, setActiveTab] = useState<"pending" | "ready" | "history">("pending");
  const [selectedMessage, setSelectedMessage] = useState<DraftMessage | null>(null);
  const [rejectingMessageId, setRejectingMessageId] = useState<number | null>(null);
  const [rejectionReason, setRejectionReason] = useState("");
  const [actioningId, setActioningId] = useState<number | null>(null);

  // Fetch data
  const { data: pendingData, isLoading: pendingLoading, mutate: mutatePending } = useSWR<{ results: DraftMessage[] } | DraftMessage[]>(
    "/notifications/pending",
    fetcher
  );
  
  // SWR doesn't have custom views for outbox, so we query the main list with status filters
  const { data: allData, isLoading: allLoading, mutate: mutateAll } = useSWR<{ results: DraftMessage[] }>(
    "/notifications/queue",
    fetcher
  );

  const allMessages = allData?.results || (Array.isArray(allData) ? allData : []);
  
  const pendingMessages = pendingData?.results || (Array.isArray(pendingData) ? pendingData : []);
  const readyMessages = allMessages.filter(m => m.status === "APPROVED");
  const historyMessages = allMessages.filter(m => ["SENT", "FAILED", "REJECTED"].includes(m.status));

  const isLoading = activeTab === "pending" ? pendingLoading : allLoading;

  const handleRefresh = () => {
    mutatePending();
    mutateAll();
    toast.success("Queue refreshed");
  };

  const handleApprove = async (id: number) => {
    try {
      setActioningId(id);
      await notificationsAPI.approveDraft(id);
      toast.success("Draft message approved");
      mutatePending();
      mutateAll();
      if (selectedMessage?.id === id) {
        setSelectedMessage(null);
      }
    } catch (err) {
      toast.error("Failed to approve draft message");
    } finally {
      setActioningId(null);
    }
  };

  const handleRejectSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rejectionReason.trim() || !rejectingMessageId) return;

    try {
      setActioningId(rejectingMessageId);
      await notificationsAPI.rejectDraft(rejectingMessageId, { reason: rejectionReason });
      toast.success("Draft message rejected");
      setRejectingMessageId(null);
      setRejectionReason("");
      mutatePending();
      mutateAll();
      if (selectedMessage?.id === rejectingMessageId) {
        setSelectedMessage(null);
      }
    } catch (err) {
      toast.error("Failed to reject draft message");
    } finally {
      setActioningId(null);
    }
  };

  const handleSend = async (id: number) => {
    try {
      setActioningId(id);
      await notificationsAPI.sendDraft(id);
      toast.success("Message dispatched successfully");
      mutatePending();
      mutateAll();
      if (selectedMessage?.id === id) {
        setSelectedMessage(null);
      }
    } catch (err) {
      toast.error("Failed to dispatch message");
    } finally {
      setActioningId(null);
    }
  };

  const getChannelBadge = (channel: string) => {
    if (channel === "EMAIL") {
      return (
        <span className="inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-100">
          <Mail className="h-3 w-3" /> Email
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full bg-purple-50 text-purple-700 border border-purple-100">
        <SmsIcon className="h-3 w-3" /> SMS
      </span>
    );
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "PENDING_APPROVAL":
        return <Badge status="MEDIUM">Pending Approval</Badge>;
      case "APPROVED":
        return <Badge status="ACTIVE">Approved / Ready</Badge>;
      case "REJECTED":
        return <Badge status="CRITICAL">Rejected</Badge>;
      case "SENT":
        return <Badge status="SUCCESS">Sent</Badge>;
      case "FAILED":
        return <Badge status="CRITICAL">Failed</Badge>;
      default:
        return <Badge status="MEDIUM">{status}</Badge>;
    }
  };

  const columns = [
    {
      id: "type",
      header: "Comm Type",
      cell: (r: DraftMessage) => (
        <span className="font-semibold text-[13px] text-[var(--text-primary)]">
          {r.comm_type.replace(/_/g, " ")}
        </span>
      ),
    },
    {
      id: "channel",
      header: "Channel",
      cell: (r: DraftMessage) => getChannelBadge(r.channel),
    },
    {
      id: "recipient",
      header: "Recipient",
      cell: (r: DraftMessage) => (
        <div className="flex flex-col">
          <span className="text-[13px] font-medium text-[var(--text-primary)]">
            {r.channel === "EMAIL" ? r.recipient_email : r.recipient_phone}
          </span>
          <span className="text-[11px] text-[var(--text-muted)]">Client ID: #{r.client}</span>
        </div>
      ),
    },
    {
      id: "preview",
      header: "Draft Body",
      cell: (r: DraftMessage) => (
        <span className="text-[13px] text-[var(--text-secondary)] truncate max-w-xs block">
          {r.body}
        </span>
      ),
    },
    {
      id: "created",
      header: "Generated",
      cell: (r: DraftMessage) => (
        <span className="text-[12px] text-[var(--text-muted)]">
          {formatRelativeTime(r.created_at)}
        </span>
      ),
    },
    {
      id: "status",
      header: "Status",
      cell: (r: DraftMessage) => getStatusBadge(r.status),
    },
    {
      id: "actions",
      header: "",
      cell: (r: DraftMessage) => (
        <div className="flex items-center gap-1.5 justify-end">
          <Button
            size="sm"
            variant="ghost"
            icon={<Eye className="h-3.5 w-3.5" />}
            onClick={() => setSelectedMessage(r)}
          >
            Review
          </Button>
          {r.status === "PENDING_APPROVAL" && (
            <>
              <Button
                size="sm"
                variant="outline"
                className="text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50 border-emerald-200"
                icon={<Check className="h-3.5 w-3.5" />}
                onClick={() => handleApprove(r.id)}
                disabled={actioningId !== null}
              />
              <Button
                size="sm"
                variant="outline"
                className="text-red-600 hover:text-red-700 hover:bg-red-50 border-red-200"
                icon={<X className="h-3.5 w-3.5" />}
                onClick={() => setRejectingMessageId(r.id)}
                disabled={actioningId !== null}
              />
            </>
          )}
          {r.status === "APPROVED" && (
            <Button
              size="sm"
              variant="primary"
              icon={<Send className="h-3.5 w-3.5" />}
              onClick={() => handleSend(r.id)}
              disabled={actioningId !== null}
            >
              Send
            </Button>
          )}
        </div>
      ),
    },
  ];

  const currentMessages = 
    activeTab === "pending" ? pendingMessages :
    activeTab === "ready" ? readyMessages :
    historyMessages;

  return (
    <div className="flex flex-col gap-4 pb-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <p className="text-[var(--text-muted)] text-sm mt-0.5">
            Approve AI-drafted client communications (A6) before Twilio or Email dispatch
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="secondary"
            onClick={handleRefresh}
            className="flex items-center gap-1.5"
            disabled={isLoading}
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
            Refresh Queue
          </Button>
        </div>
      </div>

      <div className="flex border-b border-gray-200 px-4 gap-4">
        <button
          onClick={() => setActiveTab("pending")}
          className={`text-sm font-medium py-2.5 px-1 border-b-2 transition-all relative ${
            activeTab === "pending" ? "border-blue-500 text-blue-600 font-semibold" : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
        >
          Pending Approval
          {pendingMessages.length > 0 && (
            <span className="ml-1.5 px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800">
              {pendingMessages.length}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab("ready")}
          className={`text-sm font-medium py-2.5 px-1 border-b-2 transition-all relative ${
            activeTab === "ready" ? "border-blue-500 text-blue-600 font-semibold" : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
        >
          Ready to Send
          {readyMessages.length > 0 && (
            <span className="ml-1.5 px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">
              {readyMessages.length}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab("history")}
          className={`text-sm font-medium py-2.5 px-1 border-b-2 transition-all ${
            activeTab === "history" ? "border-blue-500 text-blue-600 font-semibold" : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
        >
          Outbox / History
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card title={`${activeTab === "pending" ? "Pending Approval" : activeTab === "ready" ? "Approved Queue" : "Sent / History"}`}>
            {isLoading ? (
              <div className="flex justify-center py-12">
                <Spinner size="lg" />
              </div>
            ) : (
              <Table 
                columns={columns} 
                data={currentMessages} 
                emptyMessage={`No messages found in the ${activeTab} queue.`} 
              />
            )}
          </Card>
        </div>

        {/* Detail Panel */}
        <div className="lg:col-span-1">
          {selectedMessage ? (
            <Card title="Draft Review Panel">
              <div className="space-y-4">
                <div className="p-3 bg-gray-50 rounded-lg space-y-2 border border-gray-100">
                  <div className="flex justify-between items-center">
                    <span className="text-[12px] font-semibold text-gray-400">STATUS</span>
                    {getStatusBadge(selectedMessage.status)}
                  </div>
                  <div className="flex justify-between items-center text-[13px]">
                    <span className="text-gray-500">Comm Type</span>
                    <span className="font-semibold">{selectedMessage.comm_type.replace(/_/g, " ")}</span>
                  </div>
                  <div className="flex justify-between items-center text-[13px]">
                    <span className="text-gray-500">Channel</span>
                    {getChannelBadge(selectedMessage.channel)}
                  </div>
                  <div className="flex justify-between items-center text-[13px]">
                    <span className="text-gray-500">Recipient</span>
                    <span className="font-medium text-[var(--text-primary)]">
                      {selectedMessage.channel === "EMAIL" ? selectedMessage.recipient_email : selectedMessage.recipient_phone}
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-[13px]">
                    <span className="text-gray-500">Generated</span>
                    <span className="text-gray-600">{new Date(selectedMessage.created_at).toLocaleString()}</span>
                  </div>
                  {selectedMessage.approved_by_name && (
                    <div className="flex justify-between items-center text-[13px]">
                      <span className="text-gray-500">Approved By</span>
                      <span className="font-medium text-emerald-600">{selectedMessage.approved_by_name}</span>
                    </div>
                  )}
                  {selectedMessage.rejection_reason && (
                    <div className="p-2.5 mt-2 bg-red-50 border border-red-100 rounded text-[12px] text-red-700">
                      <span className="font-semibold block">REJECTION REASON:</span>
                      {selectedMessage.rejection_reason}
                    </div>
                  )}
                </div>

                <div className="space-y-1.5">
                  <span className="text-[12px] font-semibold text-gray-400">MESSAGE CONTENT</span>
                  {selectedMessage.channel === "EMAIL" && (
                    <div className="p-2 border rounded bg-white text-[13px] font-semibold">
                      Subject: {selectedMessage.subject || "(No Subject)"}
                    </div>
                  )}
                  <div className="p-3 border rounded-lg bg-white text-[13px] min-h-[100px] whitespace-pre-wrap leading-relaxed shadow-sm">
                    {selectedMessage.body}
                  </div>
                </div>

                {selectedMessage.ai_drafted && selectedMessage.ai_rationale && (
                  <div className="p-3 bg-blue-50/50 border border-blue-100 rounded-lg space-y-1">
                    <span className="text-[12px] font-semibold text-blue-700 flex items-center gap-1">
                      <MessageSquare className="h-3.5 w-3.5" /> A6 Drafting Rationale
                    </span>
                    <p className="text-[12px] text-blue-900/80 leading-relaxed">
                      {selectedMessage.ai_rationale}
                    </p>
                  </div>
                )}

                <div className="flex gap-2 pt-2">
                  {selectedMessage.status === "PENDING_APPROVAL" && (
                    <>
                      <Button
                        variant="primary"
                        className="flex-1 bg-emerald-600 hover:bg-emerald-700"
                        icon={<Check className="h-4 w-4" />}
                        onClick={() => handleApprove(selectedMessage.id)}
                        disabled={actioningId !== null}
                      >
                        Approve
                      </Button>
                      <Button
                        variant="outline"
                        className="text-red-600 hover:text-red-700 hover:bg-red-50 border-red-200"
                        icon={<X className="h-4 w-4" />}
                        onClick={() => setRejectingMessageId(selectedMessage.id)}
                        disabled={actioningId !== null}
                      >
                        Reject
                      </Button>
                    </>
                  )}
                  {selectedMessage.status === "APPROVED" && (
                    <Button
                      variant="primary"
                      className="w-full"
                      icon={<Send className="h-4 w-4" />}
                      onClick={() => handleSend(selectedMessage.id)}
                      disabled={actioningId !== null}
                    >
                      Dispatch Message
                    </Button>
                  )}
                </div>
              </div>
            </Card>
          ) : (
            <div className="h-full flex flex-col items-center justify-center p-8 border border-dashed rounded-xl bg-gray-50/50 text-center py-20">
              <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center text-gray-400 mb-3">
                <MessageSquare className="h-5 w-5" />
              </div>
              <h3 className="text-sm font-semibold text-gray-700">No Draft Selected</h3>
              <p className="text-[12px] text-gray-500 max-w-[200px] mt-1">
                Select a message draft from the list on the left to review drafting details.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Reject Modal */}
      {rejectingMessageId && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl border border-gray-100 max-w-md w-full overflow-hidden animate-fade-in">
            <div className="px-6 py-4 border-b flex justify-between items-center bg-gray-50">
              <h3 className="font-semibold text-[15px] flex items-center gap-1.5 text-gray-800">
                <AlertTriangle className="h-4 w-4 text-red-600" /> Reject Draft Message
              </h3>
              <button onClick={() => setRejectingMessageId(null)} className="text-gray-400 hover:text-gray-600">
                <X className="h-4 w-4" />
              </button>
            </div>
            <form onSubmit={handleRejectSubmit}>
              <div className="p-6 space-y-4">
                <p className="text-[13px] text-gray-600">
                  Please provide a brief reason for rejecting this communication draft. This helps document audit trails.
                </p>
                <div className="space-y-1.5">
                  <label className="text-[12px] font-semibold text-gray-400">REJECTION REASON</label>
                  <textarea
                    required
                    value={rejectionReason}
                    onChange={(e) => setRejectionReason(e.target.value)}
                    placeholder="e.g., Client preferred language is wrong, or late fee needs adjustment."
                    className="w-full min-h-[90px] p-3 border rounded-lg text-[13px] focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 leading-normal"
                  />
                </div>
              </div>
              <div className="px-6 py-4 bg-gray-50 border-t flex justify-end gap-2">
                <Button variant="secondary" onClick={() => setRejectingMessageId(null)}>Cancel</Button>
                <Button variant="primary" className="bg-red-600 hover:bg-red-700" type="submit" disabled={actioningId !== null}>
                  Confirm Reject
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
