// The privacy policy has to be reachable from the home page, not just by URL -
// Google's OAuth verification reviewers check for the link, not only the page.
function Footer() {
  return (
    <footer className="flex items-center justify-center gap-4 px-8 py-6 text-sm text-slate-500">
      <a href="/privacy/" className="hover:text-slate-800">
        Privacy Policy
      </a>
      <span aria-hidden="true">&middot;</span>
      <a href="/terms/" className="hover:text-slate-800">
        Terms of Service
      </a>
    </footer>
  );
}

export default Footer;
