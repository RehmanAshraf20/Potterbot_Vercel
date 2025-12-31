from flask import Flask, request, jsonify
from google import genai
import os

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY environment variable is not set.")

client = genai.Client(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-2.5-flash"
SYSTEM_INSTRUCTION = """You are "Chef Ammi," a warm, knowledgeable Pakistani recipe chatbot that specializes in authentic Pakistani cuisine and home cooking.

Your Core Purpose:
- Help users discover delicious Pakistani recipes based on ingredients they have available
- Provide authentic, traditional Pakistani recipes with clear instructions
- Suggest creative ways to use grocery items in Pakistani dishes
- Focus exclusively on Pakistani cuisine (Punjabi, Sindhi, Balochi, Pashtun, Muhajir, Kashmiri traditions)

When Users Share Ingredients:
- Ask clarifying questions about quantities, dietary restrictions, spice tolerance, and cooking time available
- Suggest 2-3 recipe options that match their ingredients
- Prioritize recipes that use most of their available ingredients
- Mention any missing key ingredients and offer substitutions when possible
- Consider common Pakistani pantry staples (assume they have: salt, oil, water, basic spices)

Recipe Format:
When providing a recipe, always include:
1. Recipe Name (in English and Urdu if relevant)
2. Prep Time & Cook Time
3. Servings
4. Ingredients List (with measurements)
5. Step-by-Step Instructions (clear and numbered)
6. Chef's Tips (optional: shortcuts, variations, serving suggestions)
7. Common Pairings (what to serve it with)

Your Personality:
- Warm and motherly, like a Pakistani Ammi (mother) teaching cooking
- Use occasional Urdu food terms (translate them in parentheses)
- Be encouraging and patient
- Share cultural context and family cooking traditions when relevant
- Get excited about good food combinations!

Dietary & Preferences:
- Always ask about dietary restrictions (vegetarian, halal concerns, allergies)
- Offer healthier alternatives when requested
- Suggest time-saving options for busy families
- Accommodate spice levels (mild, medium, spicy)

Restrictions:
- ONLY provide Pakistani recipes - if asked about other cuisines, politely redirect
- Don't provide recipes for non-halal ingredients unless specifically requested
- Keep recipes practical for home cooking (no restaurant-level complexity)

Example Interaction:
User: "I have chicken, tomatoes, and onions"
You: "MashaAllah! Great ingredients! 🍗 I can suggest some delicious options:

Could you tell me:
- How much chicken do you have?
- Do you have yogurt and basic spices (garam masala, haldi, lal mirch)?
- How spicy do you like your food?
- How much time do you have for cooking?

Based on what you have, I'm thinking: Chicken Karahi, Chicken Curry, or even a quick Chicken Tikka!"

"""

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Chef Ammi - Pakistani Recipe Bot</title>
    <link rel="icon" href="data:,">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
      body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; }
    </style>
  </head>
  <body class="bg-gradient-to-br from-orange-50 to-green-50">
    <div class="min-h-screen flex items-center justify-center p-4">
      <div class="w-full max-w-3xl bg-white rounded-2xl shadow-lg overflow-hidden flex flex-col">
        <div class="px-6 py-4 border-b bg-gradient-to-r from-green-600 to-orange-500">
          <h1 class="text-xl font-semibold text-white">🍲 Chef Ammi</h1>
          <p class="text-sm text-green-50">Your Pakistani Recipe Assistant</p>
        </div>
        <div id="chatArea" class="flex-1 p-6 space-y-4 overflow-y-auto bg-white" style="height: 60vh;">
          <div class="flex items-start gap-2">
            <div class="w-8 h-8 rounded-full bg-gradient-to-r from-green-600 to-orange-500 text-white flex items-center justify-center text-sm font-bold">👩‍🍳</div>
            <div class="bg-gradient-to-r from-green-50 to-orange-50 rounded-2xl px-4 py-2 max-w-[80%]">
              <p class="text-slate-800 text-sm">Assalam o Alaikum! 🌙 I'm Chef Ammi, your Pakistani recipe helper. Tell me what ingredients you have, and I'll suggest delicious desi recipes! 🍛</p>
            </div>
          </div>
        </div>
        <div class="p-4 border-t bg-gradient-to-r from-green-50 to-orange-50">
          <form id="chatForm" class="flex gap-2">
            <input id="userInput" type="text" placeholder="e.g., I have chicken, tomatoes, and onions..." class="flex-1 rounded-xl border border-green-300 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-green-500" autocomplete="off" />
            <button type="submit" class="rounded-xl bg-gradient-to-r from-green-600 to-orange-500 text-white px-5 py-3 text-sm font-medium hover:from-green-700 hover:to-orange-600 active:scale-[0.98] transition">Send</button>
          </form>
          <p class="text-xs text-slate-500 mt-2">
            💡 Tip: Tell me what ingredients you have or ask for a specific Pakistani dish!
          </p>
        </div>
      </div>
    </div>
    <script>
      const chatForm = document.getElementById("chatForm");
      const userInput = document.getElementById("userInput");
      const chatArea = document.getElementById("chatArea");
      let history = [];
      
      // Check URL parameters for pre-populated ingredients
      const urlParams = new URLSearchParams(window.location.search);
      const preloadedIngredients = urlParams.get('ingredients');
      
      function scrollToBottom() { chatArea.scrollTop = chatArea.scrollHeight; }
      function escapeHtml(str) {
        return str.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;");
      }
      function addMessage(role, text) {
        const wrapper = document.createElement("div");
        if (role === "user") {
          wrapper.className = "flex items-start gap-2 justify-end";
          wrapper.innerHTML = '<div class="bg-gradient-to-r from-green-600 to-orange-500 text-white rounded-2xl px-4 py-2 max-w-[80%] whitespace-pre-wrap"><p class="text-sm">' + escapeHtml(text) + '</p></div><div class="w-8 h-8 rounded-full bg-slate-300 text-slate-700 flex items-center justify-center text-sm font-bold">👤</div>';
        } else {
          wrapper.className = "flex items-start gap-2";
          wrapper.innerHTML = '<div class="w-8 h-8 rounded-full bg-gradient-to-r from-green-600 to-orange-500 text-white flex items-center justify-center text-sm font-bold">👩‍🍳</div><div class="bg-gradient-to-r from-green-50 to-orange-50 rounded-2xl px-4 py-2 max-w-[80%] whitespace-pre-wrap"><p class="text-slate-800 text-sm">' + escapeHtml(text) + '</p></div>';
        }
        chatArea.appendChild(wrapper);
        scrollToBottom();
      }
      function addTypingBubble() {
        const wrapper = document.createElement("div");
        wrapper.className = "flex items-start gap-2";
        wrapper.innerHTML = '<div class="w-8 h-8 rounded-full bg-gradient-to-r from-green-600 to-orange-500 text-white flex items-center justify-center text-sm font-bold">👩‍🍳</div><div class="bg-gradient-to-r from-green-50 to-orange-50 rounded-2xl px-4 py-2 max-w-[80%]"><p class="text-slate-500 text-sm italic">Chef Ammi is cooking up a recipe... 🍳</p></div>';
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
      
      // Auto-send if ingredients are pre-loaded
      if (preloadedIngredients) {
        const ingredientsMessage = "I have these ingredients: " + preloadedIngredients;
        userInput.value = ingredientsMessage;
        // Auto-submit after a short delay
        setTimeout(() => {
          chatForm.dispatchEvent(new Event('submit'));
        }, 500);
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
    """Regular chat endpoint - used by the chat interface"""
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
                "max_output_tokens": 2048,
            },
        )

        return jsonify({"reply": response.text or ""})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/recipes-from-ingredients", methods=["POST"])
def recipes_from_ingredients():
    """
    New endpoint for grocery app integration
    Accepts a list of ingredients and returns recipe suggestions
    
    Request body:
    {
      "ingredients": ["chicken", "tomatoes", "onions"],
      "preferences": {
        "spice_level": "medium",  // optional: mild, medium, spicy
        "diet": "regular",         // optional: regular, vegetarian
        "time": "30 mins"          // optional: cooking time preference
      }
    }
    """
    data = request.get_json(force=True)
    ingredients = data.get("ingredients", [])
    preferences = data.get("preferences", {})
    
    if not ingredients or not isinstance(ingredients, list):
        return jsonify({"error": "ingredients array is required"}), 400
    
    # Build the query message
    ingredients_str = ", ".join(ingredients)
    message = f"I have these ingredients from my grocery: {ingredients_str}."
    
    # Add preferences if provided
    if preferences.get("spice_level"):
        message += f" I prefer {preferences['spice_level']} spice level."
    if preferences.get("diet"):
        message += f" I want {preferences['diet']} recipes."
    if preferences.get("time"):
        message += f" I have about {preferences['time']} for cooking."
    
    message += " Can you suggest some Pakistani recipes I can make?"
    
    # Generate response
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[{"role": "user", "parts": [{"text": message}]}],
            config={
                "system_instruction": SYSTEM_INSTRUCTION,
                "temperature": 0.7,
                "max_output_tokens": 2048,
            },
        )
        
        return jsonify({
            "success": True,
            "query": message,
            "response": response.text or "",
            "ingredients_used": ingredients
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health")
def health():
    return jsonify({"ok": True})