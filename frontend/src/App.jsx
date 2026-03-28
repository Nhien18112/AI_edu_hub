import mermaid from "mermaid";
import { useEffect, useMemo, useRef, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";

function formatTime(isoText) {
  if (!isoText) return "Không rõ thời gian";
  const date = new Date(isoText);
  if (Number.isNaN(date.getTime())) return "Không rõ thời gian";
  return date.toLocaleString("vi-VN");
}

function normalizeApiError(value) {
  if (!value) return "Yêu cầu thất bại";
  if (typeof value === "string") return value;

  if (Array.isArray(value)) {
    const messages = value
      .map((item) => normalizeApiError(item))
      .filter(Boolean);
    return messages.length ? messages.join(" | ") : "Yêu cầu thất bại";
  }

  if (typeof value === "object") {
    if (typeof value.message === "string" && value.message.trim()) return value.message;
    if (typeof value.msg === "string" && value.msg.trim()) return value.msg;

    const loc = Array.isArray(value.loc) ? ` (${value.loc.join(".")})` : "";
    if (typeof value.type === "string" && value.type.trim()) {
      return `${value.type}${loc}`;
    }

    try {
      return JSON.stringify(value);
    } catch {
      return "Yêu cầu thất bại";
    }
  }

  return String(value);
}

function ensureText(value, fallback = "") {
  if (typeof value === "string") return value;
  if (value == null) return fallback;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return normalizeApiError(value);
}

async function callApi(path, options = {}, timeoutMs = 20000) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`${API_BASE}${path}`, { ...options, signal: controller.signal });
    const contentType = (response.headers.get("content-type") || "").toLowerCase();
    const isJson = contentType.includes("application/json");
    const rawBody = await response.text();

    if (!isJson) {
      const shortBody = rawBody.slice(0, 120).replace(/\s+/g, " ").trim();
      throw new Error(
        `API trả về dữ liệu không phải JSON (HTTP ${response.status}). Nội dung nhận được: ${shortBody || "(rỗng)"}`
      );
    }

    let data;
    try {
      data = rawBody ? JSON.parse(rawBody) : {};
    } catch {
      throw new Error(`Phản hồi JSON không hợp lệ từ máy chủ (HTTP ${response.status}).`);
    }

    if (!response.ok) {
      const detailText = normalizeApiError(data?.detail ?? data?.message ?? data);
      throw new Error(detailText || `Yêu cầu thất bại (HTTP ${response.status})`);
    }
    return data;
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error("Hết thời gian chờ phản hồi từ máy chủ. Vui lòng thử lại.");
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

function SourceLine({ sources }) {
  if (!sources?.length) return null;
  const names = sources.map((source) => source.payload?.filename || "Không rõ").join(" | ");
  return <small className="source-line">Nguồn: {names}</small>;
}

const normalizeMindmapLabel = (text) => {
  const raw = (text || "").toString().replace(/[\n\r]+/g, " ").trim();
  if (!raw) return "Nội dung";
  return raw.replace(/\s+/g, " ");
};

const mermaidLabel = (text) => normalizeMindmapLabel(text).replace(/"/g, "'").replace(/\[/g, "(").replace(/\]/g, ")");

function buildMindmapMermaid(mindmapData) {
  const lines = [
    "flowchart TD",
    "  classDef root fill:#d6f7de,stroke:#2f8e03,stroke-width:2px,color:#103a11;",
    "  classDef branch fill:#e6f4f1,stroke:#1b7c71,stroke-width:1.5px,color:#113836;",
    "  classDef detail fill:#fff8e8,stroke:#d9981b,stroke-width:1px,color:#4e3a08;",
  ];

  let seq = 0;
  const nextId = () => `n${seq++}`;

  const rootId = nextId();
  lines.push(`  ${rootId}["${mermaidLabel(mindmapData?.topic || "Mindmap")}"]:::root`);

  (mindmapData?.branches || []).forEach((branch) => {
    const branchId = nextId();
    lines.push(`  ${branchId}["${mermaidLabel(branch.title)}"]:::branch`);
    lines.push(`  ${rootId} --> ${branchId}`);

    (branch.details || []).forEach((item) => {
      const detailId = nextId();
      lines.push(`  ${detailId}["${mermaidLabel(item)}"]:::detail`);
      lines.push(`  ${branchId} --> ${detailId}`);
    });

    (branch.sub_branches || []).forEach((sub) => {
      const subId = nextId();
      lines.push(`  ${subId}["${mermaidLabel(sub.title)}"]:::branch`);
      lines.push(`  ${branchId} --> ${subId}`);

      (sub.details || []).forEach((item) => {
        const subDetailId = nextId();
        lines.push(`  ${subDetailId}["${mermaidLabel(item)}"]:::detail`);
        lines.push(`  ${subId} --> ${subDetailId}`);
      });
    });
  });

  return lines.join("\n");
}

function MindmapDiagram({ mindmap }) {
  const [svg, setSvg] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!mindmap) {
      setSvg("");
      setError("");
      return;
    }

    const renderDiagram = async () => {
      try {
        mermaid.initialize({ startOnLoad: false, theme: "default", securityLevel: "loose" });
        const id = `mindmap-${Date.now()}`;
        const chart = buildMindmapMermaid(mindmap);
        const result = await mermaid.render(id, chart);
        setSvg(result.svg);
        setError("");
      } catch (e) {
        setError(`Không thể vẽ sơ đồ mindmap: ${e?.message || "Lỗi không xác định"}`);
        setSvg("");
      }
    };

    renderDiagram();
  }, [mindmap]);

  if (!mindmap) return null;

  if (error) {
    return (
      <div className="mindmap-fallback">
        <p>{error}</p>
        <pre>{buildMindmapMermaid(mindmap)}</pre>
      </div>
    );
  }

  return <div className="mindmap-diagram" dangerouslySetInnerHTML={{ __html: svg }} />;
}

export default function App() {
  const mindmapOnlyMode = useMemo(() => {
    if (typeof window === "undefined") return false;
    return new URLSearchParams(window.location.search).get("view") === "mindmap";
  }, []);

  const uploadFormRef = useRef(null);
  const fileInputRef = useRef(null);

  const [tab, setTab] = useState(mindmapOnlyMode ? "mindmap" : "upload");
  const [documents, setDocuments] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState("");

  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");

  const [topic, setTopic] = useState("");
  const [numQuestions, setNumQuestions] = useState(5);
  const [quiz, setQuiz] = useState([]);
  const [quizAnswers, setQuizAnswers] = useState({});
  const [quizSubmitted, setQuizSubmitted] = useState(false);

  const [roadmapGoal, setRoadmapGoal] = useState("");
  const [roadmapLevels, setRoadmapLevels] = useState(6);
  const [roadmapDocIds, setRoadmapDocIds] = useState([]);
  const [roadmap, setRoadmap] = useState(null);
  const [roadmapProgress, setRoadmapProgress] = useState({});
  const [selectedLevel, setSelectedLevel] = useState(null);
  const [levelQuiz, setLevelQuiz] = useState([]);
  const [levelQuizAnswers, setLevelQuizAnswers] = useState({});
  const [levelQuizSubmitted, setLevelQuizSubmitted] = useState(false);

  const [mindmapTopic, setMindmapTopic] = useState("");
  const [mindmapDocIds, setMindmapDocIds] = useState([]);
  const [mindmap, setMindmap] = useState(null);

  const [statusText, setStatusText] = useState("Sẵn sàng.");
  const [statusError, setStatusError] = useState(false);

  const [uploading, setUploading] = useState(false);
  const [asking, setAsking] = useState(false);
  const [creatingQuiz, setCreatingQuiz] = useState(false);
  const [creatingRoadmap, setCreatingRoadmap] = useState(false);
  const [creatingLevelQuiz, setCreatingLevelQuiz] = useState(false);
  const [creatingMindmap, setCreatingMindmap] = useState(false);

  const selectedDocument = useMemo(
    () => documents.find((doc) => doc.document_id === selectedDocumentId) || null,
    [documents, selectedDocumentId]
  );

  const activeJobs = useMemo(
    () => jobs.filter((job) => job.status === "queued" || job.status === "processing"),
    [jobs]
  );

  const roadmapLevelsList = useMemo(() => {
    const levels = Array.isArray(roadmap?.levels) ? roadmap.levels : [];
    return [...levels].sort((a, b) => Number(a.level || 0) - Number(b.level || 0));
  }, [roadmap]);

  const levelQuizPercent = useMemo(() => {
    if (!levelQuizSubmitted || !levelQuiz.length || !selectedLevel) return null;
    let correct = 0;
    levelQuiz.forEach((q, idx) => {
      const user = levelQuizAnswers[idx] || "";
      const ans = q.answer || "";
      if (user && (ans.includes(user) || user.includes(ans))) correct += 1;
    });
    return Math.round((correct / levelQuiz.length) * 100);
  }, [levelQuiz, levelQuizAnswers, levelQuizSubmitted, selectedLevel]);

  const setStatus = (text, isError = false) => {
    const now = new Date().toLocaleTimeString("vi-VN");
    setStatusText(`[${now}] ${text}`);
    setStatusError(isError);
  };

  const loadDocuments = async () => {
    const data = await callApi("/documents");
    const docs = data.documents || [];
    setDocuments(docs);

    if (!docs.some((doc) => doc.document_id === selectedDocumentId)) {
      setSelectedDocumentId("");
      setMessages([]);
      setQuiz([]);
      setQuizAnswers({});
      setQuizSubmitted(false);
    }

    setRoadmapDocIds((prev) => prev.filter((id) => docs.some((doc) => doc.document_id === id)));
    setMindmapDocIds((prev) => prev.filter((id) => docs.some((doc) => doc.document_id === id)));
  };

  const loadJobs = async () => {
    const data = await callApi("/jobs");
    setJobs((data.jobs || []).slice(0, 40));
  };

  useEffect(() => {
    Promise.all([loadDocuments(), loadJobs()]).catch((error) => setStatus(error.message, true));
  }, []);

  useEffect(() => {
    if (!statusError) return;

    const retryTimer = setInterval(() => {
      Promise.all([loadDocuments(), loadJobs()])
        .then(() => setStatus("Đã kết nối lại máy chủ."))
        .catch(() => undefined);
    }, 3000);

    return () => clearInterval(retryTimer);
  }, [statusError]);

  useEffect(() => {
    if (!activeJobs.length) return;
    const timer = setInterval(() => {
      loadJobs().catch(() => undefined);
      loadDocuments().catch(() => undefined);
    }, 2000);
    return () => clearInterval(timer);
  }, [activeJobs.length]);

  const handleMultiUpload = async (event) => {
    event.preventDefault();
    const files = Array.from(fileInputRef.current?.files || []);
    if (!files.length) {
      setStatus("Vui lòng chọn ít nhất một tệp PDF/PPTX.", true);
      return;
    }

    setUploading(true);
    try {
      for (const file of files) {
        const formData = new FormData();
        formData.append("file", file);
        await callApi("/upload", { method: "POST", body: formData }, 30000);
      }
      uploadFormRef.current?.reset();
      setStatus(`Đã gửi ${files.length} tệp vào hàng đợi xử lý nền.`);
      await loadJobs();
      await loadDocuments();
    } catch (error) {
      setStatus(error.message, true);
    } finally {
      setUploading(false);
    }
  };

  const isLevelUnlocked = (levelNumber) => {
    if (!roadmapLevelsList.length) return false;
    if (levelNumber === Number(roadmapLevelsList[0]?.level)) return true;

    const index = roadmapLevelsList.findIndex((level) => Number(level.level) === Number(levelNumber));
    if (index <= 0) return false;

    const prev = roadmapLevelsList[index - 1];
    const prevProgress = roadmapProgress[prev.level];
    return Boolean(prevProgress?.passed);
  };

  const openLevel = (level) => {
    if (!isLevelUnlocked(level.level)) {
      setStatus("Chặng này đang bị khóa. Bạn cần đạt tối thiểu 80% ở chặng trước.", true);
      return;
    }
    setSelectedLevel(level);
    setLevelQuiz([]);
    setLevelQuizAnswers({});
    setLevelQuizSubmitted(false);
  };

  const handleGenerateLevelQuiz = async () => {
    if (!selectedLevel) {
      setStatus("Bạn cần chọn một chặng để làm bài.", true);
      return;
    }
    if (!roadmapDocIds.length) {
      setStatus("Bạn cần chọn tài liệu nguồn cho lộ trình.", true);
      return;
    }

    setCreatingLevelQuiz(true);
    try {
      const topicText = `${roadmap?.goal || "Lộ trình học"} - ${selectedLevel.title} - ${selectedLevel.objective}`;
      const data = await callApi(
        "/generate-roadmap-quiz",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            topic: topicText,
            document_ids: roadmapDocIds,
            num_questions: 5,
          }),
        },
        45000
      );

      setLevelQuiz(Array.isArray(data.quiz) ? data.quiz : []);
      setLevelQuizAnswers({});
      setLevelQuizSubmitted(false);
      setStatus(`Đã tạo bài luyện cho chặng ${selectedLevel.level}.`);
    } catch (error) {
      setStatus(error.message, true);
    } finally {
      setCreatingLevelQuiz(false);
    }
  };

  const submitLevelQuiz = () => {
    if (!selectedLevel || !levelQuiz.length) return;
    setLevelQuizSubmitted(true);
  };

  useEffect(() => {
    if (!selectedLevel || levelQuizPercent == null) return;

    const passed = levelQuizPercent >= 80;
    setRoadmapProgress((prev) => ({
      ...prev,
      [selectedLevel.level]: {
        score: levelQuizPercent,
        passed,
        doneAt: new Date().toISOString(),
      },
    }));

    if (passed) {
      setStatus(`Bạn đạt ${levelQuizPercent}% ở chặng ${selectedLevel.level}. Chặng tiếp theo đã mở.`);
    } else {
      setStatus(`Bạn đạt ${levelQuizPercent}%. Cần tối thiểu 80% để mở chặng tiếp theo.`, true);
    }
  }, [levelQuizPercent, selectedLevel]);

  const handleDeleteDocument = async (documentId) => {
    const accepted = window.confirm("Xóa tài liệu này khỏi hệ thống và bộ nhớ RAG?");
    if (!accepted) return;

    try {
      await callApi(`/documents/${documentId}`, { method: "DELETE" });
      if (selectedDocumentId === documentId) {
        setSelectedDocumentId("");
        setMessages([]);
        setQuiz([]);
        setQuizAnswers({});
        setQuizSubmitted(false);
      }
      setRoadmapDocIds((prev) => prev.filter((id) => id !== documentId));
      await loadDocuments();
      setStatus("Đã xóa tài liệu thành công.");
    } catch (error) {
      setStatus(error.message, true);
    }
  };

  const handleAsk = async (event) => {
    event.preventDefault();
    if (!selectedDocumentId) {
      setStatus("Bạn cần chọn tài liệu trước khi chat.", true);
      return;
    }
    if (!question.trim()) return;

    const userMsg = { role: "user", content: ensureText(question), sources: [] };
    const nextHistory = [
      ...messages.map(({ role, content }) => ({ role, content: ensureText(content) })),
      { role: "user", content: ensureText(question) },
    ];
    setMessages((prev) => [...prev, userMsg]);
    setQuestion("");
    setAsking(true);

    try {
      const data = await callApi("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: userMsg.content, document_id: selectedDocumentId, history: nextHistory }),
      });

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: ensureText(data.answer, "Không có câu trả lời."), sources: data.sources || [] },
      ]);
    } catch (error) {
      const errorText = error instanceof Error ? error.message : "Đã xảy ra lỗi khi chat với máy chủ.";
      setMessages((prev) => [...prev, { role: "assistant", content: ensureText(errorText), sources: [] }]);
    } finally {
      setAsking(false);
    }
  };

  const handleCreateQuiz = async (event) => {
    event.preventDefault();
    if (!selectedDocumentId) {
      setStatus("Bạn cần chọn tài liệu trước khi tạo quiz.", true);
      return;
    }
    if (!topic.trim()) {
      setStatus("Vui lòng nhập chủ đề quiz.", true);
      return;
    }

    setCreatingQuiz(true);
    try {
      const data = await callApi("/generate-quiz", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic, num_questions: Number(numQuestions), document_id: selectedDocumentId }),
      });

      setQuiz(Array.isArray(data.quiz) ? data.quiz : []);
      setQuizAnswers({});
      setQuizSubmitted(false);
      setStatus("Đã tạo quiz thành công.");
    } catch (error) {
      setStatus(error.message, true);
    } finally {
      setCreatingQuiz(false);
    }
  };

  const handleCreateRoadmap = async (event) => {
    event.preventDefault();
    if (!roadmapGoal.trim()) {
      setStatus("Vui lòng nhập mục tiêu học tập.", true);
      return;
    }
    if (!roadmapDocIds.length) {
      setStatus("Bạn cần chọn ít nhất một tài liệu để tạo lộ trình.", true);
      return;
    }

    setCreatingRoadmap(true);
    try {
      const data = await callApi("/generate-learning-path", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          goal: roadmapGoal,
          document_ids: roadmapDocIds,
          level_count: Number(roadmapLevels),
        }),
      }, 45000);
      setRoadmap(data);
      setRoadmapProgress({});
      setSelectedLevel(null);
      setLevelQuiz([]);
      setLevelQuizAnswers({});
      setLevelQuizSubmitted(false);
      setStatus("Đã tạo lộ trình học tập theo nhiều tài liệu.");
    } catch (error) {
      setStatus(error.message, true);
    } finally {
      setCreatingRoadmap(false);
    }
  };

  const handleCreateMindmap = async (event) => {
    event.preventDefault();
    if (!mindmapTopic.trim()) {
      setStatus("Vui lòng nhập chủ đề mindmap.", true);
      return;
    }
    if (!mindmapDocIds.length) {
      setStatus("Bạn cần chọn ít nhất một tài liệu để tạo mindmap.", true);
      return;
    }

    setCreatingMindmap(true);
    try {
      const data = await callApi(
        "/generate-mindmap",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ topic: mindmapTopic, document_ids: mindmapDocIds }),
        },
        45000
      );
      setMindmap(data);
      setStatus("Đã tạo mindmap từ tài liệu đã xử lý.");
    } catch (error) {
      setStatus(error.message, true);
    } finally {
      setCreatingMindmap(false);
    }
  };

  const score = useMemo(() => {
    if (!quizSubmitted || !quiz.length) return null;
    let correct = 0;
    quiz.forEach((q, idx) => {
      const user = quizAnswers[idx] || "";
      const ans = q.answer || "";
      if (user && (ans.includes(user) || user.includes(ans))) correct += 1;
    });
    return `${correct}/${quiz.length}`;
  }, [quiz, quizAnswers, quizSubmitted]);

  return (
    <div className="page">
      <div className="bg-a" />
      <div className="bg-b" />

      <main className={`layout ${mindmapOnlyMode ? "mindmap-only" : ""}`}>
        {!mindmapOnlyMode && (
        <aside className="sidebar card">
          <div className="hero">
            <p className="eyebrow">AI EDU HUB</p>
            <h1>Trợ lý RAG học tập</h1>
            <p>Mọi truy vấn đều bám theo tài liệu bạn chọn. Không còn trả lời từ kho tài liệu lộn xộn.</p>
          </div>

          <section className="metrics">
            <article><span>Tài liệu</span><strong>{documents.length}</strong></article>
            <article><span>Job xử lý</span><strong>{activeJobs.length}</strong></article>
            <article><span>Đoạn chat</span><strong>{messages.length}</strong></article>
          </section>

          <section className="section">
            <div className="title-row">
              <h3>Kho tài liệu</h3>
              <button onClick={() => loadDocuments().catch((e) => setStatus(e.message, true))}>Làm mới</button>
            </div>
            <label>Tài liệu đang dùng</label>
            <select value={selectedDocumentId} onChange={(e) => {
              setSelectedDocumentId(e.target.value);
              setMessages([]);
              setQuiz([]);
              setQuizAnswers({});
              setQuizSubmitted(false);
            }}>
              <option value="">-- Chọn 1 tài liệu --</option>
              {documents.map((doc) => <option key={doc.document_id} value={doc.document_id}>{doc.source_name}</option>)}
            </select>

            <div className="docs-list">
              {documents.length === 0 && <p className="hint">Chưa có tài liệu nào.</p>}
              {documents.map((doc) => (
                <article key={doc.document_id} className="doc-card">
                  <strong>{doc.source_name}</strong>
                  <p>{formatTime(doc.uploaded_at)}</p>
                  <div className="doc-actions">
                    <button onClick={() => setSelectedDocumentId(doc.document_id)}>Chọn</button>
                    <button className="danger" onClick={() => handleDeleteDocument(doc.document_id)}>Xóa</button>
                  </div>
                </article>
              ))}
            </div>
          </section>

          <section className={`status ${statusError ? "error" : ""}`}>{statusText}</section>
        </aside>
        )}

        <section className={`content ${mindmapOnlyMode ? "mindmap-only-content" : ""}`}>
          <header className="card nav-card">
            <div className="ribbon">
              {mindmapOnlyMode
                ? "Mindmap Workspace • Không gian rộng để học bằng sơ đồ"
                : "Document-first RAG • React hiện đại • Lộ trình học theo chặng"}
            </div>
            <nav>
              {!mindmapOnlyMode && <button className={tab === "upload" ? "active" : ""} onClick={() => setTab("upload")}>Upload</button>}
              {!mindmapOnlyMode && <button className={tab === "chat" ? "active" : ""} onClick={() => setTab("chat")}>Chat</button>}
              {!mindmapOnlyMode && <button className={tab === "quiz" ? "active" : ""} onClick={() => setTab("quiz")}>Quiz</button>}
              {!mindmapOnlyMode && <button className={tab === "roadmap" ? "active" : ""} onClick={() => setTab("roadmap")}>Lộ trình</button>}
              {!mindmapOnlyMode && (
                <button
                  type="button"
                  onClick={() => { window.location.href = "/?view=mindmap"; }}
                >
                  Mindmap
                </button>
              )}
              {mindmapOnlyMode && <button className="active">Mindmap</button>}
              {mindmapOnlyMode && (
                <button type="button" onClick={() => { window.location.href = "/"; }}>
                  Quay về dashboard
                </button>
              )}
            </nav>
          </header>

          {tab === "upload" && (
            <section className="card panel">
              <p className="eyebrow">Module 1</p>
              <h2>Đăng tải và xử lý tài liệu</h2>
              <form ref={uploadFormRef} onSubmit={handleMultiUpload} className="upload-form">
                <label>Chọn nhiều tệp PDF/PPTX</label>
                <input ref={fileInputRef} name="files" type="file" accept=".pdf,.pptx" multiple required />
                <button className="primary" disabled={uploading}>{uploading ? "Đang gửi..." : "Tải lên nhiều tệp"}</button>
              </form>

              <div className="job-header">
                <h3>Hàng đợi xử lý</h3>
                <button onClick={() => loadJobs().catch((e) => setStatus(e.message, true))}>Làm mới</button>
              </div>

              <div className="job-list">
                {jobs.length === 0 && <p className="hint">Chưa có job xử lý nào.</p>}
                {jobs.map((job) => (
                  <article key={job.job_id} className="job-card">
                    <div className="job-line">
                      <strong>{job.source_name}</strong>
                      <span className={`pill ${job.status}`}>{job.status}</span>
                    </div>
                    <div className="progress-track"><div className="progress-fill" style={{ width: `${Math.max(0, Math.min(100, Number(job.progress || 0)))}%` }} /></div>
                    <small>{job.message}</small>
                  </article>
                ))}
              </div>
            </section>
          )}

          {tab === "chat" && (
            <section className="card panel">
              <p className="eyebrow">Module 2</p>
              <h2>Chat theo tài liệu đã chọn</h2>
              <p className="context">Ngữ cảnh hiện tại: {selectedDocument?.source_name || "Chưa chọn tài liệu"}</p>

              <div className="chat-box">
                {messages.length === 0 && <p className="hint">Chọn tài liệu và đặt câu hỏi để bắt đầu.</p>}
                {messages.map((msg, idx) => (
                  <article key={`${msg.role}-${idx}`} className={`message ${msg.role}`}>
                    <p>{msg.content}</p>
                    <SourceLine sources={msg.sources} />
                  </article>
                ))}
              </div>

              <form onSubmit={handleAsk} className="chat-form">
                <input value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Nhập câu hỏi theo tài liệu đã chọn..." />
                <button className="primary" disabled={asking}>{asking ? "Đang hỏi..." : "Gửi câu hỏi"}</button>
              </form>
            </section>
          )}

          {tab === "quiz" && (
            <section className="card panel">
              <p className="eyebrow">Module 3</p>
              <h2>Tạo quiz theo tài liệu đã chọn</h2>
              <p className="context">Ngữ cảnh hiện tại: {selectedDocument?.source_name || "Chưa chọn tài liệu"}</p>

              <form onSubmit={handleCreateQuiz} className="quiz-config">
                <div>
                  <label>Chủ đề quiz</label>
                  <input value={topic} onChange={(e) => setTopic(e.target.value)} placeholder="Ví dụ: Thuật toán KNN" />
                </div>
                <div>
                  <label>Số câu</label>
                  <input type="number" min={1} max={15} value={numQuestions} onChange={(e) => setNumQuestions(e.target.value)} />
                </div>
                <button className="secondary" disabled={creatingQuiz}>{creatingQuiz ? "Đang tạo..." : "Tạo quiz"}</button>
              </form>

              {score && <p className="score">Điểm của bạn: {score}</p>}

              <div className="quiz-list">
                {quiz.length === 0 && <p className="hint">Chưa có quiz. Hãy nhập chủ đề và bấm tạo quiz.</p>}
                {quiz.map((q, idx) => {
                  const selected = quizAnswers[idx] || "";
                  const answer = q.answer || "";
                  const isCorrect = selected && (answer.includes(selected) || selected.includes(answer));
                  return (
                    <article className="quiz-card" key={`q-${idx}`}>
                      <h4>Câu {idx + 1}: {q.question}</h4>
                      <div className="options">
                        {(q.options || []).map((option) => (
                          <label key={option}>
                            <input
                              type="radio"
                              name={`quiz-${idx}`}
                              value={option}
                              checked={selected === option}
                              onChange={(e) => setQuizAnswers((prev) => ({ ...prev, [idx]: e.target.value }))}
                              disabled={quizSubmitted}
                            />
                            <span>{option}</span>
                          </label>
                        ))}
                      </div>
                      {quizSubmitted && (
                        <p className={`feedback ${isCorrect ? "ok" : "bad"}`}>
                          {selected
                            ? isCorrect
                              ? `Đúng. ${q.explanation || ""}`
                              : `Sai. Đáp án đúng: ${q.answer}. ${q.explanation || ""}`
                            : `Bạn chưa trả lời. Đáp án đúng: ${q.answer}. ${q.explanation || ""}`}
                        </p>
                      )}
                    </article>
                  );
                })}
              </div>

              {quiz.length > 0 && !quizSubmitted && (
                <div className="quiz-actions">
                  <button className="primary" onClick={() => setQuizSubmitted(true)}>Nộp bài và chấm điểm</button>
                </div>
              )}
            </section>
          )}

          {tab === "roadmap" && (
            <section className="card panel">
              <p className="eyebrow">Module 4</p>
              <h2>Lộ trình học tập theo nhiều tài liệu</h2>
              <p className="context">Chọn nhiều tài liệu để AI tạo các chặng học tăng dần độ khó, có mở khóa theo kết quả luyện tập.</p>

              <form onSubmit={handleCreateRoadmap} className="roadmap-config">
                <div>
                  <label>Mục tiêu học tập</label>
                  <input value={roadmapGoal} onChange={(e) => setRoadmapGoal(e.target.value)} placeholder="Ví dụ: Thành thạo Kafka từ cơ bản đến triển khai production" />
                </div>
                <div>
                  <label>Số chặng</label>
                  <input type="number" min={3} max={12} value={roadmapLevels} onChange={(e) => setRoadmapLevels(e.target.value)} />
                </div>
                <button className="secondary" disabled={creatingRoadmap}>{creatingRoadmap ? "Đang tạo..." : "Tạo lộ trình"}</button>

                <div className="multi-doc-picker">
                  <label>Chọn nhiều tài liệu</label>
                  <div className="multi-doc-grid">
                    {documents.map((doc) => {
                      const checked = roadmapDocIds.includes(doc.document_id);
                      return (
                        <label key={doc.document_id} className="multi-doc-item">
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setRoadmapDocIds((prev) => [...new Set([...prev, doc.document_id])]);
                              } else {
                                setRoadmapDocIds((prev) => prev.filter((id) => id !== doc.document_id));
                              }
                            }}
                          />
                          <span>{doc.source_name}</span>
                        </label>
                      );
                    })}
                  </div>
                </div>
              </form>

              <div className="roadmap-output">
                {!roadmap && <p className="hint">Chưa có lộ trình. Chọn tài liệu và nhập mục tiêu để bắt đầu.</p>}
                {roadmap && (
                  <>
                    <h3>{roadmap.goal || "Lộ trình học tập"}</h3>
                    <p>{roadmap.overview || ""}</p>
                    <div className="duo-path">
                      {roadmapLevelsList.map((level, index) => {
                        const unlocked = isLevelUnlocked(level.level);
                        const progress = roadmapProgress[level.level];
                        const passed = Boolean(progress?.passed);
                        const current = selectedLevel?.level === level.level;
                        const stateClass = passed ? "passed" : current ? "current" : unlocked ? "open" : "locked";

                        return (
                          <div key={`node-${level.level}`} className={`duo-node-row ${index % 2 ? "right" : "left"}`}>
                            <button
                              type="button"
                              className={`duo-node ${stateClass}`}
                              disabled={!unlocked}
                              onClick={() => openLevel(level)}
                              title={unlocked ? `Chặng ${level.level}: ${level.title}` : "Bị khóa"}
                            >
                              <span>{level.level}</span>
                            </button>
                            <div className="duo-label">
                              <strong>{level.title}</strong>
                              <small>
                                {passed
                                  ? `Đã qua (${progress.score}%)`
                                  : unlocked
                                    ? "Sẵn sàng làm bài"
                                    : "Khóa: cần >= 80% chặng trước"}
                              </small>
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    {selectedLevel && (
                      <div className="level-workspace">
                        <article className="level-card">
                          <p className="level-tag">Chặng {selectedLevel.level}</p>
                          <h4>{selectedLevel.title}</h4>
                          <p><strong>Mục tiêu:</strong> {selectedLevel.objective}</p>
                          <ul>
                            {(selectedLevel.lessons || []).map((lesson) => <li key={lesson}>{lesson}</li>)}
                          </ul>
                          <p><strong>Bài luyện:</strong> {selectedLevel.practice}</p>
                          <p><strong>Qua chặng khi:</strong> {selectedLevel.pass_criteria}</p>
                          <div className="level-actions">
                            <button className="secondary" onClick={handleGenerateLevelQuiz} disabled={creatingLevelQuiz}>
                              {creatingLevelQuiz ? "Đang tạo bài..." : "Tạo bài luyện chặng này"}
                            </button>
                          </div>
                        </article>

                        <div className="quiz-list">
                          {levelQuiz.length === 0 && <p className="hint">Bấm tạo bài luyện để bắt đầu chặng.</p>}
                          {levelQuiz.length > 0 && (
                            <>
                              {levelQuiz.map((q, idx) => {
                                const selected = levelQuizAnswers[idx] || "";
                                const answer = q.answer || "";
                                const isCorrect = selected && (answer.includes(selected) || selected.includes(answer));
                                return (
                                  <article className="quiz-card" key={`rq-${idx}`}>
                                    <h4>Câu {idx + 1}: {q.question}</h4>
                                    <div className="options">
                                      {(q.options || []).map((option) => (
                                        <label key={option}>
                                          <input
                                            type="radio"
                                            name={`roadmap-quiz-${idx}`}
                                            value={option}
                                            checked={selected === option}
                                            onChange={(e) => setLevelQuizAnswers((prev) => ({ ...prev, [idx]: e.target.value }))}
                                            disabled={levelQuizSubmitted}
                                          />
                                          <span>{option}</span>
                                        </label>
                                      ))}
                                    </div>
                                    {levelQuizSubmitted && (
                                      <p className={`feedback ${isCorrect ? "ok" : "bad"}`}>
                                        {selected
                                          ? isCorrect
                                            ? `Đúng. ${q.explanation || ""}`
                                            : `Sai. Đáp án đúng: ${q.answer}. ${q.explanation || ""}`
                                          : `Bạn chưa trả lời. Đáp án đúng: ${q.answer}. ${q.explanation || ""}`}
                                      </p>
                                    )}
                                  </article>
                                );
                              })}
                              {!levelQuizSubmitted && (
                                <div className="quiz-actions">
                                  <button type="button" className="primary" onClick={submitLevelQuiz}>Nộp bài chặng</button>
                                </div>
                              )}
                              {levelQuizSubmitted && levelQuizPercent != null && (
                                <p className={`score ${levelQuizPercent >= 80 ? "pass" : "fail"}`}>
                                  Kết quả chặng: {levelQuizPercent}% {levelQuizPercent >= 80 ? "- Đã mở khóa chặng tiếp theo" : "- Chưa đạt 80%, hãy thử lại"}
                                </p>
                              )}
                            </>
                          )}
                        </div>
                      </div>
                    )}

                    {roadmap.capstone && <p className="capstone"><strong>Capstone:</strong> {roadmap.capstone}</p>}
                  </>
                )}
              </div>
            </section>
          )}

          {tab === "mindmap" && (
            <section className={`card panel ${mindmapOnlyMode ? "mindmap-wide" : ""}`}>
              <p className="eyebrow">Module 5</p>
              <h2>Mindmap từ tài liệu đã xử lý</h2>
              <p className="context">Chọn nhiều tài liệu, nhập chủ đề, hệ thống sẽ tạo mindmap tổng hợp để học nhanh.</p>

              <form onSubmit={handleCreateMindmap} className="roadmap-config">
                <div>
                  <label>Chủ đề mindmap</label>
                  <input
                    value={mindmapTopic}
                    onChange={(e) => setMindmapTopic(e.target.value)}
                    placeholder="Ví dụ: Kiến trúc microservices và triển khai thực tế"
                  />
                </div>
                <div>
                  <label>Số tài liệu đã chọn</label>
                  <input value={mindmapDocIds.length} readOnly />
                </div>
                <button className="secondary" disabled={creatingMindmap}>{creatingMindmap ? "Đang tạo..." : "Tạo mindmap"}</button>

                <div className="multi-doc-picker">
                  <label>Chọn tài liệu cho mindmap</label>
                  <div className="multi-doc-grid">
                    {documents.map((doc) => {
                      const checked = mindmapDocIds.includes(doc.document_id);
                      return (
                        <label key={`mind-${doc.document_id}`} className="multi-doc-item">
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setMindmapDocIds((prev) => [...new Set([...prev, doc.document_id])]);
                              } else {
                                setMindmapDocIds((prev) => prev.filter((id) => id !== doc.document_id));
                              }
                            }}
                          />
                          <span>{doc.source_name}</span>
                        </label>
                      );
                    })}
                  </div>
                </div>
              </form>

              <div className="mindmap-output">
                {!mindmap && <p className="hint">Chưa có mindmap. Hãy nhập chủ đề và chọn tài liệu.</p>}
                {mindmap && (
                  <>
                    <h3>{mindmap.topic || "Mindmap"}</h3>
                    <p>{mindmap.summary || ""}</p>
                    <MindmapDiagram mindmap={mindmap} />
                  </>
                )}
              </div>
            </section>
          )}
        </section>
      </main>
    </div>
  );
}
