import { useMemo } from "react";
import { MeetingChatSection, type ChatLine } from "./MeetingChatSection";

export type TranscriptLine = {
  traceId: string;
  participantId: string;
  speakerLabel: string;
  text: string;
  final: boolean;
  at: string;
};

export type { ChatLine };

type MeetingTranscriptRailProps = {
  lines: TranscriptLine[];
  asrStatus: string;
  verdictSummary: string | null;
  verdictDetail: unknown | null;
  verdictSource: string | null;
  verdictExpanded: boolean;
  onToggleVerdict: () => void;
  chatMessages: ChatLine[];
  currentParticipantId: string;
  onSendChat: (text: string) => void;
  chatConnected?: boolean;
};

export function MeetingTranscriptRail({
  lines,
  asrStatus,
  verdictSummary,
  verdictDetail,
  verdictSource,
  verdictExpanded,
  onToggleVerdict,
  chatMessages,
  currentParticipantId,
  onSendChat,
  chatConnected = true,
}: MeetingTranscriptRailProps) {
  const linesShown = useMemo(() => [...lines].reverse(), [lines]);
  const sourceClass =
    verdictSource === "remote" || verdictSource === "local_fallback" || verdictSource === "local_stub"
      ? verdictSource
      : "local_stub";
  const sourceLabel =
    verdictSource === "remote"
      ? "NN"
      : verdictSource === "local_fallback"
        ? "fallback"
        : verdictSource === "local_stub"
          ? "stub"
          : null;

  return (
    <aside className="meeting-transcript-rail" aria-label="Транскрибация речи, вердикт AI и чат">
      <div className="meeting-transcript-rail__section meeting-transcript-rail__verdict">
        <div className="meeting-transcript-rail__section-title-row">
          <div className="meeting-transcript-rail__section-title">Вердикт AI</div>
          {sourceLabel && (
            <span
              className={`meeting-transcript-rail__source-badge meeting-transcript-rail__source-badge--${sourceClass}`}
              title={`source: ${verdictSource}`}
            >
              {sourceLabel}
            </span>
          )}
        </div>
        {verdictSummary ? (
          <>
            <button type="button" className="meeting-transcript-rail__verdict-btn" onClick={onToggleVerdict}>
              {verdictSummary}
              <span className="meeting-transcript-rail__chevron">{verdictExpanded ? " ▲" : " ▼"}</span>
            </button>
            {verdictExpanded && verdictDetail != null && (
              <pre className="meeting-transcript-rail__verdict-detail">
                {JSON.stringify(verdictDetail, null, 2)}
              </pre>
            )}
          </>
        ) : (
          <p className="meeting-transcript-rail__muted">Пока нет данных отчёта. Дождитесь частичного отчёта.</p>
        )}
      </div>

      <div className="meeting-transcript-rail__section">
        <div className="meeting-transcript-rail__section-title-row">
          <div className="meeting-transcript-rail__section-title">Транскрибация (ASR)</div>
          <span className="meeting-transcript-rail__asr-status" title="Состояние live-транскрибации речи">
            {asrStatus}
          </span>
        </div>
        <div className="meeting-transcript-rail__scroll" role="log" aria-live="polite">
          {linesShown.length === 0 ? (
            <p className="meeting-transcript-rail__muted">
              Здесь появляется распознанная речь (события text_analysis), когда включён ai-gateway и
              speech-service.
            </p>
          ) : (
            linesShown.map((line) => (
              <div key={`${line.traceId}-${line.participantId}`} className="meeting-transcript-rail__line">
                <div className="meeting-transcript-rail__line-meta">
                  <span className="meeting-transcript-rail__speaker">{line.speakerLabel}</span>
                  <span className="meeting-transcript-rail__meta-sep" aria-hidden="true">
                    ·
                  </span>
                  {line.final ? (
                    <span className="meeting-transcript-rail__badge meeting-transcript-rail__badge--final">финал</span>
                  ) : (
                    <span className="meeting-transcript-rail__badge">черновик</span>
                  )}
                </div>
                <div className="meeting-transcript-rail__line-text">{line.text || "…"}</div>
              </div>
            ))
          )}
        </div>
      </div>

      <MeetingChatSection
        messages={chatMessages}
        currentParticipantId={currentParticipantId}
        onSend={onSendChat}
        canSend={chatConnected}
      />
    </aside>
  );
}
