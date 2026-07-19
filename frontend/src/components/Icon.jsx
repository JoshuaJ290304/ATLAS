const paths = {
  atlas: <><path d="M12 3 3.8 20h3.7l1.4-3.3h6.2l1.4 3.3h3.7L12 3Z"/><path d="m10.1 13.8 1.9-4.5 1.9 4.5h-3.8Z"/></>,
  home: <><path d="m3 11 9-8 9 8"/><path d="M5 10v10h14V10"/><path d="M9 20v-6h6v6"/></>,
  document: <><path d="M6 2h8l4 4v16H6z"/><path d="M14 2v5h5"/><path d="M9 12h6M9 16h6"/></>,
  requirement: <><path d="M5 4h14v16H5z"/><path d="m8 9 1.5 1.5L12 8M8 15h8"/></>,
  governance: <><path d="M7 3h10v4H7z"/><path d="M5 7h14v14H5z"/><path d="m8 13 2 2 5-5"/><path d="M8 18h8"/></>,
  baseline: <><path d="M4 5h16v14H4z"/><path d="M8 3v4M16 3v4M4 10h16"/><path d="M8 14h3M8 17h7"/></>,
  comment: <><path d="M4 5h16v11H9l-5 4z"/><path d="M8 9h8M8 12h5"/></>,
  send: <><path d="m3 11 18-8-7 18-3-7z"/><path d="m11 14 4-4"/></>,
  compare: <><path d="M8 4H4v16h4M16 4h4v16h-4"/><path d="M9 8h6M9 12h6M9 16h6"/></>,
  history: <><path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5M12 7v5l3 2"/></>,
  trace: <><circle cx="6" cy="6" r="3"/><circle cx="18" cy="18" r="3"/><path d="m8.5 8.5 7 7M15.5 6H18v2.5M8.5 18H6v-2.5"/></>,
  impact: <><path d="M12 2 3 21h18L12 2Z"/><path d="M12 9v5M12 18h.01"/></>,
  assistant: <><path d="M8 3h8l1 4h3v10h-3l-2 4H9l-2-4H4V7h3z"/><circle cx="9" cy="12" r="1"/><circle cx="15" cy="12" r="1"/></>,
  analytics: <><path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/></>,
  plus: <path d="M12 5v14M5 12h14"/>,
  refresh: <><path d="M20 6v5h-5"/><path d="M4 18v-5h5"/><path d="M18.5 9A7 7 0 0 0 6 6.5L4 11M5.5 15A7 7 0 0 0 18 17.5l2-4.5"/></>,
  download: <><path d="M12 3v12M7 10l5 5 5-5"/><path d="M5 21h14"/></>,
  upload: <><path d="M12 21V9M7 14l5-5 5 5"/><path d="M5 3h14"/></>,
  trash: <><path d="M4 7h16M9 7V4h6v3M7 7l1 14h8l1-14M10 11v6M14 11v6"/></>,
  edit: <><path d="m4 20 4.5-1 10-10-3.5-3.5-10 10L4 20Z"/><path d="m13.5 7 3.5 3.5"/></>,
  search: <><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/></>,
  check: <path d="m5 12 4 4L19 6"/>,
  alert: <><path d="M12 3 2.8 20h18.4L12 3Z"/><path d="M12 9v4M12 17h.01"/></>,
  info: <><circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7h.01"/></>,
  menu: <path d="M4 7h16M4 12h16M4 17h16"/>,
  close: <path d="m6 6 12 12M18 6 6 18"/>,
  arrowRight: <path d="M5 12h14M14 7l5 5-5 5"/>,
  arrowLeft: <path d="M19 12H5M10 7l-5 5 5 5"/>,
  logout: <><path d="M10 4H5v16h5"/><path d="M14 8l4 4-4 4M18 12H9"/></>,
  activity: <path d="M3 12h4l2-6 4 12 2-6h6"/>,
  shield: <><path d="M12 3 5 6v5c0 5 3 8 7 10 4-2 7-5 7-10V6z"/><path d="m9 12 2 2 4-4"/></>,
  clock: <><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></>,
};

export default function Icon({ name, className = "h-5 w-5", strokeWidth = 1.8 }) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      {paths[name] || paths.info}
    </svg>
  );
}
