// UNIFIED AND CORRECTED main.js

document.addEventListener('DOMContentLoaded', () => {

    // --- Loading Overlay ---
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
        setTimeout(() => { 
            loadingOverlay.classList.add('hidden'); 
        }, 500);
    }
    
    // --- AOS Init ---
    if (typeof AOS !== 'undefined') {
        AOS.init({ duration: 800, once: true, offset: 50 });
    }

    // --- ICONS ---
    const icons = {
        menu: `<svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16m-7 6h7"></path></svg>`,
        close: `<svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>`,
        chatbotOpen: `<svg xmlns="http://www.w3.org/2000/svg" class="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path></svg>`,
        chatbotClose: `<svg xmlns="http://www.w3.org/2000/svg" class="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>`,
        chatbotSend: `<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor"><path d="M2 21l21-9L2 3v7l15 2-15 2z"></path></svg>`,
        heroPrev: `<svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path></svg>`,
        heroNext: `<svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>`,
    };
    
    // --- ICON INJECTION ---
    const setIcon = (id, icon) => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = icon;
    };
    setIcon('mobile-menu-toggle', icons.menu);
    setIcon('chatbot-toggle', icons.chatbotOpen);
    setIcon('chatbot-close-btn', icons.close);
    setIcon('chatbot-send-btn', icons.chatbotSend);
    setIcon('hero-prev-btn', icons.heroPrev);
    setIcon('hero-next-btn', icons.heroNext);
    setIcon('portfolio-prev-btn', icons.heroPrev);
    setIcon('portfolio-next-btn', icons.heroNext);

    // --- THEME TOGGLE ---
    const htmlEl = document.documentElement;
    const applyTheme = (theme) => {
        const desktopLink = document.getElementById('theme-toggle-link');
        const mobileLink = document.getElementById('mobile-theme-toggle-link');
        if (theme === 'dark') {
            htmlEl.classList.add('dark');
            if(desktopLink) desktopLink.textContent = 'DARK';
            if(mobileLink) mobileLink.textContent = 'DARK';
        } else {
            htmlEl.classList.remove('dark');
            if(desktopLink) desktopLink.textContent = 'LIGHT';
            if(mobileLink) mobileLink.textContent = 'LIGHT';
        }
    };
    const toggleTheme = () => {
        const newTheme = htmlEl.classList.contains('dark') ? 'light' : 'dark';
        localStorage.setItem('theme', newTheme);
        applyTheme(newTheme);
    };
    const currentTheme = localStorage.getItem('theme') || 'light';
    applyTheme(currentTheme);
    const themeToggleLink = document.getElementById('theme-toggle-link');
    const mobileThemeToggleLink = document.getElementById('mobile-theme-toggle-link');
    if (themeToggleLink) themeToggleLink.addEventListener('click', toggleTheme);
    if (mobileThemeToggleLink) mobileThemeToggleLink.addEventListener('click', toggleTheme);
    
    // --- MOBILE MENU ---
    const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
    const mobileMenu = document.getElementById('mobile-menu');
    if (mobileMenuToggle && mobileMenu) {
        const toggleMobileMenu = (isOpen) => {
            if (isOpen) {
                mobileMenu.classList.remove('translate-x-full');
                mobileMenuToggle.innerHTML = icons.close;
                document.body.style.overflow = 'hidden';
            } else {
                mobileMenu.classList.add('translate-x-full');
                mobileMenuToggle.innerHTML = icons.menu;
                document.body.style.overflow = 'unset';
            }
        };
        mobileMenuToggle.addEventListener('click', () => {
            toggleMobileMenu(mobileMenu.classList.contains('translate-x-full'));
        });
        mobileMenu.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => toggleMobileMenu(false));
        });
    }

    // --- HERO CAROUSEL (HOMEPAGE ONLY) ---
    const heroSlidesContainer = document.getElementById('hero-slides-container');
    if (heroSlidesContainer) {
        const heroSlidesData = [
          { image: 'https://images.unsplash.com/photo-1552664730-d307ca884978?q=80&w=2070&auto=format&fit=crop', title: 'Empowering Business Through Women-Led Innovation', description: 'Vendhan Info Tech pioneers bespoke IT solutions that drive growth and efficiency.', linkText: 'Our Services', linkHref: '/services' },
          { image: 'https://images.unsplash.com/photo-1521737604893-d14cc237f11d?q=80&w=2084&auto=format&fit=crop', title: 'Your Vision, Engineered with Precision and Passion', description: 'We collaborate with you to transform ideas into robust, scalable, and secure software.', linkText: 'View Our Work', linkHref: '/portfolio/ai-logistics-platform' },
          { image: 'https://images.unsplash.com/photo-1600880292203-757bb62b4baf?q=80&w=2070&auto=format&fit=crop', title: 'Pioneering AI-Powered Solutions for a Digital Future', description: 'From machine learning models to intelligent automation, we build the future of technology.', linkText: 'Explore AI', linkHref: '/services/ai-machine-learning' },
        ];
        const heroContentContainer = document.getElementById('hero-content-container');
        const heroDotsContainer = document.getElementById('hero-dots-container');
        let heroCurrentIndex = 0;
        
        heroSlidesData.forEach((slide, index) => {
            heroSlidesContainer.innerHTML += `<div class="hero-slide absolute inset-0 w-full h-full transition-opacity duration-1000 ease-in-out ${index === 0 ? 'opacity-100' : 'opacity-0'}"><img src="${slide.image}" alt="${slide.title}" class="w-full h-full object-cover"><div class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent"></div></div>`;
            if(heroDotsContainer) heroDotsContainer.innerHTML += `<button data-index="${index}" class="hero-dot h-1 transition-all duration-500 rounded-full ${index === 0 ? 'bg-white w-12' : 'bg-white/40 w-6 hover:bg-white'}"></button>`;
        });

        const updateHeroContent = (index) => {
            const slide = heroSlidesData[index];
            if(heroContentContainer) heroContentContainer.innerHTML = `<div class="max-w-3xl animate-fade-in"><h1 class="text-5xl md:text-6xl font-light leading-tight">${slide.title}</h1><p class="mt-6 text-lg max-w-2xl text-gray-300">${slide.description}</p><a href="${slide.linkHref}" class="mt-8 inline-block text-lg font-medium text-white border-b-2 border-transparent hover:border-white transition-all duration-300 pb-1">${slide.linkText}</a></div>`;
        };

        const showHeroSlide = (index) => {
            document.querySelectorAll('.hero-slide').forEach((slide, i) => { slide.style.opacity = i === index ? '1' : '0'; });
            document.querySelectorAll('.hero-dot').forEach((dot, i) => { dot.className = `hero-dot h-1 transition-all duration-500 rounded-full ${i === index ? 'bg-white w-12' : 'bg-white/40 w-6 hover:bg-white'}`; });
            updateHeroContent(index);
            heroCurrentIndex = index;
        };
        
        const heroPrevBtn = document.getElementById('hero-prev-btn');
        const heroNextBtn = document.getElementById('hero-next-btn');
        if(heroPrevBtn) heroPrevBtn.addEventListener('click', () => showHeroSlide((heroCurrentIndex - 1 + heroSlidesData.length) % heroSlidesData.length));
        if(heroNextBtn) heroNextBtn.addEventListener('click', () => showHeroSlide((heroCurrentIndex + 1) % heroSlidesData.length));
        if(heroDotsContainer) heroDotsContainer.addEventListener('click', (e) => { if (e.target.matches('.hero-dot')) showHeroSlide(parseInt(e.target.dataset.index)); });
        const heroInterval = setInterval(() => showHeroSlide((heroCurrentIndex + 1) % heroSlidesData.length), 7000);
        showHeroSlide(0);
    }

    // --- PORTFOLIO CAROUSEL (HOMEPAGE ONLY) ---
    const portfolioScrollContainer = document.getElementById('portfolio-scroll-container');
    if(portfolioScrollContainer) {
        const portfolioItems = [
          { image: 'https://images.unsplash.com/photo-1554744512-d6c603f27c54?q=80&w=2070&auto=format&fit=crop', title: 'AI-Powered Logistics Platform', linkHref: '/portfolio/ai-logistics-platform' },
          { image: 'https://images.unsplash.com/photo-1552664730-d307ca884978?q=80&w=2070&auto=format&fit=crop', title: 'Cloud Migration Strategy', linkHref: '/portfolio/cloud-migration' },
          { image: 'https://images.unsplash.com/photo-1521791136064-7986c2920216?q=80&w=2070&auto=format&fit=crop', title: 'Secure Fintech Application', linkHref: '/portfolio/secure-fintech-app' },
          { image: 'https://images.unsplash.com/photo-1517048676732-d65bc937f952?q=80&w=2070&auto=format&fit=crop', title: 'Enterprise ERP Implementation', linkHref: '/portfolio/enterprise-erp' },
        ];
        portfolioItems.forEach(item => {
            portfolioScrollContainer.innerHTML += `<div class="flex-shrink-0 w-[90%] sm:w-1/2 md:w-1/3 lg:w-1/4 snap-start"><div class="relative group rounded-lg overflow-hidden h-[60vh] shadow-lg"><img src="${item.image}" alt="${item.title}" class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105" /><div class="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent"></div><div class="absolute bottom-0 left-0 p-6 text-white"><h3 class="text-3xl font-light">${item.title}</h3><a href="${item.linkHref}" class="mt-2 inline-block text-lg font-medium border-b-2 border-transparent hover:border-white transition-all duration-300">Explore</a></div></div></div>`;
        });
        const scrollPortfolio = (dir) => {
            const scrollAmount = portfolioScrollContainer.offsetWidth * 0.8;
            portfolioScrollContainer.scrollBy({ left: dir === 'left' ? -scrollAmount : scrollAmount, behavior: 'smooth' });
        };
        const portfolioPrevBtn = document.getElementById('portfolio-prev-btn');
        const portfolioNextBtn = document.getElementById('portfolio-next-btn');
        if(portfolioPrevBtn) portfolioPrevBtn.addEventListener('click', () => scrollPortfolio('left'));
        if(portfolioNextBtn) portfolioNextBtn.addEventListener('click', () => scrollPortfolio('right'));
    }

    // --- REFINED SMOOTH SCROLL LOGIC FOR ALL ANCHOR LINKS ---
    document.querySelectorAll('a[href*="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const targetHref = this.getAttribute('href');
            if (targetHref.startsWith('#') || (targetHref.startsWith('/#') && window.location.pathname === '/')) {
                const hash = this.hash;
                const targetElement = document.querySelector(hash);
                if (targetElement) {
                    e.preventDefault();
                    const headerOffset = 80;
                    const elementPosition = targetElement.getBoundingClientRect().top;
                    const offsetPosition = elementPosition + window.pageYOffset - headerOffset;
                    window.scrollTo({ top: offsetPosition, behavior: 'smooth' });
                }
            }
        });
    });
    
    // --- CHATBOT (GLOBAL) ---
    const chatbotToggle = document.getElementById('chatbot-toggle');
    const chatbotWindow = document.getElementById('chatbot-window');
    const chatbotCloseBtn = document.getElementById('chatbot-close-btn');
    const messagesContainer = document.getElementById('chatbot-messages-container');
    const chatForm = document.getElementById('chat-form');
    const inputField = document.getElementById('chatbot-input');
    const sendBtn = document.getElementById('chatbot-send-btn');
    let isChatbotLoading = false;

    const addMessage = (text, type) => {
        if(!messagesContainer) return;
        const messageEl = document.createElement('div');
        messageEl.className = `flex items-start gap-3 ${type === 'user' ? 'justify-end' : 'justify-start'}`;
        const botAvatar = `<div class="w-8 h-8 rounded-full bg-header-blue flex items-center justify-center text-white font-bold flex-shrink-0">V</div>`;
        const textBubble = `<div class="chat-bubble ${type === 'user' ? 'user' : 'bot'}">${text.replace(/\n/g, '<br>')}</div>`;
        messageEl.innerHTML = type === 'bot' ? `${botAvatar}${textBubble}` : textBubble;
        messagesContainer.appendChild(messageEl);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    };
    
    const toggleChatbot = (isOpen) => {
        if(!chatbotWindow || !chatbotToggle) return;
        if (isOpen) {
            chatbotWindow.classList.remove('opacity-0', 'translate-y-4', 'pointer-events-none');
            chatbotToggle.innerHTML = icons.chatbotClose;
            if (messagesContainer.children.length === 0) {
                 addMessage("Hi there! I'm the Vendhan Info Tech AI assistant. How can I help you today?", "bot");
            }
        } else {
            chatbotWindow.classList.add('opacity-0', 'translate-y-4', 'pointer-events-none');
            chatbotToggle.innerHTML = icons.chatbotOpen;
        }
    };

    if (chatbotToggle) chatbotToggle.addEventListener('click', () => toggleChatbot(chatbotWindow.classList.contains('opacity-0')));
    if (chatbotCloseBtn) chatbotCloseBtn.addEventListener('click', () => toggleChatbot(false));
    if (chatForm) chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const userMessage = inputField.value.trim();
        if (userMessage === '' || isChatbotLoading) return;
        
        addMessage(userMessage, 'user');
        inputField.value = '';
        inputField.focus();
        isChatbotLoading = true;
        sendBtn.disabled = true;

        const loadingEl = document.createElement('div');
        loadingEl.id = 'chatbot-loading';
        loadingEl.className = 'flex items-start gap-3 justify-start';
        loadingEl.innerHTML = `<div class="w-8 h-8 rounded-full bg-header-blue flex items-center justify-center text-white font-bold flex-shrink-0">V</div><div class="chat-bubble bot"><div class="flex items-center space-x-1.5"><span class="w-2 h-2 bg-gray-500 dark:bg-gray-400 rounded-full animate-pulse [animation-delay:0s]"></span><span class="w-2 h-2 bg-gray-500 dark:bg-gray-400 rounded-full animate-pulse [animation-delay:0.2s]"></span><span class="w-2 h-2 bg-gray-500 dark:bg-gray-400 rounded-full animate-pulse [animation-delay:0.4s]"></span></div></div>`;
        messagesContainer.appendChild(loadingEl);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        try {
            const response = await fetch('/api/chatbot', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: userMessage }),
            });
            document.getElementById('chatbot-loading')?.remove();
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            addMessage(data.response || "Sorry, an error occurred.", 'bot');
        } catch(error) {
            console.error("Chat API error:", error);
            document.getElementById('chatbot-loading')?.remove();
            addMessage("Sorry, I'm having trouble connecting right now. Please try again later.", 'bot');
        } finally {
            isChatbotLoading = false;
            sendBtn.disabled = false;
        }
    });

    if (messagesContainer) messagesContainer.addEventListener('click', (e) => {
        if (e.target.matches('.chat-link')) {
             toggleChatbot(false);
        }
    });

    // --- UNIFIED FORM HANDLING LOGIC ---
    window.setupForm = (formId, sendBtnId, verifyBtnId, submitBtnId, otpSectionId, timerId, formType, submitUrl) => {
        const form = document.getElementById(formId);
        if (!form) return;

        const sendVerificationBtn = document.getElementById(sendBtnId);
        const verifyOtpBtn = document.getElementById(verifyBtnId);
        const submitBtn = document.getElementById(submitBtnId);
        const otpSection = document.getElementById(otpSectionId);
        const otpTimer = document.getElementById(timerId);
        const otpInputs = otpSection ? otpSection.querySelectorAll('.otp-input') : [];
        const emailInput = form.querySelector('input[name="email"]');
        
        let countdown;

        const showFormMessage = (type, message) => {
            const successMsg = form.querySelector('.success-message');
            const errorMsg = form.querySelector('.error-message');
            if (successMsg) successMsg.style.display = 'none';
            if (errorMsg) errorMsg.style.display = 'none';

            if (type === 'success' && successMsg) {
                successMsg.style.display = 'block';
                successMsg.querySelector('span').textContent = message;
            } else if (type === 'error' && errorMsg) {
                errorMsg.style.display = 'block';
                errorMsg.querySelector('span').textContent = message;
            }
        };

        const startTimer = () => {
            if (!otpTimer) return;
            let duration = 300; // 5 minutes
            clearInterval(countdown);
            otpTimer.style.display = 'block';
            countdown = setInterval(() => {
                const minutes = Math.floor(duration / 60);
                const seconds = duration % 60;
                otpTimer.textContent = `Code expires in ${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
                if (--duration < 0) {
                    clearInterval(countdown);
                    otpTimer.textContent = 'Code expired. Please request a new one.';
                    if(verifyOtpBtn) verifyOtpBtn.disabled = true;
                }
            }, 1000);
        };

        if (sendVerificationBtn) {
            sendVerificationBtn.addEventListener('click', async () => {
                if (!emailInput.value || !emailInput.checkValidity()) {
                    showFormMessage('error', 'Please enter a valid email address.');
                    return;
                }
                sendVerificationBtn.disabled = true;
                sendVerificationBtn.textContent = 'SENDING...';
                try {
                    const response = await fetch('/api/send-otp', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ email: emailInput.value })
                    });
                    const data = await response.json();
                    showFormMessage(response.ok ? 'success' : 'error', data.message || data.error);
                    if (response.ok) {
                        if(otpSection) otpSection.style.display = 'block';
                        startTimer();
                    }
                } catch (error) {
                    console.error('Send OTP Error:', error);
                    showFormMessage('error', 'Failed to connect. Please check your connection.');
                } finally {
                    sendVerificationBtn.disabled = false;
                    sendVerificationBtn.textContent = sendBtnId.includes('Contact') ? 'Verify Email to Send' : 'Send Verification Code';
                }
            });
        }
        
        if (verifyOtpBtn) {
            verifyOtpBtn.addEventListener('click', async () => {
                const otp = Array.from(otpInputs).map(input => input.value).join('');
                if (otp.length !== 6) {
                    showFormMessage('error', 'Please enter the full 6-digit code.');
                    return;
                }
                try {
                    const response = await fetch('/api/verify-otp', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ email: emailInput.value, otp: otp })
                    });
                    const data = await response.json();
                    if (!response.ok) {
                        showFormMessage('error', data.error);
                    } else {
                        showFormMessage('success', data.message);
                        otpSection.style.display = 'none';
                        submitBtn.disabled = false;
                        clearInterval(countdown);
                    }
                } catch (error) {
                    console.error('Verify OTP Error:', error);
                    showFormMessage('error', 'Failed to connect to the server.');
                }
            });
        }
        
        if (otpInputs.length > 0) {
            otpInputs.forEach((input, index) => {
                input.addEventListener('keyup', (e) => {
                    const key = e.key;
                    if (key >= 0 && key <= 9) {
                        input.value = key;
                        if (index < otpInputs.length - 1) otpInputs[index + 1].focus();
                    } else if (key === 'Backspace') {
                        if (index > 0) otpInputs[index - 1].focus();
                    }
                });
            });
        }

        if (form) {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                if (submitBtn.disabled) {
                    showFormMessage('error', 'Please verify your email before submitting.');
                    return;
                }
                const originalSubmitText = submitBtn.textContent;
                submitBtn.innerHTML = '<span class="animate-spin h-5 w-5 border-t-2 border-r-2 border-white rounded-full inline-block mr-2"></span>Submitting...';
                submitBtn.disabled = true;
                try {
                    const formData = new FormData(form);
                    const response = await fetch(submitUrl, {
                        method: 'POST',
                        body: formData
                    });
                    const data = await response.json();
                    showFormMessage(response.ok ? 'success' : 'error', data.message || data.error);
                    if (response.ok) {
                        form.reset();
                        submitBtn.disabled = true;
                    } else {
                        submitBtn.disabled = false;
                    }
                } catch (error) {
                    console.error('Form Submission Error:', error);
                    showFormMessage('error', 'An error occurred during submission.');
                    submitBtn.disabled = false;
                } finally {
                    submitBtn.innerHTML = originalSubmitText;
                }
            });
        }
    };
});