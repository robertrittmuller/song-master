import { GenerationForm } from "../features/generation/GenerationForm";

export function GeneratePage() {
  return (
    <div className="stack" style={{ gap: 20 }}>
      <div className="section-title">
        <div>
          <div style={{ color: "var(--gray-400)", fontSize: 13 }}>Create</div>
          <h2 style={{ margin: 0 }}>New Song</h2>
        </div>
      </div>
      <GenerationForm />
    </div>
  );
}
