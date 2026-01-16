// src/components/SessionCard.tsx
import { Link } from 'react-router-dom';

interface SessionCardProps {
  session: { id: string; title: string; date: string; status: string };
}

const SessionCard = ({ session }: SessionCardProps) => {
  return (
    <tr>
      <td>{session.title}</td>
      <td>{session.date}</td>
      <td><span className={`status status-${session.status.toLowerCase()}`}>{session.status}</span></td>
      <td><Link className="action-btn small" to={`/sessions/${session.id}`}>Присоединиться</Link></td>
    </tr>
  );
};

export default SessionCard;