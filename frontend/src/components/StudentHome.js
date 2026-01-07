import { useState, useEffect } from "react";
import "./StudentHome.css";

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
        console.error("Failed to load data", err);
      }
    }
    fetchData();
  }, []);

  // 2. Fetch Documents when a Classroom is selected in Smart Learning
  useEffect(() => {
    async function fetchDocs() {
      if (!learningData.classroom_id) {
        setClassroomDocs([]);
        return;
      }
      try {
        const token = localStorage.getItem("token");
        const res = await fetch(`http://localhost:8000/classrooms/${learningData.classroom_id}/documents`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          setClassroomDocs(await res.json());
        }
      } catch (err) {
        console.error("Failed to load documents", err);
      }
    }
    fetchDocs();
  }, [learningData.classroom_id]);

  // 3. Handle Join Classroom
  async function handleJoin() {
    if (!selectedClassId) return alert("Please select a classroom first.");
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`http://localhost:8000/classrooms/${selectedClassId}/join`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        alert("Successfully joined!");
        window.location.reload();
      } else {
        alert("Failed to join.");
      }
    } catch (err) {
      alert("Error joining classroom.");
    }
  }

  // 4. Handle Smart Learning Submission
  async function handleSmartLearning() {
    setLoading(true);
    setGeneratedContent(null);
    const token = localStorage.getItem("token");
    const headers = { 
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}` 
    };

    try {
      let url = "";
      let body = {};

      if (mode === "chat") {
        // --- CHAT / GENERATE LESSON MODE ---
        if (!learningData.topic || !learningData.question) {
            setLoading(false);
            return alert("Please provide a topic and question.");
        }
        url = "http://localhost:8000/chat/generate_lesson";
        body = {
          student_name: user.full_name,
          student_grade: learningData.grade,
          student_interest: learningData.interest,
          topic: learningData.topic,
          question: learningData.question,
          classroom_id: parseInt(learningData.classroom_id),
        };
      } else {
        // --- PERSONALIZE DOCUMENT MODE ---
        if (!learningData.document_id) {
            setLoading(false);
            return alert("Please select a document to personalize.");
        }
        url = `http://localhost:8000/documents/${learningData.document_id}/personalize`;
        body = {
          student_name: user.full_name,
          student_grade: learningData.grade,
          student_interest: learningData.interest
        };
      }

      const res = await fetch(url, {
        method: "POST",
        headers: headers,
        body: JSON.stringify(body),
      });

      if (res.ok) {
        const data = await res.json();
        setGeneratedContent(data); // Expecting { topic, content }
      } else {
        const err = await res.json();
        alert(`Error: ${err.detail}`);
      }
    } catch (error) {
      console.error(error);
      alert("An error occurred.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="home-wrapper">
      <h2>Welcome, {user.full_name}</h2>

      <div className="home-grid">
        {/* Card 1: Join Classrooms */}
        <div className="home-card student">
          <h4>📚 Join Classrooms</h4>
          <div style={{ marginTop: "1rem" }}>
            <select 
              value={selectedClassId} 
              onChange={(e) => setSelectedClassId(e.target.value)}
              style={{ padding: "8px", width: "100%", marginBottom: "8px" }}
            >
              <option value="">-- Select a Classroom --</option>
              {availableClassrooms.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
            <button onClick={handleJoin} className="btn-primary" style={{ width: "100%" }}>
              Join
            </button>
          </div>
        </div>

        {/* Card 2: Smart Learning (Dual Mode) */}
        <div className="home-card student" style={{ gridRow: "span 2" }}>
          <h4>🧠 Smart Learning</h4>
          <p>Personalized content based on your interests.</p>

          {/* Mode Switcher */}
          <div style={{ display: "flex", gap: "10px", margin: "10px 0" }}>
            <button 
                onClick={() => setMode("chat")}
                className={mode === "chat" ? "btn-primary" : "btn-secondary"}
                style={{ flex: 1, fontSize: "0.8rem" }}
            >
                Ask Question
            </button>
            <button 
                onClick={() => setMode("document")}
                className={mode === "document" ? "btn-primary" : "btn-secondary"}
                style={{ flex: 1, fontSize: "0.8rem" }}
            >
                Rewrite Document
            </button>
          </div>

          <div className="form-group" style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            
            {/* Common Fields */}
            <select
              value={learningData.classroom_id}
              onChange={(e) => setLearningData({...learningData, classroom_id: e.target.value})}
              style={{ padding: "8px", borderRadius: "4px" }}
            >
              <option value="">-- Select Your Class --</option>
              {enrolledClassrooms.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>

            <div style={{ display: "flex", gap: "5px" }}>
                <input 
                  type="text" placeholder="Grade (e.g. 5th)" 
                  value={learningData.grade}
                  onChange={(e) => setLearningData({...learningData, grade: e.target.value})}
                  style={{ flex: 1, padding: "8px" }}
                />
                <input 
                  type="text" placeholder="Interest (e.g. Lego)" 
                  value={learningData.interest}
                  onChange={(e) => setLearningData({...learningData, interest: e.target.value})}
                  style={{ flex: 1, padding: "8px" }}
                />
            </div>

            {/* Mode Specific Fields */}
            {mode === "chat" ? (
                <>
                    <input 
                      type="text" placeholder="Topic" 
                      value={learningData.topic}
                      onChange={(e) => setLearningData({...learningData, topic: e.target.value})}
                      style={{ padding: "8px" }}
                    />
                    <textarea 
                      placeholder="What is your question?" 
                      value={learningData.question}
                      onChange={(e) => setLearningData({...learningData, question: e.target.value})}
                      style={{ padding: "8px", minHeight: "60px" }}
                    />
                </>
            ) : (
                <>
                    <select
                        value={learningData.document_id}
                        onChange={(e) => setLearningData({...learningData, document_id: e.target.value})}
                        style={{ padding: "8px", borderRadius: "4px" }}
                        disabled={!learningData.classroom_id}
                    >
                        <option value="">
                            {learningData.classroom_id ? "-- Select Document --" : "-- Select Class First --"}
                        </option>
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
    </div>
  );
}