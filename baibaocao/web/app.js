// API functions
// Stable session id per window to bind to one TCP connection via gateway
const SID = (() => {
  try { return crypto.randomUUID(); } catch (_) { return 'sid-' + Date.now() + '-' + Math.random().toString(36).slice(2); }
})();

const API = {
  send: async (obj) => {
    const response = await fetch('/api/send?sid=' + encodeURIComponent(SID), {
      method: 'POST', 
      headers: {'Content-Type': 'application/json'}, 
      body: JSON.stringify(obj)
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
  },
  
  poll: () => fetch('/api/poll?sid=' + encodeURIComponent(SID)).then(r => r.json()),
};

// App state
let currentUser = null;
let currentChat = null;
let friends = [];
let groups = [];
let friendRequests = []; // pending incoming requests only

// Track displayed messages to avoid duplicates per conversation key
let displayedMessageIds = new Set();

// Track my reactions per message: messageId -> Set(emojis)
const myReactions = new Map();

// Reply state
let replyToMessage = null;

// Keep reference to the currently opened action bar
let openedActions = null;

function hideOpenedActions(except) {
  if (openedActions && openedActions !== except) {
    openedActions.style.display = 'none';
  }
  if (except) openedActions = except; else openedActions = null;
}

// Close actions when clicking outside
window.addEventListener('click', () => hideOpenedActions(null));

// DOM elements
const elements = {
  // Login screen
  loginScreen: document.getElementById('loginScreen'),
  mainScreen: document.getElementById('mainScreen'),
  username: document.getElementById('username'),
  password: document.getElementById('password'),
  loginBtn: document.getElementById('loginBtn'),
  registerBtn: document.getElementById('registerBtn'),
  loginStatus: document.getElementById('loginStatus'),
  togglePassword: document.getElementById('togglePassword'),
  
  // Main screen
  currentUser: document.getElementById('currentUser'),
  themeBtn: document.getElementById('themeBtn'),
  logoutBtn: document.getElementById('logoutBtn'),
  
  // Friends
  friendUserId: document.getElementById('friendUserId'),
  addFriendBtn: document.getElementById('addFriendBtn'),
  friendsList: document.getElementById('friendsList'),
  friendRequestsList: document.getElementById('friendRequestsList'),
  
  // Groups
  groupName: document.getElementById('groupName'),
  createGroupBtn: document.getElementById('createGroupBtn'),
  groupsList: document.getElementById('groupsList'),
  
  // Chat
  chatHeader: document.getElementById('chatHeader'),
  chatMessages: document.getElementById('chatMessages'),
  chatInput: document.getElementById('chatInput'),
  messageInput: document.getElementById('messageInput'),
  sendBtn: document.getElementById('sendBtn'),
};

const tabsBar = document.getElementById('tabsBar');
const MAX_TABS = 4;
let openTabs = []; // [{key,title,type,data}]

function convKeyForFriend(friend){ return 'peer-' + friend.user_id; }
function convKeyForGroup(group){ return 'group-' + group.group_id; }

function ensureTabForConversation(conv){
  const key = conv.type === 'friend' ? convKeyForFriend(conv.data) : convKeyForGroup(conv.data);
  const title = conv.type === 'friend' ? conv.data.username : conv.data.name;
  const exists = openTabs.find(t => t.key === key);
  if (!exists){
    if (openTabs.length >= MAX_TABS){
      // remove the oldest tab (front)
      openTabs.shift();
    }
    openTabs.push({ key, title, type: conv.type, data: conv.data });
    renderTabs();
  }
  activateTab(key);
}

function renderTabs(){
  if (!tabsBar) return;
  tabsBar.innerHTML = '';
  openTabs.forEach((t, idx) => {
    const tab = document.createElement('div');
    tab.className = 'tab-item' + ((currentChat && tabKeyOfCurrent()===t.key) ? ' active' : '');
    tab.onclick = (e)=>{ e.stopPropagation(); activateTab(t.key); };
    const title = document.createElement('div');
    title.className = 'tab-title';
    title.textContent = t.title;
    const close = document.createElement('button');
    close.className = 'tab-close';
    close.textContent = '×';
    close.onclick = (e)=>{ e.stopPropagation(); closeTab(t.key); };
    tab.appendChild(title);
    tab.appendChild(close);
    tabsBar.appendChild(tab);
  });
}

function tabKeyOfCurrent(){
  if (!currentChat) return null;
  return currentChat.type === 'friend' ? convKeyForFriend(currentChat.data) : convKeyForGroup(currentChat.data);
}

function activateTab(key){
  const t = openTabs.find(x=>x.key===key);
  if (!t) return;
  if (t.type === 'friend') selectFriend(t.data, null); else selectGroup(t.data);
  renderTabs();
}

function closeTab(key){
  const idx = openTabs.findIndex(x=>x.key===key);
  if (idx === -1) return;
  const wasActive = (tabKeyOfCurrent() === key);
  openTabs.splice(idx,1);
  renderTabs();
  if (wasActive){
    const nextIdx = Math.max(0, idx-1);
    const next = openTabs[nextIdx];
    if (next) activateTab(next.key); else { currentChat=null; clearChat(); }
  }
}

function chatKey() {
  if (!currentChat) return 'none';
  if (currentChat.type === 'friend') return 'peer-' + currentChat.data.user_id;
  if (currentChat.type === 'group') return 'group-' + currentChat.data.group_id;
  return 'none';
}

function resetConversationState() {
  displayedMessageIds = new Set();
  elements.chatMessages.innerHTML = '';
}

// Utility functions
function showScreen(screenName) {
  if (screenName === 'login') {
    elements.loginScreen.classList.remove('hidden');
    elements.mainScreen.classList.add('hidden');
  } else {
    elements.loginScreen.classList.add('hidden');
    elements.mainScreen.classList.remove('hidden');
  }
}

function showStatus(message, type = 'info') {
  elements.loginStatus.textContent = message;
  elements.loginStatus.className = `login-status ${type}`;
}

function formatTime(timestamp) {
  const date = new Date(timestamp * 1000);
  return date.toLocaleTimeString('vi-VN', { 
    hour: '2-digit', 
    minute: '2-digit' 
  });
}

// Password toggle functionality
function togglePasswordVisibility() {
  const passwordInput = elements.password;
  const toggleBtn = elements.togglePassword;
  
  if (passwordInput.type === 'password') {
    passwordInput.type = 'text';
    toggleBtn.classList.add('showing');
  } else {
    passwordInput.type = 'password';
    toggleBtn.classList.remove('showing');
  }
}

function parseReactionSummary(text) {
  const map = {};
  if (!text) return map;
  text.split(/\s{2,}/).forEach(part => {
    const m = part.trim().match(/(.+)\s+(\d+)/);
    if (m) map[m[1]] = parseInt(m[2], 10) || 0;
  });
  return map;
}

function formatReactionSummary(map) {
  const parts = Object.entries(map)
    .filter(([_, v]) => (v || 0) > 0)
    .map(([k,v]) => `${k} ${v}`);
  return parts.join('  ');
}

function createMessageActions(message, isOwn) {
  const actions = document.createElement('div');
  actions.style.display = 'none';
  actions.style.gap = '8px';
  actions.style.marginTop = '4px';
  actions.style.fontSize = '12px';
  
  setTimeout(() => {
    const msgNode = document.getElementById('msg-' + message.message_id);
    if (msgNode) {
      msgNode.onclick = (e) => {
        e.stopPropagation();
        const willShow = actions.style.display === 'none';
        hideOpenedActions(willShow ? actions : null);
        if (willShow) actions.style.display = 'flex';
      };
    }
  }, 0);

  const emojis = ['👍','❤️','😂'];
  emojis.forEach(em => {
    const btn = document.createElement('button');
    btn.className = 'btn btn-small';
    btn.textContent = em;
    btn.style.padding = '2px 6px';
    btn.onclick = async (e) => {
      e.stopPropagation();
      try {
        // Determine current toggle state based on myReactions
        const curSet = myReactions.get(message.message_id) || new Set();
        const isRemoving = curSet.has(em);
        const line = document.getElementById(`react-${message.message_id}`);
        if (line) {
          const map = parseReactionSummary(line.textContent);
          if (isRemoving) {
            if (map[em]) {
              map[em] = Math.max(0, map[em] - 1);
              if (map[em] === 0) delete map[em];
            }
            curSet.delete(em);
          } else {
            map[em] = (map[em] || 0) + 1;
            curSet.add(em);
          }
          if (curSet.size > 0) myReactions.set(message.message_id, curSet); else myReactions.delete(message.message_id);
          line.textContent = formatReactionSummary(map);
        }
        actions.style.display = 'none';
        hideOpenedActions(null);
        await API.send({ type: 'MSG_REACT', data: { message_id: message.message_id, reaction: em } });
      } catch {}
    };
    actions.appendChild(btn);
  });

  const replyBtn = document.createElement('button');
  replyBtn.className = 'btn btn-small';
  replyBtn.textContent = '↩ Trả lời';
  replyBtn.onclick = (e) => { e.stopPropagation(); replyToMessage = message; actions.style.display = 'none'; hideOpenedActions(null); showReplyBar(); };
  actions.appendChild(replyBtn);

  if (isOwn) {
    const delBtn = document.createElement('button');
    delBtn.className = 'btn btn-small btn-danger';
    delBtn.textContent = 'Xóa';
    delBtn.onclick = async (e) => { e.stopPropagation(); actions.style.display = 'none'; hideOpenedActions(null); try { await API.send({ type: 'MSG_RECALL', data: { message_id: message.message_id } }); } catch {} };
    actions.appendChild(delBtn);
  }
  return actions;
}

function showReplyBar() {
  if (!replyToMessage) return;
  let bar = document.getElementById('replyBar');
  if (!bar) {
    bar = document.createElement('div');
    bar.id = 'replyBar';
    bar.style.padding = '6px 10px';
    bar.style.borderTop = '1px solid var(--border-color)';
    bar.style.background = 'var(--bg-tertiary)';
    bar.style.display = 'flex';
    bar.style.alignItems = 'center';
    bar.style.justifyContent = 'space-between';
    const container = elements.chatInput;
    container.prepend(bar);
  }
  bar.innerHTML = '';
  const text = document.createElement('div');
  text.textContent = `Đang trả lời: "${replyToMessage.content || '[Đã thu hồi]'}"`;
  text.style.fontSize = '12px';
  text.style.color = 'var(--text-secondary)';
  const cancelBtn = document.createElement('button');
  cancelBtn.className = 'btn btn-small';
  cancelBtn.textContent = 'Hủy';
  cancelBtn.onclick = () => { replyToMessage = null; const el = document.getElementById('replyBar'); if (el) el.remove(); };
  bar.appendChild(text);
  bar.appendChild(cancelBtn);
}

// Message handling
function addMessage(message, isOwn = false) {
  if (!message || !message.message_id) { message.message_id = Math.floor(message.created_at * 1000); }
  if (displayedMessageIds.has(message.message_id)) return;
  displayedMessageIds.add(message.message_id);
  
  const messageDiv = document.createElement('div');
  messageDiv.id = 'msg-' + message.message_id;
  messageDiv.className = `message ${isOwn ? 'own' : 'other'}`;
  
  const bubble = document.createElement('div');
  bubble.className = 'message-bubble';
  bubble.textContent = message.content || '[Đã thu hồi]';
  
  const time = document.createElement('div');
  time.className = 'message-time';
  time.textContent = formatTime(message.created_at);
  
  messageDiv.appendChild(bubble);
  messageDiv.appendChild(time);
  
  const actions = createMessageActions(message, isOwn);
  messageDiv.appendChild(actions);
  
  const reactLine = document.createElement('div');
  reactLine.className = 'react-line';
  reactLine.id = `react-${message.message_id}`;
  messageDiv.appendChild(reactLine);
  updateReactionSummary(message.message_id, message.reactions_summary);
  
  elements.chatMessages.appendChild(messageDiv);
  elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

function updateReactionSummary(messageId, summary) {
  const el = document.getElementById(`react-${messageId}`);
  if (!el) return;
  if (!summary || Object.keys(summary).length === 0) {
    el.textContent = '';
    return;
  }
  const filtered = Object.fromEntries(Object.entries(summary).filter(([_, v]) => (v || 0) > 0));
  el.textContent = formatReactionSummary(filtered);
}

function clearChat() {
  displayedMessageIds = new Set();
  elements.chatMessages.innerHTML = '';
  elements.chatInput.classList.add('hidden');
  const rb = document.getElementById('replyBar'); if (rb) rb.remove();
  replyToMessage = null;
  elements.chatHeader.innerHTML = '<h3>Chọn bạn bè hoặc nhóm để bắt đầu chat</h3>';
}

// Friends management
function renderFriends() {
  // Check if friends list actually changed to avoid unnecessary re-renders
  const currentFriendsHtml = elements.friendsList.innerHTML;
  
  // Filter out current user and duplicates
  const seen = new Set();
  const cleanFriends = (friends || []).filter(f => {
    if (!f || typeof f.user_id !== 'number') return false;
    if (currentUser && f.user_id === currentUser.user_id) return false;
    if (seen.has(f.user_id)) return false;
    seen.add(f.user_id);
    return true;
  });
  
  const newFriendsHtml = cleanFriends.length === 0 
    ? '<li>Chưa có bạn bè</li>'
    : cleanFriends.map(friend => 
        `<li onclick="selectFriendById(${friend.user_id})">${friend.username} (ID: ${friend.user_id})</li>`
      ).join('');
  
  // Only update DOM if content actually changed
  if (currentFriendsHtml !== newFriendsHtml) {
    elements.friendsList.innerHTML = newFriendsHtml;
  }
}

function renderFriendRequests() {
  // Check if friend requests list actually changed to avoid unnecessary re-renders
  const currentRequestsHtml = elements.friendRequestsList.innerHTML;
  
  const newRequestsHtml = friendRequests.length === 0 
    ? '<li>Không có lời mời nào</li>'
    : friendRequests.map(request => {
        const rid = request.request_id || request.id;
        return `
          <li class="friend-request-item">
            <div class="friend-request-info">Lời mời từ: ${request.from_username || `User ${request.from_user_id}`}</div>
            <div class="friend-request-actions">
              <button class="btn btn-success" onclick="acceptFriendRequest(${rid})">Chấp nhận</button>
            </div>
          </li>
        `;
      }).join('');
  
  // Only update DOM if content actually changed
  if (currentRequestsHtml !== newRequestsHtml) {
    elements.friendRequestsList.innerHTML = newRequestsHtml;
  }
}

function selectFriendById(userId) {
  const friend = friends.find(f => f.user_id === userId);
  if (!friend) return;
  selectFriend(friend, null);
}

function selectFriend(friend, listItemEl) {
  if (!friend || (currentUser && friend.user_id === currentUser.user_id)) {
    alert('Không thể chat với chính mình');
    return;
  }
  currentChat = { type: 'friend', data: friend };
  
  // Header with unfriend button
  elements.chatHeader.innerHTML = `
    <div style="display:flex;align-items:center;justify-content:space-between;gap:12px;">
      <h3 style="margin:0;">Chat với ${friend.username}</h3>
      <button id="unfriendBtn" class="btn btn-danger btn-small">Hủy bạn</button>
    </div>`;
  elements.chatInput.classList.remove('hidden');
  
  // Set active state
  document.querySelectorAll('#friendsList li').forEach(li => li.classList.remove('active'));
  if (listItemEl) listItemEl.classList.add('active');
  
  // Bind unfriend action
  const unfriendBtn = document.getElementById('unfriendBtn');
  if (unfriendBtn) {
    unfriendBtn.onclick = async () => {
      if (!confirm(`Bạn chắc chắn muốn hủy bạn với ${friend.username}?`)) return;
      try {
        const res = await API.send({ type: 'FRIEND_REMOVE', data: { user_id: friend.user_id } });
        if (res.type === 'FRIEND_REMOVED') {
          // Refresh list and clear chat if current peer removed
          API.send({ type: 'FRIEND_LIST', data: {} });
          if (currentChat && currentChat.type === 'friend' && currentChat.data.user_id === friend.user_id) {
            currentChat = null;
            clearChat();
          }
          alert('Đã hủy kết bạn');
        } else if (res.type === 'ERROR') {
          alert('Không thể hủy: ' + (res.data?.code || 'UNKNOWN'));
        }
      } catch (e) {
        alert('Lỗi hủy bạn: ' + e.message);
      }
    };
  }
  
  // Reset per-conversation state and load history
  resetConversationState();
  // Load chat history
  API.send({ type: 'MSG_HISTORY', data: { peer_id: friend.user_id, limit: 50 } });
  // Ensure tab
  ensureTabForConversation(currentChat);
}

async function acceptFriendRequest(requestId) {
  if (!requestId) {
    alert('Thiếu request_id để chấp nhận');
    return;
  }
  try {
    const response = await API.send({ type: 'FRIEND_ACCEPT', data: { request_id: requestId } });
    if (response.type === 'FRIEND_ACCEPTED') {
      friendRequests = friendRequests.filter(r => (r.request_id||r.id) !== requestId);
      renderFriendRequests();
      API.send({ type: 'FRIEND_LIST', data: {} });
    } else if (response.type === 'ERROR') {
      alert('Không thể chấp nhận: ' + (response.data?.code || 'UNKNOWN'));
    }
  } catch (e) {
    // Fallback: vẫn yêu cầu server gửi lại danh sách để cập nhật trạng thái mới nhất
    API.send({ type: 'FRIEND_LIST', data: {} });
    alert('Kết nối tạm thời lỗi, đã yêu cầu cập nhật lại danh sách.');
  }
}

// Groups management
function renderGroups() {
  // Check if groups list actually changed to avoid unnecessary re-renders
  const currentGroupsHtml = elements.groupsList.innerHTML;
  
  const newGroupsHtml = groups.length === 0 
    ? '<li>Chưa có nhóm nào</li>'
    : groups.map(group => 
        `<li onclick="selectGroupById(${group.group_id})">${group.name} (${group.member_count} thành viên)</li>`
      ).join('');
  
  // Only update DOM if content actually changed
  if (currentGroupsHtml !== newGroupsHtml) {
    elements.groupsList.innerHTML = newGroupsHtml;
  }
}

function selectGroupById(groupId) {
  const group = groups.find(g => g.group_id === groupId);
  if (!group) return;
  selectGroup(group);
}

function selectGroup(group) {
  currentChat = { type: 'group', data: group };
  
  // Update UI
  elements.chatHeader.innerHTML = `<h3>Nhóm: ${group.name}</h3>`;
  elements.chatInput.classList.remove('hidden');
  
  // Reset conversation state when switching rooms
  resetConversationState();
  
  // Load group history
  API.send({
    type: 'GROUP_HISTORY',
    data: { group_id: group.group_id, limit: 50 }
  });
  
  // Update active state
  document.querySelectorAll('.groups-list li').forEach(li => li.classList.remove('active'));
  event?.target?.classList?.add('active');
  // Ensure tab
  ensureTabForConversation(currentChat);
}

// Event handlers
elements.loginBtn.onclick = async () => {
  const username = elements.username.value.trim();
  const password = elements.password.value.trim();
  
  if (!username || !password) {
    showStatus('Vui lòng nhập đầy đủ thông tin', 'error');
    return;
  }
  
  showStatus('Đang đăng nhập...', 'info');
  
  try {
    // Thử đăng nhập trước
    let response = await API.send({
      type: 'AUTH_LOGIN',
      data: { username, password }
    });
    
    // Nếu đăng nhập thất bại, thử đăng ký tự động
    if (response.type === 'AUTH_FAIL') {
      showStatus('Tài khoản chưa tồn tại, đang tạo tài khoản mới...', 'info');
      
      response = await API.send({
        type: 'AUTH_REGISTER',
        data: { username, password }
      });
      
      if (response.type === 'AUTH_OK') {
        showStatus('Đã tạo tài khoản mới, đang đăng nhập...', 'success');
        
        // Đăng nhập lại với tài khoản vừa tạo
        response = await API.send({
          type: 'AUTH_LOGIN',
          data: { username, password }
        });
      }
    }
    
    if (response.type === 'AUTH_OK') {
      currentUser = response.data;
      showStatus('Đăng nhập thành công!', 'success');
      
      // Switch to main screen
      setTimeout(() => {
        showScreen('main');
        elements.currentUser.textContent = `${currentUser.username} (ID: ${currentUser.user_id})`;
        
        // Load initial data
        API.send({ type: 'FRIEND_LIST', data: {} });
        API.send({ type: 'GROUP_LIST', data: {} });
      }, 1000);
      
    } else {
      showStatus('Đăng nhập thất bại: ' + (response.data?.reason || 'Lỗi không xác định'), 'error');
    }
  } catch (error) {
    showStatus('Lỗi kết nối: ' + error.message, 'error');
    console.error('Login error:', error);
  }
};

elements.registerBtn.onclick = async () => {
  const username = elements.username.value.trim();
  const password = elements.password.value.trim();
  
  if (!username || !password) {
    showStatus('Vui lòng nhập đầy đủ thông tin', 'error');
    return;
  }
  
  try {
    const response = await API.send({
      type: 'AUTH_REGISTER',
      data: { username, password }
    });
    
    if (response.type === 'AUTH_OK') {
      showStatus('Đăng ký thành công! Vui lòng đăng nhập', 'success');
      elements.username.value = '';
      elements.password.value = '';
    } else {
      showStatus('Đăng ký thất bại: ' + (response.data?.reason || 'Lỗi không xác định'), 'error');
    }
  } catch (error) {
    showStatus('Lỗi kết nối: ' + error.message, 'error');
    console.error('Register error:', error);
  }
};

// Password toggle event
elements.togglePassword.onclick = togglePasswordVisibility;

elements.addFriendBtn.onclick = async () => {
  const userId = elements.friendUserId.value.trim();
  
  if (!userId || isNaN(userId)) {
    alert('Vui lòng nhập User ID hợp lệ');
    return;
  }
  
  try {
    const response = await API.send({
      type: 'FRIEND_REQUEST',
      data: { to_user_id: parseInt(userId) }
    });
    
    if (response.type === 'FRIEND_REQUEST_SENT') {
      alert('Đã gửi lời mời kết bạn!');
      elements.friendUserId.value = '';
      // refresh lists so sender sees pending_out and receiver will get incoming via poll
      API.send({ type: 'FRIEND_LIST', data: {} });
    } else if (response.type === 'ERROR') {
      alert('Lỗi gửi lời mời: ' + (response.data?.code || 'UNKNOWN'));
    }
  } catch (error) {
    alert('Lỗi: ' + error.message);
    console.error('Add friend error:', error);
  }
};

elements.createGroupBtn.onclick = async () => {
  const groupName = elements.groupName.value.trim();
  
  if (!groupName) {
    alert('Vui lòng nhập tên nhóm');
    return;
  }
  
  try {
    const response = await API.send({
      type: 'GROUP_CREATE',
      data: { name: groupName }
    });
    
    if (response.type === 'GROUP_CREATED') {
      alert('Đã tạo nhóm thành công!');
      elements.groupName.value = '';
      
      // Refresh groups list
      setTimeout(() => {
        API.send({ type: 'GROUP_LIST', data: {} });
      }, 500);
    }
  } catch (error) {
    alert('Lỗi: ' + error.message);
  }
};

// Send message with optional reply
elements.sendBtn.onclick = async () => {
  const message = elements.messageInput.value.trim();
  if (!message || !currentChat) return;
  const replyId = replyToMessage ? replyToMessage.message_id : undefined;
  try {
    if (currentChat.type === 'friend') {
      await API.send({ type: 'MSG_SEND', data: { to_user_id: currentChat.data.user_id, content: message, reply_to_id: replyId } });
    } else if (currentChat.type === 'group') {
      await API.send({ type: 'GROUP_MSG_SEND', data: { group_id: currentChat.data.group_id, content: message, reply_to_id: replyId } });
    }
    elements.messageInput.value = '';
    replyToMessage = null; const rb = document.getElementById('replyBar'); if (rb) rb.remove();
  } catch (error) {
    let errorMessage = 'Lỗi gửi tin nhắn: ' + error.message;
    
    // Check if it's a NOT_FRIENDS error from the API response
    if (error.message && error.message.includes('NOT_FRIENDS')) {
      errorMessage = 'Không thể gửi tin nhắn: Bạn chưa kết bạn với người này';
    }
    
    alert(errorMessage);
  }
};

elements.logoutBtn.onclick = () => {
  currentUser = null;
  currentChat = null;
  friends = [];
  groups = [];
  friendRequests = [];
  
  clearChat();
  showScreen('login');
  
  // Clear inputs
  elements.username.value = '';
  elements.password.value = '';
  elements.loginStatus.textContent = '';
  
  // Reset password field type
  elements.password.type = 'password';
  elements.togglePassword.classList.remove('showing');
};

elements.themeBtn.onclick = () => {
  document.body.classList.toggle('dark');
  const isDark = document.body.classList.contains('dark');
  elements.themeBtn.textContent = isDark ? '☀️' : '\ud83c\udf19';
};

// Message input enter key
elements.messageInput.onkeypress = (e) => {
  if (e.key === 'Enter') {
    elements.sendBtn.click();
  }
};

// Poll for new messages with visibility-aware backoff
let POLL_ACTIVE_MS = 2000; // focused - tăng lên để giảm lag
let POLL_IDLE_MS = 4000;   // hidden - tăng lên để giảm lag

async function pollMessages() {
  try {
    const response = await API.poll();
    if (response.messages && response.messages.length > 0) {
      // Batch process messages to reduce DOM updates
      const messagesToProcess = response.messages.slice(0, 10); // Limit to 10 messages per poll
      messagesToProcess.forEach(msg => handleIncomingMessage(msg));
    }
  } catch (error) {
    // Silent
  }
  const delay = document.hidden ? POLL_IDLE_MS : POLL_ACTIVE_MS;
  setTimeout(pollMessages, delay);
}

document.addEventListener('visibilitychange', () => {
  // No-op; delay will adapt on next tick
});

// Handle incoming messages
function handleIncomingMessage(msg) {
  const { type, data } = msg;
  switch (type) {
    case 'FRIEND_LIST_RESULT':
      friends = data.friends || [];
      renderFriends();
      friendRequests = data.pending_in || [];
      renderFriendRequests();
      break;
    case 'GROUP_LIST_RESULT':
      groups = data.groups || [];
      renderGroups();
      break;
    case 'FRIEND_REQUEST_INCOMING':
      if (data) {
        const rid = data.request_id;
        const exists = friendRequests.some(r => (r.request_id||r.id) === rid);
        if (!exists) {
          friendRequests.push({ request_id: rid, from_user_id: data.from_user_id, from_username: data.from_username });
          renderFriendRequests();
        }
      }
      break;
    case 'MSG_RECV': {
      const peerId = data.from_user_id === currentUser.user_id ? data.to_user_id : data.from_user_id;
      if (currentChat && currentChat.type === 'friend' && peerId === currentChat.data.user_id) {
        const isOwn = data.from_user_id === currentUser.user_id;
        addMessage(data, isOwn);
      }
      break;
    }
    case 'GROUP_MSG_RECV':
      if (currentChat && currentChat.type === 'group' && data.group_id === currentChat.data.group_id) {
        const isOwn = data.from_user_id === currentUser.user_id;
        addMessage(data, isOwn);
      }
      break;
    case 'MSG_HISTORY_RESULT': {
      // Batch DOM writes
      displayedMessageIds = new Set();
      elements.chatMessages.innerHTML = '';
      const frag = document.createDocumentFragment();
      (data.messages || []).forEach(message => {
        const isOwn = message.from_user_id === currentUser.user_id;
        if (!message.message_id) message.message_id = Math.floor(message.created_at * 1000);
        if (displayedMessageIds.has(message.message_id)) return;
        displayedMessageIds.add(message.message_id);
        const node = buildMessageNode(message, isOwn);
        frag.appendChild(node);
      });
      elements.chatMessages.appendChild(frag);
      elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
      break;
    }
    case 'GROUP_HISTORY_RESULT': {
      displayedMessageIds = new Set();
      elements.chatMessages.innerHTML = '';
      const frag = document.createDocumentFragment();
      (data.messages || []).forEach(message => {
        const isOwn = message.from_user_id === currentUser.user_id;
        if (!message.message_id) message.message_id = Math.floor(message.created_at * 1000);
        if (displayedMessageIds.has(message.message_id)) return;
        displayedMessageIds.add(message.message_id);
        const node = buildMessageNode(message, isOwn);
        frag.appendChild(node);
      });
      elements.chatMessages.appendChild(frag);
      elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
      break;
    }
    case 'MSG_RECALL_UPDATE': {
      const mid = data.message_id;
      const reactNode = document.getElementById(`react-${mid}`);
      if (reactNode) {
        const bubble = reactNode.previousSibling.previousSibling;
        if (bubble) bubble.textContent = '[Đã thu hồi]';
      }
      break;
    }
    case 'MSG_REACT_UPDATE': {
      updateReactionSummary(data.message_id, data.counts);
      if (currentUser && data.by_user_id === currentUser.user_id) {
        const s = myReactions.get(data.message_id) || new Set();
        if (data.action === 'add') s.add(data.reaction); else s.delete(data.reaction);
        if (s.size > 0) myReactions.set(data.message_id, s); else myReactions.delete(data.message_id);
      }
      break;
    }
  }
}

// Build message DOM node (to batch in history rendering)
function buildMessageNode(message, isOwn){
  const messageDiv = document.createElement('div');
  messageDiv.id = 'msg-' + message.message_id;
  messageDiv.className = `message ${isOwn ? 'own' : 'other'}`;
  const bubble = document.createElement('div');
  bubble.className = 'message-bubble';
  bubble.textContent = message.content || '[Đã thu hồi]';
  const time = document.createElement('div');
  time.className = 'message-time';
  time.textContent = formatTime(message.created_at);
  messageDiv.appendChild(bubble);
  messageDiv.appendChild(time);
  const actions = createMessageActions(message, isOwn);
  messageDiv.appendChild(actions);
  const reactLine = document.createElement('div');
  reactLine.className = 'react-line';
  reactLine.id = `react-${message.message_id}`;
  messageDiv.appendChild(reactLine);
  updateReactionSummary(message.message_id, message.reactions_summary);
  return messageDiv;
}

// Group add member actions
const addGroupIdEl = document.getElementById('addGroupId');
const addUserToGroupIdEl = document.getElementById('addUserToGroupId');
const addUserToGroupBtn = document.getElementById('addUserToGroupBtn');
if (addUserToGroupBtn) {
  addUserToGroupBtn.onclick = async () => {
    const gid = parseInt((addGroupIdEl?.value || '').trim(), 10);
    const uid = parseInt((addUserToGroupIdEl?.value || '').trim(), 10);
    if (!Number.isInteger(gid) || !Number.isInteger(uid)) { alert('Nhập Group ID và User ID hợp lệ'); return; }
    try {
      const res = await API.send({ type: 'GROUP_ADD', data: { group_id: gid, user_id: uid } });
      if (res.type === 'GROUP_MEMBER_ADDED' || res.type === 'OK' || res.ok) {
        alert('Đã thêm thành viên vào nhóm');
        addGroupIdEl.value = '';
        addUserToGroupIdEl.value = '';
        API.send({ type: 'GROUP_LIST', data: {} });
      } else if (res.type === 'ERROR') {
        alert('Lỗi thêm thành viên: ' + (res.data?.code || 'UNKNOWN'));
      }
    } catch (e) { alert('Lỗi: ' + e.message); }
  };
}

// Initialize app
function init() {
  showScreen('login');
  pollMessages();
}

// Start the app
init();


