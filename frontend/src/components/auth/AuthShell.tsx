import { ReactNode } from "react";
import { Link } from "react-router-dom";

type Props = {
  eyebrow: string;
  title: string;
  description: string;
  footerLabel: string;
  footerLink: string;
  footerLinkLabel: string;
  children: ReactNode;
};

export function AuthShell({
  eyebrow,
  title,
  description,
  footerLabel,
  footerLink,
  footerLinkLabel,
  children,
}: Props) {
  return (
    <div className="auth-page">
      <section className="auth-page__visual">
        <div className="auth-page__visual-inner">
          <div className="auth-brand-card glass">
            <div className="auth-brand-card__eyebrow">Song Master</div>
            <img src="/logo.png" alt="Song Master" className="auth-brand-card__logo" />
            <p className="auth-brand-card__copy">
              Keep every lyric draft, album, and proposal inside a private workspace built for fast iteration.
            </p>
          </div>

          <div className="auth-page__story">
            <div className="pill">Private songwriting workspace</div>
            <h1>{title}</h1>
            <p>{description}</p>

            <div className="auth-metric-grid">
              <div className="auth-metric glass">
                <span className="auth-metric__value">Secure</span>
                <span className="auth-metric__label">Password-based access with private account data</span>
              </div>
              <div className="auth-metric glass">
                <span className="auth-metric__value">Scoped</span>
                <span className="auth-metric__label">Songs, albums, backups, and proposals stay user-owned</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="auth-page__panel">
        <div className="auth-panel card">
          <div className="auth-panel__header">
            <div className="auth-panel__eyebrow">{eyebrow}</div>
            <img src="/logo.png" alt="Song Master" className="auth-panel__logo" />
          </div>

          {children}

          <div className="auth-panel__footer">
            <span>{footerLabel}</span>
            <Link to={footerLink} className="auth-inline-link">
              {footerLinkLabel}
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}