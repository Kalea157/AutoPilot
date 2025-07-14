// ===== CONTACT FORM HANDLING =====

class ContactForm {
    constructor() {
        this.form = document.getElementById('contact-form');
        this.submitBtn = this.form ? this.form.querySelector('button[type="submit"]') : null;
        this.isSubmitting = false;
        
        this.init();
    }
    
    init() {
        if (!this.form) return;
        
        this.setupEventListeners();
        this.setupFormValidation();
        this.setupAutoComplete();
    }
    
    setupEventListeners() {
        // Form submission
        this.form.addEventListener('submit', this.handleSubmit.bind(this));
        
        // Real-time validation
        const inputs = this.form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', this.validateField.bind(this, input));
            input.addEventListener('input', this.clearFieldError.bind(this, input));
        });
        
        // Service selection change
        const serviceSelect = document.getElementById('service');
        if (serviceSelect) {
            serviceSelect.addEventListener('change', this.handleServiceChange.bind(this));
        }
        
        // WhatsApp integration
        this.setupWhatsAppIntegration();
    }
    
    setupFormValidation() {
        // Custom validation rules
        this.validationRules = {
            name: {
                required: true,
                minLength: 2,
                maxLength: 50,
                pattern: /^[a-zA-ZäöüßÄÖÜ\s]+$/
            },
            email: {
                required: true,
                pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/
            },
            phone: {
                required: false,
                pattern: /^[\+]?[0-9\s\-\(\)]{10,}$/
            },
            service: {
                required: false
            },
            message: {
                required: true,
                minLength: 10,
                maxLength: 1000
            },
            privacy: {
                required: true
            }
        };
    }
    
    setupAutoComplete() {
        // Auto-fill from localStorage if available
        const savedData = localStorage.getItem('contactFormData');
        if (savedData) {
            try {
                const data = JSON.parse(savedData);
                Object.keys(data).forEach(key => {
                    const field = this.form.querySelector(`[name="${key}"]`);
                    if (field && field.type !== 'checkbox') {
                        field.value = data[key];
                    }
                });
            } catch (e) {
                console.log('Could not load saved form data');
            }
        }
        
        // Save form data as user types
        const inputs = this.form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            if (input.type !== 'checkbox') {
                input.addEventListener('input', this.saveFormData.bind(this));
            }
        });
    }
    
    saveFormData() {
        const formData = new FormData(this.form);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            if (key !== 'privacy') {
                data[key] = value;
            }
        }
        
        localStorage.setItem('contactFormData', JSON.stringify(data));
    }
    
    validateField(field) {
        const fieldName = field.name;
        const value = field.value.trim();
        const rules = this.validationRules[fieldName];
        
        if (!rules) return true;
        
        let isValid = true;
        let errorMessage = '';
        
        // Required validation
        if (rules.required && !value) {
            isValid = false;
            errorMessage = 'Dieses Feld ist erforderlich.';
        }
        
        // Pattern validation
        if (isValid && rules.pattern && value) {
            if (!rules.pattern.test(value)) {
                isValid = false;
                switch (fieldName) {
                    case 'email':
                        errorMessage = 'Bitte geben Sie eine gültige E-Mail-Adresse ein.';
                        break;
                    case 'phone':
                        errorMessage = 'Bitte geben Sie eine gültige Telefonnummer ein.';
                        break;
                    case 'name':
                        errorMessage = 'Bitte geben Sie nur Buchstaben ein.';
                        break;
                    default:
                        errorMessage = 'Bitte überprüfen Sie Ihre Eingabe.';
                }
            }
        }
        
        // Length validation
        if (isValid && value) {
            if (rules.minLength && value.length < rules.minLength) {
                isValid = false;
                errorMessage = `Mindestens ${rules.minLength} Zeichen erforderlich.`;
            } else if (rules.maxLength && value.length > rules.maxLength) {
                isValid = false;
                errorMessage = `Maximal ${rules.maxLength} Zeichen erlaubt.`;
            }
        }
        
        // Special validation for privacy checkbox
        if (fieldName === 'privacy' && rules.required) {
            const privacyCheckbox = this.form.querySelector('#privacy');
            if (!privacyCheckbox.checked) {
                isValid = false;
                errorMessage = 'Bitte akzeptieren Sie die Datenschutzerklärung.';
            }
        }
        
        // Show/hide error
        this.showFieldError(field, errorMessage);
        
        return isValid;
    }
    
    showFieldError(field, message) {
        // Remove existing error
        this.clearFieldError(field);
        
        if (message) {
            // Add error class
            field.classList.add('error');
            
            // Create error message element
            const errorElement = document.createElement('div');
            errorElement.className = 'field-error';
            errorElement.textContent = message;
            errorElement.style.cssText = `
                color: #ef4444;
                font-size: 0.875rem;
                margin-top: 0.25rem;
                display: block;
            `;
            
            // Insert after field
            field.parentNode.appendChild(errorElement);
        }
    }
    
    clearFieldError(field) {
        field.classList.remove('error');
        const errorElement = field.parentNode.querySelector('.field-error');
        if (errorElement) {
            errorElement.remove();
        }
    }
    
    validateForm() {
        const fields = this.form.querySelectorAll('input, select, textarea');
        let isValid = true;
        
        fields.forEach(field => {
            if (!this.validateField(field)) {
                isValid = false;
            }
        });
        
        return isValid;
    }
    
    async handleSubmit(e) {
        e.preventDefault();
        
        if (this.isSubmitting) return;
        
        // Validate form
        if (!this.validateForm()) {
            window.MainJS.showNotification('Bitte überprüfen Sie Ihre Eingaben.', 'error');
            return;
        }
        
        this.isSubmitting = true;
        this.setSubmitButtonState(true);
        
        try {
            // Get form data
            const formData = new FormData(this.form);
            const data = Object.fromEntries(formData);
            
            // Send form data
            const success = await this.sendFormData(data);
            
            if (success) {
                // Clear form and localStorage
                this.form.reset();
                localStorage.removeItem('contactFormData');
                
                // Show success message
                window.MainJS.showNotification('Ihre Nachricht wurde erfolgreich gesendet! Wir melden uns schnellstmöglich bei Ihnen.', 'success');
                
                // Track conversion (if analytics is available)
                this.trackConversion(data);
            } else {
                throw new Error('Sending failed');
            }
            
        } catch (error) {
            console.error('Form submission error:', error);
            window.MainJS.showNotification('Es gab einen Fehler beim Senden Ihrer Nachricht. Bitte versuchen Sie es erneut oder kontaktieren Sie uns direkt.', 'error');
        } finally {
            this.isSubmitting = false;
            this.setSubmitButtonState(false);
        }
    }
    
    async sendFormData(data) {
        // Multiple sending options
        const sendMethods = [
            this.sendViaEmail.bind(this),
            this.sendViaWhatsApp.bind(this),
            this.sendViaAPI.bind(this)
        ];
        
        for (const method of sendMethods) {
            try {
                const result = await method(data);
                if (result) return true;
            } catch (error) {
                console.log(`Method failed: ${method.name}`, error);
                continue;
            }
        }
        
        return false;
    }
    
    async sendViaEmail(data) {
        // Create email content
        const subject = `Neue Anfrage: ${data.service || 'Allgemeine Anfrage'}`;
        const body = `
Neue Kontaktanfrage von der Website:

Name: ${data.name}
E-Mail: ${data.email}
Telefon: ${data.phone || 'Nicht angegeben'}
Dienstleistung: ${data.service || 'Nicht angegeben'}

Nachricht:
${data.message}

---
Gesendet von: Münster Reinigung Website
Datum: ${new Date().toLocaleString('de-DE')}
        `.trim();
        
        // Try to send via mailto
        const mailtoLink = `mailto:info@muenster-reinigung.de?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
        
        // For demo purposes, we'll simulate success
        // In production, you might want to use a server-side solution
        return new Promise((resolve) => {
            setTimeout(() => {
                // Simulate email sending
                console.log('Email would be sent:', { subject, body });
                resolve(true);
            }, 1000);
        });
    }
    
    async sendViaWhatsApp(data) {
        // Create WhatsApp message
        const message = `
*Neue Anfrage von der Website*

👤 *Name:* ${data.name}
📧 *E-Mail:* ${data.email}
📞 *Telefon:* ${data.phone || 'Nicht angegeben'}
🔧 *Dienstleistung:* ${data.service || 'Nicht angegeben'}

💬 *Nachricht:*
${data.message}

---
Gesendet von: Münster Reinigung Website
        `.trim();
        
        // Create WhatsApp link
        const whatsappLink = `https://wa.me/49123456789?text=${encodeURIComponent(message)}`;
        
        // For demo purposes, we'll simulate success
        return new Promise((resolve) => {
            setTimeout(() => {
                // Simulate WhatsApp sending
                console.log('WhatsApp message would be sent:', message);
                resolve(true);
            }, 1000);
        });
    }
    
    async sendViaAPI(data) {
        // This would be your actual API endpoint
        const apiUrl = '/api/contact';
        
        try {
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            return response.ok;
        } catch (error) {
            console.error('API error:', error);
            return false;
        }
    }
    
    setSubmitButtonState(isSubmitting) {
        if (!this.submitBtn) return;
        
        if (isSubmitting) {
            this.submitBtn.disabled = true;
            this.submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Wird gesendet...';
        } else {
            this.submitBtn.disabled = false;
            this.submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Nachricht senden';
        }
    }
    
    handleServiceChange() {
        const serviceSelect = document.getElementById('service');
        const messageField = document.getElementById('message');
        
        if (serviceSelect && messageField) {
            const selectedService = serviceSelect.value;
            const serviceMessages = {
                dachreinigung: 'Ich interessiere mich für eine professionelle Dachreinigung. Bitte informieren Sie mich über die Möglichkeiten und Preise.',
                fassadenreinigung: 'Ich benötige eine Fassadenreinigung für mein Gebäude. Können Sie mir ein Angebot machen?',
                terrassenreinigung: 'Meine Terrasse/Gehweg benötigt eine gründliche Reinigung. Bitte kontaktieren Sie mich für ein Angebot.',
                hofreinigung: 'Ich suche nach einem professionellen Service für die Hof- und Garagenreinigung.',
                maschinenreinigung: 'Ich benötige eine Reinigung für meine Maschinen/Fahrzeuge. Bitte melden Sie sich bei mir.',
                graffitientfernung: 'Ich habe ein Problem mit Graffiti und benötige professionelle Hilfe zur Entfernung.',
                zaunreinigung: 'Meine Zäune und Gartenelemente benötigen eine Reinigung. Bitte kontaktieren Sie mich.',
                bauendreinigung: 'Ich benötige eine Bauendreinigung nach abgeschlossenen Bauarbeiten.'
            };
            
            if (serviceMessages[selectedService]) {
                messageField.value = serviceMessages[selectedService];
                messageField.focus();
            }
        }
    }
    
    setupWhatsAppIntegration() {
        // Add WhatsApp quick contact button
        const contactSection = document.querySelector('.contact');
        if (contactSection) {
            const whatsappBtn = document.createElement('a');
            whatsappBtn.href = 'https://wa.me/49123456789?text=Hallo! Ich interessiere mich für Ihre Reinigungsdienstleistungen.';
            whatsappBtn.className = 'btn btn-primary whatsapp-btn';
            whatsappBtn.innerHTML = '<i class="fab fa-whatsapp"></i> WhatsApp Kontakt';
            whatsappBtn.style.cssText = `
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 1000;
                border-radius: 50px;
                padding: 15px 25px;
                box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
                animation: pulse 2s infinite;
            `;
            
            document.body.appendChild(whatsappBtn);
            
            // Add pulse animation
            const style = document.createElement('style');
            style.textContent = `
                @keyframes pulse {
                    0% { transform: scale(1); }
                    50% { transform: scale(1.05); }
                    100% { transform: scale(1); }
                }
            `;
            document.head.appendChild(style);
        }
    }
    
    trackConversion(data) {
        // Track form submission for analytics
        if (typeof gtag !== 'undefined') {
            gtag('event', 'form_submit', {
                'event_category': 'contact',
                'event_label': data.service || 'general',
                'value': 1
            });
        }
        
        // Facebook Pixel
        if (typeof fbq !== 'undefined') {
            fbq('track', 'Lead', {
                content_name: data.service || 'Contact Form',
                content_category: 'Contact'
            });
        }
    }
}

// ===== GOOGLE MAPS INTEGRATION =====

function initMap() {
    // Münster coordinates
    const muenster = { lat: 51.9607, lng: 7.6261 };
    
    // Create map
    const map = new google.maps.Map(document.getElementById('map'), {
        zoom: 12,
        center: muenster,
        styles: [
            {
                "featureType": "all",
                "elementType": "geometry",
                "stylers": [{"color": "#1e293b"}]
            },
            {
                "featureType": "all",
                "elementType": "labels.text.stroke",
                "stylers": [{"color": "#1e293b"}]
            },
            {
                "featureType": "all",
                "elementType": "labels.text.fill",
                "stylers": [{"color": "#cbd5e1"}]
            },
            {
                "featureType": "administrative.locality",
                "elementType": "labels.text.fill",
                "stylers": [{"color": "#f8fafc"}]
            },
            {
                "featureType": "poi",
                "elementType": "labels.text.fill",
                "stylers": [{"color": "#94a3b8"}]
            },
            {
                "featureType": "road",
                "elementType": "geometry",
                "stylers": [{"color": "#334155"}]
            },
            {
                "featureType": "road",
                "elementType": "geometry.stroke",
                "stylers": [{"color": "#475569"}]
            },
            {
                "featureType": "road",
                "elementType": "labels.text.fill",
                "stylers": [{"color": "#f8fafc"}]
            },
            {
                "featureType": "road.highway",
                "elementType": "geometry",
                "stylers": [{"color": "#475569"}]
            },
            {
                "featureType": "road.highway",
                "elementType": "geometry.stroke",
                "stylers": [{"color": "#64748b"}]
            },
            {
                "featureType": "road.highway",
                "elementType": "labels.text.fill",
                "stylers": [{"color": "#f8fafc"}]
            },
            {
                "featureType": "transit",
                "elementType": "geometry",
                "stylers": [{"color": "#334155"}]
            },
            {
                "featureType": "water",
                "elementType": "geometry",
                "stylers": [{"color": "#0f172a"}]
            },
            {
                "featureType": "water",
                "elementType": "labels.text.fill",
                "stylers": [{"color": "#94a3b8"}]
            }
        ]
    });
    
    // Add marker
    const marker = new google.maps.Marker({
        position: muenster,
        map: map,
        title: 'Münster Reinigung',
        icon: {
            url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                <svg width="40" height="40" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="20" cy="20" r="18" fill="#2563eb" stroke="#ffffff" stroke-width="2"/>
                    <path d="M20 8l2.5 7.5H30l-6 4.5 2.5 7.5L20 25l-6.5 4.5 2.5-7.5-6-4.5h7.5L20 8z" fill="#ffffff"/>
                </svg>
            `),
            scaledSize: new google.maps.Size(40, 40),
            anchor: new google.maps.Point(20, 20)
        }
    });
    
    // Add info window
    const infoWindow = new google.maps.InfoWindow({
        content: `
            <div style="padding: 10px; max-width: 200px;">
                <h3 style="margin: 0 0 5px 0; color: #1e293b;">Münster Reinigung</h3>
                <p style="margin: 0; color: #64748b; font-size: 14px;">
                    Musterstraße 123<br>
                    48167 Münster<br>
                    Tel: 0123 456789
                </p>
            </div>
        `
    });
    
    marker.addListener('click', () => {
        infoWindow.open(map, marker);
    });
}

// ===== INITIALIZATION =====

document.addEventListener('DOMContentLoaded', function() {
    // Initialize contact form
    new ContactForm();
    
    // Initialize map if Google Maps is loaded
    if (typeof google !== 'undefined' && google.maps) {
        initMap();
    } else {
        // Fallback if Google Maps fails to load
        const mapElement = document.getElementById('map');
        if (mapElement) {
            mapElement.innerHTML = `
                <div style="display: flex; align-items: center; justify-content: center; height: 100%; background: #1e293b; color: #cbd5e1;">
                    <div style="text-align: center;">
                        <i class="fas fa-map-marker-alt" style="font-size: 3rem; margin-bottom: 1rem; color: #2563eb;"></i>
                        <h3>Münster Reinigung</h3>
                        <p>Musterstraße 123<br>48167 Münster</p>
                        <a href="https://maps.google.com/?q=48167+Münster" target="_blank" class="btn btn-primary">
                            <i class="fas fa-external-link-alt"></i> In Google Maps öffnen
                        </a>
                    </div>
                </div>
            `;
        }
    }
});

// Export for use in other modules
window.ContactForm = ContactForm;
window.initMap = initMap;