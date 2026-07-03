"use client";

import { useState, useEffect } from "react";
import useSWR from "swr";
import {
  Brain, ShieldAlert, CheckCircle, AlertTriangle, Play, Pause,
  Sliders, Activity, ShieldCheck, History, RefreshCw, Layers, CheckSquare
} from "lucide-react";
import { auditAPI, fetcher } from "@/lib/api";
import { formatRelativeTime } from "@/lib/utils";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import Table from "@/components/ui/Table";
import { useToast } from "@/components/ui/Toast";
import { usePermissions } from "@/lib/permissions";

const AGENT_NAMES: Record<string, string> = {
  A1: "Data Collection Agent",
  A2: "Risk Assessment Agent",
  A3: "Recommendation Agent",
  A4: "Monitoring Agent",
  A5: "Fraud Detection Agent",
  A6: "Communication Agent",
};

const AGENT_DESCRIPTIONS: Record<string, string> = {
  A1: "Validates completeness and internal consistency of KYC applications.",
  A2: "Calculates borrower credit risk using multi-factor financial metrics.",
  A3: "Formulates explainable loan approval or adjustment recommendations.",
  A4: "Performs daily automated delinquency scans on active repayment schedules.",
  A5: "Identifies early behavioral indicators of identity theft or application fraud.",
  A6: "Drafts tailored notifications in English, Sinhala, or Tamil.",
};

export default function AIControlPanelPage() {
  const { can, isAdmin, isBranchManager, isRiskAnalyst, isComplianceOfficer } = usePermissions();
  const toast = useToast();
  
  const [activeTab, setActiveTab] = useState<"agents" | "incidents" | "reviews" | "audit">("agents");
  const [selectedAgent, setSelectedAgent] = useState<string>("A2");
  const [savingAgentId, setSavingAgentId] = useState<string | null>(null);

  // Form states for selected agent configuration override
  const [llmEnabled, setLlmEnabled] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [pauseReason, setPauseReason] = useState("");
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.65);
  const [modelOverride, setModelOverride] = useState("");
  const [dailyTokenBudget, setDailyTokenBudget] = useState<number | "">("");
  const [changeReason, setChangeReason] = useState("");

  // SWR fetches
  const { data: configs, error: configErr, isLoading: configLoading, mutate: mutateConfigs } = useSWR(
    can("audit:read") ? "/audit/agent-config/" : null,
    fetcher
  );
  
  const { data: health, error: healthErr, mutate: mutateHealth } = useSWR(
    can("audit:read") ? "/audit/ai/health/" : null,
    fetcher
  );

  const { data: performance, mutate: mutatePerformance } = useSWR(
    can("audit:read") ? `/audit/agent-performance/${selectedAgent}/` : null,
    fetcher
  );

  const { data: incidents, mutate: mutateIncidents } = useSWR(
    can("audit:read") && activeTab === "incidents" ? "/audit/system/incidents/" : null,
    fetcher
  );

  const { data: reviews, mutate: mutateReviews } = useSWR(
    can("audit:read") && activeTab === "reviews" ? "/audit/system/manual-review/" : null,
    fetcher
  );

  const { data: auditLogs, mutate: mutateLogs } = useSWR(
    can("audit:read") && activeTab === "audit" ? "/audit/agent-config-logs/" : null,
    fetcher
  );

  // Synchronize form values when selected agent changes
  useEffect(() => {
    if (configs && Array.isArray(configs)) {
      const cfg = configs.find((c: any) => c.agent_id === selectedAgent);
      if (cfg) {
        setLlmEnabled(cfg.llm_enabled);
        setIsPaused(cfg.is_paused);
        setPauseReason(cfg.pause_reason || "");
        setConfidenceThreshold(cfg.confidence_threshold);
        setModelOverride(cfg.model_override || "");
        setDailyTokenBudget(cfg.daily_token_budget || "");
        setChangeReason("");
      }
    }
  }, [selectedAgent, configs]);

  if (!can("audit:read")) {
    return (
      <Card className="flex flex-col items-center justify-center text-center py-16 max-w-md mx-auto">
        <div className="w-12 h-12 rounded-full bg-red-100 dark:bg-red-950/30 flex items-center justify-center mb-3">
          <ShieldAlert className="h-6 w-6 text-red-600" />
        </div>
        <h3 className="text-lg font-bold text-[var(--text-primary)]">Access Denied</h3>
        <p className="text-[var(--text-muted)] text-sm mt-2">
          You do not have permission to access the AI Agent Control Panel.
        </p>
      </Card>
    );
  }

  const handleToggleManualMode = async () => {
    try {
      if (health?.manual_mode) {
        await auditAPI.disableManualMode();
        toast.success("System manual mode disabled. AI operations restored.");
      } else {
        await auditAPI.enableManualMode();
        toast.success("System manual mode enabled. All AI agents bypassed.");
      }
      mutateHealth();
    } catch (err) {
      toast.error("Failed to update manual mode override.");
    }
  };

  const handleSaveConfig = async () => {
    try {
      setSavingAgentId(selectedAgent);
      const payload = {
        llm_enabled: llmEnabled,
        is_paused: isPaused,
        pause_reason: isPaused ? pauseReason : "",
        confidence_threshold: confidenceThreshold,
        model_override: modelOverride,
        daily_token_budget: dailyTokenBudget === "" ? null : Number(dailyTokenBudget),
        change_reason: changeReason || "Updated via Admin Control Panel",
      };

      await auditAPI.updateAgentConfig(selectedAgent, payload);
      toast.success(`Configuration for agent ${selectedAgent} updated successfully.`);
      mutateConfigs();
      mutateLogs();
    } catch (err) {
      toast.error("Failed to update agent configuration.");
    } finally {
      setSavingAgentId(null);
    }
  };

  const handleResolveIncident = async (incidentId: number) => {
    try {
      await auditAPI.resolveIncident(incidentId);
      toast.success("Incident resolved successfully.");
      mutateIncidents();
    } catch (err) {
      toast.error("Failed to resolve incident.");
    }
  };

  const handleRetryReview = async (caseId: number) => {
    try {
      const res = await auditAPI.retryAIRequest(caseId);
      toast.success(res.data?.message || "AI execution retried successfully.");
      mutateReviews();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to retry AI execution.");
    }
  };

  const handleManualDecision = async (caseId: number, decision: string) => {
    try {
      await auditAPI.submitManualReview(caseId, {
        manual_decision: decision,
        manual_notes: "Resolved via AI Control Panel override"
      });
      toast.success("Human decision saved and applied.");
      mutateReviews();
    } catch (err) {
      toast.error("Failed to submit manual decision.");
    }
  };

  // Safe health status
  const aiHealthStatus = health?.ai_service || "UNKNOWN";
  const manualModeActive = health?.manual_mode || false;

  return (
    <div className="space-y-6">
      {/* Top Banner: Service Status & Global Override */}
      <Card className="overflow-hidden relative shadow-sm border-gray-200 bg-white transition-all duration-300 hover:shadow-md">
        <div className="absolute top-0 left-0 w-1.5 h-full bg-gradient-to-b from-blue-500 to-indigo-600" />
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 p-1">
          <div className="flex items-center gap-3">
            <div className={`p-2.5 rounded-xl flex items-center justify-center flex-shrink-0 ${
              manualModeActive ? "bg-amber-100 text-amber-700" :
              aiHealthStatus === "ONLINE" ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"
            }`}>
              <Brain className="h-6 w-6 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-[16px] font-extrabold text-[var(--text-primary)]">
                  AI Orchestrator Services
                </h2>
                <Badge
                  status={manualModeActive ? "MANUAL_MODE_ACTIVE" : aiHealthStatus}
                  className="px-2.5 py-0.5 text-[10px] font-bold tracking-wide uppercase"
                />
              </div>
              <p className="text-[13px] text-[var(--text-muted)] mt-0.5">
                {manualModeActive
                  ? "SYSTEM OVERRIDE ACTIVE: All AI agents are fully bypassed. Running local rules fallback."
                  : `AI agents are communicating with the server. Consec. failures: ${health?.consecutive_failures || 0}`}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              icon={<RefreshCw className="h-4 w-4" />}
              onClick={() => {
                mutateHealth();
                mutateConfigs();
              }}
            >
              Sync status
            </Button>
            <Button
              variant={manualModeActive ? "primary" : "danger"}
              size="sm"
              disabled={!isAdmin && !isBranchManager}
              icon={manualModeActive ? <Play className="h-4 w-4" /> : <Pause className="h-4 w-4" />}
              onClick={handleToggleManualMode}
            >
              {manualModeActive ? "Resume AI Agents" : "Activate Emergency Fallback"}
            </Button>
          </div>
        </div>
      </Card>

      {/* Tabs Menu */}
      <div className="flex border-b border-[var(--border-color)] gap-2 md:gap-4 overflow-x-auto pb-px">
        {[
          { id: "agents", label: "Agent Configurations", icon: <Sliders className="h-4 w-4" /> },
          {
            id: "reviews",
            label: "Manual Review Gate",
            icon: <CheckSquare className="h-4 w-4" />,
            badge: reviews && reviews.length > 0 ? reviews.length : null,
            badgeColor: "bg-red-500 text-white"
          },
          {
            id: "incidents",
            label: "System Incidents",
            icon: <Activity className="h-4 w-4" />,
            badge: incidents && incidents.filter((i: any) => i.status === "OPEN").length > 0 ? incidents.filter((i: any) => i.status === "OPEN").length : null,
            badgeColor: "bg-amber-500 text-white"
          },
          { id: "audit", label: "Config Audit Trail", icon: <History className="h-4 w-4" /> }
        ].map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`pb-3 pt-1 px-3 text-sm font-semibold relative transition-all duration-300 whitespace-nowrap flex items-center gap-2 border-b-2 -mb-[2px] ${
                isActive
                  ? "text-blue-600 border-blue-600 scale-[1.02]"
                  : "text-[var(--text-muted)] border-transparent hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              {tab.icon}
              <span>{tab.label}</span>
              {tab.badge !== null && (
                <span className={`rounded-full text-[10px] px-2 py-0.5 font-bold animate-pulse ${tab.badgeColor}`}>
                  {tab.badge}
                </span>
              )}
              {isActive && (
                <span className="absolute bottom-0 left-1/2 -translate-x-1/2 w-6 h-1 bg-blue-500 rounded-full blur-[2px]" />
              )}
            </button>
          );
        })}
      </div>

      {/* Tab Contents: Agents Config Grid */}
      {activeTab === "agents" && (
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* List of Agents */}
          <div className="xl:col-span-1 space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)] mb-2 flex items-center gap-1.5">
              <Layers className="h-4 w-4" />
              System Agents
            </h3>
            {configs && Array.isArray(configs) ? (
              configs.map((c: any) => {
                const isSelected = selectedAgent === c.agent_id;
                return (
                  <div
                    key={c.agent_id}
                    onClick={() => setSelectedAgent(c.agent_id)}
                    className={`p-4 rounded-xl border transition-all duration-300 cursor-pointer relative overflow-hidden bg-white ${
                      isSelected
                        ? "border-blue-500 bg-gradient-to-br from-blue-50/20 to-indigo-50/5 ring-2 ring-blue-500/10 shadow-md scale-[1.01]"
                        : "border-gray-200 hover:border-blue-400/60 hover:shadow-sm"
                    }`}
                  >
                    {isSelected && (
                      <div className="absolute top-0 left-0 w-1 h-full bg-blue-500" />
                    )}
                    <div className="flex items-start justify-between">
                      <div className="min-w-0">
                        <span className="font-mono text-[10px] font-bold px-2 py-0.5 bg-gray-100 text-gray-700 rounded-md">
                          {c.agent_id}
                        </span>
                        <h4 className="font-semibold text-[14px] text-[var(--text-primary)] mt-2 truncate">
                          {AGENT_NAMES[c.agent_id]}
                        </h4>
                      </div>
                      <Badge
                        status={c.is_paused ? "PAUSED" : c.llm_enabled ? "AI_HYBRID" : "RULES_ONLY"}
                        className="text-[9px] uppercase tracking-wider font-bold"
                      />
                    </div>
                    <p className="text-[12px] text-[var(--text-muted)] leading-relaxed mt-2 line-clamp-2">
                      {AGENT_DESCRIPTIONS[c.agent_id]}
                    </p>
                  </div>
                );
              })
            ) : (
              <div className="text-sm text-[var(--text-muted)] p-4 text-center">Loading agents configurations...</div>
            )}
          </div>

          {/* Selected Agent Control Board */}
          <div className="xl:col-span-2 space-y-6">
            <Card 
              title={`${selectedAgent} — Control Panel Board`} 
              subtitle={AGENT_NAMES[selectedAgent]}
              className="shadow-sm hover:shadow-md transition-all duration-300 border-gray-200"
            >
              <div className="space-y-6 mt-4">
                {/* 1. Toggle switches */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 rounded-xl bg-gray-50/50 border border-gray-100">
                  <div className="flex items-start justify-between gap-4 p-2 rounded-lg hover:bg-white transition-all duration-200">
                    <div className="space-y-0.5">
                      <label className="text-[13px] font-bold text-[var(--text-primary)] flex items-center gap-1.5">
                        <Sliders className="h-3.5 w-3.5 text-blue-500" />
                        Enable LLM Mode
                      </label>
                      <p className="text-[11px] text-[var(--text-muted)] leading-normal">
                        Deterministic local rules fallback when disabled.
                      </p>
                    </div>
                    <label className={`relative inline-flex items-center mt-1 ${isAdmin ? "cursor-pointer" : "cursor-not-allowed opacity-60"}`}>
                      <input
                        type="checkbox"
                        checked={llmEnabled}
                        disabled={!isAdmin}
                        onChange={(e) => setLlmEnabled(e.target.checked)}
                        className="sr-only peer"
                      />
                      <div className="w-9 h-5 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>

                  <div className="flex items-start justify-between gap-4 p-2 rounded-lg hover:bg-white transition-all duration-200">
                    <div className="space-y-0.5">
                      <label className="text-[13px] font-bold text-[var(--text-primary)] flex items-center gap-1.5">
                        <AlertTriangle className="h-3.5 w-3.5 text-red-500" />
                        Emergency Pause
                      </label>
                      <p className="text-[11px] text-[var(--text-muted)] leading-normal">
                        Bypass this agent, route to fallback, and queue reviews.
                      </p>
                    </div>
                    <label className={`relative inline-flex items-center mt-1 ${isAdmin ? "cursor-pointer" : "cursor-not-allowed opacity-60"}`}>
                      <input
                        type="checkbox"
                        checked={isPaused}
                        disabled={!isAdmin}
                        onChange={(e) => setIsPaused(e.target.checked)}
                        className="sr-only peer"
                      />
                      <div className="w-9 h-5 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-red-600"></div>
                    </label>
                  </div>
                </div>

                {/* 2. Pause Reason input */}
                {isPaused && (
                  <div className="space-y-1.5 p-3 rounded-xl bg-red-50/50 border border-red-100">
                    <label className="text-[12px] font-bold text-red-600 flex items-center gap-1">
                      <AlertTriangle className="h-3.5 w-3.5" />
                      Reason for Pause *
                    </label>
                    <textarea
                      required
                      disabled={!isAdmin}
                      placeholder="Explain why this agent is being paused. This will be shown to users and logged in the audits."
                      value={pauseReason}
                      onChange={(e) => setPauseReason(e.target.value)}
                      className="w-full text-[13px] p-2.5 border rounded-xl focus:ring-2 focus:ring-red-500/10 focus:border-red-500 placeholder-gray-400 bg-white"
                      rows={2}
                    />
                  </div>
                )}

                {/* 3. Slider Threshold & Override inputs */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2 p-3 rounded-xl bg-gray-50/30 border border-gray-100/55">
                    <div className="flex justify-between items-center">
                      <label className="text-[13px] font-bold text-[var(--text-primary)] flex items-center gap-1.5">
                        <Sliders className="h-3.5 w-3.5 text-blue-500" />
                        LLM Confidence Threshold
                      </label>
                      <span className="font-mono text-[12px] font-extrabold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-md border border-blue-100">
                        {confidenceThreshold.toFixed(2)}
                      </span>
                    </div>
                    <p className="text-[11px] text-[var(--text-muted)] leading-normal">
                      Low confidence triggers the manual review gate.
                    </p>
                    <div className="pt-2">
                      <input
                        type="range"
                        min="0.30"
                        max="0.95"
                        step="0.05"
                        value={confidenceThreshold}
                        disabled={!isAdmin}
                        onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value))}
                        className={`w-full h-1.5 bg-gray-200 rounded-lg appearance-none accent-blue-600 focus:outline-none ${isAdmin ? "cursor-pointer" : "cursor-not-allowed"}`}
                      />
                    </div>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-[13px] font-bold text-[var(--text-primary)]">
                      Model Route Override
                    </label>
                    <p className="text-[11px] text-[var(--text-muted)] mt-0.5">
                      Force agent to call a specific LLM instead of default config.
                    </p>
                    <select
                      value={modelOverride}
                      disabled={!isAdmin}
                      onChange={(e) => setModelOverride(e.target.value)}
                      className="w-full text-[13px] p-2.5 border rounded-xl focus:ring-2 focus:ring-blue-500/10 focus:border-blue-500 bg-white"
                    >
                      <option value="">Default (System Managed)</option>
                      <option value="gemini-2.5-flash">Gemini 2.5 Flash</option>
                      <option value="qwen-2.5-72b-instruct">Qwen 2.5 72B Instruct</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-1.5">
                    <label className="text-[13px] font-bold text-[var(--text-primary)]">
                      Daily Token Budget
                    </label>
                    <p className="text-[11px] text-[var(--text-muted)] mt-0.5">
                      Max tokens allocated today. Leave blank/unlimited for default.
                    </p>
                    <input
                      type="number"
                      placeholder="Unlimited"
                      value={dailyTokenBudget}
                      disabled={!isAdmin}
                      onChange={(e) => setDailyTokenBudget(e.target.value === "" ? "" : Number(e.target.value))}
                      className="w-full text-[13px] p-2.5 border rounded-xl focus:ring-2 focus:ring-blue-500/10 focus:border-blue-500 bg-white"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-[13px] font-bold text-[var(--text-primary)]">
                      Policy Change Justification *
                    </label>
                    <p className="text-[11px] text-[var(--text-muted)] mt-0.5">
                      Document the reason for this configuration change.
                    </p>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Scaling up testing / Emergency pause"
                      value={changeReason}
                      disabled={!isAdmin}
                      onChange={(e) => setChangeReason(e.target.value)}
                      className="w-full text-[13px] p-2.5 border rounded-xl focus:ring-2 focus:ring-blue-500/10 focus:border-blue-500 bg-white"
                    />
                  </div>
                </div>

                {/* Save Buttons */}
                <div className="flex justify-end gap-2 pt-4 border-t border-[var(--border-color)]">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={!isAdmin}
                    onClick={() => mutateConfigs()}
                  >
                    Reset
                  </Button>
                  <Button
                    variant="primary"
                    size="sm"
                    loading={savingAgentId === selectedAgent}
                    disabled={!isAdmin || (isPaused && !pauseReason)}
                    onClick={handleSaveConfig}
                  >
                    Apply Config Settings
                  </Button>
                </div>
              </div>
            </Card>

            {/* Performance charts area */}
            {performance && (
              <Card title="Agent Running Insights" subtitle="Daily average confidence over last 30 days">
                <div className="mt-4">
                  <div className="flex items-end gap-2 h-44 border-b border-gray-100 pb-2">
                    {performance.daily_stats && performance.daily_stats.length > 0 ? (
                      performance.daily_stats.map((stat: any, idx: number) => {
                        const score = (stat.avg_confidence || 0) * 100;
                        return (
                          <div key={idx} className="flex-1 h-full flex flex-col justify-end items-center gap-1 group relative">
                            <div 
                              className="w-full bg-gradient-to-t from-blue-600 to-indigo-500 hover:from-blue-500 hover:to-indigo-400 rounded-t-md transition-all duration-300 shadow-sm shadow-blue-500/10 hover:shadow-md hover:shadow-blue-500/20" 
                              style={{ height: `${score}%` }} 
                            />
                            <span className="text-[9px] text-[var(--text-muted)] select-none font-medium">
                              {stat.day.split("-")[2]}
                            </span>
                            <div className="absolute -top-10 bg-gray-950 text-white text-[10px] px-2.5 py-1.5 rounded-lg opacity-0 group-hover:opacity-100 transition-all duration-200 whitespace-nowrap z-10 pointer-events-none shadow-md border border-gray-700/50 scale-95 group-hover:scale-100 transform origin-bottom">
                              <span className="font-extrabold text-blue-400">{score.toFixed(0)}%</span> Conf ({stat.call_count} call)
                            </div>
                          </div>
                        );
                      })
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-sm text-[var(--text-muted)]">
                        No performance log data registered yet.
                      </div>
                    )}
                  </div>
                  {performance.override_data && (
                    <div className="grid grid-cols-3 gap-4 mt-4 text-center">
                      <div className="p-3 bg-gradient-to-b from-gray-50/50 to-gray-50/10 rounded-xl border border-gray-100 transition-all duration-300 hover:shadow-sm">
                        <span className="block text-[11px] text-[var(--text-muted)] font-medium">Calls Scan Count</span>
                        <span className="text-[18px] font-extrabold text-[var(--text-primary)] mt-1 block">
                          {performance.override_data.total_recommendations || 0}
                        </span>
                      </div>
                      <div className="p-3 bg-gradient-to-b from-amber-50/40 to-amber-50/5 rounded-xl border border-amber-100/60 transition-all duration-300 hover:shadow-sm">
                        <span className="block text-[11px] text-[var(--text-muted)] font-medium">Overrides Count</span>
                        <span className="text-[18px] font-extrabold text-amber-600 mt-1 block">
                          {performance.override_data.total_overrides || 0}
                        </span>
                      </div>
                      <div className="p-3 bg-gradient-to-b from-red-50/40 to-red-50/5 rounded-xl border border-red-100/60 transition-all duration-300 hover:shadow-sm">
                        <span className="block text-[11px] text-[var(--text-muted)] font-medium">AI Override Rate</span>
                        <span className="text-[18px] font-extrabold text-red-600 mt-1 block">
                          {performance.override_data.override_rate || 0}%
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              </Card>
            )}
          </div>
        </div>
      )}

      {/* Tab Contents: Manual Reviews */}
      {activeTab === "reviews" && (
        <Card 
          title="Human-in-the-Loop Review Gate" 
          subtitle="Critical workflow overrides waiting for officer evaluation"
          className="shadow-sm border-gray-200 overflow-hidden"
        >
          <div className="mt-4 overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm">
            <Table
              data={reviews || []}
              columns={[
                { id: "agent", header: "Agent", cell: (r: any) => <span className="font-mono text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded-md border border-blue-100 font-bold">{r.agent_id}</span> },
                { id: "ref", header: "Reference Item", cell: (r: any) => <span className="font-semibold text-xs text-blue-600 hover:underline cursor-pointer">{r.reference_model} #{r.reference_id}</span> },
                { id: "status", header: "Status", cell: (r: any) => <Badge status={r.status} className="font-extrabold" /> },
                { id: "notes", header: "Review Notes", cell: (r: any) => <span className="text-xs text-[var(--text-muted)] block max-w-sm truncate" title={r.manual_notes}>{r.manual_notes}</span> },
                { id: "created", header: "Triggered At", cell: (r: any) => <span className="text-[11px] text-gray-400 font-medium">{formatRelativeTime(r.created_at)}</span> },
                {
                  id: "actions",
                  header: "Actions Override",
                  cell: (r: any) => {
                    const isRetryable = r.status === "PENDING" || r.status === "IN_PROGRESS" || r.status === "AI_RETRY_QUEUED";
                    return (
                      <div className="flex items-center gap-2">
                        <Button
                          size="sm"
                          variant="primary"
                          className="shadow-sm shadow-blue-500/10 hover:shadow-md"
                          disabled={!isAdmin && !isRiskAnalyst && !isComplianceOfficer}
                          onClick={() => handleManualDecision(r.id, "APPROVED")}
                        >
                          Approve
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          className="border-red-200 text-red-600 hover:bg-red-50 shadow-sm"
                          disabled={!isAdmin && !isRiskAnalyst && !isComplianceOfficer}
                          onClick={() => handleManualDecision(r.id, "REJECTED")}
                        >
                          Reject
                        </Button>
                        {isRetryable && (
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-gray-500 hover:bg-gray-100"
                            disabled={!isAdmin && !isComplianceOfficer}
                            icon={<RefreshCw className="h-3 w-3" />}
                            onClick={() => handleRetryReview(r.id)}
                          >
                            Retry AI
                          </Button>
                        )}
                      </div>
                    );
                  },
                },
              ]}
              emptyMessage="No pending manual review cases."
            />
          </div>
        </Card>
      )}

      {/* Tab Contents: Incidents */}
      {activeTab === "incidents" && (
        <Card 
          title="System Outage Incidents" 
          subtitle="Automated logs of AI agent offline issues and failover actions"
          className="shadow-sm border-gray-200 overflow-hidden"
        >
          <div className="mt-4 overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm">
            <Table
              data={incidents || []}
              columns={[
                { id: "type", header: "Incident Code", cell: (r: any) => <span className="font-extrabold text-xs text-gray-700">{r.incident_type}</span> },
                { id: "sev", header: "Severity", cell: (r: any) => <Badge status={r.severity} className="font-bold" /> },
                { id: "status", header: "Status", cell: (r: any) => <Badge status={r.status} className="font-extrabold" /> },
                { id: "message", header: "Error Message Details", cell: (r: any) => <span className="text-xs text-[var(--text-muted)] block max-w-sm truncate" title={r.error_message}>{r.error_message}</span> },
                { id: "time", header: "Logged At", cell: (r: any) => <span className="text-[11px] text-gray-400 font-medium">{formatRelativeTime(r.occurred_at)}</span> },
                {
                  id: "actions",
                  header: "Incident Resolve",
                  cell: (r: any) => (
                    r.status === "OPEN" ? (
                      <Button
                        size="sm"
                        variant="outline"
                        icon={<CheckCircle className="h-3.5 w-3.5" />}
                        className="hover:bg-emerald-50 hover:text-emerald-600 hover:border-emerald-200 border-gray-200"
                        disabled={!isAdmin && !isComplianceOfficer && !isBranchManager}
                        onClick={() => handleResolveIncident(r.id)}
                      >
                        Resolve Alert
                      </Button>
                    ) : (
                      <span className="text-xs text-emerald-600 flex items-center gap-1 font-bold">
                        <CheckCircle className="h-3.5 w-3.5" /> Resolved
                      </span>
                    )
                  ),
                },
              ]}
              emptyMessage="No incidents logged."
            />
          </div>
        </Card>
      )}

      {/* Tab Contents: Config Audit Trail */}
      {activeTab === "audit" && (
        <Card 
          title="Configuration Log History" 
          subtitle="Audit records of all modifications to AI thresholds and modes"
          className="shadow-sm border-gray-200 overflow-hidden"
        >
          <div className="mt-4 overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm">
            <Table
              data={auditLogs || []}
              columns={[
                { id: "agent", header: "Agent", cell: (r: any) => <span className="font-mono text-xs bg-gray-100 text-gray-700 px-2 py-0.5 rounded-md font-bold">{r.agent_id}</span> },
                { id: "field", header: "Modified Field", cell: (r: any) => <span className="font-bold text-xs text-gray-700">{r.field_changed}</span> },
                { id: "old", header: "Previous Value", cell: (r: any) => <span className="text-xs text-red-500 font-mono bg-red-50/50 px-1.5 py-0.5 rounded border border-red-100/30">{r.old_value}</span> },
                { id: "new", header: "New Value", cell: (r: any) => <span className="text-xs text-emerald-600 font-mono bg-emerald-50/50 px-1.5 py-0.5 rounded border border-emerald-100/30 font-bold">{r.new_value}</span> },
                { id: "user", header: "Officer Name", cell: (r: any) => <span className="text-xs text-gray-600 font-semibold">{r.changed_by_name || "System"}</span> },
                { id: "reason", header: "Change Motivation / Reason", cell: (r: any) => <span className="text-xs text-[var(--text-muted)] block max-w-xs truncate" title={r.reason}>{r.reason}</span> },
                { id: "time", header: "Applied At", cell: (r: any) => <span className="text-[11px] text-gray-400 font-medium">{formatRelativeTime(r.changed_at)}</span> },
              ]}
              emptyMessage="No configuration changes found."
            />
          </div>
        </Card>
      )}
    </div>
  );
}
