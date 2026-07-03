import MouseTrail from "./components/MouseTrail";
import Header from "./components/Header";
import HowItWorks from "./components/HowItWorks";
import SyllabusUploader from "./components/SyllabusUploader";

function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <MouseTrail />

      <Header />

      <HowItWorks />

      <main className="flex flex-1 flex-col items-center justify-center gap-10 px-6 pb-24">
        <SyllabusUploader />
      </main>
    </div>
  );
}

export default App;
