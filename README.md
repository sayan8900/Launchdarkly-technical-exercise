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

export GEMINI_API_KEY="your-gemini-api-key"
export LD_SDK_KEY="your-launchdarkly-sdk-key"
(Note: If you do not export LD_SDK_KEY, you must manually paste it into main.py under the LAUNCHDARKLY_SDK_KEY variable). I have pasted LD_SDK_KEY manually to main.py file.

**LaunchDarkly Dashboard Setup**
Before running the app, please recreate this setup in your LaunchDarkly environment:

Feature Flag: Create a Boolean feature flag named exactly enable-ai-chatbot.

Targeting Rules (Part 2):

Set the Default rule to serve false.

Create a targeting rule: If user_tier is one of Enterprise, serve true.

Experimentation (Extra Credit):

Go to Metrics and create a custom conversion metric named ai-chat-used (Event kind: Custom, Event key: ai-chat-used, Metric definition: Count).

Go to Experiments, create a new experiment on the enable-ai-chatbot flag using the ai-chat-used metric, and click Start iteration.

Remediation Trigger (Part 1):

In the flag's environment configuration menu, create a Generic Trigger to turn the flag OFF. Use the generated URL to test instant remediation via your terminal (e.g., curl -X POST <URL>).

4. Run the Application
Start the Flask server:

python main.py
Open your browser and navigate to http://127.0.0.1:5000.

**How to Test the Demo**
Release & Rollback and remediate: Toggle the flag ON/OFF in your LaunchDarkly dashboard and click "Send to AI" in the app to see instant access changes. Also once the Generic Trigger is created, Keep the flag ON and Use the generated URL to test instant remediation via your terminal (e.g., curl -X POST <URL>), you will see the flag is set to OFF and insatnt remediation- without any code change or redeploy (Simulates a real incident response: flag off = problem solved)

Context Targeting: Change the User Tier dropdown in the app to "Enterprise" to see the rule-based targeting grant access to the AI. **by default, "Enterprise" users and "Standard" user with only User Key (ID) "alice-123" will have access, rest "Standard" users will recieve 🔒 [Access Denied]  **

Experimentation: Click "Send to AI" with a few different User Keys. The app tracks the click and flushes the data instantly. Check the "Exposures" tab in your LD Experiment to see the telemetry data.
