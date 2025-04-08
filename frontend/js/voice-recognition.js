// Check if browser supports speech recognition
if ('webkitSpeechRecognition' in window) {
    const recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';
    
    window.voiceRecognitionActive = false;
    
    recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        document.getElementById('user-input').value = transcript;
    };
    
    recognition.onerror = function(event) {
        console.error('Voice recognition error', event.error);
        alert('Voice recognition error: ' + event.error);
        stopVoiceRecognition();
    };
    
    recognition.onend = function() {
        if (window.voiceRecognitionActive) {
            recognition.start();
        } else {
            document.getElementById('voice-btn').innerHTML = '<i class="fas fa-microphone"></i>';
        }
    };
    
    window.startVoiceRecognition = function() {
        recognition.start();
        window.voiceRecognitionActive = true;
        document.getElementById('voice-btn').innerHTML = '<i class="fas fa-microphone-slash"></i>';
    };
    
    window.stopVoiceRecognition = function() {
        recognition.stop();
        window.voiceRecognitionActive = false;
    };
} else {
    document.getElementById('voice-btn').style.display = 'none';
    console.warn('Speech recognition not supported in this browser');
}