// ----------------------------------------
// CareerHub - JavaScript for UX/UI & logic
// ----------------------------------------

// This code runs after the page loads
document.addEventListener('DOMContentLoaded', function() {
    // Set up smart validation for all forms (Analyze, Skill, etc)
    initializeFormValidation();
    // Enhance skills/analysis UX
    initializeSkillsAssessment(); // Live skill counting/checks
    initializeJobMatching();      // Suggests/auto-tags Job Matching input
    initializeCVAnalysis();       // Tips/counter for CV textarea
    initializeAnimations();       // Fade-in/results/processing effect
    initializeFileValidation();   // Only allow valid files (PDF/DOCX)
    initializeFabUpload();        // Attach plus (+) upload button & sub-options
});

// Handles all form validation flow, especially the Analyze My CV button
function initializeFormValidation() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        // Special handling for the Analyze form (CV upload)
        if (form.getAttribute('action') === '/analyze') {
            const cvTextarea = form.querySelector('textarea[name="cv_text"]');
            const cvFile = form.querySelector('#cv_file');
            // Keep the required attribute ONLY if both textarea and file are empty
            function syncRequired() {
                const hasText = cvTextarea.value.trim().length > 0;
                const hasFile = cvFile && cvFile.files && cvFile.files.length > 0;
                if (hasText || hasFile) {
                    cvTextarea.removeAttribute('required');
                } else {
                    cvTextarea.setAttribute('required', '');
                }
            }
            // As user types or uploads, adjust required attribute so browser validation behaves naturally
            cvTextarea.addEventListener('input', syncRequired);
            cvFile.addEventListener('change', syncRequired);
            // On submit, one last check so HTML5 validation only triggers if both are blank
            form.addEventListener('submit', function() { syncRequired(); });
        }

        form.addEventListener('submit', function(e) {
            const ok = validateForm(this);
            if (!ok) {
                // For non-analyze forms, prevent and show our inline errors
                if (this.getAttribute('action') !== '/analyze') {
                    e.preventDefault();
                }
                // For analyze, do not prevent; the required attribute on textarea
                // will let the browser show the native tooltip
            }
        });
    });
}

function validateForm(form) {
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            showFieldError(field, 'This field is required');
            isValid = false;
        } else {
            clearFieldError(field);
        }
    });

    // Analyze form requires either text OR file
    if (form.getAttribute('action') === '/analyze') {
        const cvTextarea = form.querySelector('textarea[name="cv_text"]');
        const cvText = cvTextarea.value.trim();
        const cvFile = form.querySelector('#cv_file');
        const hasFile = cvFile && cvFile.files && cvFile.files.length > 0;
        const hasText = cvText.length > 0;
        if (!hasFile && !hasText) {
            cvTextarea.setAttribute('required', '');
            // no inline error message; rely on native bubble
            isValid = false;
        } else {
            cvTextarea.removeAttribute('required');
        }
    }
    
    return isValid;
}

function showFieldError(field, message) {
    clearFieldError(field);
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'field-error';
    errorDiv.textContent = message;
    errorDiv.style.color = '#e74c3c';
    errorDiv.style.fontSize = '0.9rem';
    errorDiv.style.marginTop = '0.25rem';
    
    field.parentNode.appendChild(errorDiv);
    field.style.borderColor = '#e74c3c';
}

function clearFieldError(field) {
    const existingError = field.parentNode.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
    field.style.borderColor = '';
}

// Skills Assessment Enhancement
function initializeSkillsAssessment() {
    const skillCheckboxes = document.querySelectorAll('input[name="skills"]');
    const skillsForm = document.querySelector('form[action="/skills"]');
    
    if (skillsForm) {
        skillsForm.addEventListener('submit', function(e) {
            const checkedSkills = document.querySelectorAll('input[name="skills"]:checked');
            if (checkedSkills.length === 0) {
                e.preventDefault();
                showNotification('Please select at least one skill for assessment', 'error');
            }
        });
    }
    
    // Add skill selection counter
    skillCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateSkillCounter);
    });
    
    updateSkillCounter();
}

function updateSkillCounter() {
    const checkedSkills = document.querySelectorAll('input[name="skills"]:checked');
    const counter = document.querySelector('.skill-counter') || createSkillCounter();
    counter.textContent = `${checkedSkills.length} skills selected`;
}

function createSkillCounter() {
    const counter = document.createElement('div');
    counter.className = 'skill-counter';
    counter.style.cssText = `
        text-align: center;
        margin: 1rem 0;
        padding: 0.5rem;
        background: #e8f4fd;
        border-radius: 4px;
        color: #2c3e50;
        font-weight: 600;
    `;
    
    const skillsForm = document.querySelector('form[action="/skills"]');
    if (skillsForm) {
        skillsForm.insertBefore(counter, skillsForm.querySelector('button'));
    }
    
    return counter;
}

// Job Matching Enhancement
function initializeJobMatching() {
    const jobForm = document.querySelector('form[action="/match"]');
    const skillsInput = document.querySelector('input[name="user_skills"]');
    
    if (skillsInput) {
        // Add autocomplete suggestions
        skillsInput.addEventListener('input', function() {
            showSkillSuggestions(this.value);
        });
        
        // Add skill tags functionality
        skillsInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ',') {
                e.preventDefault();
                addSkillTag(this.value.trim());
                this.value = '';
            }
        });
    }
}

function showSkillSuggestions(input) {
    const suggestions = [
        'Python', 'JavaScript', 'Java', 'C++', 'C#', 'PHP', 'Ruby', 'Swift', 'Kotlin',
        'HTML', 'CSS', 'React', 'Angular', 'Vue.js', 'Node.js', 'Django', 'Flask',
        'MySQL', 'PostgreSQL', 'MongoDB', 'SQLite', 'Oracle',
        'Git', 'Docker', 'AWS', 'Azure', 'Linux', 'Windows', 'MacOS',
        'Communication', 'Teamwork', 'Problem Solving', 'Leadership', 'Time Management'
    ];
    
    const filtered = suggestions.filter(skill => 
        skill.toLowerCase().includes(input.toLowerCase()) && 
        !input.split(',').some(entered => entered.trim().toLowerCase() === skill.toLowerCase())
    );
    
    if (filtered.length > 0 && input.length > 1) {
        showSuggestionsDropdown(filtered, input);
    } else {
        hideSuggestionsDropdown();
    }
}

function showSuggestionsDropdown(suggestions, input) {
    hideSuggestionsDropdown();
    
    const dropdown = document.createElement('div');
    dropdown.className = 'suggestions-dropdown';
    dropdown.style.cssText = `
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: white;
        border: 1px solid #ddd;
        border-radius: 4px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        z-index: 1000;
        max-height: 200px;
        overflow-y: auto;
    `;
    
    suggestions.slice(0, 5).forEach(skill => {
        const item = document.createElement('div');
        item.textContent = skill;
        item.style.cssText = `
            padding: 0.5rem;
            cursor: pointer;
            border-bottom: 1px solid #f0f0f0;
        `;
        item.addEventListener('mouseenter', function() {
            this.style.backgroundColor = '#f8f9fa';
        });
        item.addEventListener('mouseleave', function() {
            this.style.backgroundColor = 'white';
        });
        item.addEventListener('click', function() {
            addSkillTag(skill);
            input.value = '';
            hideSuggestionsDropdown();
        });
        dropdown.appendChild(item);
    });
    
    input.parentNode.style.position = 'relative';
    input.parentNode.appendChild(dropdown);
}

function hideSuggestionsDropdown() {
    const existing = document.querySelector('.suggestions-dropdown');
    if (existing) {
        existing.remove();
    }
}

function addSkillTag(skill) {
    if (!skill) return;
    
    const container = document.querySelector('.skill-tags-container') || createSkillTagsContainer();
    const tag = document.createElement('span');
    tag.className = 'skill-tag';
    tag.textContent = skill;
    tag.style.cssText = `
        display: inline-block;
        background: #3498db;
        color: white;
        padding: 0.25rem 0.5rem;
        margin: 0.25rem;
        border-radius: 4px;
        font-size: 0.9rem;
    `;
    
    const removeBtn = document.createElement('span');
    removeBtn.innerHTML = ' ×';
    removeBtn.style.cursor = 'pointer';
    removeBtn.addEventListener('click', function() {
        tag.remove();
        updateSkillsInput();
    });
    
    tag.appendChild(removeBtn);
    container.appendChild(tag);
    updateSkillsInput();
}

function createSkillTagsContainer() {
    const container = document.createElement('div');
    container.className = 'skill-tags-container';
    container.style.cssText = `
        margin-top: 0.5rem;
        min-height: 2rem;
        border: 1px dashed #ddd;
        border-radius: 4px;
        padding: 0.5rem;
    `;
    
    const skillsInput = document.querySelector('input[name="user_skills"]');
    skillsInput.parentNode.insertBefore(container, skillsInput);
    
    return container;
}

function updateSkillsInput() {
    const tags = document.querySelectorAll('.skill-tag');
    const skills = Array.from(tags).map(tag => tag.textContent.replace(' ×', ''));
    const skillsInput = document.querySelector('input[name="user_skills"]');
    skillsInput.value = skills.join(', ');
}

// CV Analysis Enhancement
function initializeCVAnalysis() {
    const cvTextarea = document.querySelector('textarea[name="cv_text"]');
    
    if (cvTextarea) {
        // Add character counter
        const counter = document.createElement('div');
        counter.className = 'char-counter';
        counter.style.cssText = `
            text-align: right;
            margin-top: 0.25rem;
            font-size: 0.9rem;
            color: #7f8c8d;
        `;
        cvTextarea.parentNode.appendChild(counter);
        
        cvTextarea.addEventListener('input', function() {
            const length = this.value.length;
            counter.textContent = `${length} characters`;
            
            if (length < 50) {
                counter.style.color = '#e74c3c';
            } else if (length < 200) {
                counter.style.color = '#f39c12';
            } else {
                counter.style.color = '#27ae60';
            }
        });
        
        // Add CV tips
        showCVTips();
    }
}

// File validation for CV upload
function initializeFileValidation() {
    const fileInput = document.getElementById('cv_file');
    if (!fileInput) return;

    fileInput.addEventListener('change', function() {
        const file = this.files && this.files[0];
        if (!file) return;
        const nameAllowed = file.name.toLowerCase().endsWith('.pdf') || file.name.toLowerCase().endsWith('.docx');
        if (!nameAllowed) {
            showNotification('Only PDF or DOCX files are accepted.', 'error');
            this.value = '';
            return;
        }
        if (file.size > 8 * 1024 * 1024) { // 8 MB limit
            showNotification('File is too large (max 8MB).', 'error');
            this.value = '';
            return;
        }
        showNotification('File selected: ' + file.name, 'success');
        const badge = document.getElementById('cv_file_badge');
        const nameEl = document.getElementById('cv_file_name');
        if (badge && nameEl) {
            nameEl.textContent = file.name;
            badge.style.display = 'inline-flex';
        }
        // auto-close the floating menu after selecting a file
        const wrapper = fileInput.closest('.cv-input-wrapper');
        const fab = wrapper ? wrapper.querySelector('.fab-upload') : null;
        if (fab && fab.classList.contains('open')) {
            fab.classList.remove('open');
        }
    });
}

// Floating upload button logic
function initializeFabUpload() {
    const wrapper = document.querySelector('.cv-input-wrapper');
    const mainBtn = wrapper?.querySelector('.fab-main');
    const menu = wrapper?.querySelector('.fab-menu');
    const items = wrapper?.querySelectorAll('.fab-item');
    const fileInput = document.getElementById('cv_file');
    if (!wrapper || !mainBtn || !menu || !items || !fileInput) return;

    // Toggle menu
    mainBtn.addEventListener('click', function() {
        wrapper.querySelector('.fab-upload').classList.toggle('open');
    });

    // Handle selection (pdf or docx)
    items.forEach(btn => {
        btn.addEventListener('click', function() {
            const type = this.getAttribute('data-type');
            if (type === 'pdf') {
                fileInput.setAttribute('accept', '.pdf');
            } else if (type === 'docx') {
                fileInput.setAttribute('accept', '.docx');
            }
            // trigger file chooser
            fileInput.click();
        });
    });
}

// Remove/clear selected file from badge
document.addEventListener('click', function(e) {
    const removeBtn = e.target.closest('#cv_file_remove');
    if (!removeBtn) return;
    const fileInput = document.getElementById('cv_file');
    const badge = document.getElementById('cv_file_badge');
    const nameEl = document.getElementById('cv_file_name');
    if (fileInput) fileInput.value = '';
    if (nameEl) nameEl.textContent = '';
    if (badge) badge.style.display = 'none';
    showNotification('File removed. You can upload a different file.', 'info');
});

function showCVTips() {
    const tips = [
        'Include your contact information (email, phone)',
        'List your education and qualifications',
        'Highlight relevant work experience or projects',
        'Include technical skills and programming languages',
        'Use action verbs to describe your achievements',
        'Keep it concise but comprehensive'
    ];
    
    const tipsContainer = document.createElement('div');
    tipsContainer.className = 'cv-tips';
    tipsContainer.innerHTML = `
        <h4>💡 CV Tips:</h4>
        <ul>
            ${tips.map(tip => `<li>${tip}</li>`).join('')}
        </ul>
    `;
    tipsContainer.style.cssText = `
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 4px;
        margin-top: 1rem;
        font-size: 0.9rem;
    `;
    
    const cvForm = document.querySelector('form[action="/analyze"]');
    cvForm.appendChild(tipsContainer);
}

// Animations
function initializeAnimations() {
    // Add loading states to buttons
    const buttons = document.querySelectorAll('button[type="submit"]');
    
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            if (this.form.checkValidity()) {
                showLoadingState(this);
            }
        });
    });
    
    // Add fade-in animation to result containers
    const resultContainers = document.querySelectorAll('.result-container');
    resultContainers.forEach(container => {
        container.style.opacity = '0';
        container.style.transform = 'translateY(20px)';
        container.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        
        setTimeout(() => {
            container.style.opacity = '1';
            container.style.transform = 'translateY(0)';
        }, 100);
    });
}

function showLoadingState(button) {
    const originalText = button.innerHTML;
    button.innerHTML = '<span class="loading"></span> Processing...';
    button.disabled = true;
    
    // Re-enable after 3 seconds (in case of errors)
    setTimeout(() => {
        button.innerHTML = originalText;
        button.disabled = false;
    }, 3000);
}

// Notification System
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        border-radius: 4px;
        color: white;
        font-weight: 500;
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    
    const colors = {
        success: '#27ae60',
        error: '#e74c3c',
        warning: '#f39c12',
        info: '#3498db'
    };
    
    notification.style.backgroundColor = colors[type] || colors.info;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add CSS for animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    
    .field-error {
        animation: shake 0.5s ease;
    }
    
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-5px); }
        75% { transform: translateX(5px); }
    }
`;
document.head.appendChild(style);

// Utility Functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Export functions for potential external use
window.CareerHub = {
    showNotification,
    addSkillTag,
    validateForm
};