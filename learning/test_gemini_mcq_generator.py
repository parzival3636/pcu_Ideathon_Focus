import google.generativeai as genai
import json
import re

# ── Config ──────────────────────────────────────────────────────────────────
GEMINI_API_KEY = "AIzaSyDxej3XG1eQGjP4tLkRzNRSBnlV0OSMj3I"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

# ── User States ──────────────────────────────────────────────────────────────
USER_STATE_CONFIG = {
    1: {
        "label": "confused",
        "num_questions": 20,
        "difficulty": "beginner",
        "instruction": "The user is confused. Generate SIMPLE questions that reinforce basic understanding.",
        "take_break": False,
    },
    2: {
        "label": "bored",
        "num_questions": 20,
        "difficulty": "advanced",
        "instruction": "The user is bored. Generate CHALLENGING questions that require deeper thinking.",
        "take_break": False,
    },
    3: {
        "label": "overloaded",
        "num_questions": 10,
        "difficulty": "easy",
        "instruction": "The user is overloaded. Generate only 10 EASY questions focusing on key takeaways.",
        "take_break": True,
    },
    4: {
        "label": "focused",
        "num_questions": 20,
        "difficulty": "intermediate-to-advanced",
        "instruction": "The user is focused. Gradually INCREASE difficulty.",
        "take_break": False,
    },
}


# ── Step 1: Extract Technical Content ────────────────────────────────────────
def extract_technical_content(transcript: str) -> str:
    """Extracts educational content from transcript."""
    prompt = f"""You are an educational content extractor.
Remove: filler, jokes, timestamps, sponsor segments.
Extract: key concepts, definitions, facts, processes, examples.
Output as structured bullet points.

RAW TRANSCRIPT:
\"\"\"
{transcript}
\"\"\"

OUTPUT (bullet points only):"""
    
    response = model.generate_content(prompt)
    return response.text.strip()


# ── Step 2: Generate Adaptive MCQs ───────────────────────────────────────────
def generate_mcqs(technical_content: str, user_state: int) -> dict:
    """Generates adaptive MCQs based on user state."""
    if user_state not in USER_STATE_CONFIG:
        raise ValueError(f"user_state must be 1-4, got {user_state}")
    
    config = USER_STATE_CONFIG[user_state]
    num_q = config["num_questions"]
    instruction = config["instruction"]
    difficulty = config["difficulty"]
    
    prompt = f"""You are an expert quiz generator.

CONTEXT: {instruction}
DIFFICULTY: {difficulty}
NUMBER OF QUESTIONS: {num_q}

RULES:
- Generate EXACTLY {num_q} MCQ questions
- Each question must have 4 options (A, B, C, D)
- Only one correct answer
- Include brief explanation

CONTENT:
\"\"\"
{technical_content}
\"\"\"

Return ONLY valid JSON array:
[{{
  "question": "Question text?",
  "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
  "answer": "A",
  "explanation": "Why A is correct."
}}]"""
    
    response = model.generate_content(prompt)
    raw = response.text.strip()
    
    # Strip markdown code fences
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    
    questions = json.loads(raw)
    
    result = {
        "user_state": config["label"],
        "difficulty": difficulty,
        "num_questions": len(questions),
        "take_break_suggestion": config["take_break"],
        "break_message": (
            "⚠️  You seem overloaded. Take a 10-minute break!"
        ) if config["take_break"] else None,
        "questions": questions,
    }
    
    return result


# ── Main Pipeline ─────────────────────────────────────────────────────────────
def run_pipeline(transcript: str, user_state: int) -> dict:
    """Full pipeline: transcript → extract content → generate MCQs"""
    print(f"[1/2] Extracting technical content...")
    technical_content = extract_technical_content(transcript)
    print(f"      ✓ Extracted {len(technical_content.split())} words")
    
    print(f"[2/2] Generating MCQs for state: {USER_STATE_CONFIG[user_state]['label']}...")
    result = generate_mcqs(technical_content, user_state)
    print(f"      ✓ Generated {result['num_questions']} questions")
    
    result["extracted_content"] = technical_content
    return result


# ── Example Usage ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    sample_transcript = """
imagine creating your own professional 3D avatar Builder fully customizable and ready to use in any project in this new video series I will show you exactly how to do that step by step using 3js and react hi in today's video we'll have a look at what we will build and set up our project first of all why build an avatar configurator well not only is it a complete professional level project but the ultimate goal is to have good-looking animated Avatar ready to use in the previous and upcoming tutorials if we look at Ready Player me the Sims and Animal Crossing we can get some design Inspirations and an idea of the features we will implement the as choosing between different assets to customize the head and body parts picking different colors for the skin and hair switching clothes and accessories and finally generating a final lightweight version of our 3D model for the style of our avatars we will take inspiration from cute small characters found on dribble and peps Avatar builder thanks to Kos you can freely reuse the assets from this project in yours a good reason to follow her social media if you are looking for a different style the concepts are the same and I will show you how to prepare your assets to work with our setup here is the technical stack we will be using for this project 3js pair with reactory fiber for 3D rendering in the browser Tailwind CSS to build and style the UI quickly justen for State Management and pocket base for our back end to store and manage Avatar data let's get started by setting up a new react ref fiber project to create our react app we will be using vit if you are using npm you need to copy this command in my case I'm using yarn so I will run yarn create VD in the folder of your choice in the terminal based the command hit enter it will ask you the project name I will name it r3f ultimate character configurator enter Then I select the framework I will choose react and you have the choice between typescript or JavaScript choose whatever you prefer but for the lack of Simplicity I will stick to JavaScript now it created a folder we can go file open folder and open the folder it just created Run yarn to install the dependencies and yarn Dev to run the development server you can open the link that it will prompt you and we have a starting app with react with the count button for the UI we'll be using Tailwind CSS we can follow install Tailwind CSS with vid guide we need to install three dependencies Tailwind CSS post CSS and auto prefixer because of the dashd we will need to use Save Dev with yarn yarn add-- Dev and paste the three package names then we need to run this command simply paste and enter it will create a Tailwind config JS we can copy this part for react open Tailwind config JS in the content paste what we have then in our CSS file we need to paste those lines on the top let's open index. CSS we can remove everything and paste it let's run again our development server and let's clean a bit the template we have app. CSS we won't be using it app.jsx which is where our app will start we can get rid of everything here also the import and let's check if Tailwind Works let's take the example here paste it in the middle of the app don't forget to remove app. CSS that we deleted and we now have Hello World it is bold and underlined defined by font bold and underline classes if like me you like tailwind and you want the detail of the classes when you hover a class name go to the extensions on the left search for tailwind and it's Tailwind CSS intellisense now let's add threejs with the reactory fiber library to be able to render 3D models inside our web application we need to install the following packages three the types of three and reactory fiber yarn add and paste the package name and to have our disposal a lot of useful react components to use react ref fiber we will also install react 3 dry Library yarn add at react 3 dry we can run again yarn Dev and hide the terminal let's add some 3D to our scene we can remove this add a canvas this is where our rendering will be done we can set up our camera position with camera position and we will set three three and three let's add a cube with a mesh containing a box geometry of 0.5 0.5 0.5 and a mesh normal material if you have eslint errors like this a known property from the rule eslint a quick fix to get rid of it is either to remove es lint or to add this rule react no unknown property to ignore when it's on the args save it and you don't have the error anymore let's also add Orbit Control component from react 3 dry to be able to rotate the camera and if we look we have our Cube and we can rotate the camera but the canvas is way too small let's adjust this by going to our CSS adding root set the width and the height to be the full screen which is our main container and also to remove the default margin on the body to be sure it's taking the whole screen we can also add a background color on our canvas with color attach background we set it to be very dark since the attach is also causing issues so I will remove es lint let's open package.json remove all the lines related to es lint also the script yarn to refresh the modules and on the left remove the es L config and should be good for now we can see our canvas is taking the whole page to save our project progression and to deploy the different versions of our project let's create a GitHub repository I will name it r3f ultimate character configurator I will keep all the other things like this and create repository it's giving me a few commments I will just take the commit the branch and the push then in the terminal I will run get in it I will get add all the files by default with vit you have a git ignore so it's not taking the node modules and I can paste all the other comments if we reload this page we should have our code perfect then to deploy your project you can use the platform of your choice but I recommend you to use lso which is my go-to solution for deploying my own projects and I'm not saying this because they are the sponsor of this video I'm using it for years and my react 3 fiber course is hosted with it if you choose to use lsj click on login then I already have a service running but I will show you in the default project here head to cicd you can connect your GitHub account mine is already connected and then you choose the repository that you want to deploy for me it's the latest One Import deploy either on a new VM or an existing one choose between the different Cloud providers region and service plan which is basically the number of CPU RAM and storage the smallest one will work good for our project and hit next then you can choose which branch will be deployed when a modification is pushed on it currently we only have main we will select this one we have a static website but if you are using next you would select full stack if you are in server side rendering if not SSG would be static too then you can change the the build and output setting our install command is yarn install to build yarn build and the output if we run yarn build you can see here or on the left that the build is done into the disc folder so the output there is slash this then we are not using environment variables we can create our cicd pipeline once the deployment is done you will receive an email and you can access your deployment here here and our project is now online we can use it any change we will do on the main branch will automatically trigger a new build thank you for watching in the next video we'll dive into setting up our database with pocket base and fetching assets directly into our app if you are ready to build your own 3D avatar configurator hit that subscribe button and follow along as we build this project step by step see you in the next video
"""
    
    # Test with different user states
    USER_STATE = 1  # 1=confused, 2=bored, 3=overloaded, 4=focused
    
    result = run_pipeline(sample_transcript, USER_STATE)
    
    # Print break message if applicable
    if result["take_break_suggestion"]:
        print(f"\n{result['break_message']}\n")
    
    # Print questions
    print(f"\n=== {result['num_questions']} MCQs | State: {result['user_state']} | Difficulty: {result['difficulty']} ===\n")
    
    for i, q in enumerate(result["questions"], 1):
        print(f"Q{i}. {q['question']}")
        for key, val in q["options"].items():
            print(f"   {key}. {val}")
        print(f"   ✓ Answer: {q['answer']} — {q['explanation']}\n")
    
    # Save to JSON
    with open("mcq_output.json", "w") as f:
        json.dump(result, f, indent=2)
    
    print("✓ Saved to mcq_output.json")
