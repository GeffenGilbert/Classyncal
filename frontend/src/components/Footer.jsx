import ThemeToggle from "./ThemeToggle";

// The privacy policy has to be reachable from the home page, not just by URL -
// Google's OAuth verification reviewers check for the link, not only the page.
function Footer() {
  return (
    // `relative` + an absolutely placed toggle so the links stay optically
    // centred on the page rather than being pushed off-centre by it. The
    // top-right corner is already taken by the Google-access disclosure.
    <footer className="relative flex items-center justify-center gap-4 px-8 py-6 text-sm text-slate-500 dark:text-slate-400">
      <div className="absolute left-8 top-1/2 -translate-y-1/2 text-xs leading-tight text-slate-400 dark:text-slate-500">
        <p>any issues?</p>
        <p>
          contact us at:{" "}
          <a
            href="mailto:classyncalofficial@gmail.com"
            className="hover:text-slate-600 dark:hover:text-slate-300"
          >
            classyncalofficial@gmail.com
          </a>
        </p>
      </div>
      <a href="/privacy/" className="hover:text-slate-800 dark:hover:text-slate-100">
        Privacy Policy
      </a>
      <span aria-hidden="true">&middot;</span>
      <a href="/terms/" className="hover:text-slate-800 dark:hover:text-slate-100">
        Terms of Service
      </a>
      <ThemeToggle className="absolute right-8 top-1/2 -translate-y-1/2" />
    </footer>
  );
}

export default Footer;
