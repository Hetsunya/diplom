import { Link } from "react-router-dom";
import type { Session } from "../types/db";

interface Props {
  session: Session;
}

const SessionCard = ({ session }: Props) => {
  return (
    <div className="session-card">
      <h3>{session.title}</h3>
      <p>Запланировано: {session.startDatetime ? new Date(session.startDatetime).toLocaleString() : 'Не указано'}</p>
      <p>Тип: {session.sessionType}</p>
      <Link to={`/sessions/${session.sessionId}`}>Открыть</Link>
    </div>
  );
};

export default SessionCard;
