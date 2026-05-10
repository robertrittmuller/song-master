import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import { AuthShell } from "../components/auth/AuthShell";
import { Button } from "../components/ui/Button";
import { useAuth } from "../features/auth/AuthProvider";

export function SignupPage() {
  const navigate = useNavigate();
  const { signup } = useAuth();
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setErrorMessage(null);

    if (!form.username.trim() || !form.email.trim() || !form.password) {
      setErrorMessage("Complete every required field.");
      return;
    }

    if (form.password !== form.confirmPassword) {
      setErrorMessage("Passwords do not match.");
      return;
    }

    setIsSubmitting(true);
    try {
      await signup({
        username: form.username.trim(),
        email: form.email.trim(),
        password: form.password,
      });
      navigate("/", { replace: true });
    } catch (error: any) {
      const message = error?.response?.data?.detail || error?.message || "Unable to create account.";
      setErrorMessage(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AuthShell
      eyebrow="Create account"
      title="Start a secure Song Master account"
      description="The first account on this install will automatically claim your existing library, then every new song, album, and proposal stays isolated per user."
      footerLabel="Already have an account?"
      footerLink="/login"
      footerLinkLabel="Sign in"
    >
      <form className="auth-form" onSubmit={handleSubmit}>
        <label className="generation-field">
          <span className="generation-label">Username</span>
          <input
            className="generation-input"
            autoComplete="username"
            value={form.username}
            onChange={(event) => setForm((current) => ({ ...current, username: event.target.value }))}
            placeholder="songsmith"
          />
        </label>

        <label className="generation-field">
          <span className="generation-label">Email</span>
          <input
            className="generation-input"
            type="email"
            autoComplete="email"
            value={form.email}
            onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
            placeholder="you@example.com"
          />
        </label>

        <div className="auth-form__row">
          <label className="generation-field">
            <span className="generation-label">Password</span>
            <input
              className="generation-input"
              type="password"
              autoComplete="new-password"
              value={form.password}
              onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))}
              placeholder="At least 8 characters"
            />
          </label>

          <label className="generation-field">
            <span className="generation-label">Confirm password</span>
            <input
              className="generation-input"
              type="password"
              autoComplete="new-password"
              value={form.confirmPassword}
              onChange={(event) =>
                setForm((current) => ({ ...current, confirmPassword: event.target.value }))
              }
              placeholder="Repeat password"
            />
          </label>
        </div>

        {errorMessage && <div className="form-message form-message--error">{errorMessage}</div>}

        <Button type="submit" variant="ai-glow" size="lg" isLoading={isSubmitting}>
          Create Account
        </Button>
      </form>
    </AuthShell>
  );
}