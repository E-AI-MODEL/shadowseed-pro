"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

import {
  clearOpenAI,
  configureOpenAI,
  contradictSeed,
  createSession,
  getProviderStatus,
  getSeed,
  getSession,
  listSessions,
  resolveSeedContradiction,
  sendTurn,
  submitSeedEvidence,
} from "@/lib/api";
import type {
  CreateSessionInput,
  ProviderStatus,
  Seed,
  SeedDetail,
  SeedTimelineEvent,
  SessionSummary,
  SessionView,
} from "@/lib/types";

const emptyDraft: CreateSessionInput = {
  title: "Nieuw gesprek",
  backend: "fixture",
  authority_mode: "assisted",
  external_confirmed: false,
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

function SeedCard({
  seed,
  onOpen,
}: {
  seed: Seed;
  onOpen: () => void;
}) {
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
      <button className="seed-open" onClick={onOpen} type="button">
        Bekijk details
      </button>
    </article>
  );
}

function timelineLabel(type: string) {
  if (type === "seed_event") return "Geheugen";
  if (type === "validation") return "Validatie";
  if (type === "gate") return "Gate";
  if (type === "contradiction") return "Tegenspraak";
  if (type === "probe_feedback") return "Feedback";
  if (type === "influence") return "Gebruik";
  return type;
}

function timelineTimestamp(event: SeedTimelineEvent) {
  if (!event.timestamp) return "Geen tijd vastgelegd";
  const value = new Date(event.timestamp);
  return Number.isNaN(value.getTime())
    ? String(event.timestamp)
    : value.toLocaleString("nl-NL");
}

function SeedTimeline({ events }: { events: SeedTimelineEvent[] }) {
  if (!events.length) {
    return <p className="seed-detail__muted">Nog geen timeline-events.</p>;
  }

  return (
    <ol className="seed-timeline">
      {events.map((event) => (
        <li key={event.type + "-" + event.sequence}>
          <div className="seed-timeline__marker" />
          <div className="seed-timeline__body">
            <div className="seed-timeline__top">
              <strong>{timelineLabel(event.type)}</strong>
              <span>{timelineTimestamp(event)}</span>
            </div>
            <details>
              <summary>Canonical record</summary>
              <pre>{JSON.stringify(event.payload, null, 2)}</pre>
            </details>
          </div>
        </li>
      ))}
    </ol>
  );
}

export function ShadowseedApp() {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [session, setSession] = useState<SessionView | null>(null);
  const [question, setQuestion] = useState("");
  const [retryTurn, setRetryTurn] = useState<{
    sessionId: string;
    text: string;
    requestId: string;
  } | null>(null);
  const [draft, setDraft] = useState<CreateSessionInput>(emptyDraft);
  const [providers, setProviders] = useState<ProviderStatus[]>([]);
  const [openaiKey, setOpenaiKey] = useState("");
  const [providerBusy, setProviderBusy] = useState(false);
  const [providerError, setProviderError] = useState<string | null>(null);
  const [providerNotice, setProviderNotice] = useState<string | null>(null);
  const [externalTurnConfirmed, setExternalTurnConfirmed] = useState(false);
  const [creating, setCreating] = useState(false);
  const [sending, setSending] = useState(false);
  const [loadingSession, setLoadingSession] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [shadowOpen, setShadowOpen] = useState(false);
  const [selectedSeed, setSelectedSeed] = useState<SeedDetail | null>(null);
  const [loadingSeed, setLoadingSeed] = useState(false);
  const [seedActionBusy, setSeedActionBusy] = useState(false);
  const [seedError, setSeedError] = useState<string | null>(null);
  const [seedNotice, setSeedNotice] = useState<string | null>(null);
  const [evidenceRef, setEvidenceRef] = useState("");
  const [evidenceNote, setEvidenceNote] = useState("");
  const [evidenceVerified, setEvidenceVerified] = useState(false);
  const [resolutionBasis, setResolutionBasis] = useState("");
  const [retrySeedAction, setRetrySeedAction] = useState<{
    kind: "evidence" | "contradict" | "resolve";
    sessionId: string;
    seedId: string;
    fingerprint: string;
    requestId: string;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const sessionRequestId = useRef(0);
  const refreshRequestId = useRef(0);
  const seedRequestId = useRef(0);

  function clearSeedDetail() {
    seedRequestId.current += 1;
    setLoadingSeed(false);
    setSelectedSeed(null);
    setSeedError(null);
    setSeedNotice(null);
    setRetrySeedAction(null);
    setEvidenceRef("");
    setEvidenceNote("");
    setEvidenceVerified(false);
    setResolutionBasis("");
  }

  async function openSeed(seedId: string) {
    if (!session || seedActionBusy) return;
    const requestId = ++seedRequestId.current;
    setLoadingSeed(true);
    setSeedError(null);
    setSeedNotice(null);
    try {
      const detail = await getSeed(session.session_id, seedId);
      if (seedRequestId.current === requestId) {
        setSelectedSeed(detail);
      }
    } catch (cause) {
      if (seedRequestId.current === requestId) {
        setSeedError(
          cause instanceof Error ? cause.message : "Geheugenpunt kon niet laden",
        );
      }
    } finally {
      if (seedRequestId.current === requestId) {
        setLoadingSeed(false);
      }
    }
  }

  async function refreshSeedAfterMutation(
    nextSession: SessionView,
    seedId: string,
  ) {
    setSession(nextSession);
    const requestId = ++seedRequestId.current;
    try {
      const detail = await getSeed(nextSession.session_id, seedId);
      if (seedRequestId.current === requestId) {
        setSelectedSeed(detail);
      }
      return true;
    } catch {
      if (seedRequestId.current === requestId) {
        setSelectedSeed(null);
        setSeedNotice(
          "De wijziging is opgeslagen, maar de detailweergave kon niet worden vernieuwd.",
        );
      }
      return false;
    }
  }

  async function loadSession(sessionId: string) {
    const requestId = ++sessionRequestId.current;
    setLoadingSession(true);
    try {
      const loaded = await getSession(sessionId);
      if (sessionRequestId.current === requestId) {
        setSession(loaded);
        return loaded;
      }
      return null;
    } catch (cause) {
      if (sessionRequestId.current === requestId) {
        throw cause;
      }
      return null;
    } finally {
      if (sessionRequestId.current === requestId) {
        setLoadingSession(false);
      }
    }
  }

  async function refreshSessions(preferredId?: string) {
    const refreshId = ++refreshRequestId.current;
    let next: SessionSummary[];

    try {
      next = await listSessions();
    } catch (cause) {
      if (refreshRequestId.current !== refreshId) {
        return;
      }
      throw cause;
    }

    if (refreshRequestId.current !== refreshId) {
      return;
    }

    setSessions(next);
    const target =
      preferredId ??
      session?.session_id ??
      next.at(0)?.session_id;

    if (target) {
      await loadSession(target);
    } else if (refreshRequestId.current === refreshId) {
      sessionRequestId.current += 1;
      setLoadingSession(false);
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
    if (sending || creating || seedActionBusy) return;
    refreshRequestId.current += 1;
    setError(null);
    setNotice(null);
    setRetryTurn(null);
    clearSeedDetail();
    setMobileNavOpen(false);
    try {
      await loadSession(sessionId);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Gesprek kon niet laden");
    }
  }

  async function onCreate(event: FormEvent) {
    event.preventDefault();
    if (sending || loadingSession || seedActionBusy) return;
    setCreating(true);
    setError(null);
    setNotice(null);

    try {
      const created = await createSession(draft);

      refreshRequestId.current += 1;
      sessionRequestId.current += 1;
      setLoadingSession(false);
      setSession(created);
      setRetryTurn(null);
      clearSeedDetail();
      setMobileNavOpen(false);

      try {
        setSessions(await listSessions());
      } catch {
        setNotice(
          "Het gesprek is gemaakt, maar de gesprekslijst kon niet worden vernieuwd.",
        );
      }
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Gesprek kon niet worden gemaakt",
      );
    } finally {
      setCreating(false);
    }
  }

  async function onSend(event: FormEvent) {
    event.preventDefault();
    if (
      !session ||
      !question.trim() ||
      sending ||
      loadingSession ||
      seedActionBusy
    ) return;
    const text = question.trim();
    const requestId =
      retryTurn?.sessionId === session.session_id && retryTurn.text === text
        ? retryTurn.requestId
        : "web-turn:" + crypto.randomUUID();
    setQuestion("");
    setSending(true);
    setError(null);
    setNotice(null);

    try {
      const result = await sendTurn(session.session_id, text, requestId);
      if (selectedSeed) {
        await refreshSeedAfterMutation(result.session, selectedSeed.id);
      } else {
        setSession(result.session);
      }
      setRetryTurn(null);

      try {
        setSessions(await listSessions());
      } catch {
        setNotice(
          "Het bericht is verstuurd, maar de gesprekslijst kon niet worden vernieuwd.",
        );
      }
    } catch (cause) {
      setQuestion(text);
      setRetryTurn({
        sessionId: session.session_id,
        text,
        requestId,
      });
      setError(
        cause instanceof Error ? cause.message : "Bericht kon niet worden verstuurd",
      );
    } finally {
      setSending(false);
    }
  }

  function seedRequestKey(
    kind: "evidence" | "contradict" | "resolve",
    seedId: string,
    fingerprint: string,
  ) {
    if (
      session &&
      retrySeedAction?.kind === kind &&
      retrySeedAction.sessionId === session.session_id &&
      retrySeedAction.seedId === seedId &&
      retrySeedAction.fingerprint === fingerprint
    ) {
      return retrySeedAction.requestId;
    }
    return "web-seed-" + kind + ":" + crypto.randomUUID();
  }

  async function onSubmitEvidence(event: FormEvent) {
    event.preventDefault();
    if (
      !session ||
      !selectedSeed ||
      seedActionBusy ||
      !evidenceRef.trim() ||
      !evidenceVerified
    ) {
      return;
    }

    const sourceRef = evidenceRef.trim();
    const note = evidenceNote.trim();
    const fingerprint = sourceRef + "\u0000" + note;
    const requestId = seedRequestKey(
      "evidence",
      selectedSeed.id,
      fingerprint,
    );
    setSeedActionBusy(true);
    setSeedError(null);
    setSeedNotice(null);

    try {
      const nextSession = await submitSeedEvidence(
        session.session_id,
        selectedSeed.id,
        { sourceRef, note, requestId },
      );
      setRetrySeedAction(null);
      setEvidenceRef("");
      setEvidenceNote("");
      setEvidenceVerified(false);
      const refreshed = await refreshSeedAfterMutation(
        nextSession,
        selectedSeed.id,
      );
      if (refreshed) {
        setSeedNotice("Geverifieerde steun is opgeslagen.");
      }
    } catch (cause) {
      setRetrySeedAction({
        kind: "evidence",
        sessionId: session.session_id,
        seedId: selectedSeed.id,
        fingerprint,
        requestId,
      });
      setSeedError(
        cause instanceof Error ? cause.message : "Steun kon niet worden opgeslagen",
      );
    } finally {
      setSeedActionBusy(false);
    }
  }

  async function onContradictSeed() {
    if (!session || !selectedSeed || seedActionBusy) return;
    const fingerprint = "contradict";
    const requestId = seedRequestKey(
      "contradict",
      selectedSeed.id,
      fingerprint,
    );
    setSeedActionBusy(true);
    setSeedError(null);
    setSeedNotice(null);

    try {
      const nextSession = await contradictSeed(
        session.session_id,
        selectedSeed.id,
        requestId,
      );
      setRetrySeedAction(null);
      const refreshed = await refreshSeedAfterMutation(
        nextSession,
        selectedSeed.id,
      );
      if (refreshed) {
        setSeedNotice("Tegenspraak is vastgelegd. Dit punt is nu geblokkeerd.");
      }
    } catch (cause) {
      setRetrySeedAction({
        kind: "contradict",
        sessionId: session.session_id,
        seedId: selectedSeed.id,
        fingerprint,
        requestId,
      });
      setSeedError(
        cause instanceof Error ? cause.message : "Tegenspraak kon niet worden opgeslagen",
      );
    } finally {
      setSeedActionBusy(false);
    }
  }

  async function onResolveContradiction(event: FormEvent) {
    event.preventDefault();
    if (
      !session ||
      !selectedSeed ||
      seedActionBusy ||
      !resolutionBasis.trim()
    ) {
      return;
    }

    const basis = resolutionBasis.trim();
    const requestId = seedRequestKey("resolve", selectedSeed.id, basis);
    setSeedActionBusy(true);
    setSeedError(null);
    setSeedNotice(null);

    try {
      const nextSession = await resolveSeedContradiction(
        session.session_id,
        selectedSeed.id,
        { basis, requestId },
      );
      setRetrySeedAction(null);
      setResolutionBasis("");
      const refreshed = await refreshSeedAfterMutation(
        nextSession,
        selectedSeed.id,
      );
      if (refreshed) {
        setSeedNotice("De tegenspraak is opnieuw door de Gate beoordeeld.");
      }
    } catch (cause) {
      setRetrySeedAction({
        kind: "resolve",
        sessionId: session.session_id,
        seedId: selectedSeed.id,
        fingerprint: basis,
        requestId,
      });
      setSeedError(
        cause instanceof Error ? cause.message : "Tegenspraak kon niet worden opgelost",
      );
    } finally {
      setSeedActionBusy(false);
    }
  }


  return (
    <main className="product-shell">
      <button
        aria-label="Sluit gesprekken"
        className={
          mobileNavOpen
            ? "mobile-nav-backdrop mobile-nav-backdrop--open"
            : "mobile-nav-backdrop"
        }
        onClick={() => setMobileNavOpen(false)}
        type="button"
      />
      <button
        aria-label="Sluit Shadow"
        className={
          shadowOpen
            ? "shadow-backdrop shadow-backdrop--open"
            : "shadow-backdrop"
        }
        onClick={() => setShadowOpen(false)}
        type="button"
      />

      <aside
        className={mobileNavOpen ? "sidebar sidebar--open" : "sidebar"}
        id="session-navigation"
      >
        <div className="brand">
          <span className="brand-mark">S</span>
          <div>
            <strong>Shadowseed</strong>
            <small>web client</small>
          </div>
          <button
            aria-label="Sluit gesprekken"
            className="sidebar-close"
            onClick={() => setMobileNavOpen(false)}
            type="button"
          >
            Sluiten
          </button>
        </div>

        <form className="new-chat" onSubmit={onCreate}>
          <input
            aria-label="Titel nieuw gesprek"
            disabled={sending || creating || loadingSession || seedActionBusy}
            value={draft.title}
            onChange={(event) =>
              setDraft({ ...draft, title: event.target.value })
            }
          />
          <select
            aria-label="Authority-regime"
            disabled={sending || creating || loadingSession || seedActionBusy}
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
            disabled={sending || creating || loadingSession || seedActionBusy}
            value={draft.backend}
            onChange={(event) => {
              const backend =
                event.target.value as CreateSessionInput["backend"];
              setDraft({
                ...draft,
                backend,
                model_id: backend === "fixture" ? undefined : draft.model_id,
              });
            }}
          >
            <option value="fixture">Offline demo</option>
            <option value="ollama">Ollama lokaal</option>
          </select>
          {draft.backend === "ollama" ? (
            <input
              aria-label="Ollama model"
              disabled={sending || creating || loadingSession || seedActionBusy}
              placeholder="bijv. qwen2.5:7b"
              value={draft.model_id ?? ""}
              onChange={(event) =>
                setDraft({ ...draft, model_id: event.target.value })
              }
            />
          ) : null}
          <button
            type="submit"
            disabled={creating || sending || loadingSession || seedActionBusy}
          >
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
              disabled={sending || creating || seedActionBusy}
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
          <div className="chat-header__main">
            <button
              aria-controls="session-navigation"
              aria-expanded={mobileNavOpen}
              className="mobile-nav-button"
              disabled={sending || creating}
              onClick={() => {
                setShadowOpen(false);
                setMobileNavOpen(true);
              }}
              type="button"
            >
              Gesprekken
            </button>
            <div>
              <h1>{session?.title ?? "Shadowseed"}</h1>
              <p>
                {session
                  ? authorityLabel(session.authority_profile_id) + " · " + session.backend
                  : "Maak een gesprek om te beginnen."}
              </p>
            </div>
          </div>
          <div className="chat-header__actions">
            <button
              aria-controls="shadow-inspector"
              aria-expanded={shadowOpen}
              className="shadow-toggle-button"
              onClick={() => {
                setMobileNavOpen(false);
                setShadowOpen(true);
              }}
              type="button"
            >
              Shadow {sortedSeeds.length}
            </button>
            {session ? (
              <span className="policy-pill">
                {session.effective_gate_policy_id}
              </span>
            ) : null}
          </div>
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
            disabled={!session || sending || loadingSession}
            placeholder={
              session
                ? loadingSession
                  ? "Gesprek laden..."
                  : "Typ je bericht..."
                : "Maak eerst een gesprek..."
            }
            value={question}
            onChange={(event) => {
              const value = event.target.value;
              setQuestion(value);
              if (retryTurn && value.trim() !== retryTurn.text) {
                setRetryTurn(null);
              }
            }}
            rows={2}
          />
          <button
            disabled={
              !session ||
              sending ||
              loadingSession ||
              seedActionBusy ||
              !question.trim()
            }
          >
            {sending ? "Bezig..." : "Verstuur"}
          </button>
        </form>
        {notice ? <div className="notice-banner">{notice}</div> : null}
        {error ? <div className="error-banner">{error}</div> : null}
      </section>

      <aside
        className={shadowOpen ? "shadow-column shadow-column--open" : "shadow-column"}
        id="shadow-inspector"
      >
        <div className="shadow-heading">
          <div>
            <span className="eyebrow">SHADOW</span>
            <h2>Wat speelt mee?</h2>
          </div>
          <div className="shadow-heading__actions">
            <span className="shadow-count">{sortedSeeds.length}</span>
            <button
              aria-label="Sluit Shadow"
              className="shadow-close"
              onClick={() => setShadowOpen(false)}
              type="button"
            >
              Sluiten
            </button>
          </div>
        </div>

        {seedNotice ? (
          <div className="seed-notice">{seedNotice}</div>
        ) : null}
        {seedError ? (
          <div className="seed-error">{seedError}</div>
        ) : null}

        {selectedSeed ? (
          <div className="seed-detail">
            <button
              className="seed-detail__back"
              disabled={seedActionBusy}
              onClick={clearSeedDetail}
              type="button"
            >
              ← Alle geheugenpunten
            </button>

            <section className="seed-detail__summary">
              <div className="seed-card__top">
                <span className="seed-state">
                  {selectedSeed.current_gate_authorized
                    ? "TOEGESTAAN"
                    : selectedSeed.status}
                </span>
                <strong>{Number(selectedSeed.weight ?? 0).toFixed(2)}</strong>
              </div>
              <h3>{selectedSeed.text}</h3>
              <p>{selectedSeed.plain_explanation}</p>
              <dl className="seed-detail__facts">
                <div>
                  <dt>Teruggezien</dt>
                  <dd>{selectedSeed.occurrence_count ?? 0}</dd>
                </div>
                <div>
                  <dt>Geverifieerde steun</dt>
                  <dd>{selectedSeed.evidence_count ?? 0}</dd>
                </div>
                <div>
                  <dt>Tegenspraak</dt>
                  <dd>{selectedSeed.blocking ? "open" : "geen"}</dd>
                </div>
                <div>
                  <dt>Gate</dt>
                  <dd>{selectedSeed.effective_gate_policy_id ?? "onbekend"}</dd>
                </div>
              </dl>
              {selectedSeed.review_required ? (
                <p className="seed-review-flag">
                  Dit punt vraagt nog om menselijke beoordeling.
                </p>
              ) : null}
            </section>

            <section className="seed-action-card">
              <h3>Geverifieerde steun</h3>
              <p>
                Gebruik dit alleen als je de bron zelf hebt gecontroleerd en
                die dit geheugenpunt daadwerkelijk ondersteunt. Een bron
                toevoegen is niet automatisch bewijs.
              </p>
              <form onSubmit={onSubmitEvidence}>
                <label>
                  Bronverwijzing
                  <input
                    disabled={seedActionBusy}
                    placeholder="URL, document-ID of andere stabiele verwijzing"
                    value={evidenceRef}
                    onChange={(event) => {
                      setEvidenceRef(event.target.value);
                      if (retrySeedAction?.kind === "evidence") {
                        setRetrySeedAction(null);
                      }
                    }}
                  />
                </label>
                <label>
                  Toelichting
                  <textarea
                    disabled={seedActionBusy}
                    placeholder="Optioneel: waarom ondersteunt deze bron dit punt?"
                    rows={3}
                    value={evidenceNote}
                    onChange={(event) => {
                      setEvidenceNote(event.target.value);
                      if (retrySeedAction?.kind === "evidence") {
                        setRetrySeedAction(null);
                      }
                    }}
                  />
                </label>
                <label className="verification-check">
                  <input
                    checked={evidenceVerified}
                    disabled={seedActionBusy}
                    onChange={(event) =>
                      setEvidenceVerified(event.target.checked)
                    }
                    type="checkbox"
                  />
                  <span>
                    Ik heb deze bron gecontroleerd en bevestig dat deze dit
                    punt ondersteunt.
                  </span>
                </label>
                <button
                  disabled={
                    seedActionBusy ||
                    !evidenceRef.trim() ||
                    !evidenceVerified
                  }
                  type="submit"
                >
                  {seedActionBusy ? "Bezig..." : "Steun vastleggen"}
                </button>
              </form>
            </section>

            <section className="seed-action-card">
              <h3>Tegenspraak</h3>
              {selectedSeed.blocking ? (
                <form onSubmit={onResolveContradiction}>
                  <p>
                    Dit geheugenpunt is nu geblokkeerd. Leg vast waarom de
                    tegenspraak volgens jou kan worden opgelost. De Gate
                    beoordeelt daarna opnieuw wat er met de authority gebeurt.
                  </p>
                  <label>
                    Basis voor oplossing
                    <textarea
                      disabled={seedActionBusy}
                      placeholder="Waarom kan deze blokkade worden opgeheven?"
                      rows={3}
                      value={resolutionBasis}
                      onChange={(event) => {
                        setResolutionBasis(event.target.value);
                        if (retrySeedAction?.kind === "resolve") {
                          setRetrySeedAction(null);
                        }
                      }}
                    />
                  </label>
                  <button
                    disabled={seedActionBusy || !resolutionBasis.trim()}
                    type="submit"
                  >
                    {seedActionBusy ? "Bezig..." : "Tegenspraak oplossen"}
                  </button>
                </form>
              ) : (
                <>
                  <p>
                    Gebruik dit als informatie dit geheugenpunt tegenspreekt.
                    Het punt wordt dan geblokkeerd totdat de tegenspraak via de
                    bestaande Gate-flow is opgelost.
                  </p>
                  <button
                    className="danger-secondary"
                    disabled={seedActionBusy}
                    onClick={onContradictSeed}
                    type="button"
                  >
                    {seedActionBusy ? "Bezig..." : "Markeer als tegengesproken"}
                  </button>
                </>
              )}
            </section>

            <section className="seed-detail__timeline">
              <div>
                <span className="eyebrow">TIMELINE</span>
                <h3>Wat is er met dit punt gebeurd?</h3>
              </div>
              <SeedTimeline events={selectedSeed.timeline} />
            </section>
          </div>
        ) : (
          <>
            {session?.orchestration ? (
              <section className="handoff-card">
                <span>{orchestrationLabel(session.orchestration.state)}</span>
                <p>{session.orchestration.reason_text}</p>
              </section>
            ) : null}

            {loadingSeed ? (
              <div className="shadow-empty">
                <strong>Geheugenpunt laden...</strong>
              </div>
            ) : (
              <div className="seed-list">
                {sortedSeeds.length ? (
                  sortedSeeds.map((seed) => (
                    <SeedCard
                      key={seed.id}
                      onOpen={() => openSeed(seed.id)}
                      seed={seed}
                    />
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
            )}
          </>
        )}

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
