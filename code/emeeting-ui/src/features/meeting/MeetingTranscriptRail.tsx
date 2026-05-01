import { useMemo } from "react";

export type TranscriptLine = {
  traceId: string;
  participantId: string;
  speakerLabel: string;
  text: string;
  final: boolean;
  at: string;
};

type MeetingTranscriptRailProps = {
  lines: TranscriptLine[];
  verdictSummary: string | null;
  verdictDetail: unknown | null;
  verdictSource: string | null;
  verdictExpanded: boolean;
  onToggleVerdict: () => void;
};

export function MeetingTranscriptRail({
  lines,
  verdictSummary,
  verdictDetail,
  verdictSource,
  verdictExpanded,
  onToggleVerdict,
}: MeetingTranscriptRailProps) {
  const linesShown = useMemo(() => [...lines].reverse(), [lines]);

  return (
    <aside className="meeting-transcript-rail" aria-label="Транскрипт и вердикт AI">
      <div className="meeting-transcript-rail__section meeting-transcript-rail__verdict">
        <div className="meeting-transcript-rail__section-title-row">
          <div className="meeting-transcript-rail__section-title">Вердикт AI</div>
          {verdictSource && (
            <span className={`meeting-transcript-rail__source-badge meeting-transcript-rail__source-badge--${verdictSource}`}>
              {verdictSource}
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
        <div className="meeting-transcript-rail__section-title">Транскрипт (ASR)</div>
        <div className="meeting-transcript-rail__scroll" role="log" aria-live="polite">
          {linesShown.length === 0 ? (
            <p className="meeting-transcript-rail__muted">Сюда попадают события text_analysis, когда включён speech-service.</p>
          ) : (
            linesShown.map((line) => (
              <div key={`${line.traceId}-${line.participantId}`} className="meeting-transcript-rail__line">
                <div className="meeting-transcript-rail__line-meta">
                  <span className="meeting-transcript-rail__speaker">{line.speakerLabel}</span>
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

      <div className="meeting-transcript-rail__section meeting-transcript-rail__chat-note">
        <div className="meeting-transcript-rail__section-title">Чат</div>
        <p className="meeting-transcript-rail__muted">
          Отдельный чат участников будет здесь или в отдельной панели (BL-039). Сейчас эта колонка только для AI-транскрипта и
          вердикта.
        </p>
      </div>
    </aside>
  );
}
