import { FormEvent, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { AuthShell } from "../components/auth/AuthShell";
import { Button } from "../components/ui/Button";
import { useAuth } from "../features/auth/AuthProvider";

type LocationState = {
  from?: string;
};

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const redirectTarget = (location.state as LocationState | undefined)?.from || "/";

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setErrorMessage(null);

    if (!identifier.trim() || !password) {
      setErrorMessage("Enter your username or email and password.");
      return;
    }

    setIsSubmitting(true);
    try {
      await login({ identifier, password });
      navigate(redirectTarget, { replace: true });
    } catch (error: any) {
      const message = error?.response?.data?.detail || error?.message || "Unable to sign in.";
      setErrorMessage(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AuthShell
      eyebrow="Welcome back"
      title="Sign in to your private songwriting workspace"
      description="Use the same Song Master identity to pick up your drafts, generation history, and account-scoped backups."
      footerLabel="Need an account?"
      footerLink="/signup"
      footerLinkLabel="Create one"
    >
      <form className="auth-form" onSubmit={handleSubmit}>
        <label className="generation-field">
          <span className="generation-label">Username or email</span>
          <input
            className="generation-input"
            autoComplete="username"
            value={identifier}
            onChange={(event) => setIdentifier(event.target.value)}
            placeholder="you@example.com"
          />
        </label>

        <label className="generation-field">
          <span className="generation-label">Password</span>
          <input
            className="generation-input"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Enter your password"
          />
        </label>

        {errorMessage && <div className="form-message form-message--error">{errorMessage}</div>}

        <Button type="submit" variant="ai-glow" size="lg" isLoading={isSubmitting}>
          Sign In
        </Button>
      </form>
    </AuthShell>
  );
}