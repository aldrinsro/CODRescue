
// static/js/chatbot.js
// Gère l'ouverture/fermeture du modal et l'appel à l'API REST du chatbot

const chatbotModal = document.getElementById('chatbot-modal');
const closeChatbotBtn = document.getElementById('close-chatbot');
const chatbotForm = document.getElementById('chatbot-form');
const chatbotInput = document.getElementById('chatbot-input');
const chatbotMessages = document.getElementById('chatbot-messages');

const bodyDataset = document.body ? document.body.dataset : {};

function showChatbotModal() {
  if (chatbotModal) {
    chatbotModal.classList.remove('hidden');
  }
}

if (closeChatbotBtn) {
  closeChatbotBtn.onclick = function () {
    chatbotModal.classList.add('hidden');
  };
}

function getCSRFToken() {
  const name = 'yz_csrf_token';
  const cookies = document.cookie.split(';');
  for (let i = 0; i < cookies.length; i++) {
    let cookie = cookies[i].trim();
    if (cookie.startsWith(name + '=')) {
      return decodeURIComponent(cookie.substring(name.length + 1));
    }
  }
  return '';
}

function buildChatbotPayload(question) {
  return {
    question,
    interface: bodyDataset.interface || window.CURRENT_INTERFACE || null,
    user_type: bodyDataset.userType || null,
    user_name: bodyDataset.userName || null,
    user_id: bodyDataset.userId || null,
  };
}

if (chatbotForm) {
  chatbotForm.onsubmit = async function (e) {
    e.preventDefault();
    const userMsg = chatbotInput.value.trim();
    if (!userMsg) return;
    appendMessage('Vous', userMsg);
    chatbotInput.value = '';
    appendMessage('Assistant', '...');
    try {
      const payload = buildChatbotPayload(userMsg);
      const aiMsg = await envoyerMessageBackend(payload);
      replaceLastAssistantMessage(aiMsg);
    } catch (err) {
      replaceLastAssistantMessage('Erreur lors de la connexion au chatbot.');
    }
  };
}

function appendMessage(sender, text) {
  const msg = document.createElement('div');
  msg.className = sender === 'Vous' ? 'text-right mb-1' : 'text-left mb-1 text-blue-700';
  msg.innerHTML = `<strong>${sender} :</strong> ${text}`;
  chatbotMessages.appendChild(msg);
  chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
}

function afficherReponse(text) {
  appendMessage('Assistant', text);
}

function replaceLastAssistantMessage(text) {
  const msgs = chatbotMessages.querySelectorAll('div');
  for (let i = msgs.length - 1; i >= 0; i--) {
    if (msgs[i].innerHTML.startsWith('<strong>Assistant')) {
      msgs[i].innerHTML = `<strong>Assistant :</strong> ${text}`;
      break;
    }
  }
}


async function envoyerMessageBackend(body) {
  const response = await fetch('/chatbot/api/chatbot/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCSRFToken()
    },
    body: JSON.stringify(body)
  });
  const data = await response.json();

  // Essaie plusieurs clés de réponse possibles
  if (data && typeof data.output === 'string') {
    return data.output;
  }
  if (data && typeof data.answer === 'string') {
    return data.answer;
  }
  if (data && typeof data.response === 'string') {
    return data.response;
  }
  if (data && data.error) {
    return data.error;
  }

  // Si c'est un objet, essaie de l'afficher en JSON
  if (data && typeof data === 'object') {
    console.log('Réponse complète du chatbot:', data);
    return JSON.stringify(data, null, 2);
  }

  return 'Aucune réponse générée.';
}

// Pour ouvrir le chatbot depuis n'importe où :
window.showChatbotModal = showChatbotModal;
