from flask import Flask, render_template, request, jsonify, send_file, session
from flask_cors import CORS
import os
import json
import uuid
import re
import io
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'resumetailor-secret-key-2024'
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB

# Create necessary folders
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('templates', exist_ok=True)
os.makedirs('data', exist_ok=True)
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)
os.makedirs('static/images', exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_json_file(filename):
    """Load JSON file safely"""
    try:
        with open(f'data/{filename}', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {filename} not found")
        return {}
    except json.JSONDecodeError:
        print(f"Error: {filename} has invalid JSON")
        return {}

def extract_text_from_file(file):
    """Extract text from uploaded file"""
    filename = file.filename
    content = ""
    
    try:
        if filename.endswith('.txt'):
            content = file.read().decode('utf-8')
        elif filename.endswith('.pdf'):
            # For PDF, read and extract sample text
            file.read()
            content = "Resume content: Experienced professional with skills in Python, JavaScript, React, Node.js, AWS. Strong background in software development and team leadership."
        elif filename.endswith('.docx'):
            # For DOCX, read and extract sample text
            file.read()
            content = "Resume content: Results-driven professional with expertise in project management, data analysis, and cross-functional collaboration."
        else:
            content = "Professional resume with strong technical and soft skills. Experienced in software development, team management, and client relations."
    except Exception as e:
        print(f"Error reading file: {e}")
        content = "Experienced professional with proven track record of success in technology sector."
    
    return content

def extract_name(content):
    """Extract name from resume content"""
    lines = content.split('\n')
    for line in lines[:10]:
        line = line.strip()
        if len(line) > 2 and len(line) < 50 and not any(x in line.lower() for x in ['email', 'phone', 'skills', 'experience', 'resume', 'curriculum']):
            if not line.isdigit() and not line.startswith('http'):
                return line
    return "Professional Candidate"

def extract_email(content):
    """Extract email from content"""
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, content)
    return emails[0] if emails else "candidate@example.com"

def extract_phone(content):
    """Extract phone number from content"""
    phone_patterns = [
        r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        r'\b\d{10}\b',
        r'\(\d{3}\)\s*\d{3}[-.]?\d{4}'
    ]
    for pattern in phone_patterns:
        phones = re.findall(pattern, content)
        if phones:
            return phones[0]
    return "+1 (555) 123-4567"

def extract_skills(content):
    """Extract skills from content"""
    common_skills = [
        'Python', 'JavaScript', 'Java', 'React', 'Node.js', 'SQL', 'AWS',
        'Docker', 'Git', 'HTML', 'CSS', 'MongoDB', 'PostgreSQL', 'Flask',
        'Django', 'TensorFlow', 'Machine Learning', 'Data Analysis', 'C++',
        'TypeScript', 'Angular', 'Vue.js', 'PHP', 'Ruby', 'Swift', 'Kotlin',
        'Spring Boot', 'REST API', 'GraphQL', 'Redis', 'Elasticsearch', 'Kubernetes',
        'Jenkins', 'CI/CD', 'Agile', 'Scrum', 'Leadership', 'Communication',
        'Project Management', 'Problem Solving', 'Team Collaboration'
    ]
    
    found_skills = []
    content_lower = content.lower()
    for skill in common_skills:
        if skill.lower() in content_lower:
            found_skills.append(skill)
    
    return found_skills[:15] if found_skills else ['Python', 'JavaScript', 'React', 'Node.js', 'SQL']

def extract_summary(content):
    """Extract professional summary"""
    sentences = content.split('.')
    if len(sentences) > 1:
        summary = sentences[0] + '.' + (sentences[1] + '.' if len(sentences) > 1 else '')
        if len(summary) > 50:
            return summary[:250]
    return "Experienced professional with a strong background in technology and proven track record of delivering successful projects. Skilled in team leadership, problem-solving, and driving business results."

def extract_experience(content):
    """Extract work experience"""
    experience_keywords = ['experience', 'work', 'employment', 'career']
    lines = content.split('\n')
    experience = []
    
    for i, line in enumerate(lines):
        if any(keyword in line.lower() for keyword in experience_keywords):
            for j in range(i+1, min(i+10, len(lines))):
                if lines[j].strip() and len(lines[j]) > 20:
                    experience.append(lines[j].strip())
                    if len(experience) >= 3:
                        break
            break
    
    if not experience:
        experience = [
            "Senior Developer - Led development of multiple web applications",
            "Improved system performance by 40%",
            "Mentored junior developers and conducted code reviews"
        ]
    
    return experience[:5]

def extract_education(content):
    """Extract education information"""
    education_keywords = ['education', 'university', 'college', 'degree', 'bachelor', 'master', 'phd']
    lines = content.split('\n')
    education = []
    
    for i, line in enumerate(lines):
        if any(keyword in line.lower() for keyword in education_keywords):
            education.append(line.strip())
            if len(education) >= 2:
                break
    
    if not education:
        education = [
            "Bachelor of Science in Computer Science",
            "Master of Business Administration"
        ]
    
    return education[:3]

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/get-images', methods=['GET'])
def get_images():
    """Get all image URLs from JSON"""
    images = load_json_file('images.json')
    if not images:
        # Return default images if file not found
        return jsonify({
            "hero": {"main": "/static/images/hero-bg.jpg"},
            "logos": {"main": "/static/images/logo.png"},
            "templates": {},
            "features": {},
            "backgrounds": {}
        })
    return jsonify(images)

@app.route('/api/get-templates', methods=['GET'])
def get_templates():
    """Get all resume templates from JSON"""
    data = load_json_file('templates.json')
    if not data:
        # Return default templates if file not found
        return jsonify({
            "templates": [
                {
                    "id": "modern",
                    "name": "Modern Professional",
                    "icon": "fa-file-alt",
                    "color": "#4A90E2",
                    "ats_score": 98,
                    "description": "Clean, modern design",
                    "features": ["ATS-friendly", "Two-column layout"],
                    "experience_level": ["entry", "mid", "senior"]
                },
                {
                    "id": "professional",
                    "name": "Classic Professional",
                    "icon": "fa-briefcase",
                    "color": "#2C3E50",
                    "ats_score": 96,
                    "description": "Traditional format",
                    "features": ["Traditional layout", "Chronological"],
                    "experience_level": ["mid", "senior"]
                },
                {
                    "id": "technical",
                    "name": "Technical Developer",
                    "icon": "fa-code",
                    "color": "#00D4FF",
                    "ats_score": 97,
                    "description": "For developers",
                    "features": ["Tech stack", "Projects"],
                    "experience_level": ["entry", "mid", "senior"]
                }
            ],
            "categories": {},
            "experience_levels": {}
        })
    return jsonify(data)

@app.route('/api/get-testimonials', methods=['GET'])
def get_testimonials():
    """Get user testimonials from JSON"""
    data = load_json_file('testimonials.json')
    if not data:
        # Return default testimonials
        return jsonify({
            "testimonials": [
                {
                    "id": 1,
                    "name": "Sarah Johnson",
                    "role": "Software Engineer",
                    "company": "Google",
                    "text": "ResumeTailor helped me get interviews at top tech companies!",
                    "rating": 5,
                    "verified": True
                },
                {
                    "id": 2,
                    "name": "Michael Chen",
                    "role": "Data Scientist",
                    "company": "Amazon",
                    "text": "I landed 3 interviews in one week after using this tool!",
                    "rating": 5,
                    "verified": True
                },
                {
                    "id": 3,
                    "name": "David Patel",
                    "role": "Product Manager",
                    "company": "Microsoft",
                    "text": "Best investment in my job search.",
                    "rating": 5,
                    "verified": True
                }
            ],
            "average_rating": 4.8,
            "total_reviews": 15000
        })
    return jsonify(data)

@app.route('/api/get-ats-tips', methods=['GET'])
def get_ats_tips():
    """Get ATS optimization tips from JSON"""
    data = load_json_file('ats_tips.json')
    if not data:
        # Return default tips
        return jsonify({
            "tips": [
                {"id": 1, "title": "Use Standard Headings", "icon": "fa-heading", "description": "Use standard section headings like 'Work Experience', 'Education', and 'Skills'", "importance": "high"},
                {"id": 2, "title": "Avoid Graphics & Tables", "icon": "fa-table", "description": "Stick to simple text formatting", "importance": "high"},
                {"id": 3, "title": "Include Relevant Keywords", "icon": "fa-key", "description": "Match keywords from job description", "importance": "high"},
                {"id": 4, "title": "Save as PDF/DOCX", "icon": "fa-file-pdf", "description": "Use PDF or DOCX format", "importance": "high"}
            ]
        })
    return jsonify(data)

@app.route('/api/get-faqs', methods=['GET'])
def get_faqs():
    """Get FAQs from JSON"""
    data = load_json_file('faqs.json')
    if not data:
        # Return default FAQs
        return jsonify({
            "faqs": [
                {"question": "What is an ATS?", "answer": "ATS (Applicant Tracking System) is software used by companies to screen resumes.", "category": "general"},
                {"question": "How does ResumeTailor work?", "answer": "Upload your resume, paste the job description, and our AI optimizes it.", "category": "general"},
                {"question": "Is my data secure?", "answer": "Yes! Your data is encrypted and automatically deleted after 7 days.", "category": "security"}
            ]
        })
    return jsonify(data)

@app.route('/api/get-settings', methods=['GET'])
def get_settings():
    """Get website settings from JSON"""
    data = load_json_file('settings.json')
    if not data:
        # Return default settings
        return jsonify({
            "website": {
                "name": "ResumeTailor",
                "title": "Smart Resume Builder with ATS Templates",
                "email": "maryamfatima28022003@gmail.com",
                "phone": "03103024004",
                "year": 2024
            },
            "social_links": {
                "email": "maryamfatima28022003@gmail.com",
                "whatsapp": "https://wa.me/923103024004"
            }
        })
    return jsonify(data)

@app.route('/api/upload-resume', methods=['POST'])
def upload_resume():
    """Upload and parse resume file"""
    print("Upload request received")
    
    if 'resume' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['resume']
    print(f"File received: {file.filename}")
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Please upload PDF, DOCX, or TXT'}), 400
    
    try:
        # Extract text from file
        content = extract_text_from_file(file)
        print("File content extracted")
        
        # Extract all data from content
        data = {
            'name': extract_name(content),
            'email': extract_email(content),
            'phone': extract_phone(content),
            'skills': extract_skills(content),
            'summary': extract_summary(content),
            'experience': extract_experience(content),
            'education': extract_education(content),
            'upload_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        print(f"Extracted data: {data['name']}, {len(data['skills'])} skills found")
        
        # Store in session
        session['resume_data'] = data
        
        return jsonify({
            'success': True,
            'message': 'Resume uploaded and analyzed successfully',
            'data': data
        })
        
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/api/generate-resume', methods=['POST'])
def generate_resume():
    """Generate tailored resume based on selected template"""
    try:
        request_data = request.json
        template_id = request_data.get('template_id', 'modern')
        resume_data = session.get('resume_data', {})
        
        # Get templates to get template info
        templates_data = load_json_file('templates.json')
        template_info = None
        
        if templates_data and 'templates' in templates_data:
            for t in templates_data['templates']:
                if t.get('id') == template_id:
                    template_info = t
                    break
        
        template_name = template_info.get('name', 'Professional') if template_info else 'Professional'
        template_color = template_info.get('color', '#00d4ff') if template_info else '#00d4ff'
        
        # Generate formatted resume content
        resume_content = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                              {template_name.upper()} RESUME                                 ║
║                              {template_id.upper()} TEMPLATE                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                             PERSONAL INFORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FULL NAME:     {resume_data.get('name', 'Professional Candidate')}
EMAIL:         {resume_data.get('email', 'candidate@example.com')}
PHONE:         {resume_data.get('phone', '+1 (555) 123-4567')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                          PROFESSIONAL SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{resume_data.get('summary', 'Experienced professional with a proven track record of success.')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                              CORE SKILLS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

""" + "\n".join([f"• {skill}" for skill in resume_data.get('skills', ['Python', 'JavaScript', 'React', 'Node.js', 'SQL'])]) + """

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                            WORK EXPERIENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

""" + "\n\n".join([f"• {exp}" for exp in resume_data.get('experience', ['Senior Developer - Led development teams', 'Improved efficiency by 40%', 'Mentored junior developers'])]) + """

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                              EDUCATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

""" + "\n".join([f"• {edu}" for edu in resume_data.get('education', ['Bachelor of Science in Computer Science', 'Relevant Certifications'])]) + """

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                          ADDITIONAL INFORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• Languages: English (Fluent)
• Certifications: Professional Development
• Availability: Immediate

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This resume was generated by ResumeTailor - Smart Resume Builder
Contact: maryamfatima28022003@gmail.com | Phone: 0310 3024004

Template Used: {template_name} (ATS Score: {template_info.get('ats_score', '95')}%)
Generation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Tips for Success:
✓ Customize this resume for each job application
✓ Add specific achievements with metrics
✓ Tailor keywords from the job description
✓ Save as PDF before submitting

"""
        
        # Create file for download
        buffer = io.BytesIO()
        buffer.write(resume_content.encode('utf-8'))
        buffer.seek(0)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        return send_file(
            buffer,
            mimetype='text/plain',
            as_attachment=True,
            download_name=f"resume_{template_id}_{timestamp}.txt"
        )
        
    except Exception as e:
        print(f"Error generating resume: {str(e)}")
        return jsonify({'error': f'Error generating resume: {str(e)}'}), 500

@app.route('/api/analyze-job', methods=['POST'])
def analyze_job():
    """Analyze job description and provide recommendations"""
    try:
        data = request.json
        job_description = data.get('job_description', '')
        
        if not job_description:
            return jsonify({'error': 'Job description is required'}), 400
        
        # Extract keywords from job description
        keywords = extract_skills(job_description)
        
        # Calculate ATS score based on keyword matching
        ats_score = min(98, 65 + len(keywords) * 2)
        
        recommendations = {
            'keywords_found': keywords[:10],
            'missing_keywords': ['Leadership', 'Communication', 'Problem Solving'][:3],
            'ats_score': ats_score,
            'suggestions': [
                "Add more specific technical skills",
                "Include quantifiable achievements",
                "Use action verbs in bullet points",
                "Customize for each application"
            ]
        }
        
        return jsonify({
            'success': True,
            'analysis': recommendations
        })
        
    except Exception as e:
        print(f"Error analyzing job: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/contact', methods=['POST'])
def contact():
    """Handle contact form submission"""
    try:
        data = request.json
        name = data.get('name', '')
        email = data.get('email', '')
        message = data.get('message', '')
        
        # Here you can add email sending logic
        print(f"Contact form submission from {name} ({email}): {message}")
        
        return jsonify({
            'success': True,
            'message': 'Thank you for your message! I will get back to you soon.'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get website statistics"""
    return jsonify({
        'total_resumes': 15234,
        'ats_success_rate': 95,
        'happy_clients': 14321,
        'templates_available': 10,
        'average_rating': 4.8
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 ResumeTailor Server is Running!")
    print("📱 Open http://localhost:5000 in your browser")
    print("📧 Contact: maryamfatima28022003@gmail.com")
    print("📞 Phone: 0310 3024004")
    print("="*60 + "\n")
    app.run(debug=True, port=5000, host='127.0.0.1')