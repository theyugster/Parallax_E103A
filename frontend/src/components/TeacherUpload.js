import { useRef, useState } from "react";
import "./TeacherUpload.css";

export default function TeacherUpload() {
  const fileInputRef = useRef(null);
  const [file, setFile] = useState(null);

  function openFilePicker() {
    fileInputRef.current.click();
  }

  function handleFileChange(e) {
    setFile(e.target.files[0]);
  }

  function handleSubmit(e) {
    e.preventDefault();

    if (!file) {
      alert("Please select a document first");
      return;
    }

    alert(`Document "${file.name}" ready for upload`);
  }

  return (
    <div className="upload-wrapper">
      <h2>Upload Learning Material</h2>
      <p className="upload-subtitle">
        Upload notes, PDFs, or text files to generate learning vectors
      </p>

      <form onSubmit={handleSubmit} className="upload-card">
        {/* Hidden File Input */}
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          hidden
        />

        {/* Upload Zone */}
        <div className="upload-zone" onClick={openFilePicker}>
          <div className="upload-content">
            <span className="upload-icon">📄</span>
            <p>{file ? file.name : "Click to select a document"}</p>
            <small>Supported: PDF, TXT, DOCX</small>
          </div>
        </div>

        {/* Upload Button */}
        <button
          type="submit"
          className="btn-primary upload-btn"
        >
          Upload Document
        </button>
      </form>
    </div>
  );
}
