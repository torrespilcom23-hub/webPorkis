document.addEventListener('DOMContentLoaded', () => {
    // Header scroll shadow
    const header = document.getElementById('site-header');
    if (header) {
        window.addEventListener('scroll', () => {
            header.classList.toggle('scrolled', window.scrollY > 20);
        });
    }

    // Mobile nav toggle
    const navToggle = document.getElementById('nav-toggle');
    const mainNav = document.getElementById('main-nav');
    if (navToggle && mainNav) {
        navToggle.addEventListener('click', () => {
            const open = mainNav.classList.toggle('open');
            navToggle.setAttribute('aria-expanded', open);
        });
        mainNav.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                mainNav.classList.remove('open');
                navToggle.setAttribute('aria-expanded', 'false');
            });
        });
    }

    // Fade-in on scroll
    const fadeEls = document.querySelectorAll('.fade-in');
    if (fadeEls.length && 'IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.12 });
        fadeEls.forEach(el => observer.observe(el));
    } else {
        fadeEls.forEach(el => el.classList.add('visible'));
    }

    // Counter animation
    const counters = document.querySelectorAll('.stat-number[data-target]');
    if (counters.length && 'IntersectionObserver' in window) {
        const counterObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (!entry.isIntersecting) return;
                const el = entry.target;
                const target = parseInt(el.dataset.target, 10);
                const duration = 1800;
                const start = performance.now();
                const animate = (now) => {
                    const progress = Math.min((now - start) / duration, 1);
                    el.textContent = Math.floor(progress * target);
                    if (progress < 1) requestAnimationFrame(animate);
                    else el.textContent = target;
                };
                requestAnimationFrame(animate);
                counterObserver.unobserve(el);
            });
        }, { threshold: 0.5 });
        counters.forEach(c => counterObserver.observe(c));
    }

    // Testimonials slider
    const testimonials = document.querySelectorAll('.testimonial');
    const dotsContainer = document.getElementById('testimonial-dots');
    if (testimonials.length > 1 && dotsContainer) {
        let current = 0;
        testimonials.forEach((_, i) => {
            const dot = document.createElement('button');
            dot.className = 'dot' + (i === 0 ? ' active' : '');
            dot.setAttribute('aria-label', `Testimonio ${i + 1}`);
            dot.addEventListener('click', () => goTo(i));
            dotsContainer.appendChild(dot);
        });
        const dots = dotsContainer.querySelectorAll('.dot');

        function goTo(index) {
            testimonials[current].classList.remove('active');
            dots[current].classList.remove('active');
            current = index;
            testimonials[current].classList.add('active');
            dots[current].classList.add('active');
        }

        setInterval(() => goTo((current + 1) % testimonials.length), 5000);
    }

    // Style Django form fields in contact page
    document.querySelectorAll('.contact-form input, .contact-form select, .contact-form textarea').forEach(field => {
        if (field.type === 'hidden') return;
        field.classList.add('form-control');
    });
});
