// Main application JavaScript

// Global state
let currentStep = 1;
let totalSteps = 3;
let uploadedPhotos = [];
let selectedSaleMode = null;
let listingData = {};

// Utility functions
function formatPrice(amount) {
    if (!amount) return 'Free';
    return `₪${parseInt(amount)}`;
}

function showLoading(show = true) {
    const modal = document.getElementById('loadingModal');
    if (!modal) return;
    
    const bsModal = bootstrap.Modal.getOrCreateInstance(modal);
    if (show) {
        bsModal.show();
    } else {
        bsModal.hide();
    }
}

function showToast(message, type = 'info') {
    // Create toast if it doesn't exist
    let toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toastContainer';
        toastContainer.className = 'position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '1055';
        document.body.appendChild(toastContainer);
    }

    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : 'primary'} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;

    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();

    // Remove from DOM after hiding
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

// API functions
async function apiCall(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
                // Pass Telegram initData so backend can restore session if cookie is missing
                ...window.tgWebApp?.getAuthHeaders?.()
            },
            credentials: 'include',
            ...options
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data;
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

// Photo upload handling
function initPhotoUpload() {
    const photoInput = document.getElementById('photoInput');
    const photoGrid = document.getElementById('photoGrid');
    
    if (!photoInput || !photoGrid) return;

    photoInput.addEventListener('change', handlePhotoSelection);
}

function handlePhotoSelection(event) {
    const files = Array.from(event.target.files);
    const photoGrid = document.getElementById('photoGrid');
    
    files.forEach(file => {
        if (uploadedPhotos.length >= 10) {
            showToast('Maximum 10 photos allowed', 'error');
            return;
        }
        
        if (file.size > 16 * 1024 * 1024) {
            showToast('File too large. Maximum 16MB allowed.', 'error');
            return;
        }
        
        const reader = new FileReader();
        reader.onload = (e) => {
            const photoData = {
                file: file,
                preview: e.target.result,
                id: Date.now() + Math.random()
            };
            
            uploadedPhotos.push(photoData);
            renderPhotoGrid();
        };
        reader.readAsDataURL(file);
    });
    
    // Clear input
    event.target.value = '';
}

function renderPhotoGrid() {
    const photoGrid = document.getElementById('photoGrid');
    if (!photoGrid) return;
    
    if (uploadedPhotos.length === 0) {
        photoGrid.style.display = 'none';
        return;
    }
    
    photoGrid.style.display = 'grid';
    photoGrid.innerHTML = uploadedPhotos.map((photo, index) => `
        <div class="photo-item" data-id="${photo.id}">
            <img src="${photo.preview}" alt="Photo ${index + 1}">
            <button type="button" class="photo-remove" onclick="removePhoto('${photo.id}')">
                <i data-feather="x"></i>
            </button>
        </div>
    `).join('');
    
    feather.replace();
}

function removePhoto(photoId) {
    uploadedPhotos = uploadedPhotos.filter(photo => photo.id !== photoId);
    renderPhotoGrid();
    try {
        window.tgWebApp.hapticFeedback('impact');
    } catch(e) {
        // Haptic feedback not available, continue without it
    }
}

// Step navigation
function updateStepProgress() {
    const stepIndicator = document.getElementById('stepIndicator');
    const progressBar = document.getElementById('progressBar');
    const nextBtn = document.getElementById('nextBtn');
    const prevBtn = document.getElementById('prevBtn');
    
    if (stepIndicator) stepIndicator.textContent = `${currentStep}/${totalSteps}`;
    if (progressBar) progressBar.style.width = `${(currentStep / totalSteps) * 100}%`;
    
    // Update buttons based on step
    const normalButtons = document.getElementById('normalButtons');
    const previewButtons = document.getElementById('previewButtons');
    
    if (currentStep === totalSteps) {
        // Preview step - show special buttons
        if (normalButtons) normalButtons.style.display = 'none';
        if (previewButtons) previewButtons.style.display = 'flex';
    } else {
        // Normal steps - show regular buttons
        if (normalButtons) normalButtons.style.display = 'flex';
        if (previewButtons) previewButtons.style.display = 'none';
        
        if (prevBtn) prevBtn.style.display = currentStep > 1 ? 'block' : 'none';
        
        if (nextBtn) {
            nextBtn.textContent = 'Next';
            nextBtn.className = 'btn btn-primary w-100';
        }
    }
    
    // Show current step
    document.querySelectorAll('.step-content').forEach((step, index) => {
        step.style.display = index + 1 === currentStep ? 'block' : 'none';
    });
    
    // Update preview if on preview step
    if (currentStep === 3) {
        updatePreview();
    }
}

function nextStep() {
    if (!validateCurrentStep()) return;
    
    if (currentStep < totalSteps) {
        currentStep++;
        updateStepProgress();
        updatePreview();
        window.tgWebApp.hapticFeedback('selection');
        
        // Auto-scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

function prevStep() {
    if (currentStep > 1) {
        currentStep--;
        updateStepProgress();
        window.tgWebApp.hapticFeedback('selection');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

function validateCurrentStep() {
    switch (currentStep) {
        case 1: // Photos & Details
            return validateDetails();
        case 2: // Sale mode
            return validateSaleMode();
        case 3: // Preview
            return true; // No terms checkbox to validate
        default:
            return true;
    }
}

function validateDetails() {
    const title = document.getElementById('title').value.trim();
    if (!title) {
        showToast('Please enter a title for your listing', 'error');
        document.getElementById('title').focus();
        return false;
    }
    return true;
}

function validateSaleMode() {
    if (!selectedSaleMode) {
        showToast('Please select a sale mode', 'error');
        return false;
    }
    
    // Validate mode-specific fields
    switch (selectedSaleMode) {
        case 'fixed_price':
            const fixedPrice = document.getElementById('fixedPrice').value;
            if (!fixedPrice || parseFloat(fixedPrice) <= 0) {
                showToast('Please enter a valid price', 'error');
                document.getElementById('fixedPrice').focus();
                return false;
            }
            break;
        case 'auction':
            const startPrice = document.getElementById('startPrice').value;
            if (!startPrice || parseFloat(startPrice) <= 0) {
                showToast('Please enter a valid starting price', 'error');
                document.getElementById('startPrice').focus();
                return false;
            }
            break;
    }
    
    return true;
}

function validatePreview() {
    return true; // No validation needed for preview step
}

// Sale mode handling
function initSaleModeSelection() {
    document.querySelectorAll('.mode-card').forEach(card => {
        card.addEventListener('click', () => {
            const mode = card.dataset.mode;
            selectSaleMode(mode);
        });
    });
}

function selectSaleMode(mode) {
    selectedSaleMode = mode;
    
    // Update UI
    document.querySelectorAll('.mode-card').forEach(card => {
        card.classList.toggle('selected', card.dataset.mode === mode);
    });
    
    // Show/hide mode settings
    const modeSettings = document.getElementById('modeSettings');
    const modeConfigs = document.querySelectorAll('.mode-config');
    
    modeConfigs.forEach(config => config.style.display = 'none');
    
    if (mode !== 'free') {
        modeSettings.style.display = 'block';
        let configId;
        switch (mode) {
            case 'fixed_price':
                configId = 'fixedPriceConfig';
                break;
            case 'name_your_price':
                configId = 'nameYourPriceConfig';
                break;
            case 'auction':
                configId = 'auctionConfig';
                break;
            default:
                configId = mode + 'Config';
        }
        const config = document.getElementById(configId);
        if (config) config.style.display = 'block';
    } else {
        modeSettings.style.display = 'none';
    }
    
    window.tgWebApp.hapticFeedback('selection');
}

// Preview generation
function updatePreview() {
    if (currentStep !== 3) return;
    
    const previewContainer = document.getElementById('listingPreview');
    if (!previewContainer) return;
    
    collectListingData();
    
    const preview = generatePreviewHTML();
    previewContainer.innerHTML = preview;
    
    feather.replace();
}

function collectListingData() {
    const titleValue = document.getElementById('title').value.trim();
    const descriptionValue = document.getElementById('description').value.trim();
    
    listingData = {
        title: titleValue,
        description: descriptionValue,
        sale_mode: selectedSaleMode,
        photos: uploadedPhotos
    };
    
    console.log('Collected listing data:', listingData);
    
    // Mode-specific data
    switch (selectedSaleMode) {
        case 'fixed_price':
            listingData.fixed_price = document.getElementById('fixedPrice').value;
            listingData.is_negotiable = document.getElementById('isNegotiable').checked;
            break;
        case 'name_your_price':
            listingData.min_price = document.getElementById('minPrice').value;
            listingData.private_offers = document.getElementById('privateOffers').checked;
            break;
        case 'auction':
            listingData.start_price = document.getElementById('startPrice').value;
            listingData.bid_step = document.getElementById('bidStep').value;
            listingData.end_time = document.getElementById('endDate').value;
            break;
    }
    
    listingData.allow_queue = false;
}

function generatePreviewHTML() {
    const photos = uploadedPhotos.length > 0 ? `
        <div class="listing-image mb-3">
            <img src="${uploadedPhotos[0].preview}" alt="${listingData.title}" class="img-fluid rounded">
            ${uploadedPhotos.length > 1 ? `<div class="photo-count"><i data-feather="image"></i> ${uploadedPhotos.length}</div>` : ''}
        </div>
    ` : '';
    
    let priceInfo = '';
    switch (selectedSaleMode) {
        case 'fixed_price':
            priceInfo = `
                <div class="price">${formatPrice(listingData.fixed_price)}</div>
                ${listingData.is_negotiable ? '<div class="price-note">Negotiable</div>' : ''}
            `;
            break;
        case 'free':
            priceInfo = '<div class="price">Free</div>';
            break;
        case 'name_your_price':
            priceInfo = `
                <div class="price">Make Offer</div>
                ${listingData.min_price ? `<div class="price-note">Min: ${formatPrice(listingData.min_price)}</div>` : ''}
            `;
            break;
        case 'auction':
            priceInfo = `
                <div class="price">Starting at ${formatPrice(listingData.start_price)}</div>
                <div class="price-note">Auction</div>
            `;
            break;
    }
    
    return `
        <div class="listing-card">
            <div class="listing-header">
                <h4 class="listing-title">${listingData.title}</h4>
                <span class="status-chip status-draft">Draft</span>
            </div>
            
            ${photos}
            
            <div class="listing-details">
                <div class="price-info">
                    ${priceInfo}
                </div>
                
                ${listingData.description ? `
                    <div class="listing-description mt-2">
                        <p class="text-muted mb-0">${listingData.description}</p>
                    </div>
                ` : ''}
                
                <div class="listing-meta mt-2">
                    ${listingData.category ? `<span class="badge bg-secondary me-2">${listingData.category}</span>` : ''}
                    ${listingData.condition ? `<span class="badge bg-secondary">${listingData.condition}</span>` : ''}
                </div>
            </div>
        </div>
    `;
}

// Listing submission
async function submitListing() {
    try {
        showLoading(true);
        collectListingData();
        
        // Create listing
        const listing = await apiCall('/api/listings', {
            method: 'POST',
            body: JSON.stringify(listingData)
        });
        
        // Upload photos if any
        if (uploadedPhotos.length > 0) {
            await uploadPhotos(listing.listing_id);
        }
        
        // Publish listing
        await apiCall(`/api/listings/${listing.listing_id}/publish`, {
            method: 'POST'
        });
        
        showLoading(false);
        window.tgWebApp.hapticFeedback('notification');
        showToast('Listing created successfully!', 'success');
        
        // Redirect to main page
        setTimeout(() => {
            window.location.href = '/';
        }, 1500);
        
    } catch (error) {
        showLoading(false);
        console.error('Error submitting listing:', error);
        showToast('Failed to create listing. Please try again.', 'error');
    }
}

// Save as draft
async function saveDraft() {
    try {
        showLoading(true);
        collectListingData();
        
        // Create listing (stays as draft)
        const listing = await apiCall('/api/listings', {
            method: 'POST',
            body: JSON.stringify(listingData)
        });
        
        // Upload photos if any
        if (uploadedPhotos.length > 0) {
            await uploadPhotos(listing.listing_id);
        }
        
        showLoading(false);
        window.tgWebApp.hapticFeedback('notification');
        showToast('Draft saved successfully!', 'success');
        
        // Redirect to main page
        setTimeout(() => {
            window.location.href = '/';
        }, 1500);
        
    } catch (error) {
        showLoading(false);
        console.error('Error saving draft:', error);
        showToast('Failed to save draft. Please try again.', 'error');
    }
}

async function uploadPhotos(listingId) {
    const formData = new FormData();
    
    uploadedPhotos.forEach((photo, index) => {
        formData.append(`photo_${index}`, photo.file);
    });
    
    const response = await fetch(`/api/listings/${listingId}/photos`, {
        method: 'POST',
        credentials: 'include',
        // Attach Telegram initData header as well for auth rehydration
        headers: {
            ...window.tgWebApp?.getAuthHeaders?.()
        },
        body: formData
    });
    
    if (!response.ok) {
        throw new Error('Photo upload failed');
    }
    
    return await response.json();
}

// Create listing initialization
function initCreateListing() {
    initPhotoUpload();
    initSaleModeSelection();
    
    // Button handlers
    const nextBtn = document.getElementById('nextBtn');
    const prevBtn = document.getElementById('prevBtn');
    const prevBtnPreview = document.getElementById('prevBtnPreview');
    const saveDraftBtn = document.getElementById('saveDraftBtn');
    const publishBtn = document.getElementById('publishBtn');
    
    if (nextBtn) nextBtn.addEventListener('click', nextStep);
    if (prevBtn) prevBtn.addEventListener('click', prevStep);
    if (prevBtnPreview) prevBtnPreview.addEventListener('click', prevStep);
    if (saveDraftBtn) saveDraftBtn.addEventListener('click', saveDraft);
    if (publishBtn) publishBtn.addEventListener('click', submitListing);
    
    // Initialize first step
    updateStepProgress();
    
    // Set minimum end date for auctions
    const endDateInput = document.getElementById('endDate');
    if (endDateInput) {
        const now = new Date();
        now.setHours(now.getHours() + 1); // Minimum 1 hour from now
        endDateInput.min = now.toISOString().slice(0, 16);
    }
}

// My listings page functionality
function initMyListings() {
    // Filter handling
    document.querySelectorAll('input[name="statusFilter"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            if (e.target.checked) {
                const status = e.target.id.replace('filter', '').toLowerCase();
                const url = new URL(window.location);
                if (status === 'all') {
                    url.searchParams.delete('status');
                } else {
                    url.searchParams.set('status', status);
                }
                window.location.href = url.toString();
            }
        });
    });
    
    // Initialize auction timers
    initAuctionTimers();
}

function initAuctionTimers() {
    document.querySelectorAll('.auction-timer').forEach(timer => {
        const endTime = new Date(timer.dataset.endTime);
        updateTimer(timer, endTime);
        
        // Update every second
        setInterval(() => updateTimer(timer, endTime), 1000);
    });
}

function updateTimer(timerElement, endTime) {
    const now = new Date();
    const diff = endTime - now;
    
    const display = timerElement.querySelector('.timer-display');
    if (!display) return;
    
    if (diff <= 0) {
        display.textContent = 'Auction ended';
        timerElement.classList.add('text-danger');
        return;
    }
    
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((diff % (1000 * 60)) / 1000);
    
    if (hours > 0) {
        display.textContent = `${hours}h ${minutes}m remaining`;
    } else if (minutes > 0) {
        display.textContent = `${minutes}m ${seconds}s remaining`;
    } else {
        display.textContent = `${seconds}s remaining`;
        timerElement.classList.add('text-warning');
    }
}

// Listing actions
async function publishListing(listingId) {
    try {
        await apiCall(`/api/listings/${listingId}/publish`, {
            method: 'POST'
        });
        
        showToast('Listing published successfully!', 'success');
        setTimeout(() => location.reload(), 1000);
        
    } catch (error) {
        showToast('Failed to publish listing', 'error');
    }
}

async function closeListing(listingId) {
    const confirmed = confirm('Are you sure you want to close this listing?');
    if (!confirmed) return;
    
    try {
        await apiCall(`/api/listings/${listingId}/close`, {
            method: 'POST'
        });
        
        showToast('Listing closed successfully!', 'success');
        setTimeout(() => location.reload(), 1000);
        
    } catch (error) {
        console.error('Error closing listing:', error);
        showToast('Failed to close listing', 'error');
    }
}

function editListing(listingId) {
    // For now, redirect to create page (could be enhanced to pre-fill data)
    window.location.href = '/create';
}

function deleteListing(listingId) {
    window.tgWebApp.showConfirm(
        'Are you sure you want to delete this listing? This action cannot be undone.',
        async (confirmed) => {
            if (!confirmed) return;
            
            try {
                await apiCall(`/api/listings/${listingId}`, {
                    method: 'DELETE'
                });
                
                showToast('Listing deleted successfully!', 'success');
                setTimeout(() => location.reload(), 1000);
                
            } catch (error) {
                showToast('Failed to delete listing', 'error');
            }
        }
    );
}

// Initialize Feather icons on page load
document.addEventListener('DOMContentLoaded', () => {
    feather.replace();
});

// Handle Telegram back button
document.addEventListener('telegram-back-button-click', () => {
    if (window.location.pathname === '/create' && currentStep > 1) {
        prevStep();
    } else {
        history.back();
    }
});

// Show back button on create listing page
if (window.location.pathname === '/create') {
    window.tgWebApp.showBackButton();
}

// Fix button clicks - ensure they work without WebApp API
document.addEventListener('DOMContentLoaded', function() {
    // Make all buttons and links clickable with visual feedback
    document.querySelectorAll('button, a').forEach(element => {
        element.style.cursor = 'pointer';
        element.style.userSelect = 'none';
        
        // Add visual feedback without preventing default behavior
        element.addEventListener('touchstart', function(e) {
            this.style.transform = 'scale(0.95)';
        });
        
        element.addEventListener('touchend', function(e) {
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 100);
        });
        
        element.addEventListener('mousedown', function(e) {
            this.style.transform = 'scale(0.95)';
        });
        
        element.addEventListener('mouseup', function(e) {
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 100);
        });
    });
});
