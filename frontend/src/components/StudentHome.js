import { useState, useEffect } from "react";
import "./StudentHome.css";
import VideoGenerator from "./VideoGenerator"; // <--- Import here

export default function StudentHome({ user }) {
  const [availableClassrooms, setAvailableClassrooms] = useState([]);
  const [enrolledClassrooms, setEnrolledClassrooms] = useState([]);
  const [selectedClassId, setSelectedClassId] = useState("");

  // Smart Learning State
  const [mode, setMode] = useState("chat"); // 'chat' or 'document'
  const [classroomDocs, setClassroomDocs] = useState([]);
  
  const [learningData, setLearningData] = useState({
    classroom_id: "",
    document_id: "",
    grade: "",
    interest: "",
    topic: "",
    question: ""
  });

  const [generatedContent, setGeneratedContent] = useState(null);
  const [loading, setLoading] = useState(false);

  // 1. Fetch Classrooms on Load
  useEffect(() => {
    async function fetchData() {
      try {
        const token = localStorage.getItem("token");
        const headers = { Authorization: `Bearer ${token}` };

        // Fetch Available (for joining)
        const resAvail = await fetch("http://localhost:8000/classrooms/available", { headers });
        if (resAvail.ok) setAvailableClassrooms(await resAvail.json());

        // Fetch Enrolled (for learning)
        const resEnrolled = await fetch("http://localhost:8000/classrooms/enrolled", { headers });
        if (resEnrolled.ok) setEnrolledClassrooms(await resEnrolled.json());

      } catch (err) {
        console.error("Failed to load student data", err);
      }
    }
    fetchData();
  }, []);

  // 2. Fetch Documents when Classroom is Selected
  useEffect(() => {
    if (learningData.classroom_id) {
        const token = localStorage.getItem("token");
        fetch(`http://localhost:8000/classrooms/${learningData.classroom_id}/documents`, {
            headers: { Authorization: `Bearer ${token}` }
        })
        .then(res => res.json())
        .then(data => setClassroomDocs(data))
        .catch(err => console.error(err));
    }
  }, [learningData.classroom_id]);


  // 3. Handle Joining
  async function handleJoin() {
    if (!selectedClassId) return;
    const token = localStorage.getItem("token");
    try {
      const res = await fetch(`http://localhost:8000/classrooms/${selectedClassId}/join`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        alert("Joined Successfully!");
        window.location.reload(); // Simple refresh to update lists
      } else {
        alert("Failed to join");
      }
    } catch (err) {
      alert(err.message);
    }
  }

  // 4. Handle Smart Learning Request
  async function handleSmartLearning() {
    setLoading(true);
    setGeneratedContent(null);
    const token = localStorage.getItem("token");

    try {
        let endpoint = "";
        let body = {};

        if (mode === "chat") {
            endpoint = "http://localhost:8000/chat/generate_lesson";
            body = {
                student_name: user.full_name,
                student_grade: learningData.grade,
                student_interest: learningData.interest,
                topic: learningData.topic,
                question: learningData.question,
                classroom_id: learningData.classroom_id
            };
        } else {
            // Document Mode
            if (!learningData.document_id) {
                alert("Please select a document");
                setLoading(false);
                return;
            }
            endpoint = `http://localhost:8000/documents/${learningData.document_id}/personalize`;
            body = {
                student_name: user.full_name,
                student_grade: learningData.grade,
                student_interest: learningData.interest
            };
        }

        const res = await fetch(endpoint, {
            method: "POST",
            headers: { 
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`
            },
            body: JSON.stringify(body)
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Generation failed");
        }

        const data = await res.json();
        setGeneratedContent(data);

    } catch (error) {
        alert(error.message);
    } finally {
        setLoading(false);
    }
  }

  return (
    <div className="home-wrapper">
      <div className="home-header">
        <h2>Welcome, {user.full_name}</h2>
        <p className="home-subtitle">Join classrooms and access personalized learning.</p>
      </div>

      <div className="home-grid">
        {/* Card 1: Join Class */}
        <div className="home-card student">
          <h4>🏫 Join a Classroom</h4>
          <div className="join-section">
            <select 
              className="full-width"
              onChange={(e) => setSelectedClassId(e.target.value)}
              value={selectedClassId}
            >
              <option value="">-- Select Classroom --</option>
              {availableClassrooms.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
            <button className="btn-primary" onClick={handleJoin}>Join</button>
          </div>
          <p>Enrolled: {enrolledClassrooms.length} classes</p>
        </div>

        {/* Card 2: AI Smart Learning */}
        <div className="home-card student large-card">
          <h4>🧠 AI Smart Learning</h4>
          
          <div className="tabs" style={{marginBottom: "15px", borderBottom: "1px solid #eee"}}>
            <button 
                className={`tab-btn ${mode === "chat" ? "active" : ""}`} 
                onClick={() => setMode("chat")}
            >
                Ask a Question
            </button>
            <button 
                className={`tab-btn ${mode === "document" ? "active" : ""}`} 
                onClick={() => setMode("document")}
            >
                Personalize Document
            </button>
          </div>

          <div className="chat-form">
            <div className="form-row">
              <input 
                placeholder="Your Grade (e.g. 10th)" 
                value={learningData.grade}
                onChange={(e) => setLearningData({...learningData, grade: e.target.value})}
              />
              <input 
                placeholder="Your Interest (e.g. Football)" 
                value={learningData.interest}
                onChange={(e) => setLearningData({...learningData, interest: e.target.value})}
              />
            </div>
            
            {/* Classroom Select is common for context */}
            <select 
                className="full-width"
                value={learningData.classroom_id}
                onChange={(e) => setLearningData({...learningData, classroom_id: e.target.value})}
            >
                <option value="">-- Select Context Classroom --</option>
                {enrolledClassrooms.map(c => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                ))}
            </select>

            {mode === "chat" ? (
                <>
                    <input 
                        placeholder="Topic (e.g. Thermodynamics)" 
                        className="full-width"
                        value={learningData.topic}
                        onChange={(e) => setLearningData({...learningData, topic: e.target.value})}
                    />
                    <textarea 
                        placeholder="What is your question?" 
                        rows="3"
                        value={learningData.question}
                        onChange={(e) => setLearningData({...learningData, question: e.target.value})}
                    />
                </>
            ) : (
                <>
                    <select 
                        className="full-width"
                        value={learningData.document_id}
                        onChange={(e) => setLearningData({...learningData, document_id: e.target.value})}
                    >
                        <option value="">-- Select Document to Rewrite --</option>
                        {classroomDocs.map((d) => (
                            <option key={d.id} value={d.id}>{d.filename}</option>
                        ))}
                    </select>
                    <p style={{fontSize: "0.8rem", color: "#666", margin: 0}}>
                        This will rewrite the entire document using analogies from your interest.
                    </p>
                </>
            )}

            <button 
              onClick={handleSmartLearning} 
              className="btn-primary"
              disabled={loading}
            >
              {loading ? "Generating..." : (mode === "chat" ? "Teach Me" : "Personalize It")}
            </button>
          </div>

          {/* Results Area */}
          {generatedContent && (
            <div style={{ marginTop: "1rem", background: "#f9f9f9", padding: "10px", borderRadius: "5px", textAlign: "left" }}>
              <h5>{generatedContent.topic}</h5>
              <div style={{ whiteSpace: "pre-wrap", fontSize: "0.9rem", maxHeight: "300px", overflowY: "auto" }}>
                {generatedContent.content}
              </div>
            </div>
          )}
        </div>

        {/* Card 3: Assessments */}
        <div className="home-card student">
          <h4>📝 Assessments</h4>
          <p>Test your knowledge dynamically.</p>
          <button className="btn-secondary" style={{ width: "100%", marginTop: "10px" }}>Coming Soon</button>
        </div>
      </div>

      {/* --- NEW SECTION: Video Generator --- */}
      <div className="section-container">
         <VideoGenerator />
      </div>

    </div>
  );
}