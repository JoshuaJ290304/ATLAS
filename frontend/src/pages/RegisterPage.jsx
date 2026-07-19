import { useMemo, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";

import AuthLayout from "../components/AuthLayout";
import { Alert, FieldError } from "../components/UI";
import { useAuth } from "../context/AuthContext";
import {
  apiErrorMessage,
  clean,
  passwordRules,
  validateEmail,
  validatePassword,
  validateRequired,
} from "../utils/validation";

export default function RegisterPage() {
  const navigate = useNavigate();
  const { isAuthenticated, register } = useAuth();
  const [form, setForm] = useState({ name: "", email: "", password: "", confirmPassword: "" });
  const [errors, setErrors] = useState({});
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const strength = useMemo(() => 4 - passwordRules(form.password).length, [form.password]);

  if (isAuthenticated) return <Navigate to="/" replace />;

  function validate() {
    const next = {
      name: validateRequired(form.name, "Full name", 2, 120),
      email: validateEmail(form.email),
      password: validatePassword(form.password),
      confirmPassword:
        !form.confirmPassword
          ? "Confirm your password."
          : form.password !== form.confirmPassword
            ? "Passwords do not match."
            : "",
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
      await register({
        name: clean(form.name),
        email: clean(form.email).toLowerCase(),
        password: form.password,
      });
      navigate("/");
    } catch (requestError) {
      setError(apiErrorMessage(requestError, "Registration failed. Review the highlighted fields."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthLayout title="Create your account" subtitle="Start a secure traceability workspace for your software project.">
      <form className="space-y-5" onSubmit={handleSubmit} noValidate>
        <label className="atlas-label">
          Full name
          <input
            autoComplete="name"
            value={form.name}
            aria-invalid={Boolean(errors.name)}
            onChange={(event) => {
              setForm({ ...form, name: event.target.value });
              if (errors.name) setErrors({ ...errors, name: "" });
            }}
            className="atlas-input"
            placeholder="Joshua J"
            maxLength={120}
          />
          <FieldError>{errors.name}</FieldError>
        </label>
        <label className="atlas-label">
          Email address
          <input
            type="email"
            autoComplete="email"
            value={form.email}
            aria-invalid={Boolean(errors.email)}
            onChange={(event) => {
              setForm({ ...form, email: event.target.value });
              if (errors.email) setErrors({ ...errors, email: "" });
            }}
            className="atlas-input"
            placeholder="you@example.com"
            maxLength={320}
          />
          <FieldError>{errors.email}</FieldError>
        </label>
        <label className="atlas-label">
          Password
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
            placeholder="At least 8 characters"
            maxLength={128}
          />
          <div className="mt-2 grid grid-cols-4 gap-1.5" aria-label={`Password strength ${strength} of 4`}>
            {[1, 2, 3, 4].map((item) => (
              <span key={item} className={`h-1.5 rounded-full ${item <= strength ? "bg-indigo-500" : "bg-slate-200"}`} />
            ))}
          </div>
          <p className="atlas-help">Use uppercase, lowercase, and a number.</p>
          <FieldError>{errors.password}</FieldError>
        </label>
        <label className="atlas-label">
          Confirm password
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
            placeholder="Repeat your password"
            maxLength={128}
          />
          <FieldError>{errors.confirmPassword}</FieldError>
        </label>
        {error && <Alert type="error">{error}</Alert>}
        <button type="submit" disabled={submitting} className="atlas-button-primary w-full">
          {submitting ? "Creating account..." : "Create secure account"}
        </button>
      </form>
      <p className="mt-6 text-center text-sm text-slate-600">
        Already registered?{" "}
        <Link className="font-extrabold text-indigo-700 hover:underline" to="/login">
          Log in
        </Link>
      </p>
    </AuthLayout>
  );
}
