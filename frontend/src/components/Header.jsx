function Header() {
  return (
    <header className="flex items-center gap-3 px-8 py-6">
      <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-500 font-semibold text-white">
        C
      </div>
      <span className="text-lg font-medium tracking-tight text-slate-900">
        Company Name
      </span>
    </header>
  );
}

export default Header;
