import { useState } from "react";
import { Link, Navigate } from "react-router-dom";

import api from "../api/client";
import AuthLayout from "../components/AuthLayout";
import { Alert, FieldError } from "../components/UI";
import { useAuth } from "../context/AuthContext";
import { apiErrorMessage, clean, validateEmail } from "../utils/validation";

export default function ForgotPasswordPage() {
  const { isAuthenticated } = useAuth();
  const [email, setEmail] = useState("");
  const [fieldError, setFieldError] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (isAuthenticated) return <Navigate to="/" replace />;

  async function handleSubmit(event) {
    event.preventDefault();
    const validationError = validateEmail(email);
    setFieldError(validationError);
    if (validationError) return;

    setSubmitting(true);
    setError("");
    setMessage("");
    try {
      const response = await api.post("/auth/forgot-password", {
        email: clean(email).toLowerCase(),
      });
      setMessage(response.data.message);
    } catch (requestError) {
      setError(apiErrorMessage(requestError, "Could not start password recovery."));
    } finally {
      setSubmitting(false);
    }
  }

  const mailPreviewUrl = import.meta.env.VITE_MAIL_PREVIEW_URL;

  return (
    <AuthLayout
      title="Recover your account"
      subtitle="Enter your account email and ATLAS will send a secure, one-use password-reset link."
    >
      <form className="space-y-5" onSubmit={handleSubmit} noValidate>
        <label className="atlas-label">
          Email address
          <input
            type="email"
            autoComplete="email"
            value={email}
            aria-invalid={Boolean(fieldError)}
            onBlur={() => setFieldError(validateEmail(email))}
            onChange={(event) => {
              setEmail(event.target.value);
              if (fieldError) setFieldError("");
            }}
            className="atlas-input"
            placeholder="you@example.com"
            maxLength={320}
          />
          <FieldError>{fieldError}</FieldError>
        </label>

        {error && <Alert type="error">{error}</Alert>}
        {message && (
          <Alert type="success">
            <p>{message}</p>
            {mailPreviewUrl && (
              <p className="mt-2 text-sm">
                Local development inbox:{" "}
                <a
                  href={mailPreviewUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="font-extrabold underline"
                >
                  open Mailpit
                </a>
              </p>
            )}
          </Alert>
        )}

        <button type="submit" disabled={submitting} className="atlas-button-primary w-full">
          {submitting ? "Sending secure link..." : "Send password-reset link"}
        </button>
      </form>

      <p className="mt-6 text-center text-sm text-slate-600">
        Remembered your password?{" "}
        <Link className="font-extrabold text-indigo-700 hover:underline" to="/login">
          Return to login
        </Link>
      </p>
    </AuthLayout>
  );
}
