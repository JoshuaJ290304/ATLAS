import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";

import api from "../api/client";
import AppShell from "../components/AppShell";
import ProjectNav from "../components/ProjectNav";
import { FieldError } from "../components/UI";
import { apiErrorMessage, validateFile } from "../utils/validation";

export default function DocumentsPage() {
  const { projectId } = useParams();
  const fileInputRef = useRef(null);
  const [project, setProject] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileError, setFileError] = useState("");
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function loadWorkspace() {
    setLoading(true);
    setError("");
    try {
      const [projectResponse, documentsResponse] = await Promise.all([
        api.get(`/projects/${projectId}`),
        api.get(`/projects/${projectId}/documents`),
      ]);
      setProject(projectResponse.data);
      setDocuments(documentsResponse.data);
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Could not load the project documents.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadWorkspace();
  }, [projectId]);

  async function uploadDocument(event) {
    event.preventDefault();
    const validationMessage = validateFile(selectedFile);
    if (validationMessage) {
      setFileError(validationMessage);
      return;
    }

    setUploading(true);
    setError("");
    setNotice("");
    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await api.post(`/projects/${projectId}/documents`, formData);
      setDocuments((current) => [response.data, ...current]);
      setSelectedFile(null);
      setFileError("");
      if (fileInputRef.current) fileInputRef.current.value = "";
      setNotice(
        response.data.status === "extracted"
          ? "Document uploaded and text extracted successfully."
          : "Document uploaded, but text extraction failed. Check its status below.",
      );
    } catch (requestError) {
      setError(apiErrorMessage(requestError, "Document upload failed."));
    } finally {
      setUploading(false);
    }
  }

  async function downloadDocument(document) {
    setError("");
    try {
      const response = await api.get(
        `/projects/${projectId}/documents/${document.id}/download`,
        { responseType: "blob" },
      );
      const url = URL.createObjectURL(response.data);
      const link = window.document.createElement("a");
      link.href = url;
      link.download = document.original_filename;
      link.click();
      URL.revokeObjectURL(url);
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Could not download the document.");
    }
  }

  async function deleteDocument(document) {
    const confirmed = window.confirm(`Delete ${document.original_filename}?`);
    if (!confirmed) return;

    setError("");
    try {
      await api.delete(`/projects/${projectId}/documents/${document.id}`);
      setDocuments((current) => current.filter((item) => item.id !== document.id));
      setNotice("Document deleted.");
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Could not delete the document.");
    }
  }

  return (
    <AppShell>
      <ProjectNav projectId={projectId} />

      <section className="atlas-page-header">
        <div>
          <p className="text-sm font-bold uppercase tracking-[0.22em] text-indigo-600">
            Milestone 2
          </p>
          <h1 className="mt-2 text-4xl font-black tracking-tight text-slate-950">
            {project?.name || "Project documents"}
          </h1>
          <p className="mt-4 max-w-3xl leading-7 text-slate-600">
            Upload the project SRS in PDF or DOCX format. ATLAS stores the original file, records
            its checksum and metadata, and extracts text for requirement intelligence.
          </p>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <Metric label="Documents" value={documents.length} />
          <Metric
            label="Extracted"
            value={documents.filter((document) => document.status === "extracted").length}
          />
          <Metric
            label="Pages"
            value={documents.reduce((total, document) => total + (document.page_count || 0), 0)}
          />
          <Metric
            label="Characters"
            value={documents.reduce((total, document) => total + document.character_count, 0)}
          />
        </div>
      </section>

      <section className="mt-10 grid gap-8 lg:grid-cols-[380px_1fr]">
        <form
          onSubmit={uploadDocument}
          noValidate
          className="atlas-panel h-fit"
        >
          <h2 className="text-xl font-black text-slate-900">Upload SRS document</h2>
          <p className="mt-1 text-sm leading-6 text-slate-500">
            Accepted formats: PDF and DOCX. Maximum size: 10 MB.
          </p>

          <label className="mt-5 block text-sm font-semibold text-slate-700">
            Document file
            <input
              ref={fileInputRef}
              required
              type="file"
              accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              aria-invalid={Boolean(fileError)}
              onChange={(event) => {
                const file = event.target.files?.[0] || null;
                setSelectedFile(file);
                setFileError(validateFile(file));
              }}
              className="mt-2 block w-full rounded-xl border border-slate-300 bg-white px-3 py-3 text-sm file:mr-3 file:rounded-lg file:border-0 file:bg-indigo-50 file:px-3 file:py-2 file:font-bold file:text-indigo-700"
            />
            <FieldError>{fileError}</FieldError>
          </label>

          {selectedFile && (
            <div className="mt-4 rounded-xl bg-slate-50 p-3 text-sm text-slate-600">
              <p className="font-bold text-slate-800">{selectedFile.name}</p>
              <p>{formatBytes(selectedFile.size)}</p>
            </div>
          )}

          {error && <p className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}
          {notice && (
            <p className="mt-4 rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">
              {notice}
            </p>
          )}

          <button
            disabled={uploading || Boolean(fileError) || !selectedFile}
            className="atlas-button-primary mt-5 w-full"
          >
            {uploading ? "Uploading and extracting..." : "Upload document"}
          </button>
        </form>

        <div>
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-black text-slate-900">Project documents</h2>
            <button onClick={loadWorkspace} className="text-sm font-bold text-indigo-700 hover:underline">
              Refresh
            </button>
          </div>

          {loading ? (
            <p className="mt-5 text-slate-500">Loading documents...</p>
          ) : documents.length === 0 ? (
            <div className="mt-5 rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center">
              <p className="font-bold text-slate-800">No documents uploaded</p>
              <p className="mt-2 text-sm text-slate-500">Upload the project SRS using the form.</p>
            </div>
          ) : (
            <div className="mt-5 space-y-4">
              {documents.map((document) => (
                <article
                  key={document.id}
                  className="atlas-panel"
                >
                  <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="font-black text-slate-900">{document.original_filename}</h3>
                        <StatusBadge status={document.status} />
                      </div>
                      <p className="mt-2 text-sm text-slate-500">
                        {formatBytes(document.size_bytes)} · {document.file_extension.toUpperCase()}
                        {document.page_count ? ` · ${document.page_count} page(s)` : ""}
                      </p>
                      <p className="mt-1 text-xs text-slate-400">
                        SHA-256: {document.checksum_sha256.slice(0, 18)}…
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => downloadDocument(document)}
                        className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-bold text-slate-700 hover:bg-slate-50"
                      >
                        Download
                      </button>
                      <button
                        type="button"
                        onClick={() => deleteDocument(document)}
                        className="rounded-lg border border-red-200 px-3 py-2 text-sm font-bold text-red-700 hover:bg-red-50"
                      >
                        Delete
                      </button>
                    </div>
                  </div>

                  <div className="mt-4 grid grid-cols-2 gap-3 border-t border-slate-100 pt-4 text-sm sm:grid-cols-3">
                    <DocumentFact label="Characters" value={document.character_count.toLocaleString()} />
                    <DocumentFact
                      label="Uploaded"
                      value={new Date(document.created_at).toLocaleDateString()}
                    />
                    <DocumentFact
                      label="Extraction"
                      value={document.extraction_error || "Completed"}
                    />
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>
      </section>
    </AppShell>
  );
}

function Metric({ label, value }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-xs font-bold uppercase tracking-wider text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-black text-slate-900">{value}</p>
    </div>
  );
}

function StatusBadge({ status }) {
  const classes =
    status === "extracted"
      ? "bg-emerald-50 text-emerald-700"
      : status === "failed"
        ? "bg-red-50 text-red-700"
        : "bg-amber-50 text-amber-700";

  return (
    <span className={`rounded-full px-3 py-1 text-xs font-bold capitalize ${classes}`}>
      {status}
    </span>
  );
}

function DocumentFact({ label, value }) {
  return (
    <div>
      <p className="text-xs font-bold uppercase tracking-wider text-slate-400">{label}</p>
      <p className="mt-1 break-words font-semibold text-slate-700">{value}</p>
    </div>
  );
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
