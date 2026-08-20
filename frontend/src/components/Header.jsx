function Header() {
  return (
    <header className="flex flex-col gap-1 px-8 py-6">
      <div className="flex items-center gap-3">
        <img
          src="/logo.png"
          alt=""
          width="36"
          height="36"
          className="h-9 w-9 rounded-lg"
        />
        <span className="text-lg font-medium tracking-tight text-slate-900">
          Classyncal
        </span>
      </div>
      <p className="text-sm italic text-slate-500">
        Turns your syllabus into Google Calendar events and Tasks automatically.
      </p>
    </header>
  );
}

export default Header;
