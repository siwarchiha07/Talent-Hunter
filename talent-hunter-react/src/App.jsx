import { useState } from "react";
import "./App.css";
import { FiPrinter, FiDownload } from "react-icons/fi";

//const API_URL = "http://127.0.0.1:8001";
const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8001";
function downloadCsv(data, filename = "talents_enrichis.csv") {
  if (!data || data.length === 0) return;

  const headers = Object.keys(data[0]);
  const csvRows = [
    headers.join(","),
    ...data.map(row =>
      headers.map(fieldName => {
        const val = row[fieldName];
        if (typeof val === "string") {
          const safe = val.replace(/"/g, '""');
          return `"${safe}"`;
        }
        return val;
      }).join(",")
    ),
  ].join("\n");

  const blob = new Blob([csvRows], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

function App() {
  const [jobDescription, setJobDescription] = useState(
    "We are looking for a machine learning engineer with Python, deep learning and experience with PyTorch."
  );
  const [topK, setTopK] = useState(5);
  const [minStars, setMinStars] = useState(0);
  const [languageFilter, setLanguageFilter] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [error, setError] = useState("");
  const [selectedLogin, setSelectedLogin] = useState("");

  // Variables pour l'email de contact
  const [jobTitleEmail, setJobTitleEmail] = useState("Machine Learning Engineer");
  const [companyEmail, setCompanyEmail] = useState("YourCompany");

  const handleSearch = async () => {
    setError("");
    setLoading(true);
    setResults([]);

    try {
      const payload = {
        job_description: jobDescription,
        top_k: topK,
        min_stars: minStars > 0 ? minStars : 0,
        language_filter: languageFilter || null,
      };

    const response = await fetch(`${API_URL}/agent_search`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "Bypass-Tunnel-Reminder": "true" 
      },
      body: JSON.stringify(payload),
    });

      if (!response.ok) throw new Error(`HTTP error ${response.status}`);

      const data = await response.json();
      setResults(data.results || []);
      if ((data.results || []).length > 0) {
        setSelectedLogin(data.results[0].login || "");
      }
    } catch (err) {
      console.error(err);
      setError("Erreur lors de la recherche Agentic. Vérifiez que FastAPI et Ollama tournent bien.");
    } finally {
      setLoading(false);
    }
  };

  const selectedCandidate = results.find((r) => r.login === selectedLogin) || null;

  const emailBody = selectedCandidate
    ? `Hello ${selectedCandidate.name || selectedCandidate.login},

I found your GitHub profile and was really impressed by your background. 
${selectedCandidate.ai_summary ? `\nAnalysis of your profile: ${selectedCandidate.ai_summary}\n` : ""}
We are currently looking for a ${jobTitleEmail} at ${companyEmail}. Your skills in ${selectedCandidate.ai_skills?.join(", ") || selectedCandidate.languages_list} seem to be a very good match.

If you are open to discussing this opportunity, I would be happy to schedule a short call.

Best regards,
[Your Name]`
    : "";

  return (
    <div className="app">
      <nav className="navbar no-print">
        <div className="navbar-brand">TalentHunter AI</div>
      </nav>

      <header className="header no-print">
        <h1>🤖 Talent Hunter – Agentic AI Edition</h1>
        <p>Powered by Llama 3 & Vector Search to find your next top talent.</p>
      </header>

      <main className="main-container">
        <section className="card no-print">
          <h2>Job Description & AI Filters</h2>
          <textarea
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            rows={4}
          />
          <div className="controls-row">
            <div className="control">
              <label>Top K (AI Analysis)</label>
              <input type="number" value={topK} onChange={(e) => setTopK(Number(e.target.value))} />
            </div>
            <div className="control">
              <label>Min Stars</label>
              <input type="number" value={minStars} onChange={(e) => setMinStars(Number(e.target.value))} />
            </div>
            <div className="control">
              <label>Language</label>
              <input type="text" placeholder="Python..." value={languageFilter} onChange={(e) => setLanguageFilter(e.target.value)} />
            </div>
          </div>
          <button className="btn-primary" onClick={handleSearch} disabled={loading}>
            {loading ? "AI is analyzing profiles..." : "🔍 Agentic Search"}
          </button>
          {error && <p className="error">{error}</p>}
        </section>

        {results.length > 0 && (
          <section className="card">
            <div className="results-header">
              <h2>Top Matches Scored by AI</h2>
              <div className="actions no-print">
                <button className="btn-secondary" onClick={() => downloadCsv(results)}>
                   <FiDownload /> CSV
                </button>
                <button className="btn-secondary" onClick={() => window.print()}>
                   <FiPrinter /> Export PDF
                </button>
              </div>
            </div>

            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Score</th>
                    <th>Login</th>
                    <th>AI Extracted Skills</th>
                    <th className="no-print">Stars</th>
                    <th className="no-print">Similarity</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((r, idx) => (
                    <tr
                      key={idx}
                      className={selectedLogin === r.login ? "selected-row" : ""}
                      onClick={() => setSelectedLogin(r.login)}
                    >
                      <td className="score-cell">{(r.agent_score * 100).toFixed(0)}%</td>
                      <td><strong>{r.login}</strong></td>
                      <td>
                        <div className="skills-container">
                            {r.ai_skills?.map((s, i) => (
                            <span key={i} className="skill-tag">{s}</span>
                            ))}
                        </div>
                      </td>
                      <td className="no-print">{r.total_stars}</td>
                      <td className="no-print">{r.similarity?.toFixed(3)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {selectedCandidate && (
          <div className="details-grid">
            <section className="card">
              <h2>AI Profile Summary</h2>
              <div className="ai-summary-box">
                <p>{selectedCandidate.ai_summary || "No summary generated."}</p>
              </div>
              <div className="no-print">
                <h3>Technical Context</h3>
                <p><small>{selectedCandidate.languages_list}</small></p>
              </div>
            </section>

            <section className="card no-print">
              <h2>Contact Settings & Email</h2>
              <div className="controls-row">
                <div className="control">
                    <label>Job Title</label>
                    <input type="text" value={jobTitleEmail} onChange={(e) => setJobTitleEmail(e.target.value)} />
                </div>
                <div className="control">
                    <label>Company</label>
                    <input type="text" value={companyEmail} onChange={(e) => setCompanyEmail(e.target.value)} />
                </div>
              </div>
              <textarea rows={10} value={emailBody} readOnly className="email-box" />
            </section>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;