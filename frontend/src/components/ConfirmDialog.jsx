import { useEffect, useRef, useState } from "react";

import Icon from "./Icon";

function ConfirmDialog({ title, message, confirmLabel, tone, onResolve }) {
  const cancelRef = useRef(null);
  const confirmRef = useRef(null);

  useEffect(() => {
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    confirmRef.current?.focus();

    function onKeyDown(event) {
      if (event.key === "Escape") {
        event.preventDefault();
        onResolve(false);
      }
      if (event.key === "Tab") {
        const first = cancelRef.current;
        const last = confirmRef.current;
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last?.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first?.focus();
        }
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [onResolve]);

  return (
    <div className="atlas-dialog-backdrop" onMouseDown={() => onResolve(false)}>
      <section
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="atlas-confirm-title"
        aria-describedby="atlas-confirm-message"
        className="atlas-dialog"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className={`atlas-dialog-icon ${tone === "danger" ? "is-danger" : ""}`}>
          <Icon name={tone === "danger" ? "alert" : "info"} className="h-5 w-5" />
        </div>
        <div className="min-w-0">
          <h2 id="atlas-confirm-title">{title}</h2>
          <p id="atlas-confirm-message">{message}</p>
        </div>
        <div className="atlas-dialog-actions">
          <button ref={cancelRef} type="button" className="atlas-button-secondary" onClick={() => onResolve(false)}>
            Cancel
          </button>
          <button
            ref={confirmRef}
            type="button"
            className={tone === "danger" ? "atlas-button-danger" : "atlas-button-primary"}
            onClick={() => onResolve(true)}
          >
            {confirmLabel}
          </button>
        </div>
      </section>
    </div>
  );
}

export function useConfirmDialog() {
  const [options, setOptions] = useState(null);
  const resolver = useRef(null);

  function confirm({
    title = "Confirm action",
    message = "Are you sure you want to continue?",
    confirmLabel = "Continue",
    tone = "danger",
  } = {}) {
    return new Promise((resolve) => {
      resolver.current = resolve;
      setOptions({ title, message, confirmLabel, tone });
    });
  }

  function resolveDialog(result) {
    resolver.current?.(result);
    resolver.current = null;
    setOptions(null);
  }

  return {
    confirm,
    confirmationDialog: options ? <ConfirmDialog {...options} onResolve={resolveDialog} /> : null,
  };
}
