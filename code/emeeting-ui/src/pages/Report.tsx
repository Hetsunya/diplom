// src/pages/Report.tsx
import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { getReport } from '../api/reports';

const Report = () => {
  const { id } = useParams();
  const [report, setReport] = useState(null);

  useEffect(() => {
    const fetchReport = async () => {
      try {
        const data = await getReport(id!);
        setReport(data);
      } catch (error) {
        console.error(error);
      }
    };
    fetchReport();
  }, [id]);

  return (
    <div className="report-container">
      <header>
        <h1>Отчет по сессии {id}</h1>
      </header>
      <div className="summary-box">
        {/* Саммари */}
      </div>
      <div className="metrics-grid">
        {/* Метрики */}
      </div>
      <div className="charts-section">
        {/* Чарты */}
      </div>
      <div className="participant-section">
        <table className="participants-table">
          {/* Таблица участников */}
        </table>
      </div>
      <div className="recommendations">
        <h3>Рекомендации</h3>
        <ul>
          {/* Рекомендации */}
        </ul>
      </div>
      {report && <pre>{JSON.stringify(report, null, 2)}</pre>}
    </div>
  );
};

export default Report;