# LaunchDarkly SE Technical Exercise - Flask & Gemini

This repository contains the solution for the LaunchDarkly SE Technical Exercise, covering Part 1 (Release & Remediate), Part 2 (Target), and Extra Credit Option A (Experimentation).

## Prerequisites & Assumptions
- **Python 3.9+** is installed on your system.
- You have a valid **Google Gemini API Key**.
- You have a **LaunchDarkly Server-Side SDK Key**.

## Setup Instructions (Under 10 Minutes)

### 1. Clone & Install Dependencies
Clone this repository to your local machine, then run the following commands to install the required Python libraries:

```bash
# Recommended: Create a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

**Set Environment Variables**
The application requires your API keys to function. Export them in your terminal:

export GEMINI_API_KEY="XX-gemini-api-key"
export LD_SDK_KEY="XX-launchdarkly-sdk-key"
(Note: If you do not export LD_SDK_KEY, you must manually paste it into main.py under the LAUNCHDARKLY_SDK_KEY variable). I have pasted LD_SDK_KEY manually to main.py file.

**LaunchDarkly Dashboard Setup**
Before running the app, please recreate this setup in your LaunchDarkly environment:

**Create the Feature Flag**
Log in to LaunchDarkly and create a new Boolean feature flag.
Set the flag key exactly as enable-ai-chatbot.

Use case part 1:(Release / Rollback + Remediate)

Release: Turn the flag ON in LaunchDarkly dashboard. Go to your Flask app frontend, type a question, and click "Send to AI". You will see the Gemini AI response. This demonstrates releasing the feature to users.

Rollback: Toggle the flag OFF in LaunchDarkly. Click "Send to AI" again. The app will immediately return your "🔒 [Access Denied]" message. This shows an instant rollback with **zero code redeployments**.

Remediate with Triggers:
In your LaunchDarkly dashboard, go to the "Environment configuration" for the enable-ai-chatbot flag (production Environment).
Find the Triggers section and create a new generic trigger. LaunchDarkly will generate a unique URL.
Turn your flag ON manually
Open your computer's terminal and run a manual curl command hitting that trigger URL. (e.g., curl -X POST <URL>).
Watch the LaunchDarkly dashboard—the flag will automatically toggle OFF, simulating how a system would kill a problematic feature during an incident response, The feature disables without any code change or redeploy , Simulates a real incident response: flag off = problem solved.


Use case part 2: (Feature Flag + Context Attributes + Target)

Rule-Based Targeting (Part 1)
In LaunchDarkly's targeting rules for this flag, set the Default rule to serve false. This ensures regular users get the existing (denied) experience.
Create a new rule based on your context attributes. Set it so that if user_tier equals Enterprise, it serves true.
Go to your app, select "Standard" from the dropdown, and click send. You will be denied. Change the dropdown to "Enterprise" and try again. The AI will answer, proving the rule works.

Individual Targeting (Part 2)
In the flag's LaunchDarkly settings, find the Individual Targets section.
Add a specific user key, like alice-123, and set it to serve true.
Go to your app. Keep the User Tier as "Standard" (which normally gets blocked), but ensure the User Key input says alice-123.
Click "Send to AI". The request will succeed, showing how you can target specific users before a wider rollout.

Experimentation (Extra Credit):
Go to Metrics and create a custom conversion metric named ai-chat-used (Event kind: Custom, Event key: ai-chat-used, Metric definition: Count).
Go to Experiments, create a new experiment on the enable-ai-chatbot flag using the ai-chat-used metric, and click Start iteration.


4. Run the Application
Start the Flask server:

python main.py
Open your browser and navigate to http://127.0.0.1:5000.

**How to Test the Demo**
Release & Rollback and remediate: Toggle the flag ON/OFF in your LaunchDarkly dashboard and click "Send to AI" in the app to see instant access changes. Also once the Generic Trigger is created, Keep the flag ON and Use the generated URL to test instant remediation via your terminal (e.g., curl -X POST <URL>), you will see the flag is set to OFF and insatnt remediation- without any code change or redeploy (Simulates a real incident response: flag off = problem solved)

Context Targeting: Change the User Tier dropdown in the app to "Enterprise" to see the rule-based targeting grant access to the AI. **by default, "Enterprise" users and "Standard" user with only User Key (ID) "alice-123" will have access, rest "Standard" users will recieve 🔒 [Access Denied]**

Experimentation: Click "Send to AI" with a few different User Keys. The app tracks the click and flushes the data instantly. Check the "Exposures" tab in your LD Experiment to see the telemetry data.

### Flow chart Diagram

               [ Start ]
                   │
                   ▼
┌──────────────────────────────────────────────┐
│            Create Feature Flag               │
│ - Flag Key: "enable-ai-chatbot" (Boolean)    │
└──────────────────┬───────────────────────────┘
                   │
         ┌─────────┼────────────────────────┐
         │         │                        │
         ▼         ▼                        ▼
┌──────────────┐ ┌────────────────────┐ ┌──────────────────────┐
│  USE CASE 1  │ │     USE CASE 2     │ │     EXTRA CREDIT     │
│  Release,    │ │     Targeting      │ │    Experimentation   │
│  Rollback &  │ │                    │ └────────┬─────────────┘
│  Remediate   │ │                    │          │
└────────┬─────┘ └─────────┬──────────┘          ├─► [Create Metric]
         │                 │                     │   Key: ai-chat-used
         ├─► [Release]     ├─► [Rule Targeting]  │   Def: Count
         │   ON ──► ✅      │   Default ──► ❌     │
         │                 │   Enterprise ──► ✅  ├─► [Create Experiment]
         ├─► [Rollback]    │                     │   Use "enable-ai-chatbot"
         │   OFF ──► 🔒     ├─► [Ind. Targeting]  │
         │                 │   User: alice-123   ├─► [Start Iteration]
         └─► [Remediate]   │   ──► ✅             │   Measure usage 🚀
             Trigger URL   └────────────────────┘ 
             curl ──► Auto OFF 🚨

