import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { deleteProject, fetchProjects } from "../../services/api";
import type { Project } from "../../types/api";

export function ProjectList() {
  const queryClient = useQueryClient();
  const { data: projects = [], isLoading } = useQuery({ queryKey: ["projects"], queryFn: fetchProjects });

  const deleteMutation = useMutation({
    mutationFn: deleteProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    }
  });

  if (isLoading) {
    return <p style={{ color: "var(--gray-400)" }}>Loading albums...</p>;
  }

  return (
    <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(240px,1fr))", gap: 14 }}>
      {projects.map((project: Project) => (
        <div key={project.id} className="glass" style={{ padding: 14, borderRadius: 14 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <div style={{ fontWeight: 800 }}>{project.name}</div>
              <div style={{ color: "var(--gray-400)", fontSize: 13 }}>{project.description || "No description"}</div>
            </div>
            <button
              type="button"
              className="btn secondary"
              style={{ padding: "8px 10px" }}
              onClick={() => {
                if (deleteMutation.isPending) return;
                if (!confirm(`Delete album "${project.name}"? This will remove its songs.`)) return;
                deleteMutation.mutate(project.id);
              }}
            >
              Delete
            </button>
          </div>
          <div style={{ color: "var(--gray-500)", fontSize: 12, marginTop: 8 }}>
            Created: {new Date(project.created_at).toLocaleDateString()}
          </div>
        </div>
      ))}
      {projects.length === 0 && <p style={{ color: "var(--gray-500)" }}>No albums yet.</p>}
    </div>
  );
}
