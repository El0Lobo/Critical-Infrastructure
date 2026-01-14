(function(){
  // ========= Modal open/close =========
  function openModal(sel){
    const modal = document.querySelector(sel);
    if(!modal) return;
    modal.hidden = false;
    document.body.classList.add('modal-open');
  }
  function closeModal(elOrSel){
    let modal = null;
    if (typeof elOrSel === 'string') {
      modal = document.querySelector(elOrSel);
    } else if (elOrSel && elOrSel.closest) {
      modal = elOrSel.closest('.modal');
    }
    if (!modal) modal = document.getElementById('modalThread');
    if (modal) modal.hidden = true;
    if (!document.querySelector('.modal:not([hidden])')) {
      document.body.classList.remove('modal-open');
    }
  }

  // OPEN: static binding is fine
  document.querySelectorAll('[data-open]').forEach(btn=>{
    btn.addEventListener('click', ()=>openModal(btn.dataset.open));
  });

  // ESC closes all
  document.addEventListener('keydown', e=>{
    if(e.key === 'Escape'){
      document.querySelectorAll('.modal:not([hidden])').forEach(m=>m.hidden = true);
      document.body.classList.remove('modal-open');
    }
  });

  // ========= Compose from reply buttons =========
  document.addEventListener('click', (e)=>{
    const replyBtn = e.target.closest('[data-reply-thread]');
    if (!replyBtn) return;
    const threadId = replyBtn.getAttribute('data-reply-thread');
    const subject = replyBtn.getAttribute('data-reply-subject') || '';
    const to = replyBtn.getAttribute('data-reply-to') || '';
    const form = document.getElementById('internalComposeForm');
    if (!form) return;
    form.querySelector('input[name="thread_id"]').value = threadId;
    const subjInput = form.querySelector('input[name="subject"]');
    if (subjInput) {
      subjInput.value = subject && !subject.toLowerCase().startsWith('re:') ? ('Re: ' + subject) : subject;
    }
    const title = document.getElementById('internalModalTitle');
    if (title) title.textContent = 'Reply to internal';
    const toInput = form.querySelector('input[name="to_usernames"]');
    if (toInput) toInput.value = to;
    closeModal('#modalThread');
    openModal('#modalComposeInternal');
  });

  // Opening new internal clears reply state
  document.querySelectorAll('[data-open="#modalComposeInternal"]').forEach(btn=>{
    btn.addEventListener('click', ()=>{
      const form = document.getElementById('internalComposeForm');
      if (!form) return;
      form.querySelector('input[name="thread_id"]').value = '';
      const title = document.getElementById('internalModalTitle');
      if (title) title.textContent = 'New Message';
    });
  });

  // ========= Open thread modal by clicking a row (except actions) =========
  document.addEventListener('click', async (e)=>{
    const li = e.target.closest('li.thread-item');
    if (!li) return;
    if (e.target.closest('.thread-actions')) return;
    if (e.defaultPrevented) return;
    e.preventDefault();
    e.stopPropagation();

    const a = li.querySelector('a.thread-subject');
    const href = a ? a.getAttribute('href') : ('/cms/inbox/t/' + li.getAttribute('data-thread-id') + '/');
    const tid = li.getAttribute('data-thread-id');

    try {
      const resp = await fetch(href + 'modal/');
      const html = await resp.text();
      const body = document.getElementById('modalThreadBody');
      if (body) {
        body.innerHTML = html;
        initThreadModal(tid);  // ← pass thread id
      }
      openModal('#modalThread');
      // mark read visually
      if (tid){
        li.classList.remove('unread');
        li.querySelector('.unread-pad')?.remove();
      }
    } catch(err) {}
  });

  // ========= Open thread modal by clicking subject link =========
  document.addEventListener('click', async (e)=>{
    const a = e.target.closest('a.thread-subject');
    if (!a) return;
    e.preventDefault();

    const href = a.getAttribute('href');
    const tid = a.getAttribute('data-thread-id');

    try {
      const resp = await fetch(href + 'modal/');
      const html = await resp.text();
      const body = document.getElementById('modalThreadBody');
      if (body) {
        body.innerHTML = html;
        initThreadModal(tid);  // ← pass thread id
      }
      openModal('#modalThread');
      // Optimistically mark read in list
      if (tid){
        const li = document.querySelector(`li.thread-item[data-thread-id="${tid}"]`);
        if (li){
          li.classList.remove('unread');
          li.querySelector('.unread-pad')?.remove();
        }
      }
    } catch(err) {}
  });

  // ========= Emoji picker: toggle + file attach =========
  document.addEventListener('click',(e)=>{
    const attach = e.target.closest('[data-attach-target]');
    if (attach){
      const sel = attach.getAttribute('data-attach-target');
      const input = document.querySelector(sel);
      if (input) input.click();
      return;
    }
    const btn = e.target.closest('[data-emoji-insert]');
    if (btn){
      const wrap = btn.closest('.emoji-wrap');
      const pic = wrap && wrap.querySelector('.emoji-picker');
      if (pic) pic.hidden = !pic.hidden;
      return;
    }
  });

  // ========= Delegated close buttons =========
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-close]');
    if (!btn) return;
    const sel = btn.getAttribute('data-close');
    if (sel && document.querySelector(sel)) {
      closeModal(sel);
    } else {
      closeModal(btn);
    }
  });

  // ===== Scroll memory + jump-to-newest for thread modal =====
  const SCROLL_KEY = 'threadScroll:';
  const NEAR_PX = 32;

  function loadScrollState(tid){
    try { return JSON.parse(sessionStorage.getItem(SCROLL_KEY + tid)) || null; } catch{ return null; }
  }
  function saveScrollState(tid, st){
    try { sessionStorage.setItem(SCROLL_KEY + tid, JSON.stringify(st)); } catch{}
  }
  function isNearBottom(el){
    return (el.scrollHeight - (el.scrollTop + el.clientHeight)) <= NEAR_PX;
  }
  function scrollToBottom(el){
    el.scrollTop = el.scrollHeight;
  }
  function ensureJumpButton(chat, tid){
    let btn = chat.querySelector('.jump-to-new');
    if (!btn){
      btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'jump-to-new btn btn-sm';
      btn.textContent = 'Jump to newest';
      btn.style.position = 'sticky';
      btn.style.bottom = '8px';
      btn.style.marginLeft = 'auto';
      btn.style.alignSelf = 'flex-end';
      btn.style.zIndex = '5';
      btn.style.display = 'none';
      chat.appendChild(btn);
      btn.addEventListener('click', ()=>{
        scrollToBottom(chat);
        const st = loadScrollState(tid) || {};
        st.userPinned = false;
        st.lastHeight = chat.scrollHeight;
        st.scrollTop = chat.scrollTop;
        saveScrollState(tid, st);
        btn.style.display = 'none';
      });
    }
    return btn;
  }

  // Expose initThreadModal globally (used right after loading modal HTML)
  window.initThreadModal = function initThreadModal(tid){
    ensureEmojiPickerElement();

    // Fallback: try to derive tid from loaded HTML if not passed
    if (!tid) {
      const elTid = document.querySelector('#modalThreadBody [data-thread-id]')?.getAttribute('data-thread-id');
      if (elTid) tid = elTid;
    }
    tid = tid || 'unknown';

    const scope = document.getElementById('modalThreadBody') || document;

    // Upgrade legacy emoji pickers
    scope.querySelectorAll('div.emoji-picker').forEach(el=>{
      const picker=document.createElement('emoji-picker');
      picker.className='emoji-picker';
      if (el.hasAttribute('hidden')) picker.hidden = true;
      el.replaceWith(picker);
    });

    // Set default title when no other participants
    const title = scope.querySelector('.chat-title');
    if (title && !title.querySelector('.name')) {
      title.textContent = '(no recipient)';
    }

    // ----- Scroll memory / jump-to-newest -----
    const chat = scope.querySelector('.thread-chat');
    if (!chat) return;

    const btn = ensureJumpButton(chat, tid);
    const prev = loadScrollState(tid) || {};
    const hadUserPinnedUp = !!prev.userPinned;
    const prevHeight = prev.lastHeight || 0;

    if (hadUserPinnedUp && Number.isFinite(prev.scrollTop)){
      // restore prior position
      chat.scrollTop = Math.max(0, Math.min(prev.scrollTop, chat.scrollHeight - chat.clientHeight));
      const growth = Math.max(0, chat.scrollHeight - prevHeight);
      if (growth > 0) btn.style.display = 'inline-flex';
    } else {
      // default to bottom on open
      scrollToBottom(chat);
      btn.style.display = 'none';
    }

    saveScrollState(tid, {
      userPinned: !isNearBottom(chat),
      lastHeight: chat.scrollHeight,
      scrollTop: chat.scrollTop
    });

    if (!chat.dataset.scrollHandler){
      chat.addEventListener('scroll', ()=>{
        const near = isNearBottom(chat);
        const st = loadScrollState(tid) || {};
        st.userPinned = !near;
        st.scrollTop = chat.scrollTop;
        st.lastHeight = chat.scrollHeight;
        saveScrollState(tid, st);
        btn.style.display = st.userPinned ? 'inline-flex' : 'none';
      });
      chat.dataset.scrollHandler = '1';
    }

    // Detect growth after paint (e.g., images load, or slightly delayed content)
    requestAnimationFrame(()=> {
      const st = loadScrollState(tid) || {};
      const grew = chat.scrollHeight > (st.lastHeight || 0);
      if (grew && st.userPinned) {
        btn.style.display = 'inline-flex';
      }
      st.lastHeight = chat.scrollHeight;
      st.scrollTop = chat.scrollTop;
      saveScrollState(tid, st);
    });
  };

})();

// ========= Auto-grow textareas =========
function autoGrow(ta){
  if(!ta) return;
  ta.style.height='auto';
  const max = Math.floor(window.innerHeight*0.4);
  ta.style.height = Math.min(ta.scrollHeight, max) + 'px';
}
document.addEventListener('input',(e)=>{
  const ta = e.target.closest('.chat-reply textarea, #modalComposeInternal textarea[name="body"]');
  if(ta) autoGrow(ta);
});
document.addEventListener('DOMContentLoaded',()=>{
  document.querySelectorAll('.chat-reply textarea, #modalComposeInternal textarea[name="body"]').forEach(autoGrow);
});

// ========= Emoji picker loader =========
function ensureEmojiPickerElement(){
  try{
    if (window.customElements && customElements.get && customElements.get('emoji-picker')) return;
  }catch(_){}
  const s=document.createElement('script');
  s.type='module';
  s.src='https://cdn.jsdelivr.net/npm/emoji-picker-element@^1/index.js';
  document.head.appendChild(s);
}

// ========= Insert emoji into nearest textarea =========
document.addEventListener('emoji-click', (event)=>{
  const picker = event.target.closest('emoji-picker');
  if (!picker) return;
  const wrap = picker.closest('.emoji-wrap');
  const ta = wrap && wrap.querySelector('textarea');
  if (!ta) return;
  const start = ta.selectionStart ?? ta.value.length;
  const end   = ta.selectionEnd ?? ta.value.length;
  const val   = ta.value;
  const emoji = (event.detail && event.detail.unicode) ? event.detail.unicode : '';
  ta.value = val.slice(0,start) + emoji + val.slice(end);
  ta.focus();
  picker.hidden = true;
});

// === Chips (users/groups) selection + typeahead ===
(function(){
  // --- state ---
  function getState(){
    const form = document.getElementById('internalComposeForm');
    if (!form) return null;
    if (!form._chipsState) form._chipsState = { users:new Set(), groups:new Set() };
    return form._chipsState;
  }

  // Build name->id maps from hidden selects (so typing plain names works)
  function buildIndexes(){
    const usersSel = document.getElementById('to_user_ids');
    const groupsSel = document.getElementById('to_group_ids');
    const userNameToId = new Map();
    const groupNameToId = new Map();
    if (usersSel) Array.from(usersSel.options).forEach(o=> userNameToId.set(o.textContent.trim(), o.value));
    if (groupsSel) Array.from(groupsSel.options).forEach(o=> groupNameToId.set(o.textContent.trim(), o.value));
    return { userNameToId, groupNameToId };
  }

  function syncHidden(){
    const st = getState(); if (!st) return;
    const usersSel = document.getElementById('to_user_ids');
    const groupsSel = document.getElementById('to_group_ids');
    const usernamesHidden = document.getElementById('to_usernames');

    if (usersSel)  Array.from(usersSel.options).forEach(o=> o.selected = st.users.has(o.value));
    if (groupsSel) Array.from(groupsSel.options).forEach(o=> o.selected = st.groups.has(o.value));

    // usernames string (optional, legacy)
    if (usernamesHidden){
      const names = Array.from(document.querySelectorAll('#chipsSelected .chip[data-chip-type="user"]'))
        .map(ch => ch.dataset.label);
      usernamesHidden.value = names.join(',');
    }
  }

  function renderSelected(){
    const st = getState(); if (!st) return;
    const { userNameToId, groupNameToId } = buildIndexes();
    const host = document.getElementById('chipsSelected'); if (!host) return;

    // Build reverse id->name lookups
    const idToUser = new Map(Array.from(userNameToId.entries()).map(([n,id])=>[id,n]));
    const idToGroup= new Map(Array.from(groupNameToId.entries()).map(([n,id])=>[id,n]));

    host.innerHTML = '';

    st.users.forEach(id=>{
      const label = idToUser.get(id) || 'User';
      const b = document.createElement('button');
      b.type='button'; b.className='chip';
      b.dataset.chipType='user'; b.dataset.id=id; b.dataset.label=label;
      b.innerHTML = `${label} <span class="x">×</span>`;
      host.appendChild(b);
    });
    st.groups.forEach(id=>{
      const label = idToGroup.get(id) || 'Group';
      const b = document.createElement('button');
      b.type='button'; b.className='chip';
      b.dataset.chipType='group'; b.dataset.id=id; b.dataset.label=label;
      b.innerHTML = `${label} <span class="x">×</span>`;
      host.appendChild(b);
    });

    // Reflect selection in pickers
    document.querySelectorAll('#chipsUsers .chip').forEach(ch=>{
      ch.classList.toggle('is-selected', st.users.has(ch.dataset.id));
    });
    document.querySelectorAll('#chipsGroups .chip').forEach(ch=>{
      ch.classList.toggle('is-selected', st.groups.has(ch.dataset.id));
    });

    syncHidden();
  }

  function toggle(kind, id){
    const st = getState(); if (!st) return;
    const set = (kind === 'group') ? st.groups : st.users;
    if (set.has(id)) set.delete(id); else set.add(id);
    renderSelected();
  }

  // Parse a token from input:
  // - "u:<id>" or "g:<id>" (from datalist)
  // - plain "username" or "group name"
  function acceptToken(raw){
    const v = (raw || '').trim();
    if (!v) return false;
    const { userNameToId, groupNameToId } = buildIndexes();

    // From datalist with type prefix
    if (v.startsWith('u:')){
      toggle('user', v.slice(2));
      return true;
    }
    if (v.startsWith('g:')){
      toggle('group', v.slice(2));
      return true;
    }

    // Try exact username
    const uid = userNameToId.get(v);
    if (uid){ toggle('user', String(uid)); return true; }

    // Try exact group name
    const gid = groupNameToId.get(v);
    if (gid){ toggle('group', String(gid)); return true; }

    return false;
  }

  // Delegated handlers
  document.addEventListener('click', (e)=>{
    // Pickers -> toggle
    const ch = e.target.closest('#chipsUsers .chip, #chipsGroups .chip');
    if (ch){
      toggle(ch.dataset.chipType, ch.dataset.id);
      return;
    }
    // Selected -> remove
    const sel = e.target.closest('#chipsSelected .chip');
    if (sel){
      toggle(sel.dataset.chipType, sel.dataset.id);
      return;
    }
  });

  // Typeahead: accept on Enter / Comma / Tab, and on choosing a datalist option
  const input = document.getElementById('recipientInput');

  if (input){
    // Enter/Comma/Tab to accept one or more comma-separated tokens
    input.addEventListener('keydown', (e)=>{
      if (e.key === 'Enter' || e.key === 'Tab' || e.key === ','){
        const parts = input.value.split(',').map(s=>s.trim()).filter(Boolean);
        let any=false;
        parts.forEach(p=> any = acceptToken(p) || any);
        if (any){
          e.preventDefault(); // keep focus in input
          input.value = '';
        }
      }
    });

    // On change (picking from datalist) browsers fire 'input' then 'change'
    input.addEventListener('change', ()=>{
      if (!input.value) return;
      if (acceptToken(input.value)) input.value = '';
    });

    // Handle pasted comma-separated list
    input.addEventListener('paste', (e)=>{
      const text = (e.clipboardData || window.clipboardData).getData('text');
      if (!text || text.indexOf(',') === -1) return;
      e.preventDefault();
      const parts = text.split(',').map(s=>s.trim()).filter(Boolean);
      parts.forEach(p=> acceptToken(p));
      input.value = '';
    });
  }

  // Reset chips on "new internal" open
  document.querySelectorAll('[data-open="#modalComposeInternal"]').forEach(btn=>{
    btn.addEventListener('click', ()=>{
      const form = document.getElementById('internalComposeForm');
      if (!form) return;
      form._chipsState = { users:new Set(), groups:new Set() };
      renderSelected();
      if (input) input.value='';
    });
  });

  // Pre-fill from reply buttons (data-reply-to="username,username")
  document.addEventListener('click', (e)=>{
    const replyBtn = e.target.closest('[data-reply-thread]');
    if (!replyBtn) return;
    const form = document.getElementById('internalComposeForm'); if (!form) return;
    form._chipsState = { users:new Set(), groups:new Set() };
    const to = (replyBtn.getAttribute('data-reply-to') || '').split(',').map(s=>s.trim()).filter(Boolean);
    to.forEach(name => acceptToken(name));
    renderSelected();
  });

  // Expose helpers (optional)
  window._chipsCompose = { renderSelected, toggle, acceptToken };
})();
