import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Loader } from "../components/common/Loader";
import { SongGrid } from "../features/library/SongGrid";
import { AlbumList } from "../features/library/AlbumList";
import { SearchBar } from "../features/library/SearchBar";
import { FilterPanel } from "../features/library/FilterPanel";
import { SortControls } from "../features/library/SortControls";
import { fetchSongs, fetchPersonas, importSongMarkdown } from "../services/api";

type SortOption = "newest" | "oldest" | "a-z" | "z-a";
type ViewMode = "grid" | "list";
type Filter = {
  status?: string;
  persona?: string;
  dateRange?: string;
};

const INITIAL_VISIBLE_SONGS = 12;
const SONG_LOAD_BATCH = 12;

export function DashboardPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [filters, setFilters] = useState<Filter>({});
  const [sortBy, setSortBy] = useState<SortOption>("newest");
  const [viewMode, setViewMode] = useState<ViewMode>("grid");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const loadMoreTriggerRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [visibleSongsCount, setVisibleSongsCount] = useState(INITIAL_VISIBLE_SONGS);

  const { data: songs = [] } = useQuery({ queryKey: ["songs"], queryFn: fetchSongs });
  const { data: personas = [] } = useQuery({ queryKey: ["personas"], queryFn: fetchPersonas });

  const importMutation = useMutation({
    mutationFn: importSongMarkdown,
    onSuccess: (song) => {
      queryClient.invalidateQueries({ queryKey: ["songs"] });
      navigate(`/songs/${song.id}`);
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail || error?.message || "Failed to import song.";
      alert(message);
    }
  });

  const personaNames = useMemo(() => personas.map((p) => p.name), [personas]);

  // Reset visible count when filters/search/sort change
  useEffect(() => {
    setVisibleSongsCount(INITIAL_VISIBLE_SONGS);
  }, [searchQuery, filters, sortBy]);

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

  const visibleSongs = useMemo(() => {
    return filteredAndSortedSongs.slice(0, visibleSongsCount);
  }, [filteredAndSortedSongs, visibleSongsCount]);

  const hasMoreSongs = visibleSongsCount < filteredAndSortedSongs.length;

  useEffect(() => {
    const trigger = loadMoreTriggerRef.current;

    if (!trigger || !hasMoreSongs) {
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0];

        if (!entry?.isIntersecting) {
          return;
        }

        setVisibleSongsCount((currentVisibleSongs) => {
          if (currentVisibleSongs >= filteredAndSortedSongs.length) {
            return currentVisibleSongs;
          }

          return Math.min(currentVisibleSongs + SONG_LOAD_BATCH, filteredAndSortedSongs.length);
        });
      },
      {
        rootMargin: "0px 0px 320px 0px"
      }
    );

    observer.observe(trigger);

    return () => {
      observer.disconnect();
    };
  }, [filteredAndSortedSongs.length, hasMoreSongs]);

  return (
    <div className="stack" style={{ gap: 20 }}>
      <div className="section-title">
        <div>
          <div style={{ color: "var(--gray-400)", fontSize: "var(--text-sm)" }}>Workspace</div>
          <h2>Albums & Songs</h2>
        </div>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <input
            ref={fileInputRef}
            type="file"
            accept=".md,text/markdown"
            style={{ display: "none" }}
            onChange={(event) => {
              const file = event.target.files?.[0];
              if (!file) return;
              importMutation.mutate(file);
              event.target.value = "";
            }}
          />
          <Button
            variant="ai-glow"
            onClick={() => fileInputRef.current?.click()}
            isLoading={importMutation.isPending}
          >
            Import
          </Button>
          <Button to="/generate" variant="ai-glow">
            + New Song
          </Button>
        </div>
      </div>

      <Card title="Albums">
        <AlbumList />
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
              <Button to="/generate">
                Create Your First Song
              </Button>
            )}
          </div>
        </Card>
      ) : (
        <div className="stack" style={{ gap: 16 }}>
          <SongGrid
            songs={visibleSongs}
            viewMode={viewMode}
            totalSongsCount={filteredAndSortedSongs.length}
          />

          {hasMoreSongs && (
            <div
              ref={loadMoreTriggerRef}
              className="song-grid__load-more"
              aria-live="polite"
              aria-label="Loading more songs as you scroll"
            >
              <Loader size={18} className="song-grid__load-more-spinner" />
              <span className="song-grid__load-more-text">
                Loading more songs...
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
