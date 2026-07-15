import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";

import AuthLayout from "../components/AuthLayout";
import { Alert, FieldError } from "../components/UI";
import { useAuth } from "../context/AuthContext";
import { apiErrorMessage, clean, validateEmail, validatePassword } from "../utils/validation";

export default function LoginPage() {
  const navigate = useNavigate();
  const { isAuthenticated, login } = useAuth();
  const [form, setForm] = useState({ email: "", password: "" });
  const [errors, setErrors] = useState({});
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (isAuthenticated) return <Navigate to="/" replace />;

  function validate() {
    const next = {
      email: validateEmail(form.email),
      password: validatePassword(form.password),
    };
    Object.keys(next).forEach((key) => !next[key] && delete next[key]);
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (!validate()) return;
    setError("");
    setSubmitting(true);
    try {
      await login(clean(form.email).toLowerCase(), form.password);
      navigate("/");
    } catch (requestError) {
      setError(apiErrorMessage(requestError, "Unable to log in. Check your email and password."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthLayout title="Welcome back" subtitle="Log in to continue to your project intelligence workspace.">
      <form className="space-y-5" onSubmit={handleSubmit} noValidate>
        <label className="atlas-label">
          Email address
          <input
            type="email"
            autoComplete="email"
            value={form.email}
            aria-invalid={Boolean(errors.email)}
            onBlur={() => setErrors((current) => ({ ...current, email: validateEmail(form.email) }))}
            onChange={(event) => {
              setForm({ ...form, email: event.target.value });
              if (errors.email) setErrors({ ...errors, email: "" });
            }}
            className="atlas-input"
            placeholder="you@example.com"
          />
          <FieldError>{errors.email}</FieldError>
        </label>
        <label className="atlas-label">
          Password
          <input
            type="password"
            autoComplete="current-password"
            value={form.password}
            aria-invalid={Boolean(errors.password)}
            onChange={(event) => {
              setForm({ ...form, password: event.target.value });
              if (errors.password) setErrors({ ...errors, password: "" });
            }}
            className="atlas-input"
            placeholder="Your password"
          />
          <FieldError>{errors.password}</FieldError>
        </label>
        {error && <Alert type="error">{error}</Alert>}
        <button disabled={submitting} className="atlas-button-primary w-full">
          {submitting ? "Signing in..." : "Log in securely"}
        </button>
      </form>
      <p className="mt-6 text-center text-sm text-slate-600">
        New to ATLAS?{" "}
        <Link className="font-extrabold text-indigo-700 hover:underline" to="/register">
          Create an account
        </Link>
      </p>
    </AuthLayout>
  );
}
