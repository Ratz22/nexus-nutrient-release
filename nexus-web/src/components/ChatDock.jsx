import { useState } from "react";

// Placeholder for the assistant. Send stays disabled until the chat endpoint exists,
// so nobody thinks it works when it doesn't.
export default function ChatDock() {
  const [open, setOpen] = useState(false);
  const [text, setText] = useState("");

  if (!open) {
    return (
      <button className="ask-btn" onClick={() => setOpen(true)}>Ask NEXUS</button>
    );
  }
  return (
    <div className="chat">
      <div className="chat-head">
        <strong>NEXUS</strong>
        <button className="link-btn" onClick={() => setOpen(false)}>Close</button>
      </div>
      <div className="chat-body">
        <p>I can help you run a prediction, read a result, or find a page. The assistant comes online once the backend is connected.</p>
      </div>
      <div className="chat-input">
        <input value={text} onChange={(e) => setText(e.target.value)} placeholder="Ask about your runs" disabled />
        <button disabled>Send</button>
      </div>
    </div>
  );
}