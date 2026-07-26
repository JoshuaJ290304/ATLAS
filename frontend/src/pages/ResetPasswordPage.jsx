import { useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import api from "../api/client";
import AuthLayout from "../components/AuthLayout";
import { Alert, FieldError } from "../components/UI";
import { apiErrorMessage, passwordRules, validatePassword } from "../utils/validation";

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const token = useMemo(() => searchParams.get("token")?.trim() || "", [searchParams]);
  const [form, setForm] = useState({ password: "", confirmPassword: "" });
  const [errors, setErrors] = useState({});
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function validate() {
    const next = {
      password: validatePassword(form.password),
      confirmPassword:
        !form.confirmPassword
          ? "Confirm the new password."
          : form.password !== form.confirmPassword
            ? "Passwords do not match."
            : "",
    };
    Object.keys(next).forEach((key) => !next[key] && delete next[key]);
    setErrors(next);
    return token && Object.keys(next).length === 0;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (!token) {
      setError("This password-reset link is incomplete. Request a new link from the login page.");
      return;
    }
    if (!validate()) return;

    setSubmitting(true);
    setError("");
    setMessage("");
    try {
      const response = await api.post("/auth/reset-password", {
        token,
        new_password: form.password,
      });
      setMessage(response.data.message);
      setForm({ password: "", confirmPassword: "" });
    } catch (requestError) {
      setError(apiErrorMessage(requestError, "Could not reset the password."));
    } finally {
      setSubmitting(false);
    }
  }

  const missingRules = passwordRules(form.password);

  return (
    <AuthLayout
      title="Choose a new password"
      subtitle="Create a strong password. Using this link will invalidate older reset links and existing login sessions."
    >
      {!token && (
        <Alert type="error">
          This reset link does not contain a token. Request a new password-reset email.
        </Alert>
      )}

      {message ? (
        <div className="space-y-5">
          <Alert type="success">{message}</Alert>
          <Link className="atlas-button-primary flex w-full justify-center no-underline" to="/login">
            Continue to login
          </Link>
        </div>
      ) : (
        <form className="space-y-5" onSubmit={handleSubmit} noValidate>
          <label className="atlas-label">
            New password
            <input
              type="password"
              autoComplete="new-password"
              value={form.password}
              aria-invalid={Boolean(errors.password)}
              onChange={(event) => {
                setForm({ ...form, password: event.target.value });
                if (errors.password) setErrors({ ...errors, password: "" });
              }}
              className="atlas-input"
              placeholder="Create a strong password"
              maxLength={128}
            />
            <FieldError>{errors.password}</FieldError>
            <p className="atlas-help mt-2">
              {missingRules.length
                ? `Still needed: ${missingRules.join(", ")}.`
                : "Password strength requirements satisfied."}
            </p>
          </label>

          <label className="atlas-label">
            Confirm new password
            <input
              type="password"
              autoComplete="new-password"
              value={form.confirmPassword}
              aria-invalid={Boolean(errors.confirmPassword)}
              onChange={(event) => {
                setForm({ ...form, confirmPassword: event.target.value });
                if (errors.confirmPassword) setErrors({ ...errors, confirmPassword: "" });
              }}
              className="atlas-input"
              placeholder="Repeat the new password"
              maxLength={128}
            />
            <FieldError>{errors.confirmPassword}</FieldError>
          </label>

          {error && <Alert type="error">{error}</Alert>}

          <button
            type="submit"
            disabled={submitting || !token}
            className="atlas-button-primary w-full"
          >
            {submitting ? "Resetting password..." : "Reset password"}
          </button>
        </form>
      )}

      <p className="mt-6 text-center text-sm text-slate-600">
        <Link className="font-extrabold text-indigo-700 hover:underline" to="/forgot-password">
          Request another reset link
        </Link>
      </p>
    </AuthLayout>
  );
}
