/**
 * SEO Patent Analysis Tool - Main JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize components
    initForms();
    initApiButtons();
    
    // Handle login form
    initLoginForm();
});

/**
 * Initialize form validation and submission
 */
function initForms() {
    // Find all forms that need validation
    const forms = document.querySelectorAll('form[data-validate]');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            // Check if form is valid
            if (!validateForm(form)) {
                event.preventDefault();
            }
        });
    });
    
    // Find all forms with AJAX submission
    const ajaxForms = document.querySelectorAll('form[data-ajax]');
    
    ajaxForms.forEach(form => {
        form.addEventListener('submit', function(event) {
            event.preventDefault();
            submitFormAsync(form);
        });
    });
}

/**
 * Validate form inputs
 */
function validateForm(form) {
    let isValid = true;
    
    // Find all required inputs
    const requiredInputs = form.querySelectorAll('[required]');
    
    requiredInputs.forEach(input => {
        // Remove previous error styles
        input.classList.remove('input-error');
        const errorEl = input.parentNode.querySelector('.error-message');
        if (errorEl) {
            errorEl.remove();
        }
        
        // Check if input is empty
        if (!input.value.trim()) {
            isValid = false;
            markInputAsError(input, 'This field is required');
        }
        
        // Check for minimum length
        if (input.getAttribute('minlength') && input.value.length < parseInt(input.getAttribute('minlength'))) {
            isValid = false;
            markInputAsError(input, `Minimum length is ${input.getAttribute('minlength')} characters`);
        }
    });
    
    return isValid;
}

/**
 * Mark an input as having an error
 */
function markInputAsError(input, message) {
    input.classList.add('input-error');
    
    // Add error message below the input
    const errorEl = document.createElement('div');
    errorEl.className = 'error-message';
    errorEl.textContent = message;
    errorEl.style.color = 'var(--danger-color)';
    errorEl.style.fontSize = '0.75rem';
    errorEl.style.marginTop = '0.25rem';
    
    input.parentNode.appendChild(errorEl);
}

/**
 * Submit form asynchronously with AJAX
 */
function submitFormAsync(form) {
    const url = form.getAttribute('action');
    const method = form.getAttribute('method') || 'POST';
    const formData = new FormData(form);
    
    // Show loading state
    form.classList.add('is-loading');
    const submitBtn = form.querySelector('[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner"></span> Submitting...';
    }
    
    // Determine content type and data format
    let contentType = 'application/x-www-form-urlencoded';
    let body = new URLSearchParams(formData).toString();
    
    if (form.getAttribute('data-json') === 'true') {
        contentType = 'application/json';
        const data = {};
        formData.forEach((value, key) => {
            data[key] = value;
        });
        body = JSON.stringify(data);
    }
    
    // Make the AJAX request
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': contentType
        },
        body: body
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        
        // Check if response is JSON
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return response.json();
        }
        
        return response.text();
    })
    .then(data => {
        // Reset loading state
        form.classList.remove('is-loading');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Submit';
        }
        
        // Handle successful submission
        handleFormSuccess(form, data);
    })
    .catch(error => {
        console.error('Error:', error);
        
        // Reset loading state
        form.classList.remove('is-loading');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Submit';
        }
        
        // Handle error
        handleFormError(form, error);
    });
}

/**
 * Handle successful form submission
 */
function handleFormSuccess(form, data) {
    // Show success message
    const successMessage = form.getAttribute('data-success-message') || 'Form submitted successfully!';
    
    // Create success alert
    const alertEl = document.createElement('div');
    alertEl.className = 'alert alert-success';
    alertEl.textContent = successMessage;
    
    // Insert alert before the form
    form.parentNode.insertBefore(alertEl, form);
    
    // Clear the form if needed
    if (form.getAttribute('data-reset') === 'true') {
        form.reset();
    }
    
    // Redirect if specified
    const redirect = form.getAttribute('data-redirect');
    if (redirect) {
        if (redirect === 'response' && typeof data === 'object' && data.redirect) {
            window.location.href = data.redirect;
        } else {
            window.location.href = redirect;
        }
    }
}

/**
 * Handle form submission error
 */
function handleFormError(form, error) {
    // Show error message
    const errorMessage = form.getAttribute('data-error-message') || 'There was an error submitting the form. Please try again.';
    
    // Create error alert
    const alertEl = document.createElement('div');
    alertEl.className = 'alert alert-danger';
    alertEl.textContent = errorMessage;
    
    // Insert alert before the form
    form.parentNode.insertBefore(alertEl, form);
}

/**
 * Initialize API data loading buttons
 */
function initApiButtons() {
    const apiButtons = document.querySelectorAll('[data-api]');
    
    apiButtons.forEach(button => {
        const apiUrl = button.getAttribute('data-api');
        const targetSelector = button.getAttribute('data-target');
        const autoload = button.getAttribute('data-autoload') === 'true';
        
        if (autoload) {
            loadApiData(apiUrl, targetSelector);
        } else {
            button.addEventListener('click', function() {
                loadApiData(apiUrl, targetSelector);
            });
        }
    });
}

/**
 * Load data from API endpoint
 */
function loadApiData(apiUrl, targetSelector) {
    const targetEl = document.querySelector(targetSelector);
    
    if (!targetEl) {
        console.error(`Target element ${targetSelector} not found`);
        return;
    }
    
    // Show loading state
    targetEl.innerHTML = '<div class="loading">Loading...</div>';
    
    fetch(apiUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Process and display the data
            displayApiData(data, targetEl, apiUrl);
        })
        .catch(error => {
            console.error('Error:', error);
            targetEl.innerHTML = '<div class="error-state">Error loading data. Please try again later.</div>';
        });
}

/**
 * Display API data in the target element
 */
function displayApiData(data, targetEl, apiUrl) {
    // Clear target element
    targetEl.innerHTML = '';
    
    // If no data or empty array
    if (!data || (Array.isArray(data) && data.length === 0)) {
        targetEl.innerHTML = '<div class="empty-state">No data available.</div>';
        return;
    }
    
    // Handle different data types based on the API URL
    if (apiUrl.includes('/patents')) {
        displayPatentsData(data, targetEl);
    } else if (apiUrl.includes('/projects')) {
        displayProjectsData(data, targetEl);
    } else {
        // Generic data display
        const pre = document.createElement('pre');
        pre.textContent = JSON.stringify(data, null, 2);
        targetEl.appendChild(pre);
    }
}

/**
 * Display patents data
 */
function displayPatentsData(patents, targetEl) {
    patents.forEach(patent => {
        const patentEl = document.createElement('div');
        patentEl.className = 'patent-card';
        
        patentEl.innerHTML = `
            <h4><a href="/patents/view/${patent.id}">${patent.title}</a></h4>
            <div class="patent-meta">
                <span class="patent-id">${patent.patent_id}</span>
                <span class="patent-date">Filed: ${patent.filing_date}</span>
            </div>
            <p>${patent.abstract.length > 150 ? patent.abstract.substring(0, 150) + '...' : patent.abstract}</p>
            <div class="patent-footer">
                <span class="patent-assignee">${patent.assignee}</span>
                <a href="/patents/view/${patent.id}" class="btn btn-text">View Details →</a>
            </div>
        `;
        
        targetEl.appendChild(patentEl);
    });
}

/**
 * Display projects data
 */
function displayProjectsData(projects, targetEl) {
    projects.forEach(project => {
        const projectEl = document.createElement('div');
        projectEl.className = 'list-item';
        
        projectEl.innerHTML = `
            <div class="list-item-content">
                <h4><a href="/projects/${project.id}">${project.name}</a></h4>
                <p>${project.description || 'No description'}</p>
            </div>
            <div class="list-item-action">
                <a href="/projects/${project.id}" class="btn btn-sm">View</a>
            </div>
        `;
        
        targetEl.appendChild(projectEl);
    });
}

/**
 * Initialize login form
 */
function initLoginForm() {
    const loginForm = document.getElementById('login-form');
    
    if (loginForm) {
        loginForm.addEventListener('submit', function(event) {
            // Validate login form
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            if (!username || !password) {
                event.preventDefault();
                document.getElementById('login-error').style.display = 'block';
                document.getElementById('login-error').textContent = 'Please enter both username and password.';
            }
        });
    }
}
