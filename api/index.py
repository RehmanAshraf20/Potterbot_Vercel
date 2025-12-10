from flask import Flask, request, jsonify
from google import genai
import os

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY environment variable is not set.")

client = genai.Client(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-2.5-flash"
SYSTEM_INSTRUCTION = """You are "PotterPal," a friendly, expert chatbot dedicated ONLY to the Harry Potter MOVIE series (the 8 Warner Bros. films).

Scope / Allowed content:
- You may answer questions about: plot, characters, spells, creatures, objects, locations, timelines, themes, dialogue moments, actors, directors, soundtracks, behind-the-scenes facts, and differences BETWEEN the movies.
- Treat the MOVIES as the single source of truth. When helpful, specify which movie a detail comes from.
- You may discuss real-world film production info (casting, release order, filmmaking choices) as long as it directly relates to the Harry Potter films.

Strict Restrictions:
- Do NOT answer questions that rely on or primarily reference the books, video games, stage play ("Cursed Child"), Fantastic Beasts films, theme parks, fanfiction, or any non-movie canon.
- If the user asks about something outside the 8 Harry Potter movies, you must refuse politely and steer back to movie-only topics.

Refusal behavior:
- Be warm and respectful.
- Briefly say you're limited to the Harry Potter movie series.
- Offer to answer a related movie-franchise question instead.
- Do not provide any part of the out-of-scope answer.

Answer style:
- Be friendly, enthusiastic, and welcoming.
- Answer every in-scope question in clear detail.
- Use headings or bullet points when it improves readability.
- If the question is ambiguous, make a reasonable assumption based on the films and say what you assumed.
- If you're unsure about a movie detail, say so honestly rather than inventing.

Conversation steering:
- Always try to keep the conversation centered on the movies.
- End most answers with a short, relevant follow-up question (e.g., "Want the scene breakdown from the film?") unless the user clearly wants to stop.

Example refusal:
User: "What happens in Chapter 12 of the book?"
Assistant: "I'm sorry — I'm limited to the Harry Potter movies only, so I can't help with book-specific chapters. If you want, ask me about the corresponding moment in the films and I'll gladly dive in!"

"""

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Gemini Chatbot</title>
    <link rel="icon" href="data:,">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
      body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; }
    </style>
  </head>
  <body class="bg-slate-100">
    <div class="min-h-screen flex items-center justify-center p-4">
      <div class="w-full max-w-3xl bg-white rounded-2xl shadow-lg overflow-hidden flex flex-col">
        <div class="px-6 py-4 border-b bg-slate-50">
          <h1 class="text-xl font-semibold text-slate-800">Gemini Chatbot</h1>
          <p class="text-sm text-slate-500">Flask + Gemini API + Tailwind</p>
        </div>
        <div id="chatArea" class="flex-1 p-6 space-y-4 overflow-y-auto bg-white" style="height: 60vh;">
          <div class="flex items-start gap-2">
            <div class="w-8 h-8 rounded-full bg-indigo-600 text-white flex items-center justify-center text-sm font-bold">G</div>
            <div class="bg-slate-100 rounded-2xl px-4 py-2 max-w-[80%]">
              <p class="text-slate-800 text-sm">Hey! I'm your PotterPal. Ask me anything Muggle! 😊</p>
            </div>
          </div>
        </div>
        <div class="p-4 border-t bg-slate-50">
          <form id="chatForm" class="flex gap-2">
            <input id="userInput" type="text" placeholder="Type your message..." class="flex-1 rounded-xl border border-slate-300 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" autocomplete="off" />
            <button type="submit" class="rounded-xl bg-indigo-600 text-white px-5 py-3 text-sm font-medium hover:bg-indigo-700 active:scale-[0.98] transition">Send</button>
          </form>
          <p class="text-xs text-slate-500 mt-2">Press Enter to send.</p>
        </div>
      </div>
    </div>
    <script>
      const chatForm = document.getElementById("chatForm");
      const userInput = document.getElementById("userInput");
      const chatArea = document.getElementById("chatArea");
      let history = [];
      function scrollToBottom() { chatArea.scrollTop = chatArea.scrollHeight; }
      function escapeHtml(str) {
        return str.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;");
      }
      function addMessage(role, text) {
        const wrapper = document.createElement("div");
        if (role === "user") {
          wrapper.className = "flex items-start gap-2 justify-end";
          wrapper.innerHTML = '<div class="bg-indigo-600 text-white rounded-2xl px-4 py-2 max-w-[80%] whitespace-pre-wrap"><p class="text-sm">' + escapeHtml(text) + '</p></div><div class="w-8 h-8 rounded-full bg-slate-300 text-slate-700 flex items-center justify-center text-sm font-bold">U</div>';
        } else {
          wrapper.className = "flex items-start gap-2";
          wrapper.innerHTML = '<div class="w-8 h-8 rounded-full bg-indigo-600 text-white flex items-center justify-center text-sm font-bold">G</div><div class="bg-slate-100 rounded-2xl px-4 py-2 max-w-[80%] whitespace-pre-wrap"><p class="text-slate-800 text-sm">' + escapeHtml(text) + '</p></div>';
        }
        chatArea.appendChild(wrapper);
        scrollToBottom();
      }
      function addTypingBubble() {
        const wrapper = document.createElement("div");
        wrapper.className = "flex items-start gap-2";
        wrapper.innerHTML = '<div class="w-8 h-8 rounded-full bg-indigo-600 text-white flex items-center justify-center text-sm font-bold">G</div><div class="bg-slate-100 rounded-2xl px-4 py-2 max-w-[80%]"><p class="text-slate-500 text-sm italic">Typing...</p></div>';
        chatArea.appendChild(wrapper);
        scrollToBottom();
        return () => wrapper.remove();
      }
      async function sendToBackend(message) {
        const res = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message, history }),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.error || "Request failed");
        }
        return res.json();
      }
      chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const message = userInput.value.trim();
        if (!message) return;
        userInput.value = "";
        userInput.focus();
        addMessage("user", message);
        history.push({ role: "user", text: message });
        const removeTyping = addTypingBubble();
        userInput.disabled = true;
        try {
          const data = await sendToBackend(message);
          const reply = data.reply || "(no reply)";
          removeTyping();
          addMessage("model", reply);
          history.push({ role: "model", text: reply });
        } catch (err) {
          removeTyping();
          addMessage("model", "⚠️ Error:\\n" + err.message);
        } finally {
          userInput.disabled = false;
          userInput.focus();
        }
      });
    </script>
  </body>
</html>"""

@app.route("/")
def home():
    return HTML_CONTENT

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    user_message = (data.get("message") or "").strip()
    history = data.get("history") or []

    if not user_message:
        return jsonify({"error": "message is required"}), 400

    contents = []
    for turn in history:
        role = turn.get("role", "user")
        text = turn.get("text", "")
        if text:
            contents.append({"role": role, "parts": [{"text": text}]})

    contents.append({"role": "user", "parts": [{"text": user_message}]})

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config={
                "system_instruction": SYSTEM_INSTRUCTION,
                "temperature": 0.7,
                "max_output_tokens": 512,
            },
        )

        return jsonify({"reply": response.text or ""})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health")
def health():
    return jsonify({"ok": True})