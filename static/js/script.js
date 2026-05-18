// Global variables
let selectedTemplate = null;
let resumeData = null;
let templatesData = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initPreloader();
    initNavigation();
    initScrollSpy();
    initFileUpload();
    loadTemplates();
    loadTestimonials();
    loadTips();
    initContactForm();
});

// Preloader
function initPreloader() {
    setTimeout(() => {
        const preloader = document.getElementById('preloader');
        if (preloader) {
            preloader.style.opacity = '0';
            setTimeout(() => {
                preloader.style.display = 'none';
            }, 500);
        }
    }, 1000);
}

// Navigation
function initNavigation() {
    const hamburger = document.querySelector('.hamburger');
    const navMenu = document.querySelector('.nav-menu');
    
    if (hamburger) {
        hamburger.addEventListener('click', () => {
            navMenu.classList.toggle('active');
            hamburger.classList.toggle('active');
        });
    }
    
    // Close mobile menu on link click
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', () => {
            navMenu.classList.remove('active');
        });
    });
    
    // Navbar scroll effect
    window.addEventListener('scroll', () => {
        const navbar = document.querySelector('.navbar');
        if (window.scrollY > 100) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });
}

// Scroll Spy
function initScrollSpy() {
    const sections = document.querySelectorAll('section');
    const navLinks = document.querySelectorAll('.nav-link');
    
    window.addEventListener('scroll', () => {
        let current = '';
        
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            if (scrollY >= sectionTop - 200) {
                current = section.getAttribute('id');
            }
        });
        
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${current}`) {
                link.classList.add('active');
            }
        });
    });
}

// File Upload
function initFileUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('resumeInput');
    
    if (!uploadArea || !fileInput) return;
    
    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });
    
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#00d4ff';
        uploadArea.style.background = 'rgba(0,212,255,0.05)';
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.borderColor = 'rgba(0,212,255,0.3)';
        uploadArea.style.background = 'transparent';
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = 'rgba(0,212,255,0.3)';
        uploadArea.style.background = 'transparent';
        
        const file = e.dataTransfer.files[0];
        if (file && (file.type === 'application/pdf' || 
                     file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' ||
                     file.type === 'text/plain')) {
            handleFileUpload(file);
        } else {
            showNotification('Please upload PDF, DOCX, or TXT file', 'error');
        }
    });
    
    fileInput.addEventListener('change', (e) => {
        if (e.target.files[0]) {
            handleFileUpload(e.target.files[0]);
        }
    });
}

// Handle file upload
async function handleFileUpload(file) {
    const formData = new FormData();
    formData.append('resume', file);
    
    const statusDiv = document.getElementById('uploadStatus');
    const fileNameDiv = document.getElementById('fileNameDisplay');
    
    statusDiv.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Uploading and analyzing...';
    statusDiv.style.color = '#00d4ff';
    
    try {
        const response = await fetch('/api/upload-resume', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            resumeData = data.data;
            fileNameDiv.innerHTML = `<i class="fas fa-check-circle"></i> ${file.name}`;
            statusDiv.innerHTML = '<i class="fas fa-check-circle"></i> Resume analyzed successfully!';
            statusDiv.style.color = '#4CAF50';
            displayExtractedData(data.data);
            
            // Enable generate button if template is selected
            document.getElementById('generateBtn').disabled = !selectedTemplate;
            
            setTimeout(() => {
                statusDiv.innerHTML = '';
            }, 3000);
        } else {
            statusDiv.innerHTML = '<i class="fas fa-exclamation-circle"></i> Error uploading file';
            statusDiv.style.color = '#f44336';
        }
    } catch (error) {
        console.error('Upload error:', error);
        statusDiv.innerHTML = '<i class="fas fa-exclamation-circle"></i> Network error. Please try again.';
        statusDiv.style.color = '#f44336';
    }
}

// Display extracted data
function displayExtractedData(data) {
    const container = document.getElementById('extractedData');
    container.innerHTML = `
        <div class="data-field">
            <span class="data-label"><i class="fas fa-user"></i> Name</span>
            <span>${data.name || 'Not detected'}</span>
        </div>
        <div class="data-field">
            <span class="data-label"><i class="fas fa-envelope"></i> Email</span>
            <span>${data.email || 'Not detected'}</span>
        </div>
        <div class="data-field">
            <span class="data-label"><i class="fas fa-phone"></i> Phone</span>
            <span>${data.phone || 'Not detected'}</span>
        </div>
        <div class="data-field">
            <span class="data-label"><i class="fas fa-code"></i> Detected Skills</span>
            <div class="skills-container">
                ${data.skills && data.skills.length > 0 
                    ? data.skills.map(s => `<span class="skill-badge">${s}</span>`).join('') 
                    : '<span>No skills detected</span>'}
            </div>
        </div>
        <div class="data-field">
            <span class="data-label"><i class="fas fa-align-left"></i> Summary</span>
            <span>${data.summary || 'Not detected'}</span>
        </div>
    `;
}

// Load templates from JSON
async function loadTemplates() {
    try {
        const response = await fetch('/api/get-templates');
        const data = await response.json();
        templatesData = data.templates;
        displayTemplates(data.templates);
    } catch (error) {
        console.error('Error loading templates:', error);
        displayFallbackTemplates();
    }
}

// Display templates
function displayTemplates(templates) {
    const grid = document.getElementById('templatesGrid');
    if (!grid) return;
    
    grid.innerHTML = templates.map(template => `
        <div class="template-card" data-category="${template.experience_level.join(' ')}" data-id="${template.id}" onclick="selectTemplate('${template.id}')">
            <div class="template-preview">
                <i class="fas ${template.icon}" style="font-size: 4rem; color: ${template.color}"></i>
                <div class="ats-score">ATS: ${template.ats_score}%</div>
            </div>
            <div class="template-info">
                <div class="template-name">${template.name}</div>
                <p>${template.description}</p>
                <div class="template-features">
                    ${template.features.slice(0, 3).map(f => `<span class="feature-tag">${f}</span>`).join('')}
                </div>
            </div>
        </div>
    `).join('');
}

// Select template
function selectTemplate(templateId) {
    selectedTemplate = templateId;
    
    document.querySelectorAll('.template-card').forEach(card => {
        card.classList.remove('selected');
        if (card.dataset.id === templateId) {
            card.classList.add('selected');
            card.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    });
    
    document.getElementById('generateBtn').disabled = !resumeData;
    showNotification(`"${getTemplateName(templateId)}" template selected!`, 'success');
}

// Get template name
function getTemplateName(templateId) {
    if (!templatesData) return 'Template';
    const template = templatesData.find(t => t.id === templateId);
    return template ? template.name : 'Template';
}

// Filter templates
document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        const filter = btn.dataset.filter;
        const cards = document.querySelectorAll('.template-card');
        
        cards.forEach(card => {
            if (filter === 'all') {
                card.style.display = 'block';
            } else if (card.dataset.category.includes(filter)) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    });
});

// Generate resume
async function generateResume() {
    if (!selectedTemplate) {
        showNotification('Please select a template first!', 'error');
        return;
    }
    
    if (!resumeData) {
        showNotification('Please upload your resume first!', 'error');
        return;
    }
    
    const generateBtn = document.getElementById('generateBtn');
    const originalText = generateBtn.innerHTML;
    generateBtn.disabled = true;
    generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
    
    try {
        const response = await fetch('/api/generate-resume', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                template_id: selectedTemplate,
                resume_data: resumeData
            })
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `resume_${selectedTemplate}_${new Date().getTime()}.pdf`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            showNotification('Resume generated and downloaded successfully!', 'success');
        } else {
            throw new Error('Generation failed');
        }
    } catch (error) {
        console.error('Generation error:', error);
        showNotification('Error generating resume. Please try again.', 'error');
    } finally {
        generateBtn.disabled = false;
        generateBtn.innerHTML = originalText;
    }
}

// Load testimonials
function loadTestimonials() {
    const testimonials = [
        {
            name: "Sarah Johnson",
            role: "Software Engineer at Google",
            text: "ResumeTailor helped me get interviews at top tech companies! The ATS score feature is a game-changer.",
            rating: 5
        },
        {
            name: "Michael Chen",
            role: "Data Scientist at Amazon",
            text: "I landed 3 interviews in one week after using this tool. The keyword matching is incredibly accurate!",
            rating: 5
        },
        {
            name: "David Patel",
            role: "Product Manager at Microsoft",
            text: "Best investment in my job search. Saved hours of manual resume tailoring work.",
            rating: 5
        }
    ];
    
    const grid = document.getElementById('testimonialsGrid');
    if (!grid) return;
    
    grid.innerHTML = testimonials.map(t => `
        <div class="testimonial-card">
            <i class="fas fa-quote-left"></i>
            <p>${t.text}</p>
            <div class="testimonial-author">
                <div class="testimonial-avatar">
                    <i class="fas fa-user"></i>
                </div>
                <div>
                    <strong>${t.name}</strong><br>
                    <small style="color: var(--primary);">${t.role}</small>
                </div>
            </div>
        </div>
    `).join('');
}

// Load ATS tips
function loadTips() {
    const tips = [
        {
            icon: "fa-heading",
            title: "Use Standard Headings",
            description: "Use 'Work Experience', 'Education', 'Skills' - ATS systems recognize these"
        },
        {
            icon: "fa-table",
            title: "Avoid Graphics & Tables",
            description: "Stick to simple text formatting for better ATS parsing"
        },
        {
            icon: "fa-key",
            title: "Include Keywords",
            description: "Match keywords from job description exactly"
        },
        {
            icon: "fa-file-pdf",
            title: "Save as PDF/DOCX",
            description: "These formats preserve formatting and are ATS-friendly"
        }
    ];
    
    const grid = document.getElementById('tipsGrid');
    if (!grid) return;
    
    grid.innerHTML = tips.map(tip => `
        <div class="tip-card">
            <div class="tip-icon"><i class="fas ${tip.icon}"></i></div>
            <h4>${tip.title}</h4>
            <p>${tip.description}</p>
        </div>
    `).join('');
}

// Contact form
function initContactForm() {
    const form = document.getElementById('contactForm');
    if (!form) return;
    
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        const name = document.getElementById('contactName').value;
        showNotification(`Thank you ${name}! I'll get back to you soon.`, 'success');
        form.reset();
    });
}

// Show notification
function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Scroll functions
function scrollToBuilder() {
    document.getElementById('builder').scrollIntoView({ behavior: 'smooth' });
}

function scrollToTemplates() {
    document.getElementById('templates').scrollIntoView({ behavior: 'smooth' });
}

// Fallback templates
function displayFallbackTemplates() {
    const fallbackTemplates = [
        { id: 'modern', name: 'Modern Professional', icon: 'fa-file-alt', color: '#4A90E2', ats_score: 98, description: 'Clean, modern design', features: ['ATS-friendly', 'Two-column'] },
        { id: 'professional', name: 'Classic Professional', icon: 'fa-briefcase', color: '#2C3E50', ats_score: 96, description: 'Traditional format', features: ['Corporate', 'Chronological'] },
        { id: 'technical', name: 'Technical Developer', icon: 'fa-code', color: '#00D4FF', ats_score: 97, description: 'For developers', features: ['Tech stack', 'Projects'] }
    ];
    
    const grid = document.getElementById('templatesGrid');
    if (grid) {
        grid.innerHTML = fallbackTemplates.map(template => `
            <div class="template-card" data-id="${template.id}" onclick="selectTemplate('${template.id}')">
                <div class="template-preview">
                    <i class="fas ${template.icon}" style="font-size: 4rem; color: ${template.color}"></i>
                    <div class="ats-score">ATS: ${template.ats_score}%</div>
                </div>
                <div class="template-info">
                    <div class="template-name">${template.name}</div>
                    <p>${template.description}</p>
                    <div class="template-features">
                        ${template.features.map(f => `<span class="feature-tag">${f}</span>`).join('')}
                    </div>
                </div>
            </div>
        `).join('');
    }
}

// Add animation styles
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);