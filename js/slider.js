// ===== REVIEWS SLIDER =====

class ReviewsSlider {
    constructor() {
        this.currentSlide = 0;
        this.slides = document.querySelectorAll('.review-card');
        this.totalSlides = this.slides.length;
        this.autoPlayInterval = null;
        this.autoPlayDelay = 5000; // 5 seconds
        
        this.init();
    }
    
    init() {
        if (this.totalSlides === 0) return;
        
        this.createDots();
        this.setupEventListeners();
        this.showSlide(0);
        this.startAutoPlay();
        this.setupTouchEvents();
    }
    
    createDots() {
        const dotsContainer = document.getElementById('review-dots');
        if (!dotsContainer) return;
        
        for (let i = 0; i < this.totalSlides; i++) {
            const dot = document.createElement('div');
            dot.className = 'review-dot';
            dot.setAttribute('data-slide', i);
            dotsContainer.appendChild(dot);
        }
    }
    
    setupEventListeners() {
        const prevBtn = document.getElementById('prev-review');
        const nextBtn = document.getElementById('next-review');
        const dotsContainer = document.getElementById('review-dots');
        
        if (prevBtn) {
            prevBtn.addEventListener('click', () => {
                this.prevSlide();
                this.resetAutoPlay();
            });
        }
        
        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                this.nextSlide();
                this.resetAutoPlay();
            });
        }
        
        if (dotsContainer) {
            dotsContainer.addEventListener('click', (e) => {
                if (e.target.classList.contains('review-dot')) {
                    const slideIndex = parseInt(e.target.getAttribute('data-slide'));
                    this.goToSlide(slideIndex);
                    this.resetAutoPlay();
                }
            });
        }
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft') {
                this.prevSlide();
                this.resetAutoPlay();
            } else if (e.key === 'ArrowRight') {
                this.nextSlide();
                this.resetAutoPlay();
            }
        });
        
        // Pause autoplay on hover
        const sliderContainer = document.querySelector('.reviews-slider');
        if (sliderContainer) {
            sliderContainer.addEventListener('mouseenter', () => {
                this.pauseAutoPlay();
            });
            
            sliderContainer.addEventListener('mouseleave', () => {
                this.startAutoPlay();
            });
        }
    }
    
    setupTouchEvents() {
        const sliderContainer = document.querySelector('.reviews-slider');
        if (!sliderContainer) return;
        
        let startX = 0;
        let endX = 0;
        let isDragging = false;
        
        sliderContainer.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            isDragging = true;
            this.pauseAutoPlay();
        });
        
        sliderContainer.addEventListener('touchmove', (e) => {
            if (!isDragging) return;
            e.preventDefault();
            endX = e.touches[0].clientX;
        });
        
        sliderContainer.addEventListener('touchend', (e) => {
            if (!isDragging) return;
            isDragging = false;
            
            const diffX = startX - endX;
            const threshold = 50; // Minimum swipe distance
            
            if (Math.abs(diffX) > threshold) {
                if (diffX > 0) {
                    // Swipe left - next slide
                    this.nextSlide();
                } else {
                    // Swipe right - previous slide
                    this.prevSlide();
                }
            }
            
            this.startAutoPlay();
        });
    }
    
    showSlide(index) {
        // Hide all slides
        this.slides.forEach((slide, i) => {
            slide.style.display = 'none';
            slide.style.opacity = '0';
            slide.style.transform = 'translateX(100%)';
        });
        
        // Show current slide
        if (this.slides[index]) {
            this.slides[index].style.display = 'block';
            
            // Animate in
            setTimeout(() => {
                this.slides[index].style.opacity = '1';
                this.slides[index].style.transform = 'translateX(0)';
            }, 50);
        }
        
        // Update dots
        this.updateDots(index);
        
        this.currentSlide = index;
    }
    
    updateDots(activeIndex) {
        const dots = document.querySelectorAll('.review-dot');
        dots.forEach((dot, index) => {
            if (index === activeIndex) {
                dot.classList.add('active');
            } else {
                dot.classList.remove('active');
            }
        });
    }
    
    nextSlide() {
        const nextIndex = (this.currentSlide + 1) % this.totalSlides;
        this.showSlide(nextIndex);
    }
    
    prevSlide() {
        const prevIndex = this.currentSlide === 0 ? this.totalSlides - 1 : this.currentSlide - 1;
        this.showSlide(prevIndex);
    }
    
    goToSlide(index) {
        if (index >= 0 && index < this.totalSlides) {
            this.showSlide(index);
        }
    }
    
    startAutoPlay() {
        if (this.autoPlayInterval) {
            clearInterval(this.autoPlayInterval);
        }
        
        this.autoPlayInterval = setInterval(() => {
            this.nextSlide();
        }, this.autoPlayDelay);
    }
    
    pauseAutoPlay() {
        if (this.autoPlayInterval) {
            clearInterval(this.autoPlayInterval);
            this.autoPlayInterval = null;
        }
    }
    
    resetAutoPlay() {
        this.pauseAutoPlay();
        this.startAutoPlay();
    }
    
    destroy() {
        this.pauseAutoPlay();
        // Remove event listeners if needed
    }
}

// ===== MOBILE SLIDER (Alternative for mobile devices) =====

class MobileReviewsSlider {
    constructor() {
        this.slider = document.querySelector('.reviews-slider');
        this.slides = document.querySelectorAll('.review-card');
        this.currentIndex = 0;
        this.isMobile = window.innerWidth <= 768;
        
        this.init();
    }
    
    init() {
        if (!this.slider || this.slides.length === 0) return;
        
        if (this.isMobile) {
            this.setupMobileSlider();
        } else {
            this.setupDesktopSlider();
        }
        
        // Handle resize
        window.addEventListener('resize', this.handleResize.bind(this));
    }
    
    setupMobileSlider() {
        // For mobile, show all slides in a scrollable container
        this.slider.style.display = 'flex';
        this.slider.style.overflowX = 'auto';
        this.slider.style.scrollSnapType = 'x mandatory';
        this.slider.style.gap = '1rem';
        this.slider.style.padding = '0 1rem';
        
        this.slides.forEach(slide => {
            slide.style.flex = '0 0 auto';
            slide.style.width = 'calc(100vw - 2rem)';
            slide.style.maxWidth = '400px';
            slide.style.scrollSnapAlign = 'start';
        });
        
        // Hide navigation on mobile
        const nav = document.querySelector('.reviews-nav');
        if (nav) {
            nav.style.display = 'none';
        }
    }
    
    setupDesktopSlider() {
        // For desktop, use the regular slider functionality
        this.slider.style.display = 'flex';
        this.slider.style.overflow = 'hidden';
        this.slider.style.gap = '2rem';
        
        this.slides.forEach(slide => {
            slide.style.flex = '0 0 auto';
            slide.style.width = '350px';
            slide.style.scrollSnapAlign = 'none';
        });
    }
    
    handleResize() {
        const wasMobile = this.isMobile;
        this.isMobile = window.innerWidth <= 768;
        
        if (wasMobile !== this.isMobile) {
            if (this.isMobile) {
                this.setupMobileSlider();
            } else {
                this.setupDesktopSlider();
            }
        }
    }
}

// ===== INITIALIZATION =====

document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on mobile
    const isMobile = window.innerWidth <= 768;
    
    if (isMobile) {
        // Use mobile slider
        new MobileReviewsSlider();
    } else {
        // Use desktop slider
        new ReviewsSlider();
    }
});

// ===== SLIDER UTILITIES =====

// Smooth scroll to slide (for mobile)
function smoothScrollToSlide(slideIndex) {
    const slider = document.querySelector('.reviews-slider');
    const slides = document.querySelectorAll('.review-card');
    
    if (!slider || !slides[slideIndex]) return;
    
    const slideWidth = slides[slideIndex].offsetWidth;
    const gap = 16; // 1rem gap
    const scrollPosition = slideIndex * (slideWidth + gap);
    
    slider.scrollTo({
        left: scrollPosition,
        behavior: 'smooth'
    });
}

// Get current slide index (for mobile)
function getCurrentSlideIndex() {
    const slider = document.querySelector('.reviews-slider');
    const slides = document.querySelectorAll('.review-card');
    
    if (!slider || slides.length === 0) return 0;
    
    const slideWidth = slides[0].offsetWidth;
    const gap = 16;
    const scrollPosition = slider.scrollLeft;
    
    return Math.round(scrollPosition / (slideWidth + gap));
}

// Update dots based on scroll position (for mobile)
function updateDotsOnScroll() {
    const currentIndex = getCurrentSlideIndex();
    const dots = document.querySelectorAll('.review-dot');
    
    dots.forEach((dot, index) => {
        if (index === currentIndex) {
            dot.classList.add('active');
        } else {
            dot.classList.remove('active');
        }
    });
}

// Add scroll event listener for mobile dots
document.addEventListener('DOMContentLoaded', function() {
    const slider = document.querySelector('.reviews-slider');
    if (slider && window.innerWidth <= 768) {
        slider.addEventListener('scroll', updateDotsOnScroll);
    }
});

// Export for use in other modules
window.ReviewsSlider = {
    ReviewsSlider,
    MobileReviewsSlider,
    smoothScrollToSlide,
    getCurrentSlideIndex,
    updateDotsOnScroll
};