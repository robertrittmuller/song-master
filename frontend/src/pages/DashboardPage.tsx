import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { Card } from "../components/ui/Card";
import { SongGrid } from "../features/library/SongGrid";
import { ProjectList } from "../features/library/ProjectList";
import { SearchBar } from "../features/library/SearchBar";
import { FilterPanel } from "../features/library/FilterPanel";
import { SortControls } from "../features/library/SortControls";
import { fetchSongs, fetchPersonas } from "../services/api";
import type { Song } from "../types/api";

type SortOption = "newest" | "oldest" | "a-z" | "z-a";
type ViewMode = "grid" | "list";
type Filter = {
  status?: string;
  persona?: string;
  dateRange?: string;
};

export function DashboardPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [filters, setFilters] = useState<Filter>({});
  const [sortBy, setSortBy] = useState<SortOption>("newest");
  const [viewMode, setViewMode] = useState<ViewMode>("grid");

  const { data: songs = [] } = useQuery({ queryKey: ["songs"], queryFn: fetchSongs });
  const { data: personas = [] } = useQuery({ queryKey: ["personas"], queryFn: fetchPersonas });

  const personaNames = useMemo(() => personas.map((p) => p.name), [personas]);

  // Filter and sort songs
  const filteredAndSortedSongs = useMemo(() => {
    let result = [...songs];

    // Apply search
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (song) =>
          song.title.toLowerCase().includes(query) ||
          song.user_prompt?.toLowerCase().includes(query)
      );
    }

    // Apply filters
    if (filters.status) {
      result = result.filter((song) => song.status === filters.status);
    }
    if (filters.persona) {
      result = result.filter((song) => song.persona === filters.persona);
    }
    if (filters.dateRange) {
      const days = parseInt(filters.dateRange);
      const cutoffDate = new Date();
      cutoffDate.setDate(cutoffDate.getDate() - days);
      result = result.filter((song) => new Date(song.created_at) >= cutoffDate);
    }

    // Apply sorting
    switch (sortBy) {
      case "newest":
        result.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
        break;
      case "oldest":
        result.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
        break;
      case "a-z":
        result.sort((a, b) => a.title.localeCompare(b.title));
        break;
      case "z-a":
        result.sort((a, b) => b.title.localeCompare(a.title));
        break;
    }

    return result;
  }, [songs, searchQuery, filters, sortBy]);

  return (
    <div className="stack" style={{ gap: 20 }}>
      <div className="section-title">
        <div>
          <div style={{ color: "var(--gray-400)", fontSize: "var(--text-sm)" }}>Workspace</div>
          <h2>Albums & Songs</h2>
        </div>
        <Link to="/generate" className="btn">
          + New Song
        </Link>
      </div>

      <Card title="Albums">
        <ProjectList />
      </Card>

      {/* Search, Filter, Sort Controls */}
      <Card>
        <div className="stack" style={{ gap: 16 }}>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap", justifyContent: "space-between", alignItems: "flex-start" }}>
            <div style={{ flex: "1 1 300px", minWidth: 250 }}>
              <SearchBar value={searchQuery} onChange={setSearchQuery} />
            </div>
            <SortControls
              sortBy={sortBy}
              onSortChange={setSortBy}
              viewMode={viewMode}
              onViewModeChange={setViewMode}
            />
          </div>
          <FilterPanel filters={filters} onChange={setFilters} personas={personaNames} />
        </div>
      </Card>

      {/* Songs Grid/List */}
      {filteredAndSortedSongs.length === 0 ? (
        <Card>
          <div style={{ textAlign: "center", padding: "40px 20px" }}>
            <div style={{ fontSize: "var(--text-2xl)", marginBottom: 8 }}>🎵</div>
            <h3 style={{ color: "var(--gray-300)", marginBottom: 8 }}>No songs found</h3>
            <p style={{ color: "var(--gray-400)", marginBottom: 16 }}>
              {searchQuery || Object.values(filters).some(Boolean)
                ? "Try adjusting your search or filters"
                : "Get started by creating your first song"}
            </p>
            {!searchQuery && !Object.values(filters).some(Boolean) && (
              <Link to="/generate" className="btn">
                Create Your First Song
              </Link>
            )}
          </div>
        </Card>
      ) : (
        <SongGrid songs={filteredAndSortedSongs} viewMode={viewMode} />
      )}
    </div>
  );
}
