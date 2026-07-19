const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function clean(value) {
  return String(value ?? "").replace(/\s+/g, " ").trim();
}

export function validateRequired(value, label, minimum = 1, maximum = Infinity) {
  const normalized = clean(value);
  if (!normalized) return `${label} is required.`;
  if (normalized.length < minimum) return `${label} must be at least ${minimum} characters.`;
  if (normalized.length > maximum) return `${label} must be at most ${maximum} characters.`;
  return "";
}

export function validateEmail(value) {
  const normalized = clean(value).toLowerCase();
  if (!normalized) return "Email is required.";
  if (!emailPattern.test(normalized)) return "Enter a valid email address.";
  return "";
}

export function passwordRules(value) {
  const messages = [];
  if (value.length < 8) messages.push("at least 8 characters");
  if (!/[a-z]/.test(value)) messages.push("a lowercase letter");
  if (!/[A-Z]/.test(value)) messages.push("an uppercase letter");
  if (!/\d/.test(value)) messages.push("a number");
  return messages;
}

export function validatePassword(value) {
  if (!value) return "Password is required.";
  const missing = passwordRules(value);
  return missing.length ? `Password needs ${missing.join(", ")}.` : "";
}

export function validateFile(file, maxBytes = 10 * 1024 * 1024) {
  if (!file) return "Choose a PDF or DOCX file.";
  const extension = file.name.split(".").pop()?.toLowerCase();
  if (!["pdf", "docx"].includes(extension)) return "Only PDF and DOCX files are accepted.";
  if (file.size <= 0) return "The selected file is empty.";
  if (file.size > maxBytes) return "The file must be 10 MB or smaller.";
  return "";
}

export function apiErrorMessage(error, fallback) {
  if (error?.code === "ECONNABORTED") {
    return "The request took too long. Check the service status and try again.";
  }
  if (!error?.response) {
    return "ATLAS could not reach the application service. Check Docker and your network connection.";
  }
  const detail = error.response.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length) {
    return detail.map((item) => item.msg || "Invalid value").join(" ");
  }
  if (error.response.status >= 500) {
    return "The service encountered an unexpected error. Try again or review the backend logs.";
  }
  return fallback;
}
