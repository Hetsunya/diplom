import { Link } from "react-router-dom";
import { type Session } from "../types/db";

interface SessionCardProps {
  session: Session;
}

const SessionCard = ({ session }: SessionCardProps) => {
  return (
    <div>
      <h3>{session.title}</h3>


      <p>
        Запланировано: {new Date(session.scheduledAt).toLocaleString()}
      </p>

      <Link to={`/sessions/${session.id}`}>Join</Link>
    </div>
  );
};

export default SessionCard;
