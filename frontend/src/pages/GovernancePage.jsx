import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";

import api from "../api/client";
import AppShell from "../components/AppShell";
import { useConfirmDialog } from "../components/ConfirmDialog";
import Icon from "../components/Icon";
import ProjectNav from "../components/ProjectNav";
import { Alert, EmptyState, FieldError, LoadingState } from "../components/UI";
import { apiErrorMessage, clean, validateRequired } from "../utils/validation";

const EMPTY_REVIEW = {
  requirement_id: "",
  reviewer_id: "",
  request_note: "",
};

const EMPTY_BASELINE = {
  name: "",
  version_label: "",
  description: "",
};

const EMPTY_SUMMARY = {
  pending_reviews: 0,
  approved_requirements: 0,
  rejected_requirements: 0,
  in_review_requirements: 0,
  comments: 0,
  baselines: 0,
  approved_baseline_candidates: 0,
};

const TAB_LABELS = {
  reviews: "Review queue",
  baselines: "Baselines",
  audit: "Audit history",
};

export default function GovernancePage() {
  const { projectId } = useParams();
  const { confirm, confirmationDialog } = useConfirmDialog();

  const [project, setProject] = useState(null);
  const [requirements, setRequirements] = useState([]);
  const [reviewers, setReviewers] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [baselines, setBaselines] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [summary, setSummary] = useState(EMPTY_SUMMARY);
  const [activeTab, setActiveTab] = useState("reviews");

  const [reviewForm, setReviewForm] = useState(EMPTY_REVIEW);
  const [reviewErrors, setReviewErrors] = useState({});
  const [decisionNotes, setDecisionNotes] = useState({});
  const [baselineForm, setBaselineForm] = useState(EMPTY_BASELINE);
  const [baselineErrors, setBaselineErrors] = useState({});
  const [comparison, setComparison] = useState(null);

  const [selectedRequirementId, setSelectedRequirementId] = useState("");
  const [comments, setComments] = useState([]);
  const [commentBody, setCommentBody] = useState("");
  const [commentError, setCommentError] = useState("");

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function loadWorkspace({ preserveMessage = false } = {}) {
    setLoading(true);
    if (!preserveMessage) setError("");
    try {
      const [
        projectResponse,
        requirementsResponse,
        reviewersResponse,
        reviewsResponse,
        baselinesResponse,
        summaryResponse,
        auditResponse,
      ] = await Promise.all([
        api.get(`/projects/${projectId}`),
        api.get(`/projects/${projectId}/requirements`),
        api.get(`/projects/${projectId}/governance/reviewers`),
        api.get(`/projects/${projectId}/governance/reviews`),
        api.get(`/projects/${projectId}/governance/baselines`),
        api.get(`/projects/${projectId}/governance/summary`),
        api.get(`/projects/${projectId}/governance/audit`),
      ]);

      setProject(projectResponse.data);
      setRequirements(requirementsResponse.data);
      setReviewers(reviewersResponse.data);
      setReviews(reviewsResponse.data);
      setBaselines(baselinesResponse.data);
      setSummary(summaryResponse.data);
      setAuditLogs(auditResponse.data);

      const defaultRequirement =
        selectedRequirementId ||
        requirementsResponse.data[0]?.id ||
        "";
      setSelectedRequirementId(defaultRequirement);
      setReviewForm((current) => ({
        ...current,
        requirement_id:
          current.requirement_id || requirementsResponse.data[0]?.id || "",
        reviewer_id:
          current.reviewer_id || reviewersResponse.data[0]?.id || "",
      }));
    } catch (requestError) {
      setError(apiErrorMessage(requestError, "Could not load governance data."));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadWorkspace();
  }, [projectId]);

  useEffect(() => {
    if (!selectedRequirementId) {
      setComments([]);
      return;
    }
    loadComments(selectedRequirementId);
  }, [selectedRequirementId]);


  const pendingReviews = useMemo(
    () => reviews.filter((review) => review.status === "pending"),
    [reviews],
  );

  async function requestReview(event) {
    event.preventDefault();
    const nextErrors = {
      requirement_id: reviewForm.requirement_id ? "" : "Select a requirement.",
      reviewer_id: reviewForm.reviewer_id ? "" : "Select a reviewer.",
      request_note:
        reviewForm.request_note.length > 4000
          ? "Request note must be at most 4000 characters."
          : "",
    };
    Object.keys(nextErrors).forEach((key) => !nextErrors[key] && delete nextErrors[key]);
    setReviewErrors(nextErrors);
    if (Object.keys(nextErrors).length) return;

    setSaving("review");
    setError("");
    setNotice("");
    try {
      await api.post(
        `/projects/${projectId}/governance/requirements/${reviewForm.requirement_id}/reviews`,
        {
          reviewer_id: reviewForm.reviewer_id,
          request_note: clean(reviewForm.request_note) || null,
        },
      );
      setReviewForm((current) => ({ ...current, request_note: "" }));
      setNotice("Requirement review requested.");
      await loadWorkspace({ preserveMessage: true });
    } catch (requestError) {
      setError(apiErrorMessage(requestError, "Could not request the review."));
    } finally {
      setSaving("");
    }
  }

  async function decideReview(review, status) {
    const note = clean(decisionNotes[review.id] || "");
    if (note.length < 3) {
      setError("Add a decision note of at least 3 characters before approving or rejecting.");
      return;
    }

    setSaving(`${status}:${review.id}`);
    setError("");
    setNotice("");
    try {
      await api.post(
        `/projects/${projectId}/governance/reviews/${review.id}/decision`,
        { status, decision_note: note },
      );
      setDecisionNotes((current) => ({ ...current, [review.id]: "" }));
      setNotice(
        status === "approved"
          ? `${review.requirement_code} approved.`
          : `${review.requirement_code} rejected with feedback.`,
      );
      await loadWorkspace({ preserveMessage: true });
    } catch (requestError) {
      setError(apiErrorMessage(requestError, "Could not record the review decision."));
    } finally {
      setSaving("");
    }
  }

  async function loadComments(requirementId) {
    try {
      const response = await api.get(
        `/projects/${projectId}/governance/requirements/${requirementId}/comments`,
      );
      setComments(response.data);
    } catch (requestError) {
      setError(apiErrorMessage(requestError, "Could not load requirement comments."));
    }
  }

  async function addComment(event) {
    event.preventDefault();
    const validation = validateRequired(commentBody, "Comment", 2, 5000);
    setCommentError(validation);
    if (validation || !selectedRequirementId) return;

    setSaving("comment");
    setError("");
    setNotice("");
    try {
      await api.post(
        `/projects/${projectId}/governance/requirements/${selectedRequirementId}/comments`,
        { body: clean(commentBody) },
      );
      setCommentBody("");
      setNotice("Comment added to the requirement discussion.");
      await Promise.all([
        loadComments(selectedRequirementId),
        loadWorkspace({ preserveMessage: true }),
      ]);
    } catch (requestError) {
      setError(apiErrorMessage(requestError, "Could not add the comment."));
    } finally {
      setSaving("");
    }
  }

  async function createBaseline(event) {
    event.preventDefault();
    const nextErrors = {
      name: validateRequired(baselineForm.name, "Baseline name", 2, 160),
      version_label: validateRequired(
        baselineForm.version_label,
        "Version label",
        1,
        40,
      ),
      description:
        baselineForm.description.length > 4000
          ? "Description must be at most 4000 characters."
          : "",
    };
    Object.keys(nextErrors).forEach((key) => !nextErrors[key] && delete nextErrors[key]);
    setBaselineErrors(nextErrors);
    if (Object.keys(nextErrors).length) return;

    setSaving("baseline");
    setError("");
    setNotice("");
    try {
      await api.post(`/projects/${projectId}/governance/baselines`, {
        name: clean(baselineForm.name),
        version_label: clean(baselineForm.version_label),
        description: clean(baselineForm.description) || null,
      });
      setBaselineForm(EMPTY_BASELINE);
      setNotice("Approved requirements captured in a new baseline.");
      setActiveTab("baselines");
      await loadWorkspace({ preserveMessage: true });
    } catch (requestError) {
      setError(apiErrorMessage(requestError, "Could not create the baseline."));
    } finally {
      setSaving("");
    }
  }

  async function compareBaseline(baseline) {
    setSaving(`compare:${baseline.id}`);
    setError("");
    try {
      const response = await api.get(
        `/projects/${projectId}/governance/baselines/${baseline.id}/compare`,
      );
      setComparison(response.data);
      setActiveTab("baselines");
    } catch (requestError) {
      setError(apiErrorMessage(requestError, "Could not compare the baseline."));
    } finally {
      setSaving("");
    }
  }

  async function deleteBaseline(baseline) {
    const confirmed = await confirm({
      title: "Delete baseline?",
      message: `${baseline.name} (${baseline.version_label}) will be permanently removed. Current requirements are not deleted.`,
      confirmLabel: "Delete baseline",
      tone: "danger",
    });
    if (!confirmed) return;

    setSaving(`delete:${baseline.id}`);
    setError("");
    try {
      await api.delete(`/projects/${projectId}/governance/baselines/${baseline.id}`);
      if (comparison?.baseline_id === baseline.id) setComparison(null);
      setNotice("Baseline deleted.");
      await loadWorkspace({ preserveMessage: true });
    } catch (requestError) {
      setError(apiErrorMessage(requestError, "Could not delete the baseline."));
    } finally {
      setSaving("");
    }
  }

  return (
    <AppShell>
      {confirmationDialog}
      <ProjectNav projectId={projectId} />

      <section className="atlas-page-header">
        <div>
          <p className="atlas-eyebrow">Review, approval and baselines</p>
          <h1>{project?.name || "Governance workspace"}</h1>
          <p>
            Move requirements through a controlled review process, preserve decisions,
            capture approved baselines, and compare the current specification with an
            accepted release.
          </p>
        </div>
        <div className="atlas-header-metrics">
          <Metric label="Pending reviews" value={summary.pending_reviews} />
          <Metric label="Approved" value={summary.approved_requirements} />
          <Metric label="Baselines" value={summary.baselines} />
          <Metric label="Comments" value={summary.comments} />
        </div>
      </section>

      {(error || notice) && (
        <section className="mt-6 space-y-3">
          {error && <Alert type="error" onClose={() => setError("")}>{error}</Alert>}
          {notice && <Alert type="success" onClose={() => setNotice("")}>{notice}</Alert>}
        </section>
      )}

      {loading ? (
        <LoadingState label="Loading governance workspace..." />
      ) : (
        <section className="atlas-governance-layout">
          <aside className="atlas-governance-sidebar">
            <form onSubmit={requestReview} noValidate className="atlas-panel">
              <div className="atlas-governance-panel-heading">
                <span className="atlas-governance-icon is-review">
                  <Icon name="governance" className="h-5 w-5" />
                </span>
                <div>
                  <h2>Request review</h2>
                  <p>Assign a requirement for a documented decision.</p>
                </div>
              </div>

              <label className="atlas-label mt-5">
                Requirement
                <select
                  className="atlas-select"
                  value={reviewForm.requirement_id}
                  aria-invalid={Boolean(reviewErrors.requirement_id)}
                  onChange={(event) => {
                    setReviewForm({ ...reviewForm, requirement_id: event.target.value });
                    setReviewErrors({ ...reviewErrors, requirement_id: "" });
                  }}
                >
                  <option value="">Select requirement</option>
                  {requirements.map((requirement) => (
                    <option key={requirement.id} value={requirement.id}>
                      {requirement.code} · {requirement.title}
                    </option>
                  ))}
                </select>
                <FieldError>{reviewErrors.requirement_id}</FieldError>
              </label>

              <label className="atlas-label mt-4">
                Reviewer
                <select
                  className="atlas-select"
                  value={reviewForm.reviewer_id}
                  aria-invalid={Boolean(reviewErrors.reviewer_id)}
                  onChange={(event) => {
                    setReviewForm({ ...reviewForm, reviewer_id: event.target.value });
                    setReviewErrors({ ...reviewErrors, reviewer_id: "" });
                  }}
                >
                  <option value="">Select reviewer</option>
                  {reviewers.map((reviewer) => (
                    <option key={reviewer.id} value={reviewer.id}>
                      {reviewer.name} · {reviewer.email}
                    </option>
                  ))}
                </select>
                <FieldError>{reviewErrors.reviewer_id}</FieldError>
              </label>

              <label className="atlas-label mt-4">
                Review context <span className="font-normal text-slate-400">(optional)</span>
                <textarea
                  className="atlas-textarea"
                  rows={4}
                  maxLength={4000}
                  value={reviewForm.request_note}
                  aria-invalid={Boolean(reviewErrors.request_note)}
                  onChange={(event) => {
                    setReviewForm({ ...reviewForm, request_note: event.target.value });
                    setReviewErrors({ ...reviewErrors, request_note: "" });
                  }}
                  placeholder="Explain the decision needed or areas that require attention."
                />
                <FieldError>{reviewErrors.request_note}</FieldError>
              </label>

              <button
                type="submit"
                disabled={saving === "review" || requirements.length === 0}
                className="atlas-button-primary mt-5 w-full"
              >
                <Icon name="send" className="h-4 w-4" />
                {saving === "review" ? "Requesting review..." : "Request review"}
              </button>
            </form>

            <form onSubmit={createBaseline} noValidate className="atlas-panel">
              <div className="atlas-governance-panel-heading">
                <span className="atlas-governance-icon is-baseline">
                  <Icon name="baseline" className="h-5 w-5" />
                </span>
                <div>
                  <h2>Create baseline</h2>
                  <p>
                    Snapshot all {summary.approved_baseline_candidates} approved requirement(s).
                  </p>
                </div>
              </div>

              <label className="atlas-label mt-5">
                Baseline name
                <input
                  className="atlas-input"
                  maxLength={160}
                  value={baselineForm.name}
                  aria-invalid={Boolean(baselineErrors.name)}
                  onChange={(event) => {
                    setBaselineForm({ ...baselineForm, name: event.target.value });
                    setBaselineErrors({ ...baselineErrors, name: "" });
                  }}
                  placeholder="Approved scope"
                />
                <FieldError>{baselineErrors.name}</FieldError>
              </label>

              <label className="atlas-label mt-4">
                Version label
                <input
                  className="atlas-input"
                  maxLength={40}
                  value={baselineForm.version_label}
                  aria-invalid={Boolean(baselineErrors.version_label)}
                  onChange={(event) => {
                    setBaselineForm({ ...baselineForm, version_label: event.target.value });
                    setBaselineErrors({ ...baselineErrors, version_label: "" });
                  }}
                  placeholder="v1.0"
                />
                <FieldError>{baselineErrors.version_label}</FieldError>
              </label>

              <label className="atlas-label mt-4">
                Description <span className="font-normal text-slate-400">(optional)</span>
                <textarea
                  className="atlas-textarea"
                  rows={3}
                  maxLength={4000}
                  value={baselineForm.description}
                  aria-invalid={Boolean(baselineErrors.description)}
                  onChange={(event) => {
                    setBaselineForm({ ...baselineForm, description: event.target.value });
                    setBaselineErrors({ ...baselineErrors, description: "" });
                  }}
                  placeholder="Release scope, approval context, or decision reference."
                />
                <FieldError>{baselineErrors.description}</FieldError>
              </label>

              <button
                type="submit"
                disabled={
                  saving === "baseline" ||
                  summary.approved_baseline_candidates === 0
                }
                className="atlas-button-secondary mt-5 w-full"
              >
                <Icon name="baseline" className="h-4 w-4" />
                {saving === "baseline" ? "Creating baseline..." : "Create baseline"}
              </button>
            </form>
          </aside>

          <div className="min-w-0">
            <nav className="atlas-governance-tabs" aria-label="Governance views">
              {Object.entries(TAB_LABELS).map(([key, label]) => (
                <button
                  key={key}
                  type="button"
                  className={activeTab === key ? "is-active" : ""}
                  onClick={() => setActiveTab(key)}
                >
                  {label}
                  {key === "reviews" && <strong>{pendingReviews.length}</strong>}
                  {key === "baselines" && <strong>{summary.baselines}</strong>}
                </button>
              ))}
            </nav>

            {activeTab === "reviews" && (
              <div className="mt-5 space-y-6">
                <section className="atlas-panel">
                  <div className="atlas-section-heading">
                    <div>
                      <p className="atlas-eyebrow">Decision register</p>
                      <h2>Requirement review queue</h2>
                      <p>
                        Pending decisions appear first. Every approval and rejection retains
                        its rationale and timestamp.
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => loadWorkspace()}
                      className="atlas-button-secondary"
                    >
                      <Icon name="refresh" className="h-4 w-4" /> Refresh
                    </button>
                  </div>

                  {reviews.length === 0 ? (
                    <EmptyState
                      icon="governance"
                      title="No review requests"
                      description="Use the review form to assign the first requirement decision."
                    />
                  ) : (
                    <div className="atlas-review-list">
                      {reviews.map((review) => (
                        <article key={review.id} className="atlas-review-card">
                          <div className="atlas-review-card-header">
                            <div className="min-w-0">
                              <div className="flex flex-wrap items-center gap-2">
                                <span className="font-mono text-xs font-black text-indigo-700">
                                  {review.requirement_code}
                                </span>
                                <ReviewBadge status={review.status} />
                              </div>
                              <h3>{review.requirement_title}</h3>
                              <p>
                                Reviewer <strong>{review.reviewer.name}</strong> · requested by{" "}
                                {review.requested_by.name}
                              </p>
                            </div>
                            <time dateTime={review.created_at}>
                              {new Date(review.created_at).toLocaleDateString()}
                            </time>
                          </div>

                          {review.request_note && (
                            <div className="atlas-review-note">
                              <span>Review context</span>
                              <p>{review.request_note}</p>
                            </div>
                          )}

                          {review.status === "pending" ? (
                            <div className="atlas-review-decision">
                              <label className="atlas-label">
                                Decision note
                                <textarea
                                  className="atlas-textarea"
                                  rows={3}
                                  maxLength={4000}
                                  value={decisionNotes[review.id] || ""}
                                  onChange={(event) =>
                                    setDecisionNotes({
                                      ...decisionNotes,
                                      [review.id]: event.target.value,
                                    })
                                  }
                                  placeholder="Record the acceptance rationale or corrective feedback."
                                />
                              </label>
                              <div className="atlas-review-actions">
                                <button
                                  type="button"
                                  disabled={saving === `rejected:${review.id}`}
                                  onClick={() => decideReview(review, "rejected")}
                                  className="atlas-button-danger"
                                >
                                  <Icon name="close" className="h-4 w-4" />
                                  Reject
                                </button>
                                <button
                                  type="button"
                                  disabled={saving === `approved:${review.id}`}
                                  onClick={() => decideReview(review, "approved")}
                                  className="atlas-button-primary"
                                >
                                  <Icon name="check" className="h-4 w-4" />
                                  Approve
                                </button>
                              </div>
                            </div>
                          ) : (
                            <div className="atlas-review-decision-summary">
                              <span>Decision rationale</span>
                              <p>{review.decision_note}</p>
                              {review.decided_at && (
                                <time dateTime={review.decided_at}>
                                  Recorded {new Date(review.decided_at).toLocaleString()}
                                </time>
                              )}
                            </div>
                          )}
                        </article>
                      ))}
                    </div>
                  )}
                </section>

                <section className="atlas-panel">
                  <div className="atlas-section-heading">
                    <div>
                      <p className="atlas-eyebrow">Discussion</p>
                      <h2>Requirement comments</h2>
                      <p>
                        Capture clarification, review evidence, and follow-up decisions against
                        a specific requirement.
                      </p>
                    </div>
                  </div>

                  <label className="atlas-label mt-5">
                    Requirement
                    <select
                      className="atlas-select"
                      value={selectedRequirementId}
                      onChange={(event) => setSelectedRequirementId(event.target.value)}
                    >
                      <option value="">Select requirement</option>
                      {requirements.map((requirement) => (
                        <option key={requirement.id} value={requirement.id}>
                          {requirement.code} · {requirement.title}
                        </option>
                      ))}
                    </select>
                  </label>

                  <div className="atlas-comment-list">
                    {comments.length === 0 ? (
                      <p className="atlas-comment-empty">No comments for this requirement.</p>
                    ) : (
                      comments.map((comment) => (
                        <article key={comment.id} className="atlas-comment">
                          <div>
                            <strong>{comment.author.name}</strong>
                            <time dateTime={comment.created_at}>
                              {new Date(comment.created_at).toLocaleString()}
                            </time>
                          </div>
                          <p>{comment.body}</p>
                        </article>
                      ))
                    )}
                  </div>

                  <form onSubmit={addComment} noValidate className="mt-5">
                    <label className="atlas-label">
                      Add comment
                      <textarea
                        className="atlas-textarea"
                        rows={3}
                        maxLength={5000}
                        value={commentBody}
                        aria-invalid={Boolean(commentError)}
                        onChange={(event) => {
                          setCommentBody(event.target.value);
                          setCommentError("");
                        }}
                        placeholder="Add review evidence, clarification, or a follow-up action."
                      />
                      <FieldError>{commentError}</FieldError>
                    </label>
                    <button
                      type="submit"
                      disabled={saving === "comment" || !selectedRequirementId}
                      className="atlas-button-secondary mt-3"
                    >
                      <Icon name="comment" className="h-4 w-4" />
                      {saving === "comment" ? "Adding comment..." : "Add comment"}
                    </button>
                  </form>
                </section>
              </div>
            )}

            {activeTab === "baselines" && (
              <div className="mt-5 space-y-6">
                <section className="atlas-panel">
                  <div className="atlas-section-heading">
                    <div>
                      <p className="atlas-eyebrow">Accepted scope</p>
                      <h2>Project baselines</h2>
                      <p>
                        Baselines are immutable snapshots of approved requirements at a named
                        release point.
                      </p>
                    </div>
                  </div>

                  {baselines.length === 0 ? (
                    <EmptyState
                      icon="baseline"
                      title="No baselines"
                      description="Approve requirements, then create the first controlled baseline."
                    />
                  ) : (
                    <div className="atlas-baseline-grid">
                      {baselines.map((baseline) => (
                        <article key={baseline.id} className="atlas-baseline-card">
                          <div className="atlas-baseline-card-heading">
                            <span className="atlas-governance-icon is-baseline">
                              <Icon name="baseline" className="h-5 w-5" />
                            </span>
                            <div className="min-w-0">
                              <p>{baseline.version_label}</p>
                              <h3>{baseline.name}</h3>
                            </div>
                          </div>
                          <p className="atlas-baseline-description">
                            {baseline.description || "No baseline description provided."}
                          </p>
                          <dl>
                            <div><dt>Requirements</dt><dd>{baseline.requirement_count}</dd></div>
                            <div><dt>Created by</dt><dd>{baseline.created_by.name}</dd></div>
                            <div><dt>Created</dt><dd>{new Date(baseline.created_at).toLocaleDateString()}</dd></div>
                          </dl>
                          <div className="atlas-card-actions">
                            <button
                              type="button"
                              onClick={() => compareBaseline(baseline)}
                              disabled={saving === `compare:${baseline.id}`}
                              className="atlas-button-secondary"
                            >
                              <Icon name="compare" className="h-4 w-4" />
                              Compare
                            </button>
                            <button
                              type="button"
                              onClick={() => deleteBaseline(baseline)}
                              disabled={saving === `delete:${baseline.id}`}
                              className="atlas-button-danger"
                            >
                              <Icon name="trash" className="h-4 w-4" />
                              Delete
                            </button>
                          </div>
                        </article>
                      ))}
                    </div>
                  )}
                </section>

                {comparison && <BaselineComparison comparison={comparison} />}
              </div>
            )}

            {activeTab === "audit" && (
              <section className="atlas-panel mt-5">
                <div className="atlas-section-heading">
                  <div>
                    <p className="atlas-eyebrow">Accountability</p>
                    <h2>Governance audit history</h2>
                    <p>
                      Review requests, decisions, comments, and baseline events are retained
                      with their actor and time.
                    </p>
                  </div>
                </div>

                {auditLogs.length === 0 ? (
                  <EmptyState
                    icon="history"
                    title="No governance events"
                    description="Audit entries appear when reviews, comments, and baselines are created."
                  />
                ) : (
                  <div className="atlas-audit-list">
                    {auditLogs.map((log) => (
                      <article key={log.id} className="atlas-audit-item">
                        <span className="atlas-audit-marker">
                          <Icon name={auditIcon(log.action)} className="h-4 w-4" />
                        </span>
                        <div className="min-w-0">
                          <div>
                            <strong>{formatAction(log.action)}</strong>
                            <time dateTime={log.created_at}>
                              {new Date(log.created_at).toLocaleString()}
                            </time>
                          </div>
                          <p>
                            {log.actor.name} · {log.entity_type}
                            {log.details?.requirement_code
                              ? ` ${log.details.requirement_code}`
                              : ""}
                            {log.details?.version_label
                              ? ` ${log.details.version_label}`
                              : ""}
                          </p>
                        </div>
                      </article>
                    ))}
                  </div>
                )}
              </section>
            )}
          </div>
        </section>
      )}
    </AppShell>
  );
}

function Metric({ label, value }) {
  return (
    <div className="atlas-metric-card">
      <p className="atlas-metric-label">{label}</p>
      <p className="atlas-metric-value">{value}</p>
    </div>
  );
}

function ReviewBadge({ status }) {
  const label =
    status === "pending" ? "Pending" : status === "approved" ? "Approved" : "Rejected";
  return <span className={`atlas-review-badge is-${status}`}>{label}</span>;
}

function BaselineComparison({ comparison }) {
  const groups = [
    ["Added", comparison.added, "is-added"],
    ["Modified", comparison.modified, "is-modified"],
    ["Removed", comparison.removed, "is-removed"],
  ];

  return (
    <section className="atlas-panel">
      <div className="atlas-section-heading">
        <div>
          <p className="atlas-eyebrow">Change comparison</p>
          <h2>
            {comparison.baseline_name} · {comparison.version_label}
          </h2>
          <p>Current requirements compared with the selected approved snapshot.</p>
        </div>
      </div>

      <div className="atlas-comparison-metrics">
        <Metric label="Added" value={comparison.added_count} />
        <Metric label="Modified" value={comparison.modified_count} />
        <Metric label="Removed" value={comparison.removed_count} />
        <Metric label="Unchanged" value={comparison.unchanged_count} />
      </div>

      <div className="atlas-comparison-groups">
        {groups.map(([label, items, className]) => (
          <section key={label}>
            <h3>{label}</h3>
            {items.length === 0 ? (
              <p className="atlas-comparison-empty">No {label.toLowerCase()} requirements.</p>
            ) : (
              <div className="space-y-3">
                {items.map((item) => (
                  <article key={item.code} className={`atlas-comparison-item ${className}`}>
                    <div>
                      <strong>{item.code}</strong>
                      {item.changed_fields?.length > 0 && (
                        <span>{item.changed_fields.join(", ")}</span>
                      )}
                    </div>
                    <p>
                      {item.current?.title || item.baseline?.title || "Requirement"}
                    </p>
                  </article>
                ))}
              </div>
            )}
          </section>
        ))}
      </div>

      {comparison.unchanged.length > 0 && (
        <div className="atlas-unchanged-list">
          <strong>Unchanged</strong>
          <p>{comparison.unchanged.join(", ")}</p>
        </div>
      )}
    </section>
  );
}

function auditIcon(action) {
  if (action.includes("approved")) return "check";
  if (action.includes("rejected") || action.includes("deleted")) return "alert";
  if (action.includes("comment")) return "comment";
  if (action.includes("baseline")) return "baseline";
  return "governance";
}

function formatAction(action) {
  return action
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}
