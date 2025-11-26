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


    if (window.location.pathname.includes('payment.html')) {
        console.log('💳 Payment page detected');
        loadPaymentDetails();
    }

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
                window.location.href = "dashboard.html";
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

function displaySearchResults(results) {
    const container = document.getElementById('roomsGrid');
    
    if (!container) {
        console.error('❌ roomsGrid container not found');
        return;
    }

    console.log('🎨 Displaying', results.length, 'results');

    if (results.length === 0) {
        container.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 4rem;">
                <h3 style="color: #666; margin-bottom: 1rem;">No rooms available</h3>
                <p style="color: #999;">Try different dates or fewer guests</p>
            </div>
        `;
        return;
    }

    container.innerHTML = results.map(cat => `
        <div class="room-card">
            <div class="room-image" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                ${cat.name}
            </div>
            <div class="room-info">
                <h3>${cat.name}</h3>
                <p style="color: #666; margin-bottom: 1rem;">${cat.description || 'Luxurious and comfortable stay'}</p>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-bottom: 1rem;">
                    <p><strong>📍 Available:</strong> ${cat.available_count}</p>
                    <p><strong>👥 Capacity:</strong> ${cat.capacity}</p>
                    <p><strong>🌙 Nights:</strong> ${cat.nights}</p>
                    <p><strong>💰 Per Night:</strong> ₹${cat.base_price.toFixed(2)}</p>
                </div>
                
                <p style="font-size: 1.3rem; font-weight: bold; color: #c9a96e; margin-bottom: 1rem;">
                    Total: ₹${cat.total_price.toFixed(2)}
                </p>
                
                <p style="font-size: 0.9rem; color: #666; margin-bottom: 1rem;">
                    <strong>✨ Amenities:</strong><br>
                    ${cat.amenities.join(' • ')}
                </p>
                
                ${currentUser 
                    ? `<button class="btn btn-primary full-width" onclick="selectRoomForBooking('${cat.category_id}', '${cat.name}', ${cat.total_price}, document.getElementById('checkIn').value, document.getElementById('checkOut').value)">
                        Book Now - ₹${cat.total_price.toFixed(2)}
                       </button>`
                    : `<button class="btn btn-primary full-width" onclick="showAlert('Please login to book rooms', 'info'); setTimeout(() => window.location.href='login.html', 2000)">
                        Login to Book
                       </button>`
                }
            </div>
        </div>
    `).join('');
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

    container.innerHTML = categories.map(cat => `
        <div class="room-card">
            <div class="room-image" style="background: linear-gradient(135deg, #b8955a 0%, #c9a96e 100%);">
                ${cat.name}
            </div>
            <div class="room-info">
                <h3>${cat.name}</h3>
                <p style="color: #666;">${cat.description}</p>
                <p><strong>👥 Capacity:</strong> ${cat.capacity} guests</p>
                <p><strong>💰 Price:</strong> ₹${cat.base_price}/night</p>
                <p style="font-size: 0.9rem; color: #666;">
                    <strong>✨ Amenities:</strong><br>
                    ${cat.amenities.join(' • ')}
                </p>
                <button class="btn btn-primary full-width" onclick="showAlert('Please use the search widget above to check availability', 'info'); window.scrollTo({top: 0, behavior: 'smooth'})">
                    Check Availability
                </button>
            </div>
        </div>
    `).join('');
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

    console.log('🔐 Loading admin dashboard');

    try {
        const response = await fetch(`${API_BASE}/admin/dashboard`, {
            headers: { 'Authorization': `Bearer ${currentToken}` }
        });

        const data = await response.json();
        console.log('ADMIN DASHBOARD', data);

        if (response.ok) {
            displayAdminStats(data);
        } else {
            showAlert("Failed to load admin analytics", "error");
        }
    } catch (error) {
        console.error("Dashboard error:", error);
        showAlert("Network error", "error");
    }
}

// function displayAdminStats(data) {
//     // const totalBookings = document.getElementById('totalBookings');
//     // const totalRevenue = document.getElementById('totalRevenue');
//     // const activeUsers = document.getElementById('activeUsers');
    
//     // if (totalBookings) totalBookings.textContent = data.total_bookings || 0;
//     // if (totalRevenue) totalRevenue.textContent = `₹${parseFloat(data.total_revenue || 0).toFixed(2)}`;
//     // if (activeUsers) activeUsers.textContent = data.total_users || 0;
//     document.getElementById('totalBookings').textContent =
//         data.revenue.total_bookings || 0;

//     document.getElementById('totalRevenue').textContent =
//         "₹" + parseFloat(data.revenue.total_revenue || 0).toFixed(2);

//     document.getElementById('totalUsers').textContent =
//         data.customers.total_customers || 0;

// }

function displayAdminStats(data) {
    // Revenue Stats
    document.getElementById('totalBookings').textContent =
        data.revenue.total_bookings ?? 0;

    document.getElementById('totalRevenue').textContent =
        "₹" + parseFloat(data.revenue.total_revenue ?? 0).toFixed(2);

    // Customer Stats
    document.getElementById('totalUsers').textContent =
        data.customers.total_customers ?? 0;

    // Occupancy Stats
    document.getElementById('avgOccupancy').textContent =
        parseFloat(data.occupancy.overall_occupancy_rate ?? 0).toFixed(1) + "%";

    document.getElementById('peakOccupancy').textContent =
        parseFloat(data.occupancy.peak_occupancy ?? 0).toFixed(1) + "%";

    // Room Performance
    const roomTable = document.getElementById('roomPerformanceTable');
    if (roomTable) {
        roomTable.innerHTML = data.room_performance.room_performance
            .map(r => `
                <tr>
                    <td>${r.category_name}</td>
                    <td>${r.total_bookings}</td>
                    <td>₹${r.total_revenue.toFixed(2)}</td>
                    <td>${r.total_nights_booked}</td>
                    <td>₹${r.revenue_per_night.toFixed(2)}</td>
                </tr>
            `).join('');
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
            displayRecommendations(data.recommendations, 'allRecommendations');
        }
    } catch (error) {
        console.error('❌ Error loading recommendations:', error);
    }
}

function displayRecommendations(recommendations, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = recommendations.map(rec => {
        const price = rec.price_range ? rec.price_range.toString().replace('_', '-') : "N/A";
        const desc = rec.description || "No description available";
        const category = rec.category ? rec.category.replace('_', ' ').toUpperCase() : "UNKNOWN";

        return `
            <div class="rec-card">
                <span class="rec-category">${category}</span>
                <h3>${rec.title}</h3>
                <p style="color: #666; margin: 1rem 0;">${desc}</p>
                <div class="rec-meta">
                    <p>📍 ${rec.address}</p>
                    <p>⭐ ${rec.rating}/5 | 💰 ${price}</p>
                </div>
            </div>
        `;
    }).join('');
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

console.log('✅ Script loaded successfully - All functions ready');