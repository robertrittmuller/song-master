import { FormEvent, useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Toggle } from "../components/ui/Toggle";
import { ConfirmationModal } from "../components/ui/ConfirmationModal";
import {
  deleteSongProposal,
  fetchSettings,
  fetchSongProposals,
  generateSongProposals
} from "../services/api";
import type { SongProposal } from "../types/api";

type ProposalCount = 5 | 10;

const PROPOSAL_PLACEHOLDER =
  "Describe the creative territory: styles, artists for inspiration, emotional arc, story themes, sonic references, constraints, or anything you want the ideas to explore.";

export function SongProposalsPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: settings } = useQuery({ queryKey: ["settings"], queryFn: fetchSettings });
  const { data: proposals = [], isLoading } = useQuery({
    queryKey: ["song-proposals"],
    queryFn: fetchSongProposals
  });
  const openProposals = proposals.filter((proposal) => proposal.status !== "accepted");
  const acceptedProposals = proposals.filter((proposal) => proposal.status === "accepted");

  const [sourcePrompt, setSourcePrompt] = useState("");
  const [count, setCount] = useState<ProposalCount>(5);
  const [useLocal, setUseLocal] = useState(false);
  const [settingsInitialized, setSettingsInitialized] = useState(false);
  const [confirmDeleteProposal, setConfirmDeleteProposal] = useState<SongProposal | null>(null);

  useEffect(() => {
    if (!settings || settingsInitialized) {
      return;
    }

    setUseLocal(settings.use_local);
    setSettingsInitialized(true);
  }, [settings, settingsInitialized]);

  const generateMutation = useMutation({
    mutationFn: generateSongProposals,
    onSuccess: () => {
      setSourcePrompt("");
      queryClient.invalidateQueries({ queryKey: ["song-proposals"] });
    }
  });

  const deleteMutation = useMutation({
    mutationFn: deleteSongProposal,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["song-proposals"] })
  });

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    const normalizedPrompt = sourcePrompt.trim();
    if (!normalizedPrompt) {
      return;
    }

    generateMutation.mutate({
      source_prompt: normalizedPrompt,
      count,
      use_local: useLocal
    });
  };

  const useProposal = (proposal: SongProposal) => {
    navigate("/generate", {
      state: {
        proposalId: proposal.id,
        proposalPrompt: proposal.prompt,
        proposalTitle: proposal.title
      }
    });
  };

  const handleDelete = (proposal: SongProposal) => {
    setConfirmDeleteProposal(proposal);
  };

  const confirmDelete = () => {
    if (confirmDeleteProposal) {
      deleteMutation.mutate(confirmDeleteProposal.id);
      setConfirmDeleteProposal(null);
    }
  };

  const errorMessage = getMutationErrorMessage(generateMutation.error);

  return (
    <div className="stack song-proposals-page">
      <div className="section-title">
        <div>
          <div style={{ color: "var(--gray-400)", fontSize: 13 }}>Create</div>
          <h2 style={{ margin: 0 }}>Song Proposals</h2>
        </div>
      </div>

      <Card>
        <form onSubmit={handleSubmit} className="song-proposals-form">
          <div className="generation-field">
            <label className="generation-label" htmlFor="proposal-source-prompt">
              Creative Guidelines
            </label>
            <div className="generation-textarea-shell">
              {!sourcePrompt && (
                <span className="generation-textarea-placeholder" aria-hidden="true">
                  {PROPOSAL_PLACEHOLDER}
                </span>
              )}
              <textarea
                id="proposal-source-prompt"
                required
                value={sourcePrompt}
                onChange={(event) => setSourcePrompt(event.target.value)}
                rows={8}
                wrap="soft"
                className="generation-textarea"
              />
            </div>
            <p className="generation-help">
              Proposals follow the prompt creator guidelines and remain here until deleted.
            </p>
          </div>

          <div className="song-proposals-form__controls">
            <div className="generation-field">
              <label className="generation-label" htmlFor="proposal-count">Proposal Count</label>
              <select
                id="proposal-count"
                value={count}
                onChange={(event) => setCount(Number(event.target.value) as ProposalCount)}
                className="generation-input"
              >
                <option value={5}>5 proposals</option>
                <option value={10}>10 proposals</option>
              </select>
            </div>

            <div className="generation-field">
              <label className="generation-label">Model Location</label>
              <div className="generation-toggle-shell">
                <div>
                  <div className="generation-toggle-shell__label">{useLocal ? "Local" : "Remote"}</div>
                </div>
                <Toggle
                  value={useLocal}
                  onChange={setUseLocal}
                  leftLabel="Remote"
                  rightLabel="Local"
                />
              </div>
            </div>
          </div>

          <div className="song-proposals-form__actions">
            {generateMutation.isError && (
              <span className="generation-error">{errorMessage}</span>
            )}
            <Button type="submit" variant="ai-glow" size="lg" isLoading={generateMutation.isPending}>
              Generate Proposals
            </Button>
          </div>
        </form>
      </Card>

      <div className="song-proposals-list">
        {isLoading && <div className="generation-empty-state">Loading proposals...</div>}

        {!isLoading && proposals.length === 0 && (
          <div className="generation-empty-state">
            No saved proposals yet.
          </div>
        )}

        {!isLoading && openProposals.length > 0 && (
          <section className="song-proposals-group">
            <div className="song-proposals-group__header">
              <div>
                <div className="generation-eyebrow">Open proposals</div>
                <h3 className="song-proposals-group__title">{openProposals.length} available</h3>
              </div>
            </div>

            <div className="song-proposals-group__grid">
              {openProposals.map((proposal) => (
                <article key={proposal.id} className="song-proposal">
                  <div className="song-proposal__header">
                    <div>
                      <div className="generation-eyebrow">
                        {proposal.use_local ? "Local" : "Remote"} proposal
                      </div>
                      <h3 className="song-proposal__title">{proposal.title}</h3>
                    </div>
                    <span className="song-proposal__date">
                      {new Date(proposal.created_at).toLocaleDateString()}
                    </span>
                  </div>

                  <p className="song-proposal__prompt">{proposal.prompt}</p>

                  <div className="song-proposal__source">
                    <span>Guidelines</span>
                    <p>{proposal.source_prompt}</p>
                  </div>

                  <div className="song-proposal__actions">
                    <Button type="button" variant="ai-glow" onClick={() => useProposal(proposal)}>
                      Create Song
                    </Button>
                    <Button
                      type="button"
                      variant="danger"
                      isLoading={deleteMutation.isPending && deleteMutation.variables === proposal.id}
                      onClick={() => handleDelete(proposal)}
                    >
                      Delete
                    </Button>
                  </div>
                </article>
              ))}
            </div>
          </section>
        )}

        <details className="song-proposals-accepted">
          <summary className="song-proposals-accepted__summary">
            <span>Accepted proposals</span>
            <span className="song-proposals-accepted__count">{acceptedProposals.length}</span>
          </summary>

          <div className="song-proposals-accepted__content">
            {acceptedProposals.length === 0 ? (
              <div className="generation-empty-state generation-empty-state--compact">
                Accepted proposals will appear here after they are turned into songs.
              </div>
            ) : (
              acceptedProposals.map((proposal) => (
                <article key={proposal.id} className="song-proposal song-proposal--accepted">
                  <div className="song-proposal__header">
                    <div>
                      <div className="generation-eyebrow">
                        {proposal.use_local ? "Local" : "Remote"} proposal
                      </div>
                      <h3 className="song-proposal__title">{proposal.title}</h3>
                    </div>
                    <span className="song-proposal__status">Accepted</span>
                  </div>

                  <p className="song-proposal__prompt">{proposal.prompt}</p>

                  <div className="song-proposal__source">
                    <span>Guidelines</span>
                    <p>{proposal.source_prompt}</p>
                  </div>

                  <div className="song-proposal__actions song-proposal__actions--accepted">
                    <Button
                      type="button"
                      variant="danger"
                      isLoading={deleteMutation.isPending && deleteMutation.variables === proposal.id}
                      onClick={() => handleDelete(proposal)}
                    >
                      Delete
                    </Button>
                  </div>
                </article>
              ))
            )}
          </div>
        </details>
      <ConfirmationModal
        isOpen={confirmDeleteProposal !== null}
        onClose={() => setConfirmDeleteProposal(null)}
        onConfirm={confirmDelete}
        title="Delete Proposal"
        message={
          confirmDeleteProposal
            ? `Are you sure you want to delete the proposal "${confirmDeleteProposal.title}"? This action cannot be undone.`
            : "Are you sure you want to delete this proposal? This action cannot be undone."
        }
        confirmText="Delete"
        variant="danger"
        isConfirming={deleteMutation.isPending}
      />
      </div>
    </div>
  );
}

function getMutationErrorMessage(error: unknown): string {
  if (typeof error === "object" && error && "response" in error) {
    const response = (error as { response?: { data?: { detail?: string } } }).response;
    if (response?.data?.detail) {
      return response.data.detail;
    }
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Failed to generate proposals. Try again.";
}
