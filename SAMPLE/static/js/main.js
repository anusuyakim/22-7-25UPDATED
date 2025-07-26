// Function to handle OTP and form submission logic
function setupForm(formId, sendBtnId, verifyBtnId, submitBtnId, otpSectionId, timerId, formType, submitUrl) {
    const form = document.getElementById(formId);
    if (!form) return;
    const sendVerificationBtn = document.getElementById(sendBtnId);
    const verifyOtpBtn = document.getElementById(verifyBtnId);
    const submitBtn = document.getElementById(submitBtnId);
    const otpSection = document.getElementById(otpSectionId);
    const otpTimer = document.getElementById(timerId);
    const successMessage = form.querySelector('.success-message');
    const errorMessage = form.querySelector('.error-message');
    let countdown;
    function showMessage(element, message) {
        hideMessages();
        const span = element.querySelector('span');
        span.innerHTML = message;
        element.style.display = 'block';
    }
    function hideMessages() {
        if (successMessage) successMessage.style.display = 'none';
        if (errorMessage) errorMessage.style.display = 'none';
    }
    function startTimer(duration) {
        let timer = duration;
        otpTimer.style.display = 'block';
        sendVerificationBtn.style.display = 'none';
        countdown = setInterval(() => {
            const minutes = parseInt(timer / 60, 10);
            const seconds = parseInt(timer % 60, 10);
            otpTimer.textContent = `Resend available in ${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
            if (--timer < 0) {
                clearInterval(countdown);
                otpTimer.innerHTML = '';
                sendVerificationBtn.textContent = 'Resend Code';
                sendVerificationBtn.style.display = 'inline-block';
            }
        }, 1000);
    }
    sendVerificationBtn.addEventListener('click', async () => {
        hideMessages();
        const emailInput = form.querySelector('input[name="email"]');
        const email = emailInput.value.trim();
        if (!email || !/^\S+@\S+\.\S+$/.test(email)) {
            return showMessage(errorMessage, 'Please enter a valid email address.');
        }
        sendVerificationBtn.disabled = true;
        sendVerificationBtn.textContent = 'Sending...';
        try {
            const response = await fetch('/api/send-otp', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: email })
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Failed to send OTP.');
            showMessage(successMessage, data.message);
            otpSection.style.display = 'block';
            clearInterval(countdown);
            startTimer(120);
        } catch (error) {
            showMessage(errorMessage, error.message);
        } finally {
            sendVerificationBtn.disabled = false;
            sendVerificationBtn.textContent = 'Send Verification Code';
        }
    });
    const otpInputs = otpSection.querySelectorAll('.otp-input');
    otpInputs.forEach((input, index) => {
        input.addEventListener('input', () => {
            if (input.value && index < otpInputs.length - 1) {
                otpInputs[index + 1].focus();
            }
        });
        input.addEventListener('keydown', (e) => {
            if (e.key === "Backspace" && !input.value && index > 0) {
                 otpInputs[index - 1].focus();
            }
        });
    });
    verifyOtpBtn.addEventListener('click', async () => {
        hideMessages();
        const otp = Array.from(otpInputs).map(input => input.value).join('');
        const email = form.querySelector('input[name="email"]').value;
        if (otp.length !== 6) {
            return showMessage(errorMessage, 'Please enter the full 6-digit code.');
        }
        try {
            const response = await fetch('/api/verify-otp', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, otp })
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Verification failed.');
            showMessage(successMessage, data.message);
            otpSection.style.display = 'none';
            submitBtn.disabled = false;
            clearInterval(countdown);
            otpTimer.style.display = 'none';
        } catch (error) {
             showMessage(errorMessage, error.message);
        }
    });
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideMessages();
        submitBtn.disabled = true;
        submitBtn.textContent = 'Submitting...';
        try {
            const formData = new FormData(form);
            const response = await fetch(submitUrl, {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Submission failed.');
            showMessage(successMessage, data.message);
            form.reset();
            submitBtn.disabled = true;
        } catch (error) {
            showMessage(errorMessage, error.message);
            submitBtn.disabled = false; 
        } finally {
             submitBtn.textContent = formType === 'job' ? 'Submit Application' : 'Send Message';
        }
    });
}


document.addEventListener('DOMContentLoaded', () => {
    // --- Loading Overlay ---
    const loadingOverlay = document.getElementById('loadingOverlay');
    window.addEventListener('load', () => {
        AOS.init({ duration: 800, once: true });
        if(loadingOverlay) {
            loadingOverlay.style.opacity = '0';
            setTimeout(() => loadingOverlay.style.display = 'none', 300);
        }
    });
    
    // --- Theme Toggling ---
    const themeToggle = document.getElementById('theme-toggle-link');
    const mobileThemeToggle = document.getElementById('mobile-theme-toggle-link');
    const html = document.documentElement;
    const applyTheme = (theme) => {
        if (theme === 'dark') {
            html.classList.add('dark');
            if (themeToggle) themeToggle.textContent = 'Light';
            if (mobileThemeToggle) mobileThemeToggle.textContent = 'Light';
        } else {
            html.classList.remove('dark');
            if (themeToggle) themeToggle.textContent = 'Dark';
            if (mobileThemeToggle) mobileThemeToggle.textContent = 'Dark';
        }
    };
    const toggleTheme = () => {
        const newTheme = html.classList.contains('dark') ? 'light' : 'dark';
        localStorage.setItem('theme', newTheme);
        applyTheme(newTheme);
    };
    if (themeToggle) themeToggle.addEventListener('click', toggleTheme);
    if (mobileThemeToggle) mobileThemeToggle.addEventListener('click', toggleTheme);
    const savedTheme = localStorage.getItem('theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    applyTheme(savedTheme);

    // --- Mobile Menu ---
    const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
    const mobileMenu = document.getElementById('mobile-menu');
    if (mobileMenuToggle && mobileMenu) {
        mobileMenuToggle.addEventListener('click', () => {
            mobileMenu.classList.toggle('translate-x-full');
        });
    }

    // --- Hero Slider ---
    const heroSlidesContainer = document.getElementById('hero-slides-container');
    const heroContentContainer = document.getElementById('hero-content-container');
    const heroDotsContainer = document.getElementById('hero-dots-container');
    const heroPrevBtn = document.getElementById('hero-prev-btn');
    const heroNextBtn = document.getElementById('hero-next-btn');
    if (heroSlidesContainer) {
        // CORRECTED, VALID IMAGE URLS
        const slidesData = [
            { supertitle: 'Pioneering Women-Led Technology', title: 'Engineering the Future, Led by Vision', subtitle: 'We translate your unique business vision into high-performance, secure, and scalable software solutions.', img: 'https://images.unsplash.com/photo-1521737604893-d14cc237f11d?q=80&w=2084&auto=format&fit=crop', link: '/about-us' },
            { supertitle: 'AI & Machine Learning', title: 'Intelligent Solutions, Real-World Impact', subtitle: 'We build custom AI models to automate processes, predict outcomes, and unlock hidden value in your data.', img: 'https://images.unsplash.com/photo-1518349619113-03114f06ac3a?q=80&w=2070&auto=format&fit=crop', link: '/services/ai-machine-learning' },
            { supertitle: 'Custom Software Development', title: 'Your Vision, Engineered', subtitle: 'From complex enterprise platforms to intuitive mobile apps, we deliver high-performance software tailored to you.', img: 'https://images.unsplash.com/photo-1461749280684-dccba630e2f6?q=80&w=2070&auto=format&fit=crop', link: '/services/software-development' }
        ];
        
        let currentSlide = 0;
        let slideInterval;
        slidesData.forEach((slide, index) => {
            const slideDiv = document.createElement('div');
            slideDiv.className = 'hero-slide';
            slideDiv.innerHTML = `<img src="${slide.img}" alt="${slide.title}" class="hero-slide-img"><div class="hero-slide-overlay"></div>`;
            heroSlidesContainer.appendChild(slideDiv);
            const dot = document.createElement('button');
            dot.className = 'hero-dot';
            dot.addEventListener('click', () => { goToSlide(index); resetInterval(); });
            heroDotsContainer.appendChild(dot);
        });
        const allSlides = heroSlidesContainer.querySelectorAll('.hero-slide');
        const allDots = heroDotsContainer.querySelectorAll('.hero-dot');
        function goToSlide(index) {
            currentSlide = (index + slidesData.length) % slidesData.length;
            allSlides.forEach(s => s.classList.remove('active'));
            allSlides[currentSlide].classList.add('active');
            allDots.forEach(d => d.classList.remove('active'));
            allDots[currentSlide].classList.add('active');
            const slide = slidesData[currentSlide];
            heroContentContainer.innerHTML = `
                <div class="hero-content" style="animation: fade-in 0.8s ease-out forwards;">
                    <p class="text-lg font-semibold text-blue-300 uppercase tracking-wider">${slide.supertitle}</p>
                    <h1 class="text-4xl md:text-6xl font-extrabold tracking-tight mt-4">${slide.title}</h1>
                    <p class="mt-6 max-w-2xl text-lg text-gray-300">${slide.subtitle}</p>
                    <a href="${slide.link}" class="mt-10 inline-block bg-brand-blue hover:bg-brand-blue-light text-white font-bold py-4 px-10 rounded-lg text-lg transition-transform hover:scale-105">Learn More</a>
                </div>`;
        }
        function resetInterval() {
            clearInterval(slideInterval);
            slideInterval = setInterval(() => goToSlide(currentSlide + 1), 6000);
        }
        heroNextBtn.addEventListener('click', () => { goToSlide(currentSlide + 1); resetInterval(); });
        heroPrevBtn.addEventListener('click', () => { goToSlide(currentSlide - 1); resetInterval(); });
        goToSlide(0);
        resetInterval();
    }
    
    // --- TATA-STYLE PORTFOLIO SLIDER ---
    const portfolioSlider = document.getElementById('portfolio-slider');
    if (portfolioSlider) {
        const portfolioData = [
            { img: 'https://images.unsplash.com/photo-1554744512-d6c603f27c54?q=80&w=2070&auto=format&fit=crop', title: 'AI-Powered Logistics Platform', link: '/portfolio/ai-logistics-platform' },
            { img: 'https://images.unsplash.com/photo-1552664730-d307ca884978?q=80&w=2070&auto=format&fit=crop', title: 'Cloud Migration for Healthcare', link: '/portfolio/cloud-migration' },
            { img: 'https://images.unsplash.com/photo-1521791136064-7986c2920216?q=80&w=2070&auto=format&fit=crop', title: 'Secure Mobile Fintech App', link: '/portfolio/secure-fintech-app' },
            { img: 'https://images.unsplash.com/photo-1517048676732-d65bc937f952?q=80&w=2070&auto=format&fit=crop', title: 'Custom Enterprise ERP System', link: '/portfolio/enterprise-erp' },
            { img: 'https://images.unsplash.com/photo-1600880292203-757bb62b4baf?q=80&w=2070&auto=format&fit=crop', title: 'Predictive Analytics Engine', link: '/portfolio/ai-logistics-platform' }
        ];
        portfolioSlider.innerHTML = portfolioData.map(item => `
            <div class="portfolio-slider-card">
                <a href="${item.link}">
                    <img src="${item.img}" alt="${item.title}" class="portfolio-slider-card-img">
                    <div class="portfolio-slider-card-overlay">
                        <h3 class="portfolio-slider-card-title">${item.title}</h3>
                        <span class="portfolio-slider-card-link">Explore</span>
                    </div>
                </a>
            </div>`).join('');
        const prevBtn = document.getElementById('portfolio-prev-btn-new');
        const nextBtn = document.getElementById('portfolio-next-btn-new');
        const progressBar = document.getElementById('portfolio-progress-bar');
        let currentIndex = 0;
        const totalSlides = portfolioData.length;
        const getSlidesToDisplay = () => {
            if (window.innerWidth >= 1024) return 4;
            if (window.innerWidth >= 640) return 2;
            return 1;
        }
        let slidesToDisplay = getSlidesToDisplay();
        function updateSlider() {
            const cards = portfolioSlider.querySelectorAll('.portfolio-slider-card');
            cards.forEach(card => {
                card.style.flexBasis = `${100 / slidesToDisplay}%`;
            });
            const offset = -currentIndex * (100 / slidesToDisplay);
            portfolioSlider.style.transform = `translateX(${offset}%)`;
            const progressWidth = ((currentIndex + slidesToDisplay) / totalSlides) * 100;
            progressBar.style.width = `${progressWidth > 100 ? 100 : progressWidth}%`;
            prevBtn.style.display = currentIndex === 0 ? 'none' : 'flex';
            nextBtn.style.display = currentIndex >= totalSlides - slidesToDisplay ? 'none' : 'flex';
        }
        nextBtn.addEventListener('click', () => {
            if (currentIndex < totalSlides - slidesToDisplay) {
                currentIndex++;
                updateSlider();
            }
        });
        prevBtn.addEventListener('click', () => {
            if (currentIndex > 0) {
                currentIndex--;
                updateSlider();
            }
        });
        window.addEventListener('resize', () => {
            slidesToDisplay = getSlidesToDisplay();
            if (currentIndex > totalSlides - slidesToDisplay) {
                currentIndex = totalSlides - slidesToDisplay;
            }
            updateSlider();
        });
        updateSlider();
    }

    // --- Chatbot ---
    const chatbotToggle = document.getElementById('chatbot-toggle');
    const chatbotWindow = document.getElementById('chatbot-window');
    const closeBtn = document.getElementById('chatbot-close-btn');
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chatbot-input');
    const messagesContainer = document.getElementById('chatbot-messages-container');
    const sendBtn = document.getElementById('chatbot-send-btn');
    if (chatbotToggle) {
        chatbotToggle.innerHTML = `<i class="fas fa-robot text-2xl"></i>`;
        closeBtn.innerHTML = `<i class="fas fa-times text-xl"></i>`;
        sendBtn.innerHTML = `<i class="fas fa-paper-plane"></i>`;
        sendBtn.disabled = true;
        chatInput.addEventListener('input', () => { sendBtn.disabled = chatInput.value.trim() === ''; });
        const openChat = () => chatbotWindow.classList.remove('opacity-0', 'translate-y-4', 'pointer-events-none');
        const closeChat = () => chatbotWindow.classList.add('opacity-0', 'translate-y-4', 'pointer-events-none');
        chatbotToggle.addEventListener('click', openChat);
        closeBtn.addEventListener('click', closeChat);
        function addMessage(content, sender = 'bot') {
            const messageDiv = document.createElement('div');
            messageDiv.className = `chat-message-container ${sender === 'user' ? 'justify-end' : 'justify-start'}`;
            messageDiv.innerHTML = `<div class="${sender === 'user' ? 'user-message' : 'bot-message'}">${content}</div>`;
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        addMessage("Hello! I'm the Vendhan AI Assistant. How can I help you today?");
        chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const userMessage = chatInput.value.trim();
            if (!userMessage) return;
            addMessage(userMessage, 'user');
            chatInput.value = '';
            sendBtn.disabled = true;
            addMessage('<div class="typing-indicator"><span></span><span></span><span></span></div>', 'bot');
            try {
                const response = await fetch('/api/chatbot', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ message: userMessage })
                });
                const data = await response.json();
                messagesContainer.querySelector('.typing-indicator').parentElement.parentElement.remove();
                addMessage(data.response, 'bot');
            } catch (error) {
                console.error('Chatbot error:', error);
                const typingIndicator = messagesContainer.querySelector('.typing-indicator');
                if (typingIndicator) typingIndicator.parentElement.parentElement.remove();
                addMessage("I'm sorry, I'm having trouble connecting right now. Please try again in a moment.", 'bot');
            }
        });
    }

    // --- LIVE UPDATES CARD FEATURE ---
    const weatherCardContent = document.getElementById('weather-card-content');
    const newsCardContent = document.getElementById('news-card-content');
    if (weatherCardContent && newsCardContent) {
        const fetchLiveUpdatesForCards = (lat, lon) => {
            weatherCardContent.innerHTML = '<p class="text-gray-500 dark:text-gray-400">Loading weather...</p>';
            newsCardContent.innerHTML = '<p class="text-gray-500 dark:text-gray-400">Loading news...</p>';
            let apiUrl = '/api/live-updates';
            if (lat && lon) {
                apiUrl += `?lat=${lat}&lon=${lon}`;
            }
            fetch(apiUrl)
                .then(response => {
                    if (!response.ok) throw new Error('Failed to fetch data');
                    return response.json();
                })
                .then(data => {
                    renderWeatherDataForCard(data.weather);
                    renderNewsDataForCard(data.news);
                })
                .catch(error => {
                    console.error('Live Updates Card Error:', error);
                    weatherCardContent.innerHTML = `<p class="text-red-500">Weather data unavailable.</p>`;
                    newsCardContent.innerHTML = `<p class="text-red-500">News data unavailable.</p>`;
                });
        };
        const renderWeatherDataForCard = (weather) => {
            if (!weather || weather.error) {
                weatherCardContent.innerHTML = `<p class="text-red-500">${weather?.error || 'Weather data unavailable.'}</p>`;
                return;
            }
            const iconUrl = `https://openweathermap.org/img/wn/${weather.weather[0].icon}@2x.png`;
            weatherCardContent.innerHTML = `
                <div class="flex items-center justify-between">
                    <div>
                        <h4 class="text-3xl font-bold text-gray-900 dark:text-white">${weather.name}</h4>
                        <p class="text-lg capitalize text-gray-600 dark:text-gray-300">${weather.weather[0].description}</p>
                    </div>
                    <div class="text-right">
                        <img src="${iconUrl}" alt="${weather.weather[0].description}" class="w-16 h-16 -mt-4 -mb-4 inline-block">
                        <p class="text-4xl font-bold text-gray-900 dark:text-white">${Math.round(weather.main.temp)}°C</p>
                    </div>
                </div>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-2">
                    Feels like ${Math.round(weather.main.feels_like)}°C  •  Humidity: ${weather.main.humidity}%
                </p>`;
        };
        const renderNewsDataForCard = (news) => {
            if (!news || news.error || !news.articles || news.articles.length === 0) {
                newsCardContent.innerHTML = `<p class="text-red-500">${news?.error || 'News data unavailable. Check API Key.'}</p>`;
                return;
            }
            newsCardContent.innerHTML = news.articles.slice(0, 5).map(article => `
                <a href="${article.url}" target="_blank" rel="noopener noreferrer" class="block p-3 rounded-lg hover:bg-brand-gray dark:hover:bg-gray-800 transition-colors">
                    <h4 class="font-bold text-gray-900 dark:text-white leading-tight">${article.title}</h4>
                    <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">${article.source.name}</p>
                </a>`).join('');
        };
        const locationSuccess = (position) => {
            fetchLiveUpdatesForCards(position.coords.latitude, position.coords.longitude);
        };
        const locationError = () => {
            console.log("User denied geolocation or an error occurred. Fetching default weather.");
            fetchLiveUpdatesForCards(null, null);
        };
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(locationSuccess, locationError);
        } else {
            console.log("Geolocation is not supported. Fetching default weather.");
            fetchLiveUpdatesForCards(null, null);
        }
    }
});