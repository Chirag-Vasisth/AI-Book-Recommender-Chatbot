document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const chatContainer = document.getElementById('chat-container');
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const voiceBtn = document.getElementById('voice-btn');
    const typingIndicator = document.getElementById('typing-indicator');
    const feedbackContainer = document.getElementById('feedback-container');
    const themeToggle = document.getElementById('theme-toggle');
    const newChatBtn = document.getElementById('new-chat-btn');
    const moodSelect = document.getElementById('mood-select');
    const languageSelect = document.getElementById('language-select');
    const dailyBookElement = document.getElementById('daily-book');
    const quickSuggestionBtns = document.querySelectorAll('.quick-suggestion-btn');

    // State variables
    let conversationHistory = [];
    let currentMessageId = 0;
    let currentFeedbackMessageId = null;
    
    // Initialize the chat
    initChat();
    
    // Event Listeners
    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    voiceBtn.addEventListener('click', toggleVoiceRecognition);
    themeToggle.addEventListener('click', toggleTheme);
    newChatBtn.addEventListener('click', startNewChat);
    moodSelect.addEventListener('change', updateMoodBackground);
    languageSelect.addEventListener('change', updateLanguage);
    
    quickSuggestionBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            userInput.value = this.getAttribute('data-prompt');
            sendMessage();
        });
    });
    
    // Initialize functions
    function initChat() {
        loadThemePreference();
        loadDailyBook();
        greetUser();
    }
    
    function greetUser() {
        const hour = new Date().getHours();
        let greeting;
        
        if (hour < 12) greeting = "Good morning";
        else if (hour < 18) greeting = "Good afternoon";
        else greeting = "Good evening";
        
        addBotMessage(`${greeting}! I'm your Book Recommender chatbot. How can I assist you with your reading needs today?`);
    }
    
    function loadDailyBook() {
        // Fetch the daily book recommendation from the backend
        fetch(`${API_BASE_URL}/api/daily_book`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error('Error loading daily book:', data.error);
                    // Use fallback data if there's an error
                    dailyBookElement.innerHTML = `
                        <p><span class="book-title">The Midnight Library</span> by <span class="book-author">Matt Haig</span></p>
                        <p class="book-description">Between life and death there is a library, and within that library, the shelves go on forever. Every book provides a chance to try another life you could have lived.</p>
                        <p><small>Genre: Fiction, Fantasy</small></p>
                    `;
                } else {
                    // Parse the book string from the backend
                    // Expected format: "Title" by Author (Genre) - Description
                    const bookString = data.book;
                    const titleMatch = bookString.match(/"([^"]+)"/);
                    const authorMatch = bookString.match(/by ([^(]+)/);
                    const genreMatch = bookString.match(/\(([^)]+)\)/);
                    const descriptionMatch = bookString.match(/- (.+)$/);
                    
                    const title = titleMatch ? titleMatch[1] : 'Unknown Title';
                    const author = authorMatch ? authorMatch[1].trim() : 'Unknown Author';
                    const genre = genreMatch ? genreMatch[1] : 'Fiction';
                    const description = descriptionMatch ? descriptionMatch[1] : 'No description available.';
                    
                    dailyBookElement.innerHTML = `
                        <p><span class="book-title">${title}</span> by <span class="book-author">${author}</span></p>
                        <p class="book-description">${description}</p>
                        <p><small>Genre: ${genre}</small></p>
                    `;
                }
            })
            .catch(error => {
                console.error('Error fetching daily book:', error);
                // Use fallback data if there's an error
                dailyBookElement.innerHTML = `
                    <p><span class="book-title">The Midnight Library</span> by <span class="book-author">Matt Haig</span></p>
                    <p class="book-description">Between life and death there is a library, and within that library, the shelves go on forever. Every book provides a chance to try another life you could have lived.</p>
                    <p><small>Genre: Fiction, Fantasy</small></p>
                `;
            });
    }
    
    function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        const messageId = currentMessageId++;
        addUserMessage(message, messageId);
        userInput.value = '';
        
        // Show typing indicator
        showTypingIndicator();
        
        // Add to conversation history
        conversationHistory.push({ role: 'user', content: message });
        
        // Send to backend
        fetch(`${API_BASE_URL}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                history: conversationHistory,
                mood: moodSelect.value,
                language: languageSelect.value
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            hideTypingIndicator();
            
            if (data.error) {
                console.error('API Error:', data.error, data.details || '');
                addBotMessage("I apologize, but I'm unable to process that request. As a book recommender, I specialize in suggesting reading materials and discussing literature. Could you please ask me something related to books or reading?", messageId);
            } else {
                addBotMessage(data.response, messageId);
                currentFeedbackMessageId = messageId;
                setTimeout(() => {
                    feedbackContainer.classList.remove('hidden');
                }, 500);
                
                // Update conversation history
                conversationHistory.push({ role: 'assistant', content: data.response });
                
                // Save conversation to local storage
                saveConversation();
            }
        })
        .catch(error => {
            hideTypingIndicator();
            console.error('Error:', error);
            addBotMessage("I'm sorry, I encountered an error processing your request. Please try again later.", messageId);
        });
    }
    
    function addUserMessage(message, messageId) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message user-message';
        messageElement.dataset.messageId = messageId;
        messageElement.innerHTML = `
            <div>${message}</div>
            <div class="message-time">${formatTime(new Date())}</div>
        `;
        chatMessages.appendChild(messageElement);
        scrollToBottom();
    }
    
    function addBotMessage(message, inReplyTo = null) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message bot-message';
        if (inReplyTo !== null) {
            messageElement.dataset.inReplyTo = inReplyTo;
        }
        
        // Parse message for book recommendations (in a real app, this would be structured data from the backend)
        const parsedMessage = parseBookRecommendations(message);
        
        messageElement.innerHTML = `
            <div>${parsedMessage}</div>
            <div class="message-time">${formatTime(new Date())}</div>
        `;
        chatMessages.appendChild(messageElement);
        scrollToBottom();
        
        // Add progressive disclosure for long content
        addProgressiveDisclosure(messageElement);
    }
    
    function parseBookRecommendations(message) {
        // This is a simplified version - in a real app, the backend would send structured data
        // Here we just look for patterns that might indicate a book recommendation
        const bookPattern = /"([^"]+)" by ([^\.,]+)/g;
        return message.replace(bookPattern, '<div class="book-suggestion"><span class="book-title">$1</span> by <span class="book-author">$2</span></div>');
    }
    
    function addProgressiveDisclosure(messageElement) {
        const content = messageElement.querySelector('div:first-child');
        if (content.textContent.length > 300) {
            const shortContent = content.textContent.substring(0, 300) + '...';
            const fullContent = content.innerHTML;
            
            content.innerHTML = shortContent;
            
            const disclosureBtn = document.createElement('button');
            disclosureBtn.className = 'disclosure-btn';
            disclosureBtn.innerHTML = 'Show more <i class="fas fa-chevron-down"></i>';
            
            const disclosureContent = document.createElement('div');
            disclosureContent.className = 'disclosure-content';
            disclosureContent.innerHTML = fullContent.substring(300);
            
            disclosureBtn.addEventListener('click', function() {
                disclosureContent.classList.toggle('show');
                this.innerHTML = disclosureContent.classList.contains('show') ? 
                    'Show less <i class="fas fa-chevron-up"></i>' : 
                    'Show more <i class="fas fa-chevron-down"></i>';
            });
            
            const disclosureContainer = document.createElement('div');
            disclosureContainer.className = 'progressive-disclosure';
            disclosureContainer.appendChild(disclosureBtn);
            disclosureContainer.appendChild(disclosureContent);
            
            messageElement.appendChild(disclosureContainer);
        }
    }
    
    function showTypingIndicator() {
        typingIndicator.style.display = 'flex';
        scrollToBottom();
    }
    
    function hideTypingIndicator() {
        typingIndicator.style.display = 'none';
    }
    
    function scrollToBottom() {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    function formatTime(date) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    function toggleVoiceRecognition() {
        if (window.voiceRecognitionActive) {
            stopVoiceRecognition();
            voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
        } else {
            startVoiceRecognition();
            voiceBtn.innerHTML = '<i class="fas fa-microphone-slash"></i>';
        }
    }
    
    function toggleTheme() {
        document.body.classList.toggle('light-mode');
        const isLightMode = document.body.classList.contains('light-mode');
        localStorage.setItem('theme', isLightMode ? 'light' : 'dark');
        themeToggle.innerHTML = isLightMode ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
    }
    
    function loadThemePreference() {
        const savedTheme = localStorage.getItem('theme') || 'dark';
        if (savedTheme === 'light') {
            document.body.classList.add('light-mode');
            themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
        }
    }
    
    function startNewChat() {
        if (confirm('Are you sure you want to start a new chat? Your current conversation will be saved.')) {
            // Save current conversation to history
            saveConversationToHistory();
            
            // Clear current conversation
            chatMessages.innerHTML = '';
            conversationHistory = [];
            feedbackContainer.classList.add('hidden');
            
            // Show welcome message again
            document.querySelector('.welcome-message').style.display = 'block';
            
            // Greet user
            greetUser();
        }
    }
    
    function saveConversationToHistory() {
        if (conversationHistory.length > 0) {
            const chatHistory = JSON.parse(localStorage.getItem('chatHistory') || '[]');
            chatHistory.push({
                date: new Date().toISOString(),
                messages: conversationHistory
            });
            localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
        }
    }
    
    function saveConversation() {
        localStorage.setItem('currentConversation', JSON.stringify(conversationHistory));
    }
    
    function loadConversation() {
        const savedConversation = localStorage.getItem('currentConversation');
        if (savedConversation) {
            conversationHistory = JSON.parse(savedConversation);
            // Re-render conversation
            renderConversation();
        }
    }
    
    function renderConversation() {
        chatMessages.innerHTML = '';
        conversationHistory.forEach((msg, index) => {
            if (msg.role === 'user') {
                addUserMessage(msg.content, index);
            } else {
                addBotMessage(msg.content, index-1);
            }
        });
    }
    
    function updateMoodBackground() {
        // Remove all mood classes first
        document.body.classList.remove('adventurous', 'romantic', 'mysterious', 'thoughtful');
        
        // Add selected mood class
        const mood = moodSelect.value;
        if (mood !== 'default') {
            document.body.classList.add(mood);
        }
    }
    
    function updateLanguage() {
        const language = languageSelect.value;
        // In a real app, this would trigger a translation of the UI
        console.log('Language changed to:', language);
    }
    
    // Feedback handling
    document.querySelectorAll('.feedback-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const isLike = this.classList.contains('like');
            if (currentFeedbackMessageId !== null) {
                sendFeedback(currentFeedbackMessageId, isLike);
            }
        });
    });
    
    function sendFeedback(messageId, isPositive) {
        // In a real app, this would send feedback to the backend
        fetch(`${API_BASE_URL}/api/feedback`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                messageId: messageId,
                isPositive: isPositive
            })
        }).catch(error => console.error('Error sending feedback:', error));
    }
    
    // Load any saved conversation
    loadConversation();
});