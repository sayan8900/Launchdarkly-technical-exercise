import os
from flask import Flask, jsonify, render_template_string, request
import ldclient
from ldclient.config import Config
from ldclient.context import Context
from langchain_google_genai import ChatGoogleGenerativeAI
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

app = Flask(__name__)

# Environment Keys
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
  raise RuntimeError("GEMINI_API_KEY environment variable not set.")

# ====================================================================
# LAUNCHDARKLY SDK INITIALIZATION
# ====================================================================
# REVIEWER NOTE: 
# Please replace the default SDK key below with your own LaunchDarkly Server-Side SDK Key.
# You can also pass it via the 'LD_SDK_KEY' environment variable.
# ====================================================================
# TODO: Replace with your actual LaunchDarkly SDK Key
LAUNCHDARKLY_SDK_KEY = os.getenv("LD_SDK_KEY", "sdk-6d79dc9b-70a6-4a53-a321-fbf5a6370886")

ldclient.set_config(Config(LAUNCHDARKLY_SDK_KEY))
ld_client = ldclient.get()

if ld_client.is_initialized():
  print("--> [SYSTEM] LaunchDarkly SDK successfully initialized!")
else:
  print(
      "--> [CRITICAL WARNING] LaunchDarkly SDK failed to initialize. Check your"
      " SDK key."
  )

# ====================================================================
# MODEL CONFIGURATION
# ====================================================================
active_chat_model = "gemini-3.5-flash-lite"
llm = ChatGoogleGenerativeAI(
    model=active_chat_model, google_api_key=gemini_api_key, temperature=0.7
)


# ====================================================================
# TENACITY RETRY LOGIC (Handles 503 Vendor Errors)
# ====================================================================
def is_503_error(exception):
  return "503" in str(exception)


@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(5),
    retry=retry_if_exception(is_503_error),
    reraise=True,
)
def call_gemini_api_with_retry(prompt: str):
  response = llm.invoke(prompt)
  return response.content


# ====================================================================
# HTML FRONTEND TEMPLATE
# ====================================================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>LaunchDarkly SE Technical Exercise - Flask & Gemini</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 40px; background: #f4f6f9; color: #333; }
        .container { max-width: 700px; margin: auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
        input, select { width: 100%; padding: 10px; margin-top: 5px; margin-bottom: 15px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
        textarea { width: 100%; height: 80px; padding: 10px; margin-top: 5px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
        button { background: #0066cc; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; }
        .response-box { margin-top: 20px; padding: 15px; background: #e9ecef; border-radius: 4px; white-space: pre-wrap; min-height: 40px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>ABC Company SE Technical Demo</h2>
        <p>Test LaunchDarkly Context Targeting & Feature Flags with Google Gemini.</p>
        <hr>

        <label>User Key (ID):</label>
        <input type="text" id="userKey" value="alice-123">

        <label>User Tier (Targeting Attribute):</label>
        <select id="userTier">
            <option value="Standard">Standard</option>
            <option value="Enterprise">Enterprise</option>
        </select>

        <label>Beta Tester (True/False):</label>
        <select id="betaTester">
            <option value="false">False</option>
            <option value="true">True</option>
        </select>

        <label>Ask AI Assistant:</label>
        <textarea id="promptInput" placeholder="Ask a question..."></textarea>
        <button onclick="sendChatMessage()">Send to AI</button>

        <div class="response-box" id="responseArea">Awaiting response...</div>
    </div>

    <script>
        async function sendChatMessage() {
            const prompt = document.getElementById('promptInput').value;
            const user_key = document.getElementById('userKey').value;
            const user_tier = document.getElementById('userTier').value;
            const beta_tester = document.getElementById('betaTester').value === 'true';
            
            const responseArea = document.getElementById('responseArea');
            responseArea.innerText = "Thinking...";

            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt, user_key, user_tier, beta_tester })
                });
                const data = await res.json();
                responseArea.innerText = data.reply;
            } catch (err) {
                responseArea.innerText = "Error communicating with server.";
            }
        }
    </script>
</body>
</html>
"""


# ====================================================================
# ENDPOINTS
# ====================================================================
@app.route("/")
def home():
  return render_template_string(HTML_TEMPLATE)


@app.post("/api/chat")
def chat_endpoint():
  data = request.json or {}
  prompt = data.get("prompt", "")
  user_key = data.get("user_key", "default-user-id")
  user_tier = data.get("user_tier", "Standard")
  beta_tester = data.get("beta_tester", False)

  try:
    # ==========================================
    # PART 2: TARGETING & CONTEXT ATTRIBUTES
    # ==========================================
    context = (
        Context.builder(user_key)
        .kind("user")
        .set("user_tier", user_tier)
        .set("beta_tester", beta_tester)
        .build()
    )

    # ==========================================
    # PART 1 & 2: FEATURE FLAG EVALUATION
    # ==========================================
    flag_key = "enable-ai-chatbot"
    is_chatbot_enabled = ld_client.variation(flag_key, context, False)
    # This ensures LaunchDarkly tracks the click for ALL users, 
    # regardless of whether the chatbot is enabled or disabled for them.
    ld_client.track("ai-chat-used", context)
    if not is_chatbot_enabled:
      print(
          f"--> [RESTRICTED] Chatbot feature is disabled for user:"
          f" {user_key} (Tier: {user_tier})"
      )
      return jsonify({
          "status": "disabled",
          "reply": (
              "🔒 [Access Denied] The AI Support Assistant is currently offline"
              " or not available for your account tier."
          ),
      })

    print(f"--> [AI CHAT MODE] Generating LLM response for user: {user_key}")
    final_prompt = f"""
You are a helpful enterprise AI assistant for ABC Company. Answer the user query professionally.

USER QUERY:
{prompt}
"""

    reply_text = call_gemini_api_with_retry(final_prompt)
    return jsonify({"status": "success", "reply": reply_text})

  except Exception as e:
    error_msg = f"SYSTEM ERROR: {str(e)}"
    print(error_msg)
    return jsonify({"status": "error", "reply": error_msg}), 500


if __name__ == "__main__":
  app.run(debug=True, port=5000)
