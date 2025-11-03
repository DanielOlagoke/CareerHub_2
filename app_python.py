# CareerHub - Professional Career Development Platform
from flask import Flask, request, render_template, flash, redirect, url_for
import re
import json
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from typing import Optional

# 3rd party modules for parsing and AI (may be optional)
try:
    from openai import OpenAI
except Exception:
    OpenAI = None  # type: ignore
try:
    import PyPDF2
except Exception:
    PyPDF2 = None  # type: ignore
try:
    import docx  # python-docx
except Exception:
    docx = None  # type: ignore

# ---- Flask SETUP ----
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Enables Flask's flash messages

# ---- Tech skills/categories for UI ----
TECH_SKILLS = {
    'programming': ['Python', 'JavaScript', 'Java', 'C++', 'C#', 'PHP', 'Ruby', 'Swift', 'Kotlin'],
    'web_dev': ['HTML', 'CSS', 'React', 'Angular', 'Vue.js', 'Node.js', 'Django', 'Flask'],
    'databases': ['MySQL', 'PostgreSQL', 'MongoDB', 'SQLite', 'Oracle'],
    'tools': ['Git', 'Docker', 'AWS', 'Azure', 'Linux', 'Windows', 'MacOS'],
    'soft_skills': ['Communication', 'Teamwork', 'Problem Solving', 'Leadership', 'Time Management']
}

JOB_CATEGORIES = {
    'software_engineer': {
        'title': 'Software Engineer',
        'skills': ['programming', 'web_dev', 'databases', 'tools'],
        'description': 'Design, develop, and maintain software applications'
    },
    'web_developer': {
        'title': 'Web Developer',
        'skills': ['web_dev', 'programming', 'databases'],
        'description': 'Create and maintain websites and web applications'
    },
    'data_analyst': {
        'title': 'Data Analyst',
        'skills': ['programming', 'databases', 'tools'],
        'description': 'Analyze data to help businesses make informed decisions'
    },
    'cybersecurity': {
        'title': 'Cybersecurity Specialist',
        'skills': ['programming', 'tools', 'soft_skills'],
        'description': 'Protect systems and networks from cyber threats'
    }
}

# ---- File Reading Helpers (Called in Analyze Route) ----
ALLOWED_EXTENSIONS = {'.pdf', '.docx'}

def allowed_file(filename: str) -> bool:
    _, ext = os.path.splitext(filename.lower())
    return ext in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_stream) -> str:
    if PyPDF2 is None:
        return ''
    try:
        reader = PyPDF2.PdfReader(file_stream)
        pages = []
        for page in reader.pages:
            try:
                pages.append(page.extract_text() or '')
            except Exception:
                continue
        return "\n".join(pages).strip()
    except Exception:
        return ''

def extract_text_from_docx(file_stream) -> str:
    if docx is None:
        return ''
    try:
        document = docx.Document(file_stream)
        return "\n".join(p.text for p in document.paragraphs).strip()
    except Exception:
        return ''

def parse_uploaded_cv(cv_file) -> str:
    """Return extracted text from uploaded PDF/DOCX or empty string on failure."""
    if not cv_file or cv_file.filename == '':
        return ''
    filename = secure_filename(cv_file.filename)
    if not allowed_file(filename):
        return ''
    _, ext = os.path.splitext(filename.lower())
    # Read into memory so parsers can re-read
    file_bytes = cv_file.read()
    from io import BytesIO
    stream = BytesIO(file_bytes)
    if ext == '.pdf':
        return extract_text_from_pdf(stream)
    if ext == '.docx':
        return extract_text_from_docx(stream)
    return ''

# ---- MAIN WEB ROUTES ----
@app.route('/')
def home():
    # Serve the main HTML template (UI page)
    return render_template('index.html', tech_skills=TECH_SKILLS)

@app.route('/analyze', methods=['POST'])
def analyze():
    # --- STEP 1: Gather Input from Form
    # Textarea text
    typed_cv_text = request.form.get('cv_text', '').strip()
    # Job Description (optional)
    job_description = request.form.get('job_description', '').strip()
    # Uploaded file (if any)
    cv_file = request.files.get('cv_file')
    # Try to extract all text from PDF or DOCX file
    uploaded_text = parse_uploaded_cv(cv_file) if cv_file else ''
    # Merge uploaded file text and any extra textarea edits
    combined_cv = (uploaded_text + "\n\n" + typed_cv_text).strip() if uploaded_text else typed_cv_text

    # --- STEP 2: Validate (server-side, always double checking!)
    if not combined_cv:
        flash('Please provide your CV (paste text and/or upload PDF/DOCX).', 'error')
        return redirect(url_for('home'))
    if len(combined_cv) < 50:
        flash('CV content looks too short. Add more detail for a better review.', 'error')
        return redirect(url_for('home'))

    # --- STEP 3: Generate Analysis (AI if OpenAI API key set, otherwise fallback)
    api_key = os.getenv('OPENAI_API_KEY')
    use_llm = bool(api_key and OpenAI is not None)

    if use_llm:
        try:
            client = OpenAI(api_key=api_key)
            prompt = (
                "You are a senior career coach. Analyze the candidate's CV against the provided job description. "
                "Identify strengths, gaps, and suggest specific, actionable improvements. "
                "Rewrite key sections (summary, skills, experience bullets) to better match the job. "
                "Use clear bullet points, quantify impact where possible, and keep a professional tone.\n\n"
                "Job Description (JD):\n" + (job_description or "[No JD provided]") + "\n\n"
                "Candidate CV:\n" + combined_cv
            )
            response = client.chat.completions.create(
                model="gpt-4.1",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            ai_reply = response.choices[0].message.content
            # --- STEP 4: Show results on web page using template variable 'output'
            return render_template('index.html', output=ai_reply, tech_skills=TECH_SKILLS)
        except Exception:
            flash('LLM analysis unavailable; showing basic analysis.', 'error')

    # --- Fallback: Rule-based analysis (if no API or API fails)
    analysis_result = analyze_cv_professionally(combined_cv)
    return render_template('index.html', output=analysis_result, tech_skills=TECH_SKILLS)

# ---- PERSONAL STATEMENT GENERATOR ----
@app.route('/statement', methods=['POST'])
def statement():
    user_goal = request.form.get('goal_text', '').strip()
    
    if not user_goal:
        flash('Please enter your career goal before generating a statement.', 'error')
        return redirect(url_for('home'))
    
    # Generate professional personal statement
    statement_result = generate_personal_statement(user_goal)
    
    return render_template('index.html', statement_output=statement_result, tech_skills=TECH_SKILLS)

# ---- SKILLS ASSESSMENT ----
@app.route('/skills', methods=['POST'])
def skills_assessment():
    selected_skills = request.form.getlist('skills')
    
    if not selected_skills:
        flash('Please select at least one skill for assessment.', 'error')
        return redirect(url_for('home'))
    
    assessment_result = assess_skills(selected_skills)
    
    return render_template('index.html', skills_output=assessment_result, tech_skills=TECH_SKILLS)

# ---- JOB MATCHING ----
@app.route('/match', methods=['POST'])
def job_matching():
    user_skills = request.form.get('user_skills', '').strip()
    
    if not user_skills:
        flash('Please enter your skills for job matching.', 'error')
        return redirect(url_for('home'))
    
    match_result = match_jobs(user_skills)
    
    return render_template('index.html', match_output=match_result, tech_skills=TECH_SKILLS)

# ---- HELPER FUNCTIONS ----

def analyze_cv_professionally(cv_text):
    """Analyze CV using professional criteria"""
    analysis = {
        'strengths': [],
        'weaknesses': [],
        'suggestions': [],
        'improved_sections': []
    }
    
    # Check for contact information
    if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', cv_text):
        analysis['strengths'].append("✓ Contact information is present")
    else:
        analysis['weaknesses'].append("✗ Missing email address")
        analysis['suggestions'].append("Add a professional email address")
    
    # Check for phone number
    if re.search(r'(\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}', cv_text):
        analysis['strengths'].append("✓ Phone number is included")
    else:
        analysis['weaknesses'].append("✗ Missing phone number")
        analysis['suggestions'].append("Include a contact phone number")
    
    # Check for skills section
    skills_keywords = ['skills', 'technical skills', 'programming', 'languages', 'technologies']
    if any(keyword in cv_text.lower() for keyword in skills_keywords):
        analysis['strengths'].append("✓ Skills section is present")
    else:
        analysis['weaknesses'].append("✗ No clear skills section")
        analysis['suggestions'].append("Add a dedicated skills section highlighting your technical abilities")
    
    # Check for experience section
    experience_keywords = ['experience', 'work', 'employment', 'internship', 'project']
    if any(keyword in cv_text.lower() for keyword in experience_keywords):
        analysis['strengths'].append("✓ Work experience is mentioned")
    else:
        analysis['weaknesses'].append("✗ Limited work experience mentioned")
        analysis['suggestions'].append("Include any work experience, internships, or relevant projects")
    
    # Check for education
    education_keywords = ['education', 'degree', 'university', 'college', 'school', 'qualification']
    if any(keyword in cv_text.lower() for keyword in education_keywords):
        analysis['strengths'].append("✓ Education section is present")
    else:
        analysis['weaknesses'].append("✗ Education information missing")
        analysis['suggestions'].append("Include your educational background and qualifications")
    
    # Generate improved CV sections
    analysis['improved_sections'] = generate_improved_sections(cv_text)
    
    return format_analysis_result(analysis)

def generate_personal_statement(goal):
    """Generate a professional personal statement based on user goal"""
    # Extract key information from the goal
    goal_lower = goal.lower()
    
    # Determine the type of role
    role_type = "apprenticeship"
    if "engineer" in goal_lower:
        role_type = "software engineering"
    elif "developer" in goal_lower:
        role_type = "web development"
    elif "analyst" in goal_lower:
        role_type = "data analysis"
    elif "cyber" in goal_lower or "security" in goal_lower:
        role_type = "cybersecurity"
    
    # Extract company if mentioned
    companies = ["google", "microsoft", "amazon", "apple", "meta", "netflix", "tesla", "spacex"]
    mentioned_company = None
    for company in companies:
        if company in goal_lower:
            mentioned_company = company.title()
            break
    
    # Generate statement
    statement = f"""I am writing to express my strong interest in pursuing a {role_type} apprenticeship"""
    
    if mentioned_company:
        statement += f" at {mentioned_company}"
    
    statement += """. My passion for technology and problem-solving drives me to continuously learn and grow in this field.

Key Strengths:
• Strong foundation in programming and software development
• Excellent problem-solving and analytical thinking skills
• Eager to learn new technologies and methodologies
• Strong communication and teamwork abilities
• Self-motivated with a genuine passion for technology

I am particularly drawn to this opportunity because it offers the perfect blend of hands-on experience and structured learning. I am committed to contributing meaningfully to your team while developing the skills necessary for a successful career in technology.

I am excited about the possibility of bringing my enthusiasm, dedication, and fresh perspective to your organization and would welcome the opportunity to discuss how I can contribute to your team's success."""
    
    return statement

def assess_skills(selected_skills):
    """Assess user's selected skills and provide recommendations"""
    assessment = {
        'current_skills': selected_skills,
        'recommendations': [],
        'learning_path': [],
        'job_matches': []
    }
    
    # Categorize skills
    skill_categories = {}
    for skill in selected_skills:
        for category, skills_list in TECH_SKILLS.items():
            if skill in skills_list:
                if category not in skill_categories:
                    skill_categories[category] = []
                skill_categories[category].append(skill)
    
    # Generate recommendations
    if 'programming' in skill_categories:
        assessment['recommendations'].append("Great! You have programming skills. Consider learning version control with Git.")
    else:
        assessment['recommendations'].append("Consider learning a programming language like Python or JavaScript.")
    
    if 'web_dev' in skill_categories:
        assessment['recommendations'].append("Web development skills are valuable. Consider learning a framework like React or Vue.js.")
    else:
        assessment['recommendations'].append("Web development skills are in high demand. Start with HTML, CSS, and JavaScript.")
    
    if 'databases' in skill_categories:
        assessment['recommendations'].append("Database knowledge is excellent. Consider learning cloud platforms like AWS or Azure.")
    else:
        assessment['recommendations'].append("Database skills are essential. Start with SQL and MySQL.")
    
    # Generate learning path
    assessment['learning_path'] = [
        "1. Master the fundamentals of your chosen programming language",
        "2. Learn version control with Git and GitHub",
        "3. Build projects to apply your knowledge",
        "4. Learn about databases and data management",
        "5. Explore cloud platforms and deployment",
        "6. Contribute to open source projects"
    ]
    
    # Find job matches
    for job_id, job_info in JOB_CATEGORIES.items():
        matching_skills = []
        for skill in selected_skills:
            for category in job_info['skills']:
                if skill in TECH_SKILLS.get(category, []):
                    matching_skills.append(skill)
        
        if matching_skills:
            match_percentage = (len(matching_skills) / len(job_info['skills'])) * 100
            assessment['job_matches'].append({
                'title': job_info['title'],
                'description': job_info['description'],
                'match_percentage': round(match_percentage),
                'matching_skills': matching_skills
            })
    
    return format_skills_assessment(assessment)

def match_jobs(user_skills):
    """Match user skills with available job categories"""
    user_skills_list = [skill.strip() for skill in user_skills.split(',')]
    
    matches = []
    for job_id, job_info in JOB_CATEGORIES.items():
        matching_skills = []
        for skill in user_skills_list:
            for category in job_info['skills']:
                if skill in TECH_SKILLS.get(category, []):
                    matching_skills.append(skill)
        
        if matching_skills:
            match_percentage = (len(matching_skills) / len(job_info['skills'])) * 100
            matches.append({
                'title': job_info['title'],
                'description': job_info['description'],
                'match_percentage': round(match_percentage),
                'matching_skills': matching_skills,
                'missing_skills': get_missing_skills(job_info['skills'], user_skills_list)
            })
    
    # Sort by match percentage
    matches.sort(key=lambda x: x['match_percentage'], reverse=True)
    
    return format_job_matches(matches)

def get_missing_skills(job_skills, user_skills):
    """Get skills that are missing for a job"""
    missing = []
    for category in job_skills:
        for skill in TECH_SKILLS.get(category, []):
            if skill not in user_skills:
                missing.append(skill)
    return missing[:5]  # Return top 5 missing skills

def generate_improved_sections(cv_text):
    """Generate improved CV sections"""
    improvements = []
    
    # Check if CV has a professional summary
    if not re.search(r'(summary|profile|objective|about)', cv_text.lower()):
        improvements.append({
            'section': 'Professional Summary',
            'content': 'Add a compelling 2-3 sentence summary highlighting your key strengths and career objectives.'
        })
    
    # Check for quantified achievements
    if not re.search(r'\d+%|\d+\+|\$\d+|\d+x', cv_text):
        improvements.append({
            'section': 'Quantified Achievements',
            'content': 'Include specific numbers and metrics to demonstrate your impact (e.g., "Improved efficiency by 25%", "Managed team of 5 developers").'
        })
    
    # Check for action verbs
    action_verbs = ['developed', 'created', 'implemented', 'managed', 'led', 'designed', 'built', 'optimized']
    if not any(verb in cv_text.lower() for verb in action_verbs):
        improvements.append({
            'section': 'Action-Oriented Language',
            'content': 'Use strong action verbs to describe your accomplishments (e.g., "Developed", "Implemented", "Led", "Optimized").'
        })
    
    return improvements

def format_analysis_result(analysis):
    """Format the CV analysis result for display"""
    result = "<div class='analysis-result'>"
    result += "<h3>📊 CV Analysis Report</h3>"
    
    if analysis['strengths']:
        result += "<div class='strengths'><h4>✅ Strengths:</h4><ul>"
        for strength in analysis['strengths']:
            result += f"<li>{strength}</li>"
        result += "</ul></div>"
    
    if analysis['weaknesses']:
        result += "<div class='weaknesses'><h4>⚠️ Areas for Improvement:</h4><ul>"
        for weakness in analysis['weaknesses']:
            result += f"<li>{weakness}</li>"
        result += "</ul></div>"
    
    if analysis['suggestions']:
        result += "<div class='suggestions'><h4>💡 Recommendations:</h4><ul>"
        for suggestion in analysis['suggestions']:
            result += f"<li>{suggestion}</li>"
        result += "</ul></div>"
    
    if analysis['improved_sections']:
        result += "<div class='improvements'><h4>🔧 Suggested Improvements:</h4>"
        for improvement in analysis['improved_sections']:
            result += f"<div class='improvement-item'><strong>{improvement['section']}:</strong> {improvement['content']}</div>"
        result += "</div>"
    
    result += "</div>"
    return result

def format_skills_assessment(assessment):
    """Format the skills assessment result for display"""
    result = "<div class='skills-assessment'>"
    result += "<h3>🎯 Skills Assessment Report</h3>"
    
    result += "<div class='current-skills'><h4>Your Current Skills:</h4><ul>"
    for skill in assessment['current_skills']:
        result += f"<li>{skill}</li>"
    result += "</ul></div>"
    
    if assessment['recommendations']:
        result += "<div class='recommendations'><h4>📈 Recommendations:</h4><ul>"
        for rec in assessment['recommendations']:
            result += f"<li>{rec}</li>"
        result += "</ul></div>"
    
    if assessment['learning_path']:
        result += "<div class='learning-path'><h4>📚 Learning Path:</h4><ol>"
        for step in assessment['learning_path']:
            result += f"<li>{step}</li>"
        result += "</ol></div>"
    
    if assessment['job_matches']:
        result += "<div class='job-matches'><h4>💼 Job Matches:</h4>"
        for match in assessment['job_matches']:
            result += f"<div class='job-match'><strong>{match['title']}</strong> - {match['match_percentage']}% match<br>"
            result += f"<small>Matching skills: {', '.join(match['matching_skills'])}</small></div>"
        result += "</div>"
    
    result += "</div>"
    return result

def format_job_matches(matches):
    """Format the job matches result for display"""
    result = "<div class='job-matches'>"
    result += "<h3>🎯 Job Matching Results</h3>"
    
    if not matches:
        result += "<p>No job matches found. Consider expanding your skill set.</p>"
    else:
        for match in matches:
            result += f"<div class='job-match'>"
            result += f"<h4>{match['title']} - {match['match_percentage']}% Match</h4>"
            result += f"<p>{match['description']}</p>"
            result += f"<p><strong>Your matching skills:</strong> {', '.join(match['matching_skills'])}</p>"
            if match['missing_skills']:
                result += f"<p><strong>Skills to develop:</strong> {', '.join(match['missing_skills'])}</p>"
            result += "</div>"
    
    result += "</div>"
    return result

# ---- RUN APP ----
if __name__ == '__main__':
    app.run(debug=True)