const STEPS = [
  "Upload your syllabus",
  "Review and edit the details",
  "Sign into your Google account", 
  "Watch as everything automatically gets added to your Google Calendar", 
];

function HowItWorks() {
  return (
    // This sits outside the centered column, so its left inset has to be capped
    // or it slides under the upload box on a narrower window - opening a browser
    // sidebar is enough to trigger it. 508px is half the max-w-xl content (288)
    // + a 40px gutter + this aside's own 180px, so past that point it tracks the
    // box at a constant gutter instead of overlapping it. Under ~1060px there is
    // no room beside the box at all and it is hidden rather than shrunk.
    <aside className="fixed left-[min(7rem,calc(50%_-_508px))] top-[50%] hidden w-[180px] -translate-y-1/2 flex-col gap-6 min-[1060px]:flex">
      <p className="text-xs font-medium uppercase tracking-wider text-slate-400 dark:text-slate-500">
        How it works
      </p>
      {STEPS.map((step, index) => (
        <div key={step} className="flex items-start gap-3">
          <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-slate-300 dark:border-slate-700 text-xs text-slate-400 dark:text-slate-500">
            {index + 1}
          </span>
          <p className="text-sm text-slate-400 dark:text-slate-500">{step}</p>
        </div>
      ))}
    </aside>
  );
}

export default HowItWorks;
