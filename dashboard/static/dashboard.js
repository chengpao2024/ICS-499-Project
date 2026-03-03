// Campus Asset Tracker — Dashboard JS
// SCRIPT_URL / CURRENT_SORT_BY / CURRENT_SORT_DIR are set by inline <script> in the template.

// ── Search debounce ──────────────────────────────────────────────
const searchInput = document.getElementById('search');
let debounceTimer;
searchInput.addEventListener('input', () => {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => submitForm(), 400);
});

function submitForm() {
  document.getElementById('filter-form').submit();
}

// ── Toast ────────────────────────────────────────────────────────
function showToast(msg, type = 'success') {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'show ' + type;
  setTimeout(() => { t.className = ''; }, 2800);
}

// ═══════════════════════════════════════════════════════════════
//  FLOATING DROPDOWN MANAGER
//  One dropdown open at a time. Shared by status, kebab, sort.
// ═══════════════════════════════════════════════════════════════
let activeDropdown = null;

function closeDropdown() {
  if (activeDropdown) {
    activeDropdown.remove();
    activeDropdown = null;
  }
}

function openDropdown(dropdown, anchor) {
  closeDropdown();
  document.body.appendChild(dropdown);

  const r  = anchor.getBoundingClientRect();
  const dd = dropdown.getBoundingClientRect();
  let top  = r.bottom + 6;
  let left = r.left;

  // Flip up if cut off at bottom
  if (top + dd.height > window.innerHeight - 8)
    top = r.top - dd.height - 6;
  // Nudge left if cut off at right edge
  if (left + dd.width > window.innerWidth - 8)
    left = window.innerWidth - dd.width - 8;

  dropdown.style.top  = top  + 'px';
  dropdown.style.left = left + 'px';
  activeDropdown = dropdown;
}

// Close when clicking outside any dropdown
document.addEventListener('click', function(e) {
  if (activeDropdown && !activeDropdown.contains(e.target)) {
    closeDropdown();
  }
});
window.addEventListener('scroll', closeDropdown, true);

// ── Helper: make a dropdown div ──────────────────────────────────
function makeDropdown() {
  const d = document.createElement('div');
  d.className = 'float-dropdown';
  return d;
}

// Updated to support both raw SVG and image icons. 
// Use with: 
//  - makeItem('item_label', '/image_path.png', 'style', { type: "img" });
function makeItem(label, icon, extraClass, isImage = false) {
  const item = document.createElement('div');
  item.className = 'float-dropdown-item' + (extraClass ? ' ' + extraClass : '');

  const iconHTML = isImage
    ? `<img src="${icon}" width="13" height="13" style="margin-right:6px;">`
    : `<svg xmlns="http://www.w3.org/2000/svg" fill="none"
            viewBox="0 0 24 24" width="13" height="13"
            stroke-width="1.8" stroke="currentColor">
         <path stroke-linecap="round"
               stroke-linejoin="round"
               d="${icon}"/>
       </svg>`;

  item.innerHTML = `${iconHTML}${label}`;

  return item;
}
function makeDivider() {
  const d = document.createElement('div');
  d.className = 'float-dropdown-divider';
  return d;
}

// ═══════════════════════════════════════════════════════════════
//  STATUS DROPDOWN
// ═══════════════════════════════════════════════════════════════
const DOT_COLORS = {
  'available':   '#22c55e',
  'in-use':      '#3b82f6',
  'maintenance': '#f59e0b'
};
const STATUS_LABELS = {
  'available':   'Available',
  'in-use':      'In Use',
  'maintenance': 'Maintenance'
};
const BADGE_CLASSES = {
  'available':   'badge-available',
  'in-use':      'badge-inuse',
  'maintenance': 'badge-maintenance'
};

function openStatusDropdown(badge, assetId, currentStatus) {
  const dd = makeDropdown();

  ['available', 'in-use', 'maintenance'].forEach(s => {
    const item = document.createElement('div');
    item.className = 'float-dropdown-item' + (s === currentStatus ? ' active' : '');

    const dot = document.createElement('span');
    dot.className = 'status-dot-sm';
    dot.style.background = DOT_COLORS[s];
    item.appendChild(dot);
    item.appendChild(document.createTextNode(STATUS_LABELS[s]));

    item.addEventListener('click', function(e) {
      e.stopPropagation();
      closeDropdown();
      if (s !== currentStatus) updateStatus(assetId, s, badge);
    });
    dd.appendChild(item);
  });

  openDropdown(dd, badge);
}

function updateStatus(assetId, newStatus, badge) {
  const params = new URLSearchParams({
    action: 'update_status', id: assetId, status: newStatus
  });
  fetch(SCRIPT_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: params.toString()
  })
  .then(r => r.json())
  .then(data => {
    if (data.success) {
      const cell = badge.closest('.status-cell');
      badge.className     = 'status-badge ' + data.badge_class + ' status-toggle';
      badge.textContent   = data.label;
      cell.dataset.status = newStatus;
      showToast('Status updated to ' + data.label);
    } else {
      showToast('Update failed: ' + (data.error || 'unknown'), 'error');
    }
  })
  .catch(() => showToast('Network error.', 'error'));
}

// ═══════════════════════════════════════════════════════════════
//  KEBAB (ACTION) MENU
// ═══════════════════════════════════════════════════════════════
function openActionMenu(btn) {
  const assetId = btn.dataset.id;
  const name    = btn.dataset.name;
  const editUrl = btn.dataset.editUrl;

  const dd = makeDropdown();

  // Edit — navigate to asset_create.php
  const editItem = document.createElement('a');
  editItem.className = 'float-dropdown-item';
  editItem.href = editUrl;
  editItem.innerHTML =
    `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
          width="13" height="13" stroke-width="1.8" stroke="currentColor">
       <path stroke-linecap="round" stroke-linejoin="round"
             d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582
                16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0
                011.13-1.897l8.932-8.931zm0 0L19.5 7.125"/>
     </svg>Edit`;
  dd.appendChild(editItem);
  dd.appendChild(makeDivider());

  // Delete
  const delItem = makeItem(
    'Delete',
    'M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0',
    'danger'
  );
  delItem.addEventListener('click', function(e) {
    e.stopPropagation();
    closeDropdown();
    if (confirm('Delete "' + name + '"?\nThis cannot be undone.')) {
      window.location.href = SCRIPT_URL + '?action=delete&id=' + assetId;
    }
  });
  dd.appendChild(delItem);

  openDropdown(dd, btn);
}

// ═══════════════════════════════════════════════════════════════
//  SORT DROPDOWN
// ═══════════════════════════════════════════════════════════════
function openSortDropdown(btn) {
  const dd = makeDropdown();

  const options = [
    { label: 'ID — Ascending',    by: 'asset_id', dir: 'asc'  },
    { label: 'ID — Descending',   by: 'asset_id', dir: 'desc' },
    { label: 'Name — A → Z',      by: 'name',     dir: 'asc'  },
    { label: 'Name — Z → A',      by: 'name',     dir: 'desc' },
  ];

  options.forEach(opt => {
    const item = document.createElement('div');
    const isActive = (opt.by === CURRENT_SORT_BY && opt.dir === CURRENT_SORT_DIR);
    item.className = 'float-dropdown-item' + (isActive ? ' active' : '');
    item.textContent = opt.label;
    item.addEventListener('click', function(e) {
      e.stopPropagation();
      closeDropdown();
      applySort(opt.by, opt.dir);
    });
    dd.appendChild(item);
  });

  openDropdown(dd, btn);
}

function applySort(by, dir) {
  const form = document.getElementById('filter-form');
  form.querySelector('[name="sort_by"]').value  = by;
  form.querySelector('[name="sort_dir"]').value = dir;
  form.submit();
}

// ═══════════════════════════════════════════════════════════════
//  DELEGATED CLICK HANDLER
//  All button interactions handled here
//  fires before the "close dropdown" listener above.
// ═══════════════════════════════════════════════════════════════
document.addEventListener('click', function(e) {
  // Status badge
  if (e.target.classList.contains('status-toggle')) {
    e.stopPropagation();
    const badge = e.target;
    const cell  = badge.closest('.status-cell');
    openStatusDropdown(badge, cell.dataset.id, cell.dataset.status);
    return;
  }
  // Kebab button
  if (e.target.classList.contains('btn-kebab')) {
    e.stopPropagation();
    openActionMenu(e.target);
    return;
  }
  // Sort button
  if (e.target.id === 'sort-btn' || e.target.closest('#sort-btn')) {
    e.stopPropagation();
    openSortDropdown(document.getElementById('sort-btn'));
    return;
  }
});

// ═══════════════════════════════════════════════════════════════
//  INLINE EDIT (Function: double-click on editable cells: name, category, location)
// ═══════════════════════════════════════════════════════════════
document.addEventListener('dblclick', function(e) {
  const span = e.target.closest('.editable');
  if (!span || span.querySelector('input')) return; // already editing

  const assetId    = span.dataset.id;
  const field      = span.dataset.field;
  const original   = span.textContent.trim();

  const input = document.createElement('input');
  input.type      = 'text';
  input.value     = original;
  input.className = 'editable-input';

  span.textContent = '';
  span.appendChild(input);
  input.focus();
  input.select();

  function commit() {
    const newVal = input.value.trim();
    if (!newVal || newVal === original) {
      span.textContent = original;
      return;
    }
    span.textContent = newVal; // optimistic update

    const params = new URLSearchParams({
      action: 'update_field',
      id:     assetId,
      field:  field,
      value:  newVal
    });
    fetch(SCRIPT_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: params.toString()
    })
    .then(r => r.json())
    .then(data => {
      if (data.success) {
        span.textContent = data.value;
        showToast('Saved');
      } else {
        span.textContent = original;
        showToast('Save failed: ' + (data.error || 'unknown'), 'error');
      }
    })
    .catch(() => {
      span.textContent = original;
      showToast('Network error.', 'error');
    });
  }

  function cancel() { span.textContent = original; }

  input.addEventListener('blur',    commit);
  input.addEventListener('keydown', function(e) {
    if (e.key === 'Enter')  { input.blur(); }
    if (e.key === 'Escape') { input.removeEventListener('blur', commit); cancel(); }
  });
});