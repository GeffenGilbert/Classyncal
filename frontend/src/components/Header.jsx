function Header() {
  return (
    <header className="flex items-center gap-3 px-8 py-6">
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
    </header>
  );
}

export default Header;
