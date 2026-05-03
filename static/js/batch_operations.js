// Batch Operations JavaScript
let selectedUsers = new Set();
let currentSingleUser = null;

// Dropdown functionality
function toggleDropdown(event, button) {
    event.stopPropagation();
    const dropdown = button.closest('.dropdown');
    const isOpen = dropdown.classList.contains('show');
    
    // Close all dropdowns
    document.querySelectorAll('.dropdown.show').forEach(d => {
        d.classList.remove('show');
    });
    
    // Toggle current dropdown
    if (!isOpen) {
        dropdown.classList.add('show');
    }
}

// Close dropdowns when clicking outside
document.addEventListener('click', function(event) {
    if (!event.target.closest('.dropdown')) {
        document.querySelectorAll('.dropdown.show').forEach(d => {
            d.classList.remove('show');
        });
    }
});

// Close modals when clicking outside
document.querySelectorAll('.modal-overlay').forEach(modal => {
    modal.addEventListener('click', function(e) {
        if (e.target === this) {
            closeAllModals();
        }
    });
});

function closeAllModals() {
    document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.classList.remove('show');
    });
}

function updateBatchActions() {
    const batchActions = document.getElementById('batchActions');
    const batchCount = document.getElementById('batchCount');
    const count = selectedUsers.size;
    
    if (count > 0) {
        batchActions.classList.add('show');
        batchCount.textContent = `${count} selected`;
    } else {
        batchActions.classList.remove('show');
    }
}

function toggleUserSelection(checkbox, userId) {
    if (checkbox.checked) {
        selectedUsers.add(userId);
    } else {
        selectedUsers.delete(userId);
    }
    updateBatchActions();
}

function toggleSelectAll(checkbox) {
    const checkboxes = document.querySelectorAll('.user-checkbox');
    checkboxes.forEach(cb => {
        cb.checked = checkbox.checked;
        const userId = cb.dataset.userId;
        if (checkbox.checked) {
            selectedUsers.add(userId);
        } else {
            selectedUsers.delete(userId);
        }
    });
    updateBatchActions();
}

function clearSelection() {
    selectedUsers.clear();
    document.querySelectorAll('.user-checkbox').forEach(cb => cb.checked = false);
    const selectAll = document.getElementById('selectAll');
    if (selectAll) selectAll.checked = false;
    updateBatchActions();
}

function getCSRFToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    if (token) return token.value;
    
    // Fallback: get from cookie
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// ===== SINGLE USER MODALS =====

function openSingleDeleteModal(userId, username, email) {
    console.log('openSingleDeleteModal called', userId, username, email);
    currentSingleUser = { id: userId, username: username, email: email };
    document.getElementById('singleDeleteUserInfo').innerHTML = `
        <p class="user-info-item"><strong>Username:</strong> ${username}</p>
        <p class="user-info-item"><strong>Email:</strong> ${email}</p>
    `;
    document.getElementById('singleDeleteUsernameInput').value = '';
    document.getElementById('singleDeleteSubmitBtn').disabled = true;
    document.getElementById('singleDeleteModal').classList.add('show');
    console.log('Modal should be visible now');
}

function closeSingleDeleteModal() {
    document.getElementById('singleDeleteModal').classList.remove('show');
    currentSingleUser = null;
}

document.getElementById('singleDeleteUsernameInput')?.addEventListener('input', function() {
    const submitBtn = document.getElementById('singleDeleteSubmitBtn');
    submitBtn.disabled = this.value !== currentSingleUser?.username;
});

async function confirmSingleDelete() {
    if (!currentSingleUser) return;
    
    const btn = document.getElementById('singleDeleteSubmitBtn');
    if (btn) { btn.disabled = true; btn.textContent = 'Deleting…'; }

    try {
        const response = await fetch(`/users/${currentSingleUser.id}/delete/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `confirmation=${encodeURIComponent(currentSingleUser.username)}`
        });
        
        if (response.redirected) {
            // Success — view redirected to users:list
            closeSingleDeleteModal();
            window.location.href = response.url;
            return;
        }

        // Non-redirect: check if it's an error page
        const text = await response.text();

        if (response.status === 403) {
            alert('Permission denied. Please refresh the page and try again.');
        } else {
            // Extract Django message from response if possible
            const match = text.match(/class="[^"]*alert[^"]*"[^>]*>([\s\S]*?)<\/div>/);
            const msg = match ? match[1].replace(/<[^>]+>/g, '').trim() : 'Error deleting user. Please try again.';
            alert(msg);
        }
        // Re-enable button on error
        if (btn) { btn.disabled = false; btn.textContent = 'Delete User'; }
    } catch (error) {
        if (btn) { btn.disabled = false; btn.textContent = 'Delete User'; }
        alert('Error: ' + error.message);
    }
}

function openSingleDeactivateModal(userId, username, email) {
    currentSingleUser = { id: userId, username: username, email: email };
    document.getElementById('singleDeactivateUserInfo').innerHTML = `
        <p class="user-info-item"><strong>Username:</strong> ${username}</p>
        <p class="user-info-item"><strong>Email:</strong> ${email}</p>
    `;
    document.getElementById('singleDeactivateModal').classList.add('show');
}

function closeSingleDeactivateModal() {
    document.getElementById('singleDeactivateModal').classList.remove('show');
    currentSingleUser = null;
}

async function confirmSingleDeactivate() {
    if (!currentSingleUser) return;
    
    const btn = document.querySelector('#singleDeactivateModal .btn-warning');
    if (btn) { btn.disabled = true; btn.textContent = 'Deactivating…'; }

    try {
        const response = await fetch(`/users/${currentSingleUser.id}/deactivate/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken(),
            }
        });
        
        if (response.redirected) {
            // Check if redirected back to detail (means an error message was set)
            // Either way, follow the redirect so the Django message is visible
            closeSingleDeactivateModal();
            window.location.href = response.url;
        } else {
            // Unexpected non-redirect — reload to show any Django messages
            closeSingleDeactivateModal();
            window.location.reload();
        }
    } catch (error) {
        if (btn) { btn.disabled = false; btn.textContent = 'Deactivate'; }
        alert('Error: ' + error.message);
    }
}

function openSingleActivateModal(userId, username, email) {
    currentSingleUser = { id: userId, username: username, email: email };
    document.getElementById('singleActivateUserInfo').innerHTML = `
        <p class="user-info-item"><strong>Username:</strong> ${username}</p>
        <p class="user-info-item"><strong>Email:</strong> ${email}</p>
    `;
    document.getElementById('singleActivateModal').classList.add('show');
}

function closeSingleActivateModal() {
    document.getElementById('singleActivateModal').classList.remove('show');
    currentSingleUser = null;
}

async function confirmSingleActivate() {
    if (!currentSingleUser) return;
    
    const btn = document.querySelector('#singleActivateModal .btn-success');
    if (btn) { btn.disabled = true; btn.textContent = 'Activating…'; }

    try {
        const response = await fetch(`/users/${currentSingleUser.id}/activate/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken(),
            }
        });
        
        if (response.redirected) {
            closeSingleActivateModal();
            window.location.href = response.url;
        } else {
            closeSingleActivateModal();
            window.location.reload();
        }
    } catch (error) {
        if (btn) { btn.disabled = false; btn.textContent = 'Activate'; }
        alert('Error: ' + error.message);
    }
}

// ===== BATCH OPERATIONS =====

function batchActivate() {
    if (selectedUsers.size === 0) return;
    
    // Open modal instead of confirm
    document.getElementById('batchActivateCount').textContent = selectedUsers.size;
    document.getElementById('batchActivateModal').classList.add('show');
}

function closeBatchActivateModal() {
    document.getElementById('batchActivateModal').classList.remove('show');
}

async function confirmBatchActivate() {
    if (selectedUsers.size === 0) return;
    
    try {
        const formData = new FormData();
        selectedUsers.forEach(id => formData.append('user_ids[]', id));
        
        const response = await fetch('/users/batch/activate/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken()
            },
            body: formData
        });
        
        let data;
        const contentType = response.headers.get('content-type') || '';
        if (contentType.includes('application/json')) {
            data = await response.json();
        } else {
            // Non-JSON response (redirect or HTML error)
            const text = await response.text();
            console.error('Non-JSON response from batch activate:', response.status, text.slice(0, 200));
            alert('Server error activating users. Please refresh and try again.');
            return;
        }
        
        if (data.success) {
            closeBatchActivateModal();
            alert(data.message);
            location.reload();
        } else {
            alert('Error: ' + data.message);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

function batchDeactivate() {
    if (selectedUsers.size === 0) return;
    
    // Open modal instead of confirm
    document.getElementById('batchDeactivateCount').textContent = selectedUsers.size;
    document.getElementById('batchDeactivateModal').classList.add('show');
}

function closeBatchDeactivateModal() {
    document.getElementById('batchDeactivateModal').classList.remove('show');
}

async function confirmBatchDeactivate() {
    if (selectedUsers.size === 0) return;
    
    try {
        const formData = new FormData();
        selectedUsers.forEach(id => formData.append('user_ids[]', id));
        
        const response = await fetch('/users/batch/deactivate/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken()
            },
            body: formData
        });
        
        let data;
        const contentType = response.headers.get('content-type') || '';
        if (contentType.includes('application/json')) {
            data = await response.json();
        } else {
            const text = await response.text();
            console.error('Non-JSON response from batch deactivate:', response.status, text.slice(0, 200));
            alert('Server error deactivating users. Please refresh and try again.');
            return;
        }
        
        if (data.success) {
            closeBatchDeactivateModal();
            alert(data.message);
            location.reload();
        } else {
            alert('Error: ' + data.message);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

function batchDelete() {
    if (selectedUsers.size === 0) return;
    
    // Open modal for batch delete
    document.getElementById('batchDeleteCount').textContent = selectedUsers.size;
    document.getElementById('batchDeleteInput').value = '';
    document.getElementById('batchDeleteSubmitBtn').disabled = true;
    document.getElementById('batchDeleteModal').classList.add('show');
}

function closeBatchDeleteModal() {
    document.getElementById('batchDeleteModal').classList.remove('show');
}

document.getElementById('batchDeleteInput')?.addEventListener('input', function() {
    const submitBtn = document.getElementById('batchDeleteSubmitBtn');
    submitBtn.disabled = this.value !== 'DELETE';
});

async function confirmBatchDelete() {
    if (selectedUsers.size === 0) return;
    
    try {
        const formData = new FormData();
        selectedUsers.forEach(id => formData.append('user_ids[]', id));
        formData.append('confirmation', 'DELETE');
        
        const response = await fetch('/users/batch/delete/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken()
            },
            body: formData
        });
        
        let data;
        const contentType = response.headers.get('content-type') || '';
        if (contentType.includes('application/json')) {
            data = await response.json();
        } else {
            // Server returned HTML — likely a CSRF failure (403) or server error (500)
            const text = await response.text();
            console.error('Non-JSON response from batch delete:', response.status, text.slice(0, 200));
            if (response.status === 403) {
                alert('Permission denied. Please refresh the page and try again.');
            } else {
                alert('Server error deleting users. Please refresh and try again.');
            }
            return;
        }
        
        if (data.success) {
            closeBatchDeleteModal();
            alert(data.message);
            location.reload();
        } else {
            alert('Error: ' + data.message);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}
