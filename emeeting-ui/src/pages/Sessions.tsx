import { useEffect, useState } from "react";
import { getSessions } from "../api/sessions";
import { type Session } from "../types/db";
import SessionCard from "../components/SessionCard";

const Sessions = () => {
  const [sessions, setSessions] = useState<Session[]>([]);

  useEffect(() => {
    getSessions().then(setSessions).catch(console.error);
  }, []);

  return (
    <div>
      <h2>Сессии</h2>
      {sessions.map((s) => (
        <SessionCard key={s.sessionId} session={s} />
      ))}
    </div>
  );
};

export default Sessions;
