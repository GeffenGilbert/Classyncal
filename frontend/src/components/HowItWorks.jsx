const STEPS = [
  "Upload your syllabus",
  "Review and edit the details",
  "Sign into your Google account", 
  "Watch as everything automatically gets added to your Google Calendar", 
];

function HowItWorks() {
  return (
    <aside className="fixed left-28 top-[50%] hidden w-[180px] -translate-y-1/2 flex-col gap-6 lg:flex">
      <p className="text-xs font-medium uppercase tracking-wider text-slate-400">
        How it works
      </p>
      {STEPS.map((step, index) => (
        <div key={step} className="flex items-start gap-3">
          <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-slate-300 text-xs text-slate-400">
            {index + 1}
          </span>
          <p className="text-sm text-slate-400">{step}</p>
        </div>
      ))}
    </aside>
  );
}

export default HowItWorks;
