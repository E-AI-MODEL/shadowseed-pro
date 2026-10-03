"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  createSession,
  getSession,
  listSessions,
  sendTurn,
} from "@/lib/api";
import type {
  CreateSessionInput,
  Seed,
  SessionSummary,
  SessionView,
} from "@/lib/types";

const emptyDraft: CreateSessionInput = {
  title: "Nieuw gesprek",
  backend: "fixture",
  authority_mode: "assisted",
};

function authorityLabel(profile: string) {
  if (profile === "autonomous") return "Verkennen";
  if (profile === "assisted") return "Onderbouwd";
  return "Gecontroleerd";
}

function orchestrationLabel(state?: string) {
  if (state === "human_turn") return "Jij bent aan zet";
  if (state === "ssl_turn") return "Shadowseed is aan zet";
  if (state === "blocked") return "Geblokkeerd";
  return "Geen actie nodig";
}

function SeedCard({ seed }: { seed: Seed }) {
  return (
    <article className="seed-card">
      <div className="seed-card__top">
        <span className="seed-state">
          {seed.current_gate_authorized ? "TOEGESTAAN" : seed.status}
        </span>
        <strong>{Number(seed.weight ?? 0).toFixed(2)}</strong>
      </div>
      <p className="seed-text">{seed.text}</p>
      <dl className="seed-facts">
        <div>
          <dt>Teruggezien</dt>
          <dd>{seed.occurrence_count ?? 0}</dd>
        </div>
        <div>
          <dt>Steun</dt>
          <dd>{seed.evidence_count ?? 0}</dd>
        </div>
        <div>
          <dt>Tegenspraak</dt>
          <dd>{seed.blocking ? "open" : "geen"}</dd>
        </div>
      </dl>
      {seed.orchestration?.reason_text ? (
        <p className="seed-note">{seed.orchestration.reason_text}</p>
      ) : null}
    </article>
  );
}

export function ShadowseedApp() {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [session, setSession] = useState<SessionView | null>(null);
  const [question, setQuestion] = useState("");
  const [draft, setDraft] = useState<CreateSessionInput>(emptyDraft);
  const [creating, setCreating] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refreshSessions(preferredId?: string) {
    const next = await listSessions();
    setSessions(next);
    const target =
      preferredId ??
      session?.session_id ??
      next.at(0)?.session_id;
    if (target) {
      setSession(await getSession(target));
    } else {
      setSession(null);
    }
  }

  useEffect(() => {
    refreshSessions().catch((cause: unknown) => {
      setError(cause instanceof Error ? cause.message : "API niet bereikbaar");
    });
  }, []);

  const sortedSeeds = useMemo(
    () =>
      [...(session?.seeds ?? [])].sort(
        (a, b) => Number(b.weight ?? 0) - Number(a.weight ?? 0),
      ),
    [session],
  );

  async function selectSession(sessionId: string) {
    if (sending) return;
    setError(null);
    try {
      setSession(await getSession(sessionId));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Gesprek kon niet laden");
    }
  }

  async function onCreate(event: FormEvent) {
    event.preventDefault();
    if (sending) return;
    setCreating(true);
    setError(null);
    try {
      const created = await createSession(draft);
      setSession(created);
      await refreshSessions(created.session_id);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Gesprek kon niet worden gemaakt");
    } finally {
      setCreating(false);
    }
  }

  async function onSend(event: FormEvent) {
    event.preventDefault();
    if (!session || !question.trim() || sending) return;
    const text = question.trim();
    setQuestion("");
    setSending(true);
    setError(null);
    try {
      const result = await sendTurn(session.session_id, text);
      setSession(result.session);
      setSessions(await listSessions());
    } catch (cause) {
      setQuestion(text);
      setError(cause instanceof Error ? cause.message : "Bericht kon niet worden verstuurd");
    } finally {
      setSending(false);
    }
  }

  return (
    <main className="product-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">S</span>
          <div>
            <strong>Shadowseed</strong>
            <small>web client</small>
          </div>
        </div>

        <form className="new-chat" onSubmit={onCreate}>
          <input
            aria-label="Titel nieuw gesprek"
            disabled={sending || creating}
            value={draft.title}
            onChange={(event) =>
              setDraft({ ...draft, title: event.target.value })
            }
          />
          <select
            aria-label="Authority-regime"
            disabled={sending || creating}
            value={draft.authority_mode}
            onChange={(event) =>
              setDraft({
                ...draft,
                authority_mode: event.target
                  .value as CreateSessionInput["authority_mode"],
              })
            }
          >
            <option value="controlled">Gecontroleerd</option>
            <option value="assisted">Onderbouwd</option>
            <option value="exploratory">Verkennen</option>
          </select>
          <select
            aria-label="Modelprovider"
            disabled={sending || creating}
            value={draft.backend}
            onChange={(event) =>
              setDraft({
                ...draft,
                backend: event.target.value as CreateSessionInput["backend"],
              })
            }
          >
            <option value="fixture">Offline demo</option>
            <option value="ollama">Ollama lokaal</option>
          </select>
          {draft.backend === "ollama" ? (
            <input
              aria-label="Ollama model"
              disabled={sending || creating}
              placeholder="bijv. qwen2.5:7b"
              value={draft.model_id ?? ""}
              onChange={(event) =>
                setDraft({ ...draft, model_id: event.target.value })
              }
            />
          ) : null}
          <button type="submit" disabled={creating || sending}>
            {creating ? "Maken..." : "+ Nieuw gesprek"}
          </button>
        </form>

        <nav className="conversation-list" aria-label="Gesprekken">
          {sessions.map((item) => (
            <button
              className={
                item.session_id === session?.session_id
                  ? "conversation conversation--active"
                  : "conversation"
              }
              disabled={sending}
              key={item.session_id}
              onClick={() => selectSession(item.session_id)}
              type="button"
            >
              <strong>{item.title}</strong>
              <span>
                {item.turn_count} beurten · {item.seed_count} punten
              </span>
            </button>
          ))}
        </nav>
      </aside>

      <section className="chat-column">
        <header className="chat-header">
          <div>
            <h1>{session?.title ?? "Shadowseed"}</h1>
            <p>
              {session
                ? authorityLabel(session.authority_profile_id) + " · " + session.backend
                : "Maak links een gesprek om te beginnen."}
            </p>
          </div>
          {session ? (
            <span className="policy-pill">
              {session.effective_gate_policy_id}
            </span>
          ) : null}
        </header>

        <div className="messages">
          {!session ? (
            <div className="empty-state">
              <strong>De engine blijft de enige waarheid.</strong>
              <p>
                Deze webclient presenteert Shadowseed. Hij implementeert geen
                eigen Gate, recurrence of authority.
              </p>
            </div>
          ) : session.messages.length === 0 ? (
            <div className="empty-state">
              <strong>Waar wil je over praten?</strong>
              <p>
                Shadowseed observeert op de achtergrond en houdt authority
                gescheiden van gewone modeloutput.
              </p>
            </div>
          ) : (
            session.messages.map((message, index) => (
              <article
                className={"message message--" + message.role}
                key={message.role + "-" + index}
              >
                <span>
                  {message.role === "user" ? "Jij" : "Antwoord"}
                </span>
                <p>{message.content}</p>
              </article>
            ))
          )}
        </div>

        <form className="composer" onSubmit={onSend}>
          <textarea
            aria-label="Bericht"
            disabled={!session || sending}
            placeholder={
              session ? "Typ je bericht..." : "Maak eerst een gesprek..."
            }
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            rows={2}
          />
          <button disabled={!session || sending || !question.trim()}>
            {sending ? "Bezig..." : "Verstuur"}
          </button>
        </form>
        {error ? <div className="error-banner">{error}</div> : null}
      </section>

      <aside className="shadow-column">
        <div className="shadow-heading">
          <div>
            <span className="eyebrow">SHADOW</span>
            <h2>Wat speelt mee?</h2>
          </div>
          <span className="shadow-count">{sortedSeeds.length}</span>
        </div>

        {session?.orchestration ? (
          <section className="handoff-card">
            <span>{orchestrationLabel(session.orchestration.state)}</span>
            <p>{session.orchestration.reason_text}</p>
          </section>
        ) : null}

        <div className="seed-list">
          {sortedSeeds.length ? (
            sortedSeeds.map((seed) => (
              <SeedCard key={seed.id} seed={seed} />
            ))
          ) : (
            <div className="shadow-empty">
              <strong>Nog geen geheugenpunten</strong>
              <p>
                Nieuwe kandidaten starten zonder steering authority.
              </p>
            </div>
          )}
        </div>

        {session ? (
          <footer className="runtime-footer">
            <span>Behavior</span>
            <code>{session.behavior_config_digest.slice(0, 10)}</code>
          </footer>
        ) : null}
      </aside>
    </main>
  );
}
