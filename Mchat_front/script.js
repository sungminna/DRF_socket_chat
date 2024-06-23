let currentUserEmail = null;
let currentRoomId = null;
let socket = null;
let visitorUserEmail = null; 
let sortedEmails = null; 

document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const messageInput = document.getElementById('message-input');
    const sendBtn = document.getElementById('send-btn');

    messageInput.addEventListener('keyup', (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            sendMessage(currentUserEmail);
        }
    });

    window.loginAsUser = async (email) => {
        currentUserEmail = email;
        visitorUserEmail = email === "qw@naver.com" ? "er@naver.com" : "qw@naver.com";
        await openOrCreateRoom();
    };

    async function openOrCreateRoom() {
        if (socket) {
            socket.close();
        }

        sortedEmails = [currentUserEmail, visitorUserEmail].sort();

        const response = await fetch('http://127.0.0.1:8000/chat/rooms/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                shop_user_email: sortedEmails[0],
                visitor_user_email: sortedEmails[1]
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const roomData = await response.json();
        currentRoomId = roomData.id;
        displayMessages(roomData.messages);
        setupWebSocket(currentRoomId);

        sendBtn.onclick = () => sendMessage(currentUserEmail);
    }

    function displayMessages(messages) {
        chatMessages.innerHTML = '';
        messages.forEach((message) => {
            if (message.sender_email && message.text) {
                const messageElem = document.createElement('div');
                messageElem.classList.add('message-bubble');
                messageElem.textContent = `${message.sender_email}: ${message.text}`;

                if (message.sender_email === currentUserEmail) {
                    messageElem.classList.add('sent');
                } else {
                    messageElem.classList.add('received');
                }

                chatMessages.appendChild(messageElem);
            }
        });
        chatMessages.scrollTop = chatMessages.scrollHeight; 
    }

    function setupWebSocket(roomId) {
        socket = new WebSocket(`ws://127.0.0.1:8000/ws/room/${roomId}/messages`);

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            const messageElem = document.createElement('div');
            messageElem.classList.add('message-bubble');
            messageElem.textContent = `${data.sender_email}: ${data.message}`;

            if (data.sender_email === currentUserEmail) {
                messageElem.classList.add('sent');
            } else {
                messageElem.classList.add('received');
            }

            chatMessages.appendChild(messageElem);
            chatMessages.scrollTop = chatMessages.scrollHeight; 
        };
    }

    function sendMessage(userEmail) {
        const message = messageInput.value;
        if (message) {
            const messagePayload = {
                'sender_email': userEmail,
                'message': message,
                'shop_user_email': sortedEmails[0],
                'visitor_user_email': sortedEmails[1]
            };

            socket.send(JSON.stringify(messagePayload));
            messageInput.value = ''; 
        }
    }
});