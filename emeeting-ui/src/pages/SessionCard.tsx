import { Link } from "react-router-dom";

// src/components/SessionCard.tsx
interface SessionCardProps {
  session: { id: string; title: string; date: string };
}

const SessionCard = ({ session }: SessionCardProps) => {
  return (
    <div>
      <h3>{session.title}</h3>
      <p>{session.date}</p>
      <Link to={`/sessions/${session.id}`}>Join</Link>
    </div>
  );
};

export default SessionCard;