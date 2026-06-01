// ============================================
// HOTEL BOOKING SYSTEM - DEBUGGED VERSION
// ============================================
const API_BASE = 'http://localhost:5000/api';

// ============================================
// GLOBAL STATE
// ============================================
let currentUser = null;
let currentToken = null;
let selectedRoom = null;
let searchResults = [];

console.log('🚀 Script loading started...');

// ============================================
// INITIALIZATION - RUNS WHEN PAGE LOADS
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ DOM Content Loaded - Novacrest Hotel System Initializing');
    console.log('📍 Current page:', window.location.pathname);
    
    // Load user from localStorage
    loadUserFromStorage();
    updateNavbar();

    // ============================================
    // DATE RESTRICTION - PAST DATES DISABLED
    // ============================================
    const today = new Date();
    today.setHours(0, 0, 0, 0); // Reset to midnight
    const todayString = today.toISOString().split('T')[0];
    
    const checkInInput = document.getElementById('checkIn');
    const checkOutInput = document.getElementById('checkOut');
    
    if (checkInInput) {
        checkInInput.min = todayString;
        console.log('✅ Check-in min date set to:', todayString);
        
        // When check-in changes, update check-out minimum
        checkInInput.addEventListener('change', function() {
            const checkInDate = new Date(this.value);
            checkInDate.setDate(checkInDate.getDate() + 1); // Next day
            const minCheckOut = checkInDate.toISOString().split('T')[0];
            
            if (checkOutInput) {
                checkOutInput.min = minCheckOut;
                console.log('✅ Check-out min date updated to:', minCheckOut);
                
                // If current check-out is before new minimum, clear it
                if (checkOutInput.value && checkOutInput.value <= this.value) {
                    checkOutInput.value = '';
                }
            }
        });
    }
    
    if (checkOutInput) {
        const tomorrow = new Date(today);
        tomorrow.setDate(tomorrow.getDate() + 1);
        checkOutInput.min = tomorrow.toISOString().split('T')[0];
        console.log('✅ Check-out min date set to:', checkOutInput.min);
    }

    // ============================================
    // GUEST COUNTER
    // ============================================
    const guestCount = document.getElementById('guestCount');
    const decrease = document.getElementById('decreaseGuests');
    const increase = document.getElementById('increaseGuests');

    if (guestCount && decrease && increase) {
        console.log('✅ Guest counter elements found');
        
        decrease.addEventListener('click', function(e) {
            e.preventDefault();
            let count = parseInt(guestCount.textContent);
            if (count > 1) {
                count--;
                guestCount.textContent = count;
                console.log('👥 Guest count decreased to:', count);
            }
        });

        increase.addEventListener('click', function(e) {
            e.preventDefault();
            let count = parseInt(guestCount.textContent);
            if (count < 10) {
                count++;
                guestCount.textContent = count;
                console.log('👥 Guest count increased to:', count);
            }
        });
    } else {
        console.log('⚠️ Guest counter elements not found');
    }

    // ============================================
    // SEARCH BUTTON - CRITICAL FIX
    // ============================================
    const searchBtn = document.getElementById('searchBtn');
    if (searchBtn) {
        console.log('✅ Search button found:', searchBtn);
        
        // Remove any existing listeners
        searchBtn.onclick = null;
        
        // Add new click listener
        searchBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('🔍 SEARCH BUTTON CLICKED!');
            searchRooms();
        });
        
        console.log('✅ Search button listener attached');
    } else {
        console.error('❌ Search button NOT FOUND! Looking for element with id="searchBtn"');
        console.log('Available buttons:', document.querySelectorAll('button'));
    }

    // ============================================
    // MOBILE MENU TOGGLE
    // ============================================
    const toggle = document.querySelector('.mobile-toggle');
    if (toggle) {
        toggle.addEventListener('click', () => {
            document.querySelector('.nav-links').classList.toggle('active');
            console.log('📱 Mobile menu toggled');
        });
    }

    // ============================================
    // PAGE-SPECIFIC INITIALIZATIONS
    // ============================================
    
    // Load initial rooms on homepage
    if (document.getElementById('roomsGrid')) {
        console.log('🏠 Homepage detected - Loading room categories');
        loadAllRooms();
    }

    // Load recommendations preview
    if (document.getElementById('recommendationsGrid') && document.body.id !== "recommendationsPage") {
        console.log('🌟 Loading recommendations preview');
        loadRecommendationsPreview();   // homepage only
    }


    // Dashboard pages
    // Admin dashboard must be checked BEFORE customer dashboard
    // Dashboard pages
    const bodyId = document.body.id;

    if (bodyId === 'adminDashboardPage') {
        console.log('🔐 Admin dashboard detected');
        loadAdminDashboard();
    }
    else if (bodyId === 'userDashboardPage') {
        console.log('📊 User dashboard detected');
        loadUserBookings();
    }



    if (document.body.id === "recommendationsPage") {
        console.log('🗺️ Full recommendations page detected');
        loadAllRecommendations();
    }

    // ============================================
    // HEADER SCROLL & MOBILE BOOK NOW BAR
    // ============================================
    const header = document.getElementById('mainHeader');
    const bookBar = document.getElementById('mobileBookNowBar');
    
    if (header && window.scrollY > 50) {
        header.classList.add('scrolled');
    }
    
    window.addEventListener('scroll', () => {
        if (header) {
            if (window.scrollY > 50) {
                header.classList.add('scrolled');
            } else {
                header.classList.remove('scrolled');
            }
        }
        
        if (bookBar) {
            if (window.scrollY > 400 && window.innerWidth <= 768) {
                bookBar.style.display = 'flex';
            } else {
                bookBar.style.display = 'none';
            }
        }
    });

    console.log('✅ Initialization complete!');
});

// ============================================
// AUTHENTICATION
// ============================================
async function register() {
    console.log('📝 Registration started');
    
    const email = document.getElementById('registerEmail')?.value;
    const password = document.getElementById('registerPassword')?.value;
    const firstName = document.getElementById('registerFirstName')?.value;
    const lastName = document.getElementById('registerLastName')?.value;
    const phone = document.getElementById('registerPhone')?.value;

    if (!email || !password || !firstName || !lastName || !phone) {
        showAlert('Please fill all fields', 'error');
        return;
    }

    if (password.length < 8) {
        showAlert('Password must be at least 8 characters', 'error');
        return;
    }

    try {
        showSpinner('registerBtn', true);

        const response = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                email, 
                password, 
                first_name: firstName, 
                last_name: lastName, 
                phone 
            })
        });

        const data = await response.json();
        console.log('Registration response:', data);

        if (response.ok) {
            showAlert('Registration successful! Redirecting to login...', 'success');
            setTimeout(() => window.location.href = 'login.html', 2000);
        } else {
            showAlert(data.message || 'Registration failed', 'error');
        }
    } catch (error) {
        console.error('❌ Registration error:', error);
        showAlert('Network error. Please try again.', 'error');
    } finally {
        showSpinner('registerBtn', false);
    }
}

async function login() {
    console.log('🔐 Login started');
    
    const email = document.getElementById('email')?.value;
    const password = document.getElementById('password')?.value;

    if (!email || !password) {
        showAlert('Please enter email and password', 'error');
        return;
    }

    try {
        showSpinner('loginBtn', true);

        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();
        console.log('Login response:', data);

        if (response.ok) {
            saveUserToStorage(data.user, data.access_token);

            setTimeout(() => {
                if (data.user.role === "admin") {
                    window.location.href = "dashboard-admin.html";
                } else {
                    const urlParams = new URLSearchParams(window.location.search);
                    const redirect = urlParams.get('redirect');
                    if (redirect) {
                        window.location.href = redirect;
                    } else {
                        window.location.href = "dashboard.html";
                    }
                }
            }, 1500);
        } else {
            showAlert(data.message || 'Invalid credentials', 'error');
        }
    } catch (error) {
        console.error('❌ Login error:', error);
        showAlert('Network error. Please try again.', 'error');
    } finally {
        showSpinner('loginBtn', false);
    }
}

function logout() {
    console.log('👋 Logging out');
    localStorage.removeItem('user');
    localStorage.removeItem('token');
    currentUser = null;
    currentToken = null;
    showAlert('Logged out successfully', 'success');
    setTimeout(() => window.location.href = 'index.html', 1000);
}

function saveUserToStorage(user, token) {
    if (!user || !token) {
        console.error("❌ Missing user or token in saveUserToStorage");
        return;
    }

    const userData = {
        user_id: user.user_id,
        email: user.email,
        role: user.role,
    };

    localStorage.setItem("user", JSON.stringify(userData));
    localStorage.setItem("token", token);

    currentUser = userData;
    currentToken = token;

    console.log("✅ User saved to localStorage:", userData);
}


function loadUserFromStorage() {
    const userStr = localStorage.getItem('user');
    const token = localStorage.getItem('token');
    
    if (userStr && token) {
        try {
            currentUser = JSON.parse(userStr);
            currentToken = token;
            console.log('✅ User loaded from localStorage:', currentUser);
        } catch (e) {
            console.error('❌ Error parsing user data:', e);
            localStorage.removeItem('user');
            localStorage.removeItem('token');
        }
    } else {
        console.log('ℹ️ No user in localStorage');
    }
}

function updateNavbar() {
    const userInfo = document.getElementById('userInfo');
    const loginBtn = document.querySelector('a[href="login.html"]');
    const registerBtn = document.querySelector('a[href="register.html"]');
    const logoutBtn = document.getElementById('logoutBtn');
    const dashboardBtn = document.getElementById('dashboardBtn');

    if (currentUser) {
        console.log('👤 Updating navbar for logged-in user');
        if (userInfo) {
            const username = currentUser.email?.split('@')[0] || 'User';
            userInfo.innerHTML = `Hello, ${username}`;
        }
        if (loginBtn) loginBtn.style.display = 'none';
        if (registerBtn) registerBtn.style.display = 'none';
        if (logoutBtn) logoutBtn.style.display = 'inline-block';
        if (dashboardBtn) {
            dashboardBtn.style.display = 'inline-block';
            dashboardBtn.href = currentUser.role === 'admin' ? 'dashboard-admin.html' : 'dashboard.html';
        }
    } else {
        console.log('🔓 Updating navbar for guest user');
        if (userInfo) userInfo.innerHTML = '';
        if (loginBtn) loginBtn.style.display = 'inline-block';
        if (registerBtn) registerBtn.style.display = 'inline-block';
        if (logoutBtn) logoutBtn.style.display = 'none';
        if (dashboardBtn) dashboardBtn.style.display = 'none';
    }
}

// ============================================
// ROOM SEARCH & DISPLAY
// ============================================
async function searchRooms() {
    console.log('🔍 ========== SEARCH FUNCTION CALLED ==========');
    
    const checkIn = document.getElementById('checkIn')?.value;
    const checkOut = document.getElementById('checkOut')?.value;
    const guestCount = document.getElementById('guestCount')?.textContent || 2;

    console.log('📅 Check-in:', checkIn);
    console.log('📅 Check-out:', checkOut);
    console.log('👥 Guests:', guestCount);

    // Validation
    if (!checkIn || !checkOut) {
        showAlert('Please select check-in and check-out dates', 'error');
        console.log('❌ Missing dates');
        return;
    }

    const checkInDate = new Date(checkIn);
    const checkOutDate = new Date(checkOut);
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    if (checkInDate < today) {
        showAlert('Check-in date cannot be in the past', 'error');
        console.log('❌ Check-in date is in the past');
        return;
    }

    if (checkOutDate <= checkInDate) {
        showAlert('Check-out must be after check-in', 'error');
        console.log('❌ Invalid date range');
        return;
    }

    try {
        showSpinner('searchBtn', true);

        const url = `${API_BASE}/bookings/search?check_in=${checkIn}&check_out=${checkOut}&guests=${guestCount}`;
        console.log('📡 Fetching:', url);

        const response = await fetch(url);
        const data = await response.json();

        console.log('📦 Response status:', response.status);
        console.log('📦 Response data:', data);

        if (response.ok) {
            searchResults = data.available_categories || [];
            console.log(`✅ Found ${searchResults.length} room categories`);
            displaySearchResults(searchResults);
            showAlert(`Found ${data.total_found} room type(s) available`, 'success');
            
            // Scroll to results
            document.getElementById('rooms')?.scrollIntoView({ behavior: 'smooth' });
        } else {
            showAlert(data.message || 'Search failed', 'error');
            console.log('❌ Search failed:', data.message);
        }
    } catch (error) {
        console.error('❌ Search error:', error);
        showAlert('Network error. Please check if the server is running.', 'error');
    } finally {
        showSpinner('searchBtn', false);
    }
}

function getRoomImageUrl(name) {
    const images = {
        'Standard Room': 'https://images.unsplash.com/photo-1591088398332-8a7791972843?auto=format&fit=crop&w=800&q=80',
        'Deluxe Room': 'https://images.unsplash.com/photo-1611892440504-42a792e24d32?auto=format&fit=crop&w=800&q=80',
        'Super Deluxe Room': 'https://images.unsplash.com/photo-1582719508461-905c673771fd?auto=format&fit=crop&w=800&q=80',
        'Executive Room': 'https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=800&q=80',
        'Family Suite': 'https://images.unsplash.com/photo-1598928506311-c55ded91a20c?auto=format&fit=crop&w=800&q=80',
        'Honeymoon Suite': 'https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=800&q=80'
    };
    return images[name] || 'https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=800&q=80';
}

function displaySearchResults(results) {
    const container = document.getElementById('roomsGrid');
    
    if (!container) {
        console.error('❌ roomsGrid container not found');
        return;
    }

    console.log('🎨 Displaying', results.length, 'results');

    if (results.length === 0) {
        container.innerHTML = `
            <div class="empty-state" style="grid-column: 1/-1; text-align: center; padding: 4rem;">
                <h3 style="color: var(--color-gold); font-family: var(--font-serif); margin-bottom: 1rem;">No suites available</h3>
                <p style="color: #666;">Try different dates or fewer guests.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = results.map(cat => {
        const imageUrl = getRoomImageUrl(cat.name);
        return `
            <div class="room-card">
                <div class="room-image-wrapper">
                    <div class="room-image" style="background-image: url('${imageUrl}');"></div>
                    <div class="room-price-badge">From <span>₹${cat.base_price.toFixed(2)}</span></div>
                </div>
                <div class="room-info">
                    <h3>${cat.name}</h3>
                    <p class="room-desc">${cat.description || 'A private sanctuary of absolute comfort and design.'}</p>
                    
                    <div class="room-details">
                        <span class="room-detail-item">👥 Capacity: <strong>${cat.capacity} Guests</strong></span>
                        <span class="room-detail-item">🌙 Nights: <strong>${cat.nights}</strong></span>
                        <span class="room-detail-item">📍 Chambers: <strong>${cat.available_count} Left</strong></span>
                    </div>
                    
                    <p style="font-family: var(--font-serif); font-size: 1.35rem; color: var(--color-gold); margin-bottom: 1.5rem;">
                        Total for stay: ₹${cat.total_price.toFixed(2)}
                    </p>
                    
                    <p style="font-size: 0.82rem; color: #666; margin-bottom: 1.8rem; line-height: 1.6;">
                        <strong>Amenities Included:</strong><br>
                        ${cat.amenities.join(' • ')}
                    </p>
                    
                    ${currentUser 
                        ? `<button class="btn btn-primary full-width" onclick="selectRoomForBooking('${cat.category_id}', '${cat.name}', ${cat.total_price}, document.getElementById('checkIn').value, document.getElementById('checkOut').value)">
                            Book Suite
                           </button>`
                        : `<button class="btn btn-primary full-width" onclick="showAlert('Please login to book rooms', 'info'); setTimeout(() => window.location.href='login.html', 1500)">
                            Login to Book
                           </button>`
                    }
                </div>
            </div>
        `;
    }).join('');
}

async function loadAllRooms() {
    try {
        console.log('📦 Loading all room categories');
        const response = await fetch(`${API_BASE}/bookings/categories`);
        const data = await response.json();

        if (response.ok) {
            const categories = data.categories || [];
            console.log('✅ Loaded', categories.length, 'categories');
            displayAllRooms(categories);
        }
    } catch (error) {
        console.error('❌ Error loading rooms:', error);
    }
}

function displayAllRooms(categories) {
    const container = document.getElementById('roomsGrid');
    if (!container) return;

    container.innerHTML = categories.map(cat => {
        const imageUrl = getRoomImageUrl(cat.name);
        return `
            <div class="room-card">
                <div class="room-image-wrapper">
                    <div class="room-image" style="background-image: url('${imageUrl}');"></div>
                    <div class="room-price-badge">From <span>₹${cat.base_price}/night</span></div>
                </div>
                <div class="room-info">
                    <h3>${cat.name}</h3>
                    <p class="room-desc">${cat.description}</p>
                    <div class="room-details" style="border-bottom: none; margin-bottom: 0.5rem;">
                        <span class="room-detail-item">👥 Capacity: <strong>Max ${cat.capacity} Guests</strong></span>
                    </div>
                    <p style="font-size: 0.82rem; color: #666; margin-bottom: 1.8rem; line-height: 1.6;">
                        <strong>Amenities Included:</strong><br>
                        ${cat.amenities.join(' • ')}
                    </p>
                    <button class="btn btn-primary full-width" onclick="showAlert('Please use the search widget above to check availability', 'info'); window.scrollTo({top: 0, behavior: 'smooth'})">
                        Check Availability
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

function selectRoomForBooking(categoryId, categoryName, totalPrice, checkIn, checkOut) {
    const guests = parseInt(document.getElementById("guestCount")?.textContent || 1);

    console.log('🎯 Room selected:', { categoryId, categoryName, totalPrice, checkIn, checkOut, guests });
    
    selectedRoom = { categoryId, categoryName, totalPrice, checkIn, checkOut, guests };
    
    if (confirm(`📋 Confirm Booking\n\nRoom: ${categoryName}\nPrice: ₹${totalPrice}\nCheck-in: ${checkIn}\nCheck-out: ${checkOut}\n\nProceed to book?`)) {
        bookRoom(categoryId, checkIn, checkOut, guests);
    }
}

// ============================================
// BOOKING
// ============================================
async function bookRoom(categoryId, checkIn, checkOut, guests) {
    if (!currentUser || !currentToken) {
        showAlert('Please login to book', 'error');
        setTimeout(() => window.location.href = 'login.html', 1500);
        return;
    }

    console.log('📝 Booking room:', { categoryId, checkIn, checkOut, guests });

    try {
        const response = await fetch(`${API_BASE}/bookings`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentToken}`
            },
            body: JSON.stringify({
                category_id: parseInt(categoryId),
                check_in_date: checkIn,
                check_out_date: checkOut,
                guests: guests
            })
        });

        const data = await response.json();
        console.log('📦 Booking response:', data);  // ✅ Check this in console

        if (response.ok) {
            // ✅ FIXED: Use the variable you created
            const bookingId = data.booking_id;
            
            console.log('✅ Booking ID:', bookingId);  // Debug log
            
            if (!bookingId) {
                showAlert('Booking created but no ID received', 'error');
                console.error('❌ Missing booking_id in response:', data);
                return;
            }
            
            showAlert('Booking successful! Redirecting to payment...', 'success');
            setTimeout(() => {
                window.location.href = `payment.html?booking_id=${bookingId}`;  // ✅ Use the variable
            }, 1500);
        } else {
            showAlert(data.message || 'Booking failed', 'error');
        }
    } catch (error) {
        console.error('❌ Booking error:', error);
        showAlert('Network error. Please try again.', 'error');
    }
}

// ============================================
// PAYMENT
// ============================================
async function loadPaymentDetails() {
    const urlParams = new URLSearchParams(window.location.search);
    const bookingId = urlParams.get('booking_id');
    
    if (!bookingId) {
        showAlert('No booking ID found', 'error');
        setTimeout(() => window.location.href = 'index.html', 2000);
        return;
    }

    if (!currentUser || !currentToken) {
        showAlert('Please login to view booking', 'error');
        setTimeout(() => window.location.href = 'login.html', 2000);
        return;
    }

    console.log('💳 Loading payment details for booking:', bookingId);
    
    try {
        // FETCH THE BOOKING DATA
        const response = await fetch(`${API_BASE}/bookings/${bookingId}`, {
            headers: { 'Authorization': `Bearer ${currentToken}` }
        });

        const data = await response.json();
        console.log('📦 Booking data:', data);

        if (response.ok && data.booking) {
            const booking = data.booking;
            console.log('✅ Booking loaded:', booking);
            
            // Update the page content - using querySelector to find elements more reliably
            // const roomTypeEl = document.querySelector('.booking-summary p:nth-of-type(1)');
            // const datesEl = document.querySelector('.booking-summary p:nth-of-type(2)');
            // const guestsEl = document.querySelector('.booking-summary p:nth-of-type(3)');
            // const totalEl = document.querySelector('.booking-summary p:nth-of-type(4)');
            
            const roomTypeEl = document.getElementById('roomType');
            const datesEl = document.getElementById('dates');
            const guestsEl = document.getElementById('guestsCount');
            const totalEl = document.getElementById('totalAmount');

            // Apply values
            roomTypeEl.textContent = `Room ${booking.room_id}`;
            datesEl.textContent = `${booking.check_in_date} to ${booking.check_out_date}`;
            guestsEl.textContent = booking.guests;
            totalEl.textContent = `₹${booking.total_amount}`;

            console.log('📝 Found elements:', { roomTypeEl, datesEl, guestsEl, totalEl });
            
            if (roomTypeEl) {
                roomTypeEl.innerHTML = `<strong>Room Type:</strong> Room ${booking.room_id}`;
                console.log('✅ Updated room type');
            } else {
                console.error('❌ Room type element not found');
            }
            
            if (datesEl) {
                datesEl.innerHTML = `<strong>Dates:</strong> ${booking.check_in_date} to ${booking.check_out_date}`;
                console.log('✅ Updated dates');
            }
            
            if (guestsEl) {
                guestsEl.innerHTML = `<strong>Guests:</strong> ${booking.guests}`;
                console.log('✅ Updated guests');
            }
            
            if (totalEl) {
                totalEl.innerHTML = `<strong>Total Amount:</strong> ₹${parseFloat(booking.total_amount).toFixed(2)}`;
                console.log('✅ Updated total');
            }
            
            // Display booking ID
            const bookingIdEl = document.getElementById('bookingIdDisplay');
            if (bookingIdEl) {
                bookingIdEl.textContent = bookingId;
                console.log('✅ Updated booking ID display');
            }
            
            // Remove any error messages
            const alerts = document.querySelectorAll('.alert');
            alerts.forEach(alert => alert.remove());
            
            console.log('✅ Payment page loaded successfully');
            
        } else {
            console.error('❌ Invalid response:', data);
            showAlert(data.message || 'Failed to load booking details', 'error');
            setTimeout(() => window.location.href = 'dashboard.html', 2000);
        }
    } catch (error) {
        console.error('❌ Error loading booking:', error);
        showAlert('Network error. Please try again.', 'error');
    }
}

async function processPayment() {
    const urlParams = new URLSearchParams(window.location.search);
    const bookingId = urlParams.get('booking_id');
    const paymentMethod = document.getElementById('paymentMethod')?.value;

    if (!bookingId || !paymentMethod) {
        showAlert('Please select a payment method', 'error');
        return;
    }

    console.log('💳 Processing payment:', { bookingId, paymentMethod });

    try {
        showSpinner('payBtn', true);

        // First, get booking details to get the amount
        const bookingResponse = await fetch(`${API_BASE}/bookings/${bookingId}`, {
            headers: { 'Authorization': `Bearer ${currentToken}` }
        });
        const bookingData = await bookingResponse.json();
        
        if (!bookingResponse.ok) {
            throw new Error('Failed to fetch booking details');
        }

        const amount = bookingData.booking.total_amount;
        console.log('💰 Payment amount:', amount);

        // Process payment - FIXED ENDPOINT
        const response = await fetch(`${API_BASE}/payments/process`, {  // ✅ Changed from /pay to /process
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentToken}`
            },
            body: JSON.stringify({
                booking_id: parseInt(bookingId),
                payment_method: paymentMethod,
                amount: amount
            })
        });

        const data = await response.json();
        console.log('💳 Payment response:', data);

        if (response.ok) {
            showAlert('Payment successful! Redirecting to dashboard...', 'success');
            setTimeout(() => window.location.href = 'dashboard.html', 2000);
        } else {
            showAlert(data.message || 'Payment failed', 'error');
        }
    } catch (error) {
        console.error('❌ Payment error:', error);
        showAlert('Network error. Please try again.', 'error');
    } finally {
        showSpinner('payBtn', false);
    }
}
// ============================================
// DASHBOARD
// ============================================
async function loadUserBookings() {
    if (!currentUser || !currentToken) {
        showAlert('Please login to view bookings', 'error');
        setTimeout(() => window.location.href = 'login.html', 1500);
        return;
    }

    console.log('📊 Loading user bookings');

    try {
        const response = await fetch(`${API_BASE}/bookings/my-bookings?filter=all`, {
            headers: { 'Authorization': `Bearer ${currentToken}` }
        });

        const data = await response.json();
        console.log('Bookings response:', data);

        if (response.ok) {
            displayUserBookings(data.bookings || []);
        } else {
            showAlert('Failed to load bookings', 'error');
        }
    } catch (error) {
        console.error('❌ Error loading bookings:', error);
        showAlert('Network error', 'error');
    }
}

function displayUserBookings(bookings) {
    const container = document.getElementById('bookingsTable');
    if (!container) return;

    console.log('📋 Displaying', bookings.length, 'bookings');

    if (bookings.length === 0) {
        container.innerHTML = '<tr><td colspan="6" style="text-align:center; padding: 2rem; color: #666;">No bookings found. Start by searching for rooms!</td></tr>';
        return;
    }

    container.innerHTML = bookings.map(b => `
        <tr>
            <td>#${b.booking_id}</td>
            <td>Room ${b.room_id}</td>
            <td>${b.check_in_date}</td>
            <td>${b.check_out_date}</td>
            <td>₹${parseFloat(b.total_amount).toFixed(2)}</td>
            <td><span class="badge badge-${getBadgeClass(b.status)}">${b.status.toUpperCase()}</span></td>
        </tr>
    `).join('');
}

function getBadgeClass(status) {
    const classes = {
        'pending': 'warning',
        'confirmed': 'success',
        'cancelled': 'danger',
        'completed': 'info'
    };
    return classes[status?.toLowerCase()] || 'info';
}

// ============================================
// ADMIN DASHBOARD
// ============================================
async function loadAdminDashboard() {
    if (!currentUser || currentUser.role !== 'admin') {
        showAlert('Admin access required', 'error');
        setTimeout(() => window.location.href = 'index.html', 1500);
        return;
    }

    console.log('🔐 Loading admin dashboard (simplified)');
    loadAdminBookings();
    loadAdminRooms();
}

async function loadAdminBookings() {
    const table = document.getElementById('adminBookingsTable');
    if (!table) return;

    const status = document.getElementById('adminBookingStatus')?.value || '';
    const url = `${API_BASE}/admin/bookings${status ? `?status=${status}` : ''}`;

    try {
        const response = await fetch(url, {
            headers: { 'Authorization': `Bearer ${currentToken}` }
        });
        const data = await response.json();
        const bookings = data.bookings || [];

        table.innerHTML = bookings.length ? bookings.map(b => `
            <tr>
                <td>#${b.booking_id}</td>
                <td>User ID: ${b.user_id}</td>
                <td>Room ${b.room_id}</td>
                <td>${b.check_in_date} to ${b.check_out_date}</td>
                <td>₹${Number(b.total_amount || 0).toFixed(2)}</td>
                <td><span class="badge badge-${getBadgeClass(b.status)}">${b.status}</span></td>
                <td class="table-actions">
                    <button class="btn btn-success" onclick="updateAdminBookingStatus(${b.booking_id}, 'confirmed')">Confirm</button>
                    <button class="btn btn-accent" onclick="updateAdminBookingStatus(${b.booking_id}, 'checked_in')">Check In</button>
                    <button class="btn btn-accent" onclick="updateAdminBookingStatus(${b.booking_id}, 'checked_out')">Check Out</button>
                    <button class="btn btn-danger" onclick="updateAdminBookingStatus(${b.booking_id}, 'cancelled')">Cancel</button>
                </td>
            </tr>
        `).join('') : '<tr><td colspan="7">No bookings found.</td></tr>';
    } catch (error) {
        console.error('Admin bookings error:', error);
        table.innerHTML = '<tr><td colspan="7">Failed to load bookings.</td></tr>';
    }
}

async function updateAdminBookingStatus(bookingId, status) {
    try {
        const response = await fetch(`${API_BASE}/admin/bookings/${bookingId}/status`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentToken}`
            },
            body: JSON.stringify({ status })
        });
        const data = await response.json();

        if (response.ok) {
            showAlert('Booking status updated', 'success');
            loadAdminDashboard();
        } else {
            showAlert(data.message || 'Unable to update booking', 'error');
        }
    } catch (error) {
        console.error('Admin status error:', error);
        showAlert('Network error while updating booking', 'error');
    }
}

async function loadAdminRooms() {
    const table = document.getElementById('adminRoomsTable');
    if (!table) return;

    try {
        const response = await fetch(`${API_BASE}/admin/rooms`, {
            headers: { 'Authorization': `Bearer ${currentToken}` }
        });
        const data = await response.json();
        const rooms = data.rooms || [];

        table.innerHTML = rooms.length ? rooms.map(room => `
            <tr>
                <td>${room.room_number}</td>
                <td>${room.category?.name || '-'}</td>
                <td>${room.floor}</td>
                <td>${room.status}</td>
                <td>₹${Number(room.category?.base_price || 0).toFixed(2)}</td>
                <td class="table-actions">
                    <button class="btn btn-accent" onclick="editAdminRoom(${room.room_id}, '${room.status}', ${Number(room.category?.base_price || 0)})">Edit</button>
                </td>
            </tr>
        `).join('') : '<tr><td colspan="6">No rooms found.</td></tr>';
    } catch (error) {
        console.error('Admin rooms error:', error);
        table.innerHTML = '<tr><td colspan="6">Failed to load rooms.</td></tr>';
    }
}

async function addAdminRoom() {
    const payload = {
        room_number: document.getElementById('newRoomNumber').value.trim(),
        category_id: parseInt(document.getElementById('newRoomCategory').value),
        floor: parseInt(document.getElementById('newRoomFloor').value)
    };

    try {
        const response = await fetch(`${API_BASE}/admin/rooms`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentToken}`
            },
            body: JSON.stringify(payload)
        });
        const data = await response.json();

        if (response.ok) {
            showAlert('Room added successfully', 'success');
            document.getElementById('newRoomNumber').value = '';
            document.getElementById('newRoomCategory').value = '';
            document.getElementById('newRoomFloor').value = '';
            loadAdminRooms();
        } else {
            showAlert(data.message || 'Unable to add room', 'error');
        }
    } catch (error) {
        console.error('Add room error:', error);
        showAlert('Network error while adding room', 'error');
    }
}

async function editAdminRoom(roomId, currentStatus, currentPrice) {
    const status = prompt('Room status: available, occupied, maintenance, reserved', currentStatus) || currentStatus;
    const price = prompt('Price per night for this room category', currentPrice) || currentPrice;

    try {
        const response = await fetch(`${API_BASE}/admin/rooms/${roomId}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentToken}`
            },
            body: JSON.stringify({ status, base_price: Number(price) })
        });
        const data = await response.json();

        if (response.ok) {
            showAlert('Room updated successfully', 'success');
            loadAdminRooms();
        } else {
            showAlert(data.message || 'Unable to update room', 'error');
        }
    } catch (error) {
        console.error('Edit room error:', error);
        showAlert('Network error while updating room', 'error');
    }
}

// ============================================
// RECOMMENDATIONS
// ============================================
async function loadRecommendationsPreview() {
    try {
        console.log('🌟 Loading recommendations preview');
        const response = await fetch(`${API_BASE}/recommendations`);
        const data = await response.json();

        if (response.ok) {
            const recommendations = data.recommendations.slice(0, 4); // Show first 4
            displayRecommendations(recommendations, 'recommendationsGrid');
        }
    } catch (error) {
        console.error('❌ Error loading recommendations:', error);
    }
}

async function loadAllRecommendations() {
    try {
        console.log('🗺️ Loading all recommendations');
        const response = await fetch(`${API_BASE}/recommendations`);
        const data = await response.json();

        if (response.ok) {
            displayRecommendations(data.recommendations, 'recommendationsGrid');
        }
    } catch (error) {
        console.error('❌ Error loading recommendations:', error);
    }
}

function displayRecommendations(recommendations, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = recommendations.map(rec => {
        const desc = rec.description || "No description available";
        const mapsUrl = rec.google_maps_url || "#";

        return `
            <div class="rec-card">
                <div class="rec-thumbnail" style="background-image: url('${rec.image_url || '/static/images/nearby/default.jpg'}')"></div>
                <div class="rec-info">
                    <h3>${rec.title}</h3>
                    <p>${desc}</p>
                    <a href="${mapsUrl}" target="_blank" class="maps-link">📍 View on Google Maps</a>
                </div>
            </div>
        `;
    }).join('');
}

// ============================================
// STAY PACKAGES BOOKING
// ============================================
let currentPackageName = '';
let currentPackageDesc = '';
let roomCategoriesCached = [];

async function openPackageModal(packageName, packageDesc) {
    currentPackageName = packageName;
    currentPackageDesc = packageDesc;
    
    document.getElementById('modalPackageTitle').textContent = packageName;
    document.getElementById('modalPackageDesc').textContent = packageDesc;
    document.getElementById('modalPackageName').value = packageName;
    
    // Reset inputs
    document.getElementById('packageCheckIn').value = '';
    document.getElementById('packageCheckOut').value = '';
    document.getElementById('packageSpecialRequests').value = '';
    document.getElementById('modalTotalAmount').textContent = '₹0';
    document.getElementById('modalDiscountNote').style.display = 'none';
    
    // Show/hide category selection
    const categoryGroup = document.getElementById('modalCategoryGroup');
    const guestGroup = document.getElementById('guestCountGroup');
    const rateEl = document.getElementById('modalRatePerNight');
    
    try {
        if (roomCategoriesCached.length === 0) {
            const resp = await fetch(`${API_BASE}/bookings/categories`);
            const data = await resp.json();
            roomCategoriesCached = data.categories || [];
        }
        
        const catSelect = document.getElementById('modalRoomCategory');
        catSelect.innerHTML = '';
        
        if (packageName === 'Weekend Discount' || packageName === 'Long-Stay Discount') {
            categoryGroup.style.display = 'block';
            guestGroup.style.display = 'block';
            
            // Filter categories based on package rules
            let allowedCats = roomCategoriesCached;
            if (packageName === 'Weekend Discount') {
                allowedCats = roomCategoriesCached.filter(c => c.category_id === 1 || c.category_id === 2);
            }
            
            catSelect.innerHTML = allowedCats.map(c => `
                <option value="${c.category_id}" data-price="${c.base_price}" data-capacity="${c.capacity}">
                    ${c.name} - ₹${c.base_price}/night (Max ${c.capacity} guests)
                </option>
            `).join('');
            
            rateEl.textContent = `₹${parseFloat(allowedCats[0]?.base_price || 0).toFixed(2)}`;
        } else {
            categoryGroup.style.display = 'none';
            if (packageName === 'Honeymoon Package') {
                guestGroup.style.display = 'none'; // Lock to 2 guests
                document.getElementById('packageGuests').value = 2;
                const suite = roomCategoriesCached.find(c => c.category_id === 6);
                rateEl.textContent = `₹${parseFloat(suite?.base_price || 5000).toFixed(2)}`;
            } else if (packageName === 'Corporate Package') {
                guestGroup.style.display = 'none'; // Lock to 1 guest
                document.getElementById('packageGuests').value = 1;
                const exec = roomCategoriesCached.find(c => c.category_id === 4);
                rateEl.textContent = `₹${parseFloat(exec?.base_price || 2800).toFixed(2)}`;
            }
        }
        
        // Check authentication status
        const confirmBtn = document.getElementById('confirmPackageBookingBtn');
        const authAlert = document.getElementById('modalAuthAlert');
        
        if (!currentUser || !currentToken) {
            confirmBtn.style.display = 'none';
            authAlert.style.display = 'block';
        } else {
            confirmBtn.style.display = 'block';
            authAlert.style.display = 'none';
        }
        
        document.getElementById('packageBookingModal').style.display = 'block';
        
    } catch (e) {
        console.error('Error loading package categories:', e);
        showAlert('Error loading package details', 'error');
    }
}

function closePackageModal() {
    document.getElementById('packageBookingModal').style.display = 'none';
}

function calculatePackageTotal() {
    const checkInStr = document.getElementById('packageCheckIn').value;
    const checkOutStr = document.getElementById('packageCheckOut').value;
    const totalAmountEl = document.getElementById('modalTotalAmount');
    const rateEl = document.getElementById('modalRatePerNight');
    const discountEl = document.getElementById('modalDiscountNote');
    
    if (!checkInStr || !checkOutStr) {
        totalAmountEl.textContent = '₹0';
        discountEl.style.display = 'none';
        return;
    }
    
    const checkIn = new Date(checkInStr);
    const checkOut = new Date(checkOutStr);
    const diffTime = checkOut - checkIn;
    const nights = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (nights <= 0) {
        totalAmountEl.textContent = 'Invalid Dates';
        discountEl.style.display = 'none';
        return;
    }
    
    let basePricePerNight = 0;
    let finalPrice = 0;
    let discountApplied = false;
    
    if (currentPackageName === 'Weekend Discount' || currentPackageName === 'Long-Stay Discount') {
        const selectEl = document.getElementById('modalRoomCategory');
        const option = selectEl.options[selectEl.selectedIndex];
        if (option) {
            basePricePerNight = parseFloat(option.dataset.price);
        }
        
        if (currentPackageName === 'Weekend Discount') {
            basePricePerNight = basePricePerNight * 0.85; // 15% discount
            discountApplied = true;
        } else if (currentPackageName === 'Long-Stay Discount' && nights >= 7) {
            basePricePerNight = basePricePerNight * 0.80; // 20% discount
            discountApplied = true;
        }
    } else if (currentPackageName === 'Honeymoon Package') {
        const suite = roomCategoriesCached.find(c => c.category_id === 6);
        basePricePerNight = suite ? parseFloat(suite.base_price) : 5000;
    } else if (currentPackageName === 'Corporate Package') {
        const exec = roomCategoriesCached.find(c => c.category_id === 4);
        basePricePerNight = exec ? parseFloat(exec.base_price) : 2800;
    }
    
    rateEl.textContent = `₹${basePricePerNight.toFixed(2)}`;
    finalPrice = basePricePerNight * nights;
    totalAmountEl.textContent = `₹${finalPrice.toFixed(2)}`;
    
    if (discountApplied) {
        discountEl.style.display = 'block';
    } else {
        discountEl.style.display = 'none';
    }
}

async function submitPackageBooking() {
    if (!currentUser || !currentToken) {
        showAlert('Please sign in to complete booking', 'error');
        redirectToLogin();
        return;
    }
    
    const checkIn = document.getElementById('packageCheckIn').value;
    const checkOut = document.getElementById('packageCheckOut').value;
    const guests = parseInt(document.getElementById('packageGuests').value || 2);
    const requests = document.getElementById('packageSpecialRequests').value || '';
    
    if (!checkIn || !checkOut) {
        showAlert('Please choose check-in and check-out dates', 'error');
        return;
    }
    
    const checkInDate = new Date(checkIn);
    const checkOutDate = new Date(checkOut);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    if (checkInDate < today) {
        showAlert('Check-in date cannot be in the past', 'error');
        return;
    }
    
    if (checkOutDate <= checkInDate) {
        showAlert('Check-out must be after check-in', 'error');
        return;
    }
    
    let categoryId = 0;
    if (currentPackageName === 'Weekend Discount' || currentPackageName === 'Long-Stay Discount') {
        categoryId = parseInt(document.getElementById('modalRoomCategory').value);
    } else if (currentPackageName === 'Honeymoon Package') {
        categoryId = 6;
    } else if (currentPackageName === 'Corporate Package') {
        categoryId = 4;
    }
    
    try {
        showSpinner('confirmPackageBookingBtn', true);
        
        const payload = {
            category_id: categoryId,
            check_in_date: checkIn,
            check_out_date: checkOut,
            guests: guests,
            special_requests: `[Package: ${currentPackageName}] ${requests}`.trim(),
            package_name: currentPackageName
        };
        
        console.log('Sending package booking payload:', payload);
        
        const response = await fetch(`${API_BASE}/bookings`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentToken}`
            },
            body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        console.log('Package booking response:', data);
        
        if (response.ok) {
            showAlert('Package booking successful! Redirecting to payment...', 'success');
            closePackageModal();
            setTimeout(() => {
                window.location.href = `payment.html?booking_id=${data.booking_id}`;
            }, 1500);
        } else {
            showAlert(data.message || 'Package booking failed', 'error');
        }
    } catch (e) {
        console.error('Error during package booking:', e);
        showAlert('Network error. Please try again.', 'error');
    } finally {
        showSpinner('confirmPackageBookingBtn', false);
    }
}

function redirectToLogin() {
    window.location.href = `login.html?redirect=offers.html`;
}

// ============================================
// UTILITIES
// ============================================
function showAlert(message, type = 'info') {
    console.log(`🔔 Alert [${type}]:`, message);
    
    const container = document.getElementById('alertContainer') || createAlertContainer();
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    
    const icon = {
        'success': '✅',
        'error': '❌',
        'info': 'ℹ️',
        'warning': '⚠️'
    }[type] || 'ℹ️';
    
    alert.innerHTML = `${icon} ${message}`;
    container.appendChild(alert);
    
    setTimeout(() => alert.remove(), 5000);
}

function createAlertContainer() {
    const div = document.createElement('div');
    div.id = 'alertContainer';
    document.body.appendChild(div);
    return div;
}

function showSpinner(btnId, show) {
    const btn = document.getElementById(btnId);
    if (!btn) return;
    
    if (show) {
        btn.dataset.originalText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span> Processing...';
    } else {
        btn.disabled = false;
        btn.innerHTML = btn.dataset.originalText || 'Submit';
    }
}

// ============================================
// EXPOSE FUNCTIONS GLOBALLY FOR onclick
// ============================================
window.register = register;
window.login = login;
window.logout = logout;
window.searchRooms = searchRooms;
window.bookRoom = bookRoom;
window.processPayment = processPayment;
window.selectRoomForBooking = selectRoomForBooking;
window.cancelBooking = cancelBooking;
window.downloadInvoice = downloadInvoice;
window.downloadInvoiceFromConfirmation = downloadInvoiceFromConfirmation;
window.openPackageModal = openPackageModal;
window.closePackageModal = closePackageModal;
window.calculatePackageTotal = calculatePackageTotal;
window.submitPackageBooking = submitPackageBooking;
window.redirectToLogin = redirectToLogin;
window.loadAdminBookings = loadAdminBookings;
window.updateAdminBookingStatus = updateAdminBookingStatus;
window.addAdminRoom = addAdminRoom;
window.editAdminRoom = editAdminRoom;

console.log('✅ Script loaded successfully - All functions ready');