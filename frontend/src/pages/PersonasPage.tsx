import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { fetchPersonas, deletePersona, createPersona, updatePersona } from "../services/api";
import { Persona } from "../types/api";

export function PersonasPage() {
  const queryClient = useQueryClient();
  const { data: personas = [], isLoading } = useQuery({
    queryKey: ["personas"],
    queryFn: fetchPersonas
  });

  const [editingPersona, setEditingPersona] = useState<Persona | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  const deleteMutation = useMutation({
    mutationFn: deletePersona,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["personas"] });
    }
  });

  const saveMutation = useMutation({
    mutationFn: async (persona: Persona) => {
      if (isCreating) {
        return createPersona({
          name: persona.name,
          styles: persona.styles || "",
          visual_styles: persona.visual_styles
        });
      } else {
        return updatePersona(persona.name, {
          styles: persona.styles || "",
          visual_styles: persona.visual_styles
        });
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["personas"] });
      setEditingPersona(null);
      setIsCreating(false);
    }
  });

  const handleEdit = (persona: Persona) => {
    setEditingPersona(persona);
    setIsCreating(false);
  };

  const handleDelete = (name: string) => {
    if (window.confirm(`Are you sure you want to delete the persona "${name}"?`)) {
      deleteMutation.mutate(name);
    }
  };

  const handleCreate = () => {
    setEditingPersona({ name: "", styles: "", visual_styles: "" });
    setIsCreating(true);
  };

  if (isLoading) return <div>Loading personas...</div>;

  return (
    <div className="stack" style={{ gap: 20 }}>
      <div className="section-title">
        <div>
          <div style={{ color: "var(--gray-400)", fontSize: 13 }}>Management</div>
          <h2 style={{ margin: 0 }}>Personas</h2>
        </div>
        <Button onClick={handleCreate}>+ New Persona</Button>
      </div>

      {personas.length === 0 ? (
        <Card>
          <div style={{ textAlign: "center", padding: "40px 20px" }}>
            <div style={{ fontSize: "var(--text-2xl)", marginBottom: 8 }}>👤</div>
            <h3 style={{ color: "var(--gray-300)", marginBottom: 8 }}>No personas found</h3>
            <p style={{ color: "var(--gray-400)", marginBottom: 16 }}>
              Create your first persona to get started
            </p>
            <Button onClick={handleCreate}>Create Your First Persona</Button>
          </div>
        </Card>
      ) : (
        <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: 20 }}>
          {personas.map((persona) => (
            <Card key={persona.name} title={persona.name}>
            <div className="stack" style={{ gap: 12 }}>
              <div>
                <div style={{ fontWeight: 700, fontSize: 12, color: "var(--gray-400)", marginBottom: 4 }}>STYLES</div>
                <div style={{ fontSize: 14, color: "var(--gray-200)" }}>{persona.styles || "No styles defined"}</div>
              </div>
              {persona.visual_styles && (
                <div>
                  <div style={{ fontWeight: 700, fontSize: 12, color: "var(--gray-400)", marginBottom: 4 }}>VISUAL STYLES</div>
                  <div style={{ fontSize: 14, color: "var(--gray-200)" }}>{persona.visual_styles}</div>
                </div>
              )}
              <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                <Button variant="secondary" onClick={() => handleEdit(persona)}>Edit</Button>
                <Button variant="ghost" onClick={() => handleDelete(persona.name)} style={{ color: "#ff4d4d" }}>Delete</Button>
              </div>
            </div>
          </Card>
        ))}
      </div>
      )}

      {(editingPersona || isCreating) && (
        <div style={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: "rgba(0,0,0,0.8)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 1000,
          padding: 20
        }}>
          <div style={{ width: "100%", maxWidth: 600 }}>
            <Card title={isCreating ? "Create New Persona" : `Edit Persona: ${editingPersona?.name}`}>
              <form onSubmit={(e) => {
              e.preventDefault();
              if (editingPersona) saveMutation.mutate(editingPersona);
            }} className="stack" style={{ gap: 16 }}>
              <div className="stack" style={{ gap: 8 }}>
                <label style={{ fontWeight: 600 }}>Name</label>
                <input
                  type="text"
                  value={editingPersona?.name}
                  onChange={(e) => setEditingPersona(prev => prev ? { ...prev, name: e.target.value } : null)}
                  disabled={!isCreating}
                  required
                  className="glass"
                  style={{ width: "100%", padding: "10px 12px", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, background: "rgba(255,255,255,0.05)", color: "white" }}
                />
              </div>
              <div className="stack" style={{ gap: 8 }}>
                <label style={{ fontWeight: 600 }}>Persona Styles</label>
                <textarea
                  value={editingPersona?.styles}
                  onChange={(e) => setEditingPersona(prev => prev ? { ...prev, styles: e.target.value } : null)}
                  required
                  rows={4}
                  className="glass"
                  style={{ width: "100%", padding: "10px 12px", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, background: "rgba(255,255,255,0.05)", color: "white" }}
                />
              </div>
              <div className="stack" style={{ gap: 8 }}>
                <label style={{ fontWeight: 600 }}>Visual Styles</label>
                <textarea
                  value={editingPersona?.visual_styles}
                  onChange={(e) => setEditingPersona(prev => prev ? { ...prev, visual_styles: e.target.value } : null)}
                  rows={4}
                  className="glass"
                  style={{ width: "100%", padding: "10px 12px", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, background: "rgba(255,255,255,0.05)", color: "white" }}
                />
              </div>
              <div style={{ display: "flex", gap: 12, justifyContent: "flex-end", marginTop: 8 }}>
                <Button variant="secondary" type="button" onClick={() => { setEditingPersona(null); setIsCreating(false); }}>Cancel</Button>
                <Button type="submit" disabled={saveMutation.isPending}>
                  {saveMutation.isPending ? "Saving..." : isCreating ? "Create Persona" : "Save Changes"}
                </Button>
                </div>
              </form>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
