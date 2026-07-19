import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";

import api from "../api/client";
import AppShell from "../components/AppShell";
import Icon from "../components/Icon";
import ProjectNav from "../components/ProjectNav";
import { Alert, EmptyState, LoadingState, PageHeader, ProgressBar, StatCard } from "../components/UI";
import { apiErrorMessage } from "../utils/validation";

const HEALTH_TONES = {
  excellent: "text-emerald-700 bg-emerald-50 border-emerald-200",
  good: "text-indigo-700 bg-indigo-50 border-indigo-200",
  fair: "text-amber-800 bg-amber-50 border-amber-200",
  needs_attention: "text-rose-700 bg-rose-50 border-rose-200",
};

export default function AnalyticsPage() {
  const { projectId } = useParams();
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState("");
  const [error, setError] = useState("");

  async function loadAnalytics() {
    setLoading(true);
    setError("");
    try {
      const response = await api.get(`/projects/${projectId}/analytics`);
      setAnalytics(response.data);
    } catch (requestError) {
      setError(apiErrorMessage(requestError, "Could not load project analytics."));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadAnalytics(); }, [projectId]);

  async function downloadReport(format) {
    setExporting(format);
    setError("");
    try {
      const response = await api.get(`/projects/${projectId}/analytics/export`, {
        params: { format }, responseType: "blob",
      });
      const contentDisposition = response.headers["content-disposition"] || "";
      const match = contentDisposition.match(/filename="?([^";]+)"?/);
      const filename = match?.[1] || `atlas-project-report.${format}`;
      const url = URL.createObjectURL(response.data);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      link.click();
      URL.revokeObjectURL(url);
    } catch (requestError) {
      setError(apiErrorMessage(requestError, "Could not export the analytics report."));
    } finally {
      setExporting("");
    }
  }

  const healthTone = analytics ? HEALTH_TONES[analytics.health.grade] : "";
  const recommendations = useMemo(() => {
    if (!analytics) return [];
    return [...analytics.health.factors]
      .sort((a, b) => a.score / a.maximum - b.score / b.maximum)
      .slice(0, 3);
  }, [analytics]);

  return (
    <AppShell>
      <ProjectNav projectId={projectId} />
      <PageHeader
        eyebrow="Analytics & reporting"
        title={analytics?.project_name || "Project analytics"}
        description="Measure requirement quality, traceability coverage, change risk, AI readiness, and overall project health from live ATLAS data."
        actions={
          <>
            <button type="button" onClick={loadAnalytics} className="atlas-button-secondary"><Icon name="refresh" className="h-4 w-4" />Refresh</button>
            <ExportButton label="HTML report" format="html" exporting={exporting} onClick={downloadReport} />
            <ExportButton label="CSV" format="csv" exporting={exporting} onClick={downloadReport} />
            <ExportButton label="JSON" format="json" exporting={exporting} onClick={downloadReport} />
          </>
        }
      />

      {error && <div className="mt-6"><Alert type="error" onClose={() => setError("")}>{error}</Alert></div>}

      {loading ? (
        <LoadingState label="Calculating project health..." />
      ) : !analytics ? (
        <div className="mt-7"><EmptyState icon="analytics" title="Analytics unavailable" description="Refresh the workspace or check the backend logs." /></div>
      ) : (
        <>
          <section className="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard label="Health score" value={`${analytics.health.score}/100`} detail={analytics.health.label} icon="activity" tone="indigo" />
            <StatCard label="Requirements" value={analytics.requirements.total} detail={`${analytics.requirements.review_rate_percent}% reviewed`} icon="requirement" tone="violet" />
            <StatCard label="Requirement coverage" value={`${analytics.traceability.requirement_coverage_percent}%`} detail={`${analytics.traceability.accepted} accepted links`} icon="trace" tone="emerald" />
            <StatCard label="Average risk" value={analytics.impacts.average_risk_score} detail={`${analytics.impacts.total} impact reports`} icon="impact" tone="amber" />
          </section>

          <section className="mt-6 grid gap-6 xl:grid-cols-[1.1fr_.9fr]">
            <div className="atlas-panel">
              <div className="flex flex-col gap-5 sm:flex-row sm:items-center">
                <HealthGauge score={analytics.health.score} />
                <div className="min-w-0 flex-1">
                  <span className={`inline-flex rounded-full border px-3 py-1 text-xs font-black ${healthTone}`}>{analytics.health.label}</span>
                  <h2 className="mt-3 text-2xl font-black text-slate-950">Project health overview</h2>
                  <p className="mt-2 text-sm leading-6 text-slate-600">{analytics.health.summary}</p>
                </div>
              </div>
              <div className="mt-6 space-y-5">
                {analytics.health.factors.map((factor) => (
                  <div key={factor.key}>
                    <div className="mb-2 flex items-start justify-between gap-4">
                      <div><p className="text-sm font-black text-slate-800">{factor.label}</p><p className="mt-1 text-xs leading-5 text-slate-500">{factor.explanation}</p></div>
                      <strong className="shrink-0 text-sm text-slate-700">{factor.score}/{factor.maximum}</strong>
                    </div>
                    <ProgressBar value={(factor.score / factor.maximum) * 100} tone={factor.status === "strong" ? "emerald" : factor.status === "missing" ? "rose" : factor.status === "attention" ? "amber" : "indigo"} />
                  </div>
                ))}
              </div>
            </div>

            <div className="atlas-panel">
              <p className="atlas-eyebrow">Priority actions</p>
              <h2 className="mt-2 text-xl font-black text-slate-950">Improve the weakest signals</h2>
              <div className="mt-5 space-y-3">
                {recommendations.map((factor, index) => (
                  <div key={factor.key} className="rounded-2xl border border-slate-200 bg-slate-50/70 p-4">
                    <div className="flex gap-3"><span className="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-white text-xs font-black text-indigo-600 shadow-sm">{index + 1}</span><div><p className="font-black text-slate-800">{factor.label}</p><p className="mt-1 text-xs leading-5 text-slate-500">{factor.explanation}</p></div></div>
                  </div>
                ))}
              </div>
              <div className="mt-6 rounded-2xl bg-gradient-to-br from-indigo-600 to-violet-700 p-5 text-white">
                <Icon name="download" className="h-6 w-6 text-indigo-200" />
                <h3 className="mt-3 font-black">Shareable project report</h3>
                <p className="mt-2 text-sm leading-6 text-indigo-100">Export a standalone HTML report for evaluation, CSV for analysis, or JSON for integrations.</p>
              </div>
            </div>
          </section>

          <section className="mt-6 grid gap-6 xl:grid-cols-2">
            <ChartPanel title="Requirement type" subtitle="Functional versus quality constraints">
              <DonutChart items={analytics.requirements.type_distribution} centerLabel={analytics.requirements.total} />
            </ChartPanel>
            <ChartPanel title="Requirement lifecycle" subtitle="Review and approval progress">
              <HorizontalBars items={analytics.requirements.status_distribution} />
            </ChartPanel>
            <ChartPanel title="Software artifact inventory" subtitle={`${analytics.artifacts.total} registered artifacts`}>
              <HorizontalBars items={analytics.artifacts.type_distribution} />
            </ChartPanel>
            <ChartPanel title="Impact severity" subtitle={`Maximum risk score ${analytics.impacts.maximum_risk_score}`}>
              <DonutChart items={analytics.impacts.severity_distribution} centerLabel={analytics.impacts.total} />
            </ChartPanel>
          </section>

          <section className="mt-6 grid gap-6 xl:grid-cols-[.9fr_1.1fr]">
            <div className="atlas-panel">
              <h2 className="text-xl font-black text-slate-950">Coverage & readiness</h2>
              <div className="mt-6 space-y-6">
                <ProgressBar label="Requirement traceability" value={analytics.traceability.requirement_coverage_percent} tone="indigo" />
                <ProgressBar label="Artifact traceability" value={analytics.traceability.artifact_coverage_percent} tone="emerald" />
                <ProgressBar label="Document extraction" value={analytics.documents.extraction_rate_percent} tone="cyan" />
                <ProgressBar label="Requirement review" value={analytics.requirements.review_rate_percent} tone="violet" />
              </div>
              <div className="mt-7 grid grid-cols-2 gap-3">
                <MiniMetric label="Suggested" value={analytics.traceability.suggested} />
                <MiniMetric label="Rejected" value={analytics.traceability.rejected} />
                <MiniMetric label="Indexed chunks" value={analytics.assistant.indexed_chunks} />
                <MiniMetric label="AI conversations" value={analytics.assistant.conversations} />
              </div>
            </div>

            <div className="atlas-panel">
              <div className="flex items-center justify-between"><div><h2 className="text-xl font-black text-slate-950">Recent project activity</h2><p className="mt-1 text-sm text-slate-500">Latest evidence and analysis changes</p></div><Icon name="activity" className="h-6 w-6 text-indigo-500" /></div>
              {analytics.recent_activity.length === 0 ? (
                <div className="mt-5"><EmptyState icon="activity" title="No activity yet" description="Upload a document or create a requirement to begin." /></div>
              ) : (
                <div className="mt-5 space-y-1">
                  {analytics.recent_activity.map((item, index) => (
                    <div key={`${item.kind}-${item.occurred_at}-${index}`} className="flex gap-3 rounded-xl p-3 hover:bg-slate-50">
                      <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-indigo-50 text-indigo-600"><Icon name={activityIcon(item.kind)} className="h-4 w-4" /></span>
                      <div className="min-w-0 flex-1"><p className="truncate text-sm font-black text-slate-800">{item.title}</p><p className="mt-0.5 text-xs text-slate-500">{item.detail}</p></div>
                      <time className="shrink-0 text-[10px] text-slate-400">{new Date(item.occurred_at).toLocaleDateString()}</time>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </section>
        </>
      )}
    </AppShell>
  );
}

function ExportButton({ label, format, exporting, onClick }) {
  return <button type="button" disabled={Boolean(exporting)} onClick={() => onClick(format)} className="atlas-button-primary"><Icon name="download" className="h-4 w-4" />{exporting === format ? "Preparing..." : label}</button>;
}

function ChartPanel({ title, subtitle, children }) {
  return <div className="atlas-panel"><div><h2 className="text-xl font-black text-slate-950">{title}</h2><p className="mt-1 text-sm text-slate-500">{subtitle}</p></div><div className="mt-6">{children}</div></div>;
}

function HealthGauge({ score }) {
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const dash = (score / 100) * circumference;
  return (
    <div className="relative h-36 w-36 shrink-0">
      <svg viewBox="0 0 128 128" className="h-full w-full -rotate-90">
        <circle cx="64" cy="64" r={radius} fill="none" stroke="#e2e8f0" strokeWidth="10" />
        <circle cx="64" cy="64" r={radius} fill="none" stroke="url(#health-gradient)" strokeWidth="10" strokeLinecap="round" strokeDasharray={`${dash} ${circumference - dash}`} />
        <defs><linearGradient id="health-gradient"><stop stopColor="#4f46e5"/><stop offset="1" stopColor="#06b6d4"/></linearGradient></defs>
      </svg>
      <div className="absolute inset-0 grid place-items-center text-center"><div><strong className="text-3xl font-black text-slate-950">{score}</strong><p className="text-[10px] font-black uppercase tracking-wider text-slate-400">Health</p></div></div>
    </div>
  );
}

const chartColors = ["#4f46e5", "#8b5cf6", "#06b6d4", "#10b981", "#f59e0b", "#f43f5e", "#64748b"];
function DonutChart({ items, centerLabel }) {
  const total = items.reduce((sum, item) => sum + item.count, 0);
  let offset = 25;
  return (
    <div className="grid gap-5 sm:grid-cols-[180px_1fr] sm:items-center">
      <div className="relative mx-auto h-40 w-40">
        <svg viewBox="0 0 42 42" className="h-full w-full -rotate-90">
          <circle cx="21" cy="21" r="15.9" fill="none" stroke="#e2e8f0" strokeWidth="6" />
          {items.filter((item) => item.count > 0).map((item, index) => {
            const value = total ? (item.count / total) * 100 : 0;
            const circle = <circle key={item.key} cx="21" cy="21" r="15.9" fill="none" stroke={chartColors[index % chartColors.length]} strokeWidth="6" strokeDasharray={`${value} ${100 - value}`} strokeDashoffset={offset} />;
            offset -= value;
            return circle;
          })}
        </svg>
        <div className="absolute inset-0 grid place-items-center text-center"><div><strong className="text-3xl font-black">{centerLabel}</strong><p className="text-[10px] uppercase tracking-wider text-slate-400">Total</p></div></div>
      </div>
      <div className="space-y-3">{items.map((item, index) => <div key={item.key} className="flex items-center gap-3"><span className="h-3 w-3 rounded-full" style={{ backgroundColor: chartColors[index % chartColors.length] }} /><span className="flex-1 text-sm font-semibold text-slate-600">{item.label}</span><strong className="text-sm text-slate-900">{item.count}</strong><span className="w-12 text-right text-xs text-slate-400">{item.percent}%</span></div>)}</div>
    </div>
  );
}

function HorizontalBars({ items }) {
  const maximum = Math.max(...items.map((item) => item.count), 1);
  return <div className="space-y-4">{items.map((item, index) => <div key={item.key}><div className="mb-1.5 flex justify-between text-sm"><span className="font-semibold text-slate-600">{item.label}</span><strong>{item.count}</strong></div><div className="h-3 overflow-hidden rounded-full bg-slate-100"><span className="block h-full rounded-full" style={{ width: `${(item.count / maximum) * 100}%`, backgroundColor: chartColors[index % chartColors.length] }} /></div></div>)}</div>;
}

function MiniMetric({ label, value }) { return <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4"><p className="text-xs font-black uppercase tracking-wider text-slate-400">{label}</p><strong className="mt-2 block text-2xl font-black text-slate-900">{value}</strong></div>; }
function activityIcon(kind) { return { document: "document", requirement: "requirement", artifact: "trace", impact: "impact", assistant: "assistant" }[kind] || "activity"; }
