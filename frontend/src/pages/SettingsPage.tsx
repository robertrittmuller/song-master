import { useQuery } from "@tanstack/react-query";

import { Card } from "../components/ui/Card";
import { fetchSettings } from "../services/api";

export function SettingsPage() {
  const { data: settings } = useQuery({ queryKey: ["settings"], queryFn: fetchSettings });

  return (
    <div className="stack" style={{ gap: 20 }}>
      <div className="section-title">
        <div>
          <div style={{ color: "var(--gray-400)", fontSize: 13 }}>Preferences</div>
          <h2 style={{ margin: 0 }}>Settings</h2>
        </div>
      </div>

      <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(280px,1fr))" }}>
        <Card title="LLM Config">
          <div className="stack">
            <div className="glass">
              <div style={{ fontWeight: 700 }}>Provider</div>
              <div style={{ color: "var(--gray-400)" }}>{settings?.llm_provider ?? "openrouter"}</div>
            </div>
            <div className="glass">
              <div style={{ fontWeight: 700 }}>Model</div>
              <div style={{ color: "var(--gray-400)" }}>{settings?.model ?? "gpt-4o-mini"}</div>
            </div>
            <div className="glass">
              <div style={{ fontWeight: 700 }}>Temperature</div>
              <div style={{ color: "var(--gray-400)" }}>{settings?.temperature ?? 0.6}</div>
            </div>
          </div>
        </Card>

        <Card title="Generation Defaults">
          <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(160px,1fr))" }}>
            {settings &&
              Object.entries(settings.generation).map(([key, value]) => (
                <div key={key} className="glass">
                  <div style={{ fontWeight: 700, textTransform: "capitalize" }}>{key}</div>
                  <div style={{ color: "var(--gray-400)" }}>{String(value ?? "—")}</div>
                </div>
              ))}
          </div>
        </Card>

        <Card title="UI Preferences">
          <div className="stack">
            <div className="glass">
              <div style={{ fontWeight: 700 }}>Theme</div>
              <div style={{ color: "var(--gray-400)" }}>{settings?.ui?.theme ?? "dark"}</div>
            </div>
            <div className="glass">
              <div style={{ fontWeight: 700 }}>Notifications</div>
              <div style={{ color: "var(--gray-400)" }}>Toast + live logs enabled</div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
