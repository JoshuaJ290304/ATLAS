import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";

import api from "../api/client";
import AppShell from "../components/AppShell";
import ProjectNav from "../components/ProjectNav";
import { FieldError } from "../components/UI";
import { apiErrorMessage, clean, validateRequired } from "../utils/validation";

const SOURCE_STYLES = {
  document: "bg-sky-50 text-sky-700",
  requirement: "bg-indigo-50 text-indigo-700",
  artifact: "bg-emerald-50 text-emerald-700",
  impact_analysis: "bg-amber-50 text-amber-800",
};

export default function AssistantPage() {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const [status, setStatus] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [activeConversation, setActiveConversation] = useState(null);
  const [question, setQuestion] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [questionError, setQuestionError] = useState("");
  const [searchError, setSearchError] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(true);
  const [indexing, setIndexing] = useState(false);
  const [asking, setAsking] = useState(false);
  const [searching, setSearching] = useState(false);
  const [mode, setMode] = useState("chat");

  async function loadWorkspace() {
    setLoading(true);
    try {
      const [projectResponse, statusResponse, conversationResponse] = await Promise.all([
        api.get(`/projects/${projectId}`),
        api.get(`/projects/${projectId}/assistant/status`, { timeout: 30000 }),
        api.get(`/projects/${projectId}/assistant/conversations`),
      ]);
      setProject(projectResponse.data);
      setStatus(statusResponse.data);
      setConversations(conversationResponse.data);
      setError("");
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Could not load the AI assistant workspace.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadWorkspace();
  }, [projectId]);

  async function rebuildIndex() {
    setIndexing(true);
    setError("");
    setNotice("");
    try {
      const response = await api.post(`/projects/${projectId}/assistant/index`, null, {
        timeout: 600000,
      });
      setNotice(
        `Knowledge index ready with ${response.data.chunk_count} chunks from ${response.data.source_count} sources.`,
      );
      await loadWorkspace();
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Could not build the project knowledge index.");
    } finally {
      setIndexing(false);
    }
  }

  async function clearIndex() {
    if (!window.confirm("Clear the project knowledge index? Chat history will be kept.")) return;
    try {
      await api.delete(`/projects/${projectId}/assistant/index`, { timeout: 120000 });
      setNotice("Project knowledge index cleared.");
      setSearchResults([]);
      await loadWorkspace();
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Could not clear the knowledge index.");
    }
  }

  async function openConversation(conversationId) {
    try {
      const response = await api.get(
        `/projects/${projectId}/assistant/conversations/${conversationId}`,
      );
      setActiveConversation(response.data);
      setMode("chat");
      setError("");
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Could not open the conversation.");
    }
  }

  function newConversation() {
    setActiveConversation(null);
    setQuestion("");
    setMode("chat");
  }

  async function askQuestion(event) {
    event.preventDefault();
    const value = clean(question);
    const validationMessage = validateRequired(value, "Question", 3, 2000);
    setQuestionError(validationMessage);
    if (validationMessage) return;
    setAsking(true);
    setError("");
    setNotice("");
    try {
      const response = await api.post(
        `/projects/${projectId}/assistant/ask`,
        {
          question: value,
          conversation_id: activeConversation?.id || null,
          top_k: 5,
        },
        { timeout: 300000 },
      );
      const conversationId = response.data.conversation.id;
      await loadWorkspace();
      await openConversation(conversationId);
      setQuestion("");
      if (response.data.used_retrieval_fallback) {
        setNotice("Ollama was unavailable, so ATLAS returned retrieval-only evidence.");
      }
    } catch (requestError) {
      setError(apiErrorMessage(requestError, "Could not answer the project question."));
    } finally {
      setAsking(false);
    }
  }

  async function runSearch(event) {
    event.preventDefault();
    const value = clean(searchQuery);
    const validationMessage = validateRequired(value, "Search query", 3, 1000);
    setSearchError(validationMessage);
    if (validationMessage) return;
    setSearching(true);
    setError("");
    try {
      const response = await api.post(`/projects/${projectId}/assistant/search`, {
        query: value,
        top_k: 8,
      });
      setSearchResults(response.data.results);
    } catch (requestError) {
      setError(apiErrorMessage(requestError, "Could not search project evidence."));
    } finally {
      setSearching(false);
    }
  }

  async function deleteConversation(conversationId) {
    if (!window.confirm("Delete this assistant conversation?")) return;
    try {
      await api.delete(`/projects/${projectId}/assistant/conversations/${conversationId}`);
      if (activeConversation?.id === conversationId) setActiveConversation(null);
      await loadWorkspace();
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Could not delete the conversation.");
    }
  }

  const indexReady = status?.index?.status === "ready" && status?.index?.chunk_count > 0;
  const modelLabel = status?.model_available
    ? "Ready"
    : status?.ollama_available
      ? "Model missing"
      : "Offline / fallback";

  const messages = useMemo(() => activeConversation?.messages || [], [activeConversation]);

  return (
    <AppShell>
      <ProjectNav projectId={projectId} />

      <section className="atlas-page-header">
        <div>
          <p className="text-sm font-bold uppercase tracking-[0.22em] text-violet-600">
            Milestone 6
          </p>
          <h1 className="mt-2 text-4xl font-black tracking-tight text-slate-950">
            {project?.name || "AI project assistant"}
          </h1>
          <p className="mt-4 max-w-3xl leading-7 text-slate-600">
            Search indexed project evidence and ask source-grounded questions using ChromaDB,
            Sentence Transformers, and a local Ollama model.
          </p>
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 xl:grid-cols-2">
          <Metric label="Index" value={status?.index?.status || "—"} />
          <Metric label="Sources" value={status?.index?.source_count ?? 0} />
          <Metric label="Chunks" value={status?.index?.chunk_count ?? 0} />
          <Metric label="Ollama" value={modelLabel} />
        </div>
      </section>

      {(error || notice) && (
        <section className="mt-6 space-y-3">
          {error && <p className="rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</p>}
          {notice && (
            <p className="rounded-xl bg-emerald-50 p-4 text-sm text-emerald-700">{notice}</p>
          )}
        </section>
      )}

      <section className="mt-8 atlas-card p-5">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-black text-slate-900">Project knowledge index</h2>
            <p className="mt-1 text-sm text-slate-500">
              {status?.status_message || "Checking Ollama and index status..."}
            </p>
            <p className="mt-1 text-xs text-slate-400">
              Embeddings: {status?.embedding_model || "—"} · Chat model: {status?.model_name || "—"}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={rebuildIndex}
              disabled={indexing}
              className="rounded-xl bg-violet-600 px-4 py-2.5 text-sm font-bold text-white hover:bg-violet-700 disabled:opacity-50"
            >
              {indexing ? "Indexing project..." : indexReady ? "Rebuild index" : "Build index"}
            </button>
            <button
              onClick={clearIndex}
              disabled={!indexReady || indexing}
              className="rounded-xl border border-slate-300 px-4 py-2.5 text-sm font-bold text-slate-700 hover:bg-slate-50 disabled:opacity-50"
            >
              Clear index
            </button>
          </div>
        </div>
        {indexing && (
          <p className="mt-4 rounded-lg bg-amber-50 p-3 text-sm text-amber-800">
            The first index build downloads the embedding model and can take several minutes.
          </p>
        )}
      </section>

      <div className="mt-8 flex gap-2 rounded-xl bg-slate-100 p-1 sm:w-fit">
        <ModeButton active={mode === "chat"} onClick={() => setMode("chat")}>
          Ask project
        </ModeButton>
        <ModeButton active={mode === "search"} onClick={() => setMode("search")}>
          Semantic search
        </ModeButton>
      </div>

      {mode === "chat" ? (
        <section className="mt-5 grid gap-6 xl:grid-cols-[310px_minmax(0,1fr)]">
          <aside className="atlas-card p-5">
            <div className="flex items-center justify-between gap-3">
              <h2 className="font-black text-slate-900">Conversations</h2>
              <button onClick={newConversation} className="text-sm font-bold text-violet-700">
                + New
              </button>
            </div>
            {loading ? (
              <p className="mt-4 text-sm text-slate-500">Loading...</p>
            ) : conversations.length === 0 ? (
              <p className="mt-4 text-sm leading-6 text-slate-500">No project questions yet.</p>
            ) : (
              <div className="mt-4 space-y-2">
                {conversations.map((conversation) => (
                  <div
                    key={conversation.id}
                    className={`rounded-xl border p-3 ${
                      activeConversation?.id === conversation.id
                        ? "border-violet-300 bg-violet-50"
                        : "border-slate-200"
                    }`}
                  >
                    <button
                      onClick={() => openConversation(conversation.id)}
                      className="w-full text-left"
                    >
                      <p className="line-clamp-2 text-sm font-bold text-slate-900">
                        {conversation.title}
                      </p>
                      <p className="mt-1 text-xs text-slate-500">
                        {new Date(conversation.updated_at).toLocaleString()}
                      </p>
                    </button>
                    <button
                      onClick={() => deleteConversation(conversation.id)}
                      className="mt-2 text-xs font-bold text-red-600 hover:underline"
                    >
                      Delete
                    </button>
                  </div>
                ))}
              </div>
            )}
          </aside>

          <div className="min-w-0 rounded-2xl border border-slate-200 bg-white shadow-sm">
            <div className="min-h-[480px] space-y-5 p-6">
              {messages.length === 0 ? (
                <div className="flex min-h-[420px] items-center justify-center text-center">
                  <div>
                    <p className="text-xl font-black text-slate-900">Ask about this project</p>
                    <p className="mt-2 max-w-xl text-sm leading-6 text-slate-500">
                      Try “Which requirements affect authentication?”, “Explain the highest-risk
                      change”, or “Which test cases verify password reset?”
                    </p>
                  </div>
                </div>
              ) : (
                messages.map((message) => <ChatMessage key={message.id} message={message} />)
              )}
            </div>
            <form onSubmit={askQuestion} noValidate className="border-t border-slate-200 p-5">
              <textarea
                rows={3}
                value={question}
                aria-invalid={Boolean(questionError)}
                onChange={(event) => {
                  setQuestion(event.target.value);
                  if (questionError) setQuestionError("");
                }}
                disabled={!indexReady || asking}
                maxLength={2000}
                className="atlas-textarea disabled:bg-slate-50"
                placeholder={indexReady ? "Ask a source-grounded project question..." : "Build the project index first."}
              />
              <FieldError>{questionError}</FieldError>
              <div className="mt-3 flex items-center justify-between gap-3">
                <p className="text-xs text-slate-500">
                  Answers are limited to indexed project evidence and include citations.
                </p>
                <button
                  disabled={!indexReady || asking || question.trim().length < 3}
                  className="shrink-0 rounded-xl bg-violet-600 px-5 py-2.5 font-bold text-white hover:bg-violet-700 disabled:opacity-50"
                >
                  {asking ? "Thinking..." : "Ask ATLAS"}
                </button>
              </div>
            </form>
          </div>
        </section>
      ) : (
        <section className="mt-5 grid gap-6 lg:grid-cols-[360px_minmax(0,1fr)]">
          <form onSubmit={runSearch} noValidate className="atlas-panel h-fit">
            <h2 className="text-xl font-black text-slate-900">Semantic evidence search</h2>
            <p className="mt-1 text-sm leading-6 text-slate-500">
              Retrieve the most relevant document, requirement, artifact, and impact chunks.
            </p>
            <textarea
              rows={5}
              value={searchQuery}
              aria-invalid={Boolean(searchError)}
              onChange={(event) => {
                setSearchQuery(event.target.value);
                if (searchError) setSearchError("");
              }}
              maxLength={1000}
              className="atlas-textarea mt-5"
              placeholder="Search for password reset security and related test cases"
            />
            <FieldError>{searchError}</FieldError>
            <button
              disabled={!indexReady || searching || searchQuery.trim().length < 3}
              className="mt-4 w-full rounded-xl bg-violet-600 px-4 py-3 font-bold text-white disabled:opacity-50"
            >
              {searching ? "Searching..." : "Search evidence"}
            </button>
          </form>
          <div className="min-w-0 space-y-4">
            {searchResults.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center">
                <p className="font-bold text-slate-800">No search results yet</p>
                <p className="mt-2 text-sm text-slate-500">Build the index, then search project evidence.</p>
              </div>
            ) : (
              searchResults.map((citation, index) => (
                <CitationCard key={citation.chunk_id} citation={citation} number={index + 1} />
              ))
            )}
          </div>
        </section>
      )}
    </AppShell>
  );
}

function ChatMessage({ message }) {
  const assistant = message.role === "assistant";
  return (
    <article className={`flex ${assistant ? "justify-start" : "justify-end"}`}>
      <div
        className={`max-w-3xl rounded-2xl px-5 py-4 ${
          assistant ? "bg-slate-100 text-slate-800" : "bg-violet-600 text-white"
        }`}
      >
        <p className="whitespace-pre-wrap text-sm leading-7">{message.content}</p>
        {assistant && message.citations?.length > 0 && (
          <div className="mt-4 space-y-2 border-t border-slate-200 pt-3">
            <p className="text-xs font-black uppercase tracking-wider text-slate-500">Sources</p>
            {message.citations.map((citation, index) => (
              <CitationCard key={`${citation.chunk_id}-${index}`} citation={citation} number={index + 1} compact />
            ))}
          </div>
        )}
        <p className={`mt-2 text-[11px] ${assistant ? "text-slate-400" : "text-violet-100"}`}>
          {new Date(message.created_at).toLocaleString()}
          {message.latency_ms ? ` · ${message.latency_ms} ms` : ""}
        </p>
      </div>
    </article>
  );
}

function CitationCard({ citation, number, compact = false }) {
  return (
    <article className={`rounded-xl border border-slate-200 bg-white ${compact ? "p-3" : "p-5 shadow-sm"}`}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="text-sm font-black text-slate-500">[{number}]</span>
          <span className={`rounded-full px-2.5 py-1 text-xs font-bold ${SOURCE_STYLES[citation.source_type] || "bg-slate-100 text-slate-700"}`}>
            {citation.source_type.replaceAll("_", " ")}
          </span>
        </div>
        <span className="text-xs font-bold text-slate-500">
          {Math.round(citation.relevance_score * 100)}% match
        </span>
      </div>
      <h3 className="mt-3 break-words text-sm font-black text-slate-900">{citation.source_label}</h3>
      <p className={`mt-2 whitespace-pre-wrap text-slate-600 ${compact ? "line-clamp-3 text-xs leading-5" : "text-sm leading-6"}`}>
        {citation.excerpt}
      </p>
    </article>
  );
}

function ModeButton({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      className={`flex-1 rounded-lg px-5 py-2.5 text-sm font-bold sm:flex-none ${
        active ? "bg-white text-violet-700 shadow-sm" : "text-slate-600"
      }`}
    >
      {children}
    </button>
  );
}

function Metric({ label, value }) {
  return (
    <div className="min-w-0 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-xs font-bold uppercase tracking-wider text-slate-500">{label}</p>
      <p className="mt-2 truncate text-xl font-black capitalize text-slate-900">{value}</p>
    </div>
  );
}
