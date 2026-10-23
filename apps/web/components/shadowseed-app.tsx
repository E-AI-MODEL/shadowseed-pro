"use client";

import {
  FormEvent,
  KeyboardEvent,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

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
  title: "",
  backend: "fixture",
  authority_mode: "assisted",
  external_confirmed: false,
};

const AUTHORITY_MODES: Record<
  CreateSessionInput["authority_mode"],
  { label: string; help: string }
> = {
  controlled: {
    label: "Controlled",
    help: "Gate policy evidence_backed. Influence requires verified evidence. No review prompts.",
  },
  assisted: {
    label: "Guided",
    help: "Gate policy evidence_backed. Influence requires verified evidence. Prompts when a candidate reaches the review threshold.",
  },
  exploratory: {
    label: "Exploratory",
    help: "Gate policy exploratory. Recurrence counts as a support signal; no external evidence required.",
  },
};

const BACKEND_LABELS: Record<string, string> = {
  fixture: "Offline demo",
  ollama: "Ollama",
  openai: "OpenAI",
};

const GATE_POLICY_LABELS: Record<string, string> = {
  evidence_backed: "Evidence required",
  exploratory: "Exploratory",
  legacy_evidence_required: "Legacy evidence rule",
};

function authorityLabel(profile: string) {
  if (profile === "autonomous") return AUTHORITY_MODES.exploratory.label;
  if (profile === "assisted") return AUTHORITY_MODES.assisted.label;
  return AUTHORITY_MODES.controlled.label;
}

function backendLabel(backend: string) {
  return BACKEND_LABELS[backend] ?? backend;
}

function gatePolicyLabel(policy?: string | null) {
  if (!policy) return "Unknown";
  return GATE_POLICY_LABELS[policy] ?? policy;
}

function compactModelLabel(modelId?: string | null) {
  if (!modelId) return "default";
  return modelId.replace(":latest", "");
}

function modelRoleSummary(session: SessionView) {
  const roles = session.model_roles;
  if (!roles) return null;

  const generation = compactModelLabel(roles.generation.model_id);
  const revision = compactModelLabel(roles.revision.model_id);
  const detection = compactModelLabel(roles.detection.model_id);

  if (generation === revision && generation === detection) {
    return generation === "default" ? null : generation;
  }
  if (revision === detection) {
    return generation + " · detection/revision " + revision;
  }
  return generation + " · detection " + detection + " · revision " + revision;
}

type Tone = "neutral" | "warning" | "success" | "danger" | "muted";

function seedStatus(seed: Seed): { label: string; tone: Tone } {
  if (seed.blocking) return { label: "Contradicted", tone: "danger" };
  if (seed.current_gate_authorized) {
    return { label: "Authorized", tone: "success" };
  }
  const status = String(seed.status ?? "").toLowerCase();
  if (status === "expired") return { label: "Expired", tone: "muted" };
  if (status === "dormant") return { label: "Dormant", tone: "muted" };
  if (seed.orchestration?.state === "human_turn") {
    return { label: "Evidence required", tone: "warning" };
  }
  if (status === "promoted") {
    return { label: "Promoted (inactive)", tone: "neutral" };
  }
  return { label: "Observed", tone: "neutral" };
}

function StatusBadge({ seed }: { seed: Seed }) {
  const status = seedStatus(seed);
  return (
    <span className={"badge badge--" + status.tone}>{status.label}</span>
  );
}

function handoffTitle(state?: string) {
  if (state === "human_turn") return "Action required";
  if (state === "blocked") return "Blocked";
  return null;
}

function plural(count: number, one: string, many: string) {
  return count + " " + (count === 1 ? one : many);
}

function Icon({ name }: { name: "plus" | "menu" | "panel" | "close" | "back" | "send" }) {
  const paths: Record<string, string> = {
    plus: "M12 5v14M5 12h14",
    menu: "M4 7h16M4 12h16M4 17h16",
    panel: "M4 5h16v14H4zM14 5v14",
    close: "M6 6l12 12M18 6L6 18",
    back: "M15 6l-6 6 6 6",
    send: "M5 12h14M13 6l6 6-6 6",
  };
  return (
    <svg
      aria-hidden="true"
      className="icon"
      fill="none"
      height="16"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="2"
      viewBox="0 0 24 24"
      width="16"
    >
      <path d={paths[name]} />
    </svg>
  );
}

function BrandMark() {
  return (
    <svg aria-hidden="true" className="brand-mark" viewBox="0 0 32 32">
      <rect fill="currentColor" height="32" rx="9" width="32" />
      <circle cx="16" cy="16" fill="none" r="7" stroke="var(--surface)" strokeDasharray="3 3" strokeWidth="2" />
      <circle cx="16" cy="16" fill="var(--surface)" r="3" />
    </svg>
  );
}

function RawJson({ label, value }: { label: string; value: unknown }) {
  const text = useMemo(
    () =>
      JSON.stringify(value, null, 2).replace(
        /\[\s*(-?[\d.eE+-]+(?:,\s*-?[\d.eE+-]+)*)\s*\]/g,
        (_match, items: string) => "[" + items.split(/,\s*/).join(", ") + "]",
      ),
    [value],
  );
  const [copied, setCopied] = useState(false);
  return (
    <details className="raw-json">
      <summary>
        <span>{label}</span>
        <span className="mono">{text.length.toLocaleString()} chars</span>
      </summary>
      <div className="raw-json__body">
        <button
          className="button button--ghost raw-json__copy"
          onClick={() => {
            navigator.clipboard
              ?.writeText(text)
              .then(() => {
                setCopied(true);
                setTimeout(() => setCopied(false), 1500);
              })
              .catch(() => undefined);
          }}
          type="button"
        >
          {copied ? "Copied" : "Copy"}
        </button>
        <pre>{text}</pre>
      </div>
    </details>
  );
}

function SeedCard({
  seed,
  onOpen,
}: {
  seed: Seed;
  onOpen: () => void;
}) {
  const seen = seed.occurrence_count ?? 0;
  const evidence = seed.evidence_count ?? 0;
  return (
    <button className="seed-card" onClick={onOpen} type="button">
      <StatusBadge seed={seed} />
      <p className="seed-text">{seed.text}</p>
      <p className="seed-meta">
        <span>Seen {seen}×</span>
        <span>{plural(evidence, "source", "sources")}</span>
        <span>{seed.blocking ? "Contradiction open" : "No contradiction"}</span>
      </p>
    </button>
  );
}

function timelineLabel(type: string) {
  if (type === "seed_event") return "Memory";
  if (type === "validation") return "Validation";
  if (type === "gate") return "Gate decision";
  if (type === "contradiction") return "Contradiction";
  if (type === "probe_feedback") return "Feedback";
  if (type === "influence") return "Used in an answer";
  return type;
}

function timelineTimestamp(event: SeedTimelineEvent) {
  if (!event.timestamp) return "No time recorded";
  const value = new Date(event.timestamp);
  return Number.isNaN(value.getTime())
    ? String(event.timestamp)
    : value.toLocaleString(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
      });
}

function SeedTimeline({ events }: { events: SeedTimelineEvent[] }) {
  if (!events.length) {
    return <p className="muted">No events recorded.</p>;
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
              <summary>Event payload (JSON)</summary>
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
  const [createError, setCreateError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [newChatOpen, setNewChatOpen] = useState(false);
  const [lastTurn, setLastTurn] = useState<{
    sessionId: string;
    report: Record<string, unknown>;
    comparison: Record<string, unknown> | null;
  } | null>(null);
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
          cause instanceof Error ? cause.message : "Could not load this candidate.",
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
          "The change was saved, but the detail view could not be refreshed.",
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

  async function refreshProviderStatus() {
    const next = await getProviderStatus();
    setProviders(next);
    return next;
  }

  async function syncSelectedProviderReadiness() {
    if (!session) return;
    try {
      setSession(await getSession(session.session_id));
    } catch {
      return;
    }
  }

  useEffect(() => {
    refreshSessions().catch((cause: unknown) => {
      setError(cause instanceof Error ? cause.message : "The local Shadowseed service is not reachable.");
    });
    refreshProviderStatus().catch((cause: unknown) => {
      setProviderError(
        cause instanceof Error ? cause.message : "Provider status is unavailable.",
      );
    });
  }, []);

  const openaiStatus = useMemo(
    () => providers.find((item) => item.provider === "openai") ?? null,
    [providers],
  );

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
    setExternalTurnConfirmed(false);
    clearSeedDetail();
    setMobileNavOpen(false);
    try {
      await loadSession(sessionId);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not load this conversation.");
    }
  }

  async function onConfigureOpenAI(event: FormEvent) {
    event.preventDefault();
    if (!openaiKey.trim() || providerBusy) return;
    setProviderBusy(true);
    setProviderError(null);
    setProviderNotice(null);

    try {
      const next = await configureOpenAI(openaiKey.trim());
      setProviders(next);
      setOpenaiKey("");
      setProviderNotice(
        "OpenAI is configured for this app session. The key is not stored in the workspace.",
      );
    } catch (cause) {
      setProviderError(
        cause instanceof Error ? cause.message : "Could not configure OpenAI.",
      );
      setProviderBusy(false);
      return;
    }

    try {
      setSessions(await listSessions());
      await syncSelectedProviderReadiness();
    } catch {
      setProviderNotice(
        "OpenAI is configured, but the conversation status could not be refreshed.",
      );
    } finally {
      setProviderBusy(false);
    }
  }

  async function onClearOpenAI() {
    if (providerBusy) return;
    setProviderBusy(true);
    setProviderError(null);
    setProviderNotice(null);

    try {
      const next = await clearOpenAI();
      setProviders(next);
      setOpenaiKey("");
      setProviderNotice(
        "The temporary OpenAI key was cleared from memory. An OPENAI_API_KEY from the environment stays active.",
      );
    } catch (cause) {
      setProviderError(
        cause instanceof Error ? cause.message : "Could not clear the OpenAI key.",
      );
      setProviderBusy(false);
      return;
    }

    try {
      setSessions(await listSessions());
      await syncSelectedProviderReadiness();
    } catch {
      setProviderNotice(
        "The temporary key was cleared, but the conversation status could not be refreshed.",
      );
    } finally {
      setProviderBusy(false);
    }
  }

  async function onCreate(event: FormEvent) {
    event.preventDefault();
    if (sending || loadingSession || seedActionBusy || providerBusy) return;
    if (
      draft.backend === "openai" &&
      (!openaiStatus?.ready || !draft.external_confirmed)
    ) {
      setCreateError(
        "Configure OpenAI and confirm external processing before starting this conversation.",
      );
      return;
    }
    setCreating(true);
    setError(null);
    setCreateError(null);
    setNotice(null);

    try {
      const created = await createSession(draft);

      refreshRequestId.current += 1;
      sessionRequestId.current += 1;
      setLoadingSession(false);
      setSession(created);
      setRetryTurn(null);
      setExternalTurnConfirmed(false);
      if (draft.backend === "openai") {
        setDraft({ ...draft, external_confirmed: false });
      }
      clearSeedDetail();
      setMobileNavOpen(false);
      setNewChatOpen(false);
      setDraft({ ...emptyDraft, backend: draft.backend, model_id: draft.model_id, authority_mode: draft.authority_mode });

      try {
        setSessions(await listSessions());
      } catch {
        setNotice(
          "The conversation was created, but the list could not be refreshed.",
        );
      }
    } catch (cause) {
      setCreateError(
        cause instanceof Error ? cause.message : "Could not start the conversation.",
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
      const result = await sendTurn(
        session.session_id,
        text,
        requestId,
        session.backend === "openai" ? externalTurnConfirmed : false,
      );
      if (selectedSeed) {
        await refreshSeedAfterMutation(result.session, selectedSeed.id);
      } else {
        setSession(result.session);
      }
      setLastTurn({
        sessionId: session.session_id,
        report: result.report,
        comparison: result.comparison,
      });
      setRetryTurn(null);
      if (session.backend === "openai") {
        setExternalTurnConfirmed(false);
      }

      try {
        setSessions(await listSessions());
      } catch {
        setNotice(
          "The message was sent, but the conversation list could not be refreshed.",
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
        cause instanceof Error ? cause.message : "Could not send the message.",
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
        setSeedNotice("Verified evidence recorded.");
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
        cause instanceof Error ? cause.message : "Could not record the evidence.",
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
        setSeedNotice("Contradiction recorded. This candidate is now blocked.");
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
        cause instanceof Error ? cause.message : "Could not record the contradiction.",
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
        setSeedNotice("The Gate has re-evaluated the contradiction.");
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
        cause instanceof Error ? cause.message : "Could not resolve the contradiction.",
      );
    } finally {
      setSeedActionBusy(false);
    }
  }


  function onComposerKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      event.currentTarget.form?.requestSubmit();
    }
  }

  const formBusy = sending || creating || loadingSession || seedActionBusy;
  const answerAuthor = session
    ? compactModelLabel(session.model_roles?.generation.model_id ?? session.model_id) === "default"
      ? backendLabel(session.backend)
      : compactModelLabel(session.model_roles?.generation.model_id ?? session.model_id)
    : "";
  const showNewChat = newChatOpen || sessions.length === 0;
  const handoff = handoffTitle(session?.orchestration?.state);
  const sessionMeta = session
    ? [
        backendLabel(session.backend),
        modelRoleSummary(session),
        authorityLabel(session.authority_profile_id),
      ]
        .filter(Boolean)
        .join(" · ")
    : null;

  return (
    <main className="product-shell">
      <button
        aria-label="Close conversations"
        className={
          mobileNavOpen
            ? "mobile-nav-backdrop mobile-nav-backdrop--open"
            : "mobile-nav-backdrop"
        }
        onClick={() => setMobileNavOpen(false)}
        type="button"
      />
      <button
        aria-label="Close shadow memory"
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
          <BrandMark />
          <div className="brand__text">
            <strong>Shadowseed</strong>
            <span>Research Preview</span>
          </div>
          <button
            aria-label="Close conversations"
            className="icon-button sidebar-close"
            onClick={() => setMobileNavOpen(false)}
            type="button"
          >
            <Icon name="close" />
          </button>
        </div>

        {showNewChat ? (
          <form className="new-chat" onSubmit={onCreate}>
            <div className="new-chat__head">
              <h2>New conversation</h2>
              {sessions.length ? (
                <button
                  aria-label="Cancel new conversation"
                  className="icon-button"
                  onClick={() => {
                    setNewChatOpen(false);
                    setCreateError(null);
                  }}
                  type="button"
                >
                  <Icon name="close" />
                </button>
              ) : null}
            </div>
            <label className="field">
              <span>Title</span>
              <input
                disabled={formBusy}
                placeholder="Untitled conversation"
                value={draft.title}
                onChange={(event) =>
                  setDraft({ ...draft, title: event.target.value })
                }
              />
            </label>
            <label className="field">
              <span>Model</span>
              <select
                disabled={formBusy || providerBusy}
                value={draft.backend}
                onChange={(event) => {
                  const backend =
                    event.target.value as CreateSessionInput["backend"];
                  setDraft({
                    ...draft,
                    backend,
                    model_id:
                      backend === "openai"
                        ? openaiStatus?.default_model ?? "gpt-4o-mini"
                        : undefined,
                    external_confirmed: false,
                  });
                }}
              >
                <option value="fixture">Offline demo (no model)</option>
                <option value="ollama">Ollama (local)</option>
                <option disabled={!openaiStatus?.ready} value="openai">
                  OpenAI (hosted)
                </option>
              </select>
            </label>
            {draft.backend === "ollama" ? (
              <label className="field">
                <span>Ollama model</span>
                <input
                  aria-describedby="ollama-setup-help"
                  disabled={formBusy}
                  placeholder="e.g. qwen2.5:7b"
                  value={draft.model_id ?? ""}
                  onChange={(event) =>
                    setDraft({ ...draft, model_id: event.target.value })
                  }
                />
                <small className="field-help" id="ollama-setup-help">
                  Start Ollama and enter an installed chat model. Shadowseed
                  also needs <code>embeddinggemma</code>: run{" "}
                  <code>ollama pull embeddinggemma</code> once.
                </small>
              </label>
            ) : null}
            {draft.backend === "openai" ? (
              <>
                <label className="field">
                  <span>OpenAI model</span>
                  <input
                    disabled={formBusy || providerBusy}
                    placeholder={openaiStatus?.default_model ?? "gpt-4o-mini"}
                    value={draft.model_id ?? ""}
                    onChange={(event) =>
                      setDraft({ ...draft, model_id: event.target.value })
                    }
                  />
                </label>
                <label className="check">
                  <input
                    checked={Boolean(draft.external_confirmed)}
                    disabled={creating || providerBusy || !openaiStatus?.ready}
                    onChange={(event) =>
                      setDraft({
                        ...draft,
                        external_confirmed: event.target.checked,
                      })
                    }
                    type="checkbox"
                  />
                  <span>
                    I agree that prompts, shadow context and embeddings for
                    this conversation are sent to OpenAI.
                  </span>
                </label>
              </>
            ) : null}
            <label className="field">
              <span>Authority mode</span>
              <select
                disabled={formBusy}
                value={draft.authority_mode}
                onChange={(event) =>
                  setDraft({
                    ...draft,
                    authority_mode: event.target
                      .value as CreateSessionInput["authority_mode"],
                  })
                }
              >
                <option value="controlled">{AUTHORITY_MODES.controlled.label}</option>
                <option value="assisted">{AUTHORITY_MODES.assisted.label}</option>
                <option value="exploratory">{AUTHORITY_MODES.exploratory.label}</option>
              </select>
              <small className="field-help">
                {AUTHORITY_MODES[draft.authority_mode].help}
              </small>
            </label>
            <button
              className="button button--primary"
              type="submit"
              disabled={
                formBusy ||
                providerBusy ||
                (draft.backend === "ollama" && !draft.model_id?.trim()) ||
                (draft.backend === "openai" &&
                  (!openaiStatus?.ready ||
                    !draft.external_confirmed ||
                    !draft.model_id?.trim()))
              }
            >
              {creating ? "Starting…" : "Start conversation"}
            </button>
            {createError ? (
              <div className="alert alert--danger" role="alert">{createError}</div>
            ) : null}
          </form>
        ) : (
          <button
            className="button button--primary button--block"
            disabled={formBusy}
            onClick={() => setNewChatOpen(true)}
            type="button"
          >
            <Icon name="plus" />
            New conversation
          </button>
        )}

        {sessions.length ? (
          <nav className="conversation-list" aria-label="Conversations">
            <h2 className="section-label">Conversations</h2>
            {sessions.map((item) => (
              <button
                aria-current={item.session_id === session?.session_id ? "page" : undefined}
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
                  {backendLabel(item.backend)} · {plural(item.turn_count, "turn", "turns")} ·{" "}
                  {plural(item.seed_count, "candidate", "candidates")}
                  {item.provider_ready === false ? " · provider needed" : ""}
                </span>
              </button>
            ))}
          </nav>
        ) : (
          <div className="conversation-list" />
        )}

        <details className="provider-settings">
          <summary>
            <span>Providers</span>
            <span
              className={
                openaiStatus?.ready ? "dot dot--success" : "dot dot--muted"
              }
            >
              {openaiStatus?.ready
                ? "OpenAI ready"
                : openaiStatus?.configured
                  ? "OpenAI runtime missing"
                  : "OpenAI not configured"}
            </span>
          </summary>
          <div className="provider-settings__body">
            {!openaiStatus?.available ? (
              <p className="muted">
                The OpenAI runtime is not installed. Install the{" "}
                <code>shadowseed[openai]</code> extra to use this provider.
              </p>
            ) : null}
            <form onSubmit={onConfigureOpenAI}>
              <label className="field">
                <span>Temporary API key</span>
                <input
                  autoComplete="off"
                  disabled={providerBusy}
                  onChange={(event) => setOpenaiKey(event.target.value)}
                  placeholder="sk-…"
                  type="password"
                  value={openaiKey}
                />
              </label>
              <button
                className="button button--secondary"
                disabled={providerBusy || !openaiKey.trim()}
                type="submit"
              >
                {providerBusy ? "Working…" : "Configure"}
              </button>
            </form>
            {openaiStatus?.configured ? (
              <button
                className="button button--ghost"
                disabled={providerBusy}
                onClick={onClearOpenAI}
                type="button"
              >
                Clear temporary key
              </button>
            ) : null}
            <p className="muted">
              The key goes only to the local Python service. It is never
              stored in the workspace, browser storage or exports.
            </p>
            {providerNotice ? (
              <div className="alert alert--info">{providerNotice}</div>
            ) : null}
            {providerError ? (
              <div className="alert alert--danger">{providerError}</div>
            ) : null}
          </div>
        </details>
      </aside>

      <section className="chat-column">
        <header className="chat-header">
          <button
            aria-controls="session-navigation"
            aria-expanded={mobileNavOpen}
            aria-label="Open conversations"
            className="icon-button mobile-nav-button"
            disabled={sending || creating}
            onClick={() => {
              setShadowOpen(false);
              setMobileNavOpen(true);
            }}
            type="button"
          >
            <Icon name="menu" />
          </button>
          <div className="chat-header__main">
            <h1>{session?.title ?? "Shadowseed"}</h1>
            <p>{sessionMeta ?? "Start a conversation to begin."}</p>
          </div>
          <div className="chat-header__actions">
            {session?.provider_ready === false ? (
              <span className="badge badge--warning">Provider needed</span>
            ) : null}
            {session ? (
              <span
                className="badge badge--outline policy-badge"
                title={"Gate policy: " + session.effective_gate_policy_id}
              >
                {gatePolicyLabel(session.effective_gate_policy_id)}
              </span>
            ) : null}
            <button
              aria-controls="shadow-inspector"
              aria-expanded={shadowOpen}
              className="button button--secondary shadow-toggle-button"
              onClick={() => {
                setMobileNavOpen(false);
                setShadowOpen(true);
              }}
              type="button"
            >
              <Icon name="panel" />
              Shadow
              {sortedSeeds.length ? (
                <span className="count">{sortedSeeds.length}</span>
              ) : null}
            </button>
          </div>
        </header>

        <div className="messages">
          {!session ? (
            <div className="empty-state">
              <h2>No conversation selected</h2>
              <p>Create a conversation in the sidebar.</p>
            </div>
          ) : session.messages.length === 0 ? (
            <div className="empty-state">
              <h2>No messages</h2>
              <p>
                Detected candidates are listed in the Shadow panel with
                weight 0.
              </p>
            </div>
          ) : (
            <div className="message-stack">
              {session.messages.map((message, index) => (
                <article
                  className={"message message--" + message.role}
                  key={message.role + "-" + index}
                >
                  {message.role === "assistant" ? (
                    <span className="message__author">{answerAuthor}</span>
                  ) : null}
                  <p>{message.content}</p>
                </article>
              ))}
              {sending ? (
                <article className="message message--assistant message--pending">
                  <span className="message__author">{answerAuthor}</span>
                  <p aria-live="polite">Waiting for response…</p>
                </article>
              ) : null}
            </div>
          )}
        </div>

        {notice ? <div className="alert alert--info chat-alert">{notice}</div> : null}
        {error ? <div className="alert alert--danger chat-alert" role="alert">{error}</div> : null}

        <form className="composer" onSubmit={onSend}>
          {session?.backend === "openai" ? (
            <label className="check composer-consent">
              <input
                checked={externalTurnConfirmed}
                disabled={
                  sending ||
                  loadingSession ||
                  session.provider_ready === false
                }
                onChange={(event) =>
                  setExternalTurnConfirmed(event.target.checked)
                }
                type="checkbox"
              />
              <span>
                Send this message and the shadow context it uses to OpenAI for
                this turn.
              </span>
            </label>
          ) : null}
          <div className="composer__row">
            <textarea
              aria-label="Message"
              disabled={
                !session ||
                sending ||
                loadingSession ||
                session.provider_ready === false
              }
              onKeyDown={onComposerKeyDown}
              placeholder={
                session
                  ? session.provider_ready === false
                    ? "Configure the provider first…"
                    : loadingSession
                      ? "Loading conversation…"
                      : "Message"
                  : "No conversation selected"
              }
              value={question}
              onChange={(event) => {
                const value = event.target.value;
                setQuestion(value);
                if (retryTurn && value.trim() !== retryTurn.text) {
                  setRetryTurn(null);
                }
              }}
              rows={1}
            />
            <button
              aria-label="Send"
              className="button button--primary composer__send"
              disabled={
                !session ||
                sending ||
                loadingSession ||
                seedActionBusy ||
                session.provider_ready === false ||
                (session.backend === "openai" && !externalTurnConfirmed) ||
                !question.trim()
              }
            >
              {sending ? "Sending…" : <><span>Send</span><Icon name="send" /></>}
            </button>
          </div>
          <p className="composer__hint">
            Enter to send · Shift+Enter for a new line
          </p>
        </form>
      </section>

      <aside
        className={shadowOpen ? "shadow-column shadow-column--open" : "shadow-column"}
        id="shadow-inspector"
      >
        <div className="shadow-heading">
          <div>
            <h2>Shadow memory</h2>
            <p>{plural(sortedSeeds.length, "candidate", "candidates")}</p>
          </div>
          <button
            aria-label="Close shadow memory"
            className="icon-button shadow-close"
            onClick={() => setShadowOpen(false)}
            type="button"
          >
            <Icon name="close" />
          </button>
        </div>

        <div className="shadow-body">
          {seedNotice ? (
            <div className="alert alert--info">{seedNotice}</div>
          ) : null}
          {seedError ? (
            <div className="alert alert--danger">{seedError}</div>
          ) : null}

          {selectedSeed ? (
            <div className="seed-detail">
              <button
                className="link-button"
                disabled={seedActionBusy}
                onClick={clearSeedDetail}
                type="button"
              >
                <Icon name="back" />
                All candidates
              </button>

              <section className="panel">
                <StatusBadge seed={selectedSeed} />
                <h3 className="seed-detail__text">{selectedSeed.text}</h3>
                <p className="muted">{selectedSeed.plain_explanation}</p>
                <dl className="facts">
                  <div>
                    <dt>Seen</dt>
                    <dd>{selectedSeed.occurrence_count ?? 0}×</dd>
                  </div>
                  <div>
                    <dt>Verified sources</dt>
                    <dd>{selectedSeed.evidence_count ?? 0}</dd>
                  </div>
                  <div>
                    <dt>Contradiction</dt>
                    <dd>{selectedSeed.blocking ? "Open" : "None"}</dd>
                  </div>
                  <div>
                    <dt>Weight</dt>
                    <dd className="mono">
                      {Number(selectedSeed.weight ?? 0).toFixed(2)}
                    </dd>
                  </div>
                </dl>
                {selectedSeed.review_required ? (
                  <div className="alert alert--warning">
                    Review required.
                  </div>
                ) : null}
              </section>

              <section className="panel">
                <h3>Add verified evidence</h3>
                <p className="muted">
                  Submit only a source you have checked yourself. The Gate
                  records it as operator-verified evidence.
                </p>
                <form className="stack" onSubmit={onSubmitEvidence}>
                  <label className="field">
                    <span>Source reference</span>
                    <input
                      disabled={seedActionBusy}
                      placeholder="URL, DOI or another stable reference"
                      value={evidenceRef}
                      onChange={(event) => {
                        setEvidenceRef(event.target.value);
                        if (retrySeedAction?.kind === "evidence") {
                          setRetrySeedAction(null);
                        }
                      }}
                    />
                  </label>
                  <label className="field">
                    <span>Note <em>optional</em></span>
                    <textarea
                      disabled={seedActionBusy}
                      placeholder="Why does this source support the candidate?"
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
                  <label className="check">
                    <input
                      checked={evidenceVerified}
                      disabled={seedActionBusy}
                      onChange={(event) =>
                        setEvidenceVerified(event.target.checked)
                      }
                      type="checkbox"
                    />
                    <span>
                      I checked this source and confirm it supports this
                      candidate.
                    </span>
                  </label>
                  <button
                    className="button button--primary"
                    disabled={
                      seedActionBusy ||
                      !evidenceRef.trim() ||
                      !evidenceVerified
                    }
                    type="submit"
                  >
                    {seedActionBusy ? "Working…" : "Record evidence"}
                  </button>
                </form>
              </section>

              <section className="panel">
                <h3>Contradiction</h3>
                {selectedSeed.blocking ? (
                  <form className="stack" onSubmit={onResolveContradiction}>
                    <p className="muted">
                      Blocked by an open contradiction. Record the basis for
                      resolution; the Gate re-evaluates authority.
                    </p>
                    <label className="field">
                      <span>Basis for resolution</span>
                      <textarea
                        disabled={seedActionBusy}
                        placeholder="Why can this block be lifted?"
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
                      className="button button--primary"
                      disabled={seedActionBusy || !resolutionBasis.trim()}
                      type="submit"
                    >
                      {seedActionBusy ? "Working…" : "Resolve contradiction"}
                    </button>
                  </form>
                ) : (
                  <>
                    <p className="muted">
                      Blocks this candidate from influencing answers until the
                      contradiction is resolved through the Gate.
                    </p>
                    <button
                      className="button button--danger"
                      disabled={seedActionBusy}
                      onClick={onContradictSeed}
                      type="button"
                    >
                      {seedActionBusy ? "Working…" : "Mark as contradicted"}
                    </button>
                  </>
                )}
              </section>

              <section className="panel">
                <h3>Timeline</h3>
                <SeedTimeline events={selectedSeed.timeline} />
              </section>

              <section className="panel">
                <h3>Raw data</h3>
                <RawJson label="Seed record" value={selectedSeed} />
              </section>
            </div>
          ) : (
            <>
              {session?.orchestration && handoff ? (
                <section className="alert alert--warning handoff">
                  <strong>{handoff}</strong>
                  <p>{session.orchestration.reason_text}</p>
                </section>
              ) : null}

              {loadingSeed ? (
                <div className="shadow-empty">
                  <p>Loading candidate…</p>
                </div>
              ) : sortedSeeds.length ? (
                <div className="seed-list">
                  {sortedSeeds.map((seed) => (
                    <SeedCard
                      key={seed.id}
                      onOpen={() => openSeed(seed.id)}
                      seed={seed}
                    />
                  ))}
                </div>
              ) : (
                <div className="shadow-empty">
                  <strong>No candidates</strong>
                  <p>Candidates are created with weight 0.</p>
                </div>
              )}
            </>
          )}
        </div>

        {session ? (
          <details className="tech-details">
            <summary>Technical details and raw data</summary>
            <dl>
              <div>
                <dt>Gate policy</dt>
                <dd className="mono">{session.effective_gate_policy_id}</dd>
              </div>
              <div>
                <dt>Authority profile</dt>
                <dd className="mono">{session.authority_profile_id}</dd>
              </div>
              <div>
                <dt>Behavior digest</dt>
                <dd className="mono">{session.behavior_config_digest.slice(0, 16)}</dd>
              </div>
              <div>
                <dt>Session</dt>
                <dd className="mono">{session.session_id}</dd>
              </div>
            </dl>
            <div className="raw-stack">
              <RawJson label="Session" value={session} />
              {lastTurn && lastTurn.sessionId === session.session_id ? (
                <>
                  <RawJson label="Last turn report" value={lastTurn.report} />
                  {lastTurn.comparison ? (
                    <RawJson label="Last turn comparison" value={lastTurn.comparison} />
                  ) : null}
                </>
              ) : (
                <p className="muted">Turn reports appear here after the next message.</p>
              )}
            </div>
          </details>
        ) : null}
      </aside>
    </main>
  );
}
