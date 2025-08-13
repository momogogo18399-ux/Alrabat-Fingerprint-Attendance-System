    document.addEventListener('DOMContentLoaded', () => {
        const translations = {
            en: {
                'page-title': 'Smart Employee Portal', 'main-title': 'Smart Employee Portal', 'identifier-placeholder': 'Enter Employee Code or Phone',
                'status-today': "Today's Status", 'monthly-attendance': 'Monthly Attendance', 'day': 'Day(s)',
                'no-reason': '-- Select reason (optional) --', 'late-permission': 'Late Permission',
                'morning-mission': 'Morning Mission', 'emergency': 'Emergency', 'check-in-btn': 'Check In',
                'check-out-btn': 'Check Out', 'todays-log-title': "Today's Log",
                'welcome': 'Welcome,', 'status-in': '✅ You are IN', 'status-out': '❌ You are OUT',
                'log-in': 'Check-In', 'log-out': 'Check-Out', 'not-found-name': 'Unknown Employee',
                'not-found-status': 'Please check the Code or Phone Number.', 'server-error': 'Cannot connect to the server.',
                'processing': 'Processing...'
            },
            ar: {
                'page-title': 'بوابة الموظف الذكية', 'main-title': 'بوابة الموظف الذكية', 'identifier-placeholder': 'الكود الوظيفي أو رقم الهاتف',
                'status-today': 'حالة اليوم', 'monthly-attendance': 'حضور الشهر', 'day': 'يوم',
                'no-reason': '-- تحديد سبب التأخير (اختياري) --', 'late-permission': 'إذن تأخير',
                'morning-mission': 'مأمورية صباحية', 'emergency': 'ظرف طارئ', 'check-in-btn': 'تسجيل حضور',
                'check-out-btn': 'تسجيل انصراف', 'todays-log-title': 'سجل اليوم',
                'welcome': 'مرحباً،', 'status-in': '✅ أنت بالداخل', 'status-out': '❌ أنت بالخارج',
                'log-in': 'حضور', 'log-out': 'انصراف', 'not-found-name': 'موظف غير معروف',
                'not-found-status': 'يرجى التأكد من الكود أو رقم الهاتف.', 'server-error': 'لا يمكن الاتصال بالخادم.',
                'processing': 'جاري المعالجة...'
            }
        };

        const identifierInput = document.getElementById('identifier-input');
        const dashboard = document.getElementById('dashboard');
        const checkInButton = document.getElementById('check-in-btn');
        const checkOutButton = document.getElementById('check-out-btn');
        const welcomeMessage = document.getElementById('welcome-message');
        const jobTitleDisplay = document.getElementById('job-title-display');
        const currentStatus = document.getElementById('current-status');
        const monthlyAttendanceStat = document.getElementById('monthly-attendance-stat');
        const lateReasonGroup = document.getElementById('late-reason-group');
        const lateReasonSelect = document.getElementById('late-reason');
        const todaysLog = document.getElementById('todays-log');
        const todaysLogList = document.getElementById('todays-log-list');
        const messageDiv = document.getElementById('message');
        const clockDiv = document.getElementById('clock');
        const themeSwitcher = document.getElementById('theme-switcher');
        const langSwitcher = document.getElementById('lang-switcher');
        let messageTimer;
        const DEVICE_TOKEN_KEY = 'attendance_device_token';

        let currentLang = localStorage.getItem('language') || 'ar';
        let currentTheme = localStorage.getItem('theme') || 'light';

        const setLanguage = (lang) => {
            currentLang = lang; localStorage.setItem('language', lang);
            document.documentElement.lang = lang; document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
            document.querySelectorAll('[data-key], title').forEach(el => {
                const key = el.getAttribute('data-key') || 'page-title';
                if (translations[lang][key]) { el.textContent = translations[lang][key]; }
            });
            document.querySelectorAll('[data-key-placeholder]').forEach(el => {
                const key = el.getAttribute('data-key-placeholder');
                 if (translations[lang][key]) { el.placeholder = translations[lang][key]; }
            });
            langSwitcher.querySelector('.active')?.classList.remove('active');
            langSwitcher.querySelector(`[data-lang="${lang}"]`).classList.add('active');
            fetchEmployeeStatus();
        };

        const setTheme = (theme) => {
            currentTheme = theme; localStorage.setItem('theme', theme);
            document.documentElement.setAttribute('data-theme', theme);
            themeSwitcher.querySelector('.active')?.classList.remove('active');
            themeSwitcher.querySelector(`[data-theme="${theme}"]`).classList.add('active');
        };

        themeSwitcher.addEventListener('click', (e) => { if (e.target.dataset.theme) setTheme(e.target.dataset.theme); });
        langSwitcher.addEventListener('click', (e) => { if (e.target.dataset.lang) setLanguage(e.target.dataset.lang); });
        
        setTheme(currentTheme); setLanguage(currentLang);

        identifierInput.addEventListener('input', debounce(fetchEmployeeStatus, 500));
        checkInButton.addEventListener('click', () => recordAttendance('Check-In'));
        checkOutButton.addEventListener('click', () => recordAttendance('Check-Out'));

        updateClock(); getOrGenerateDeviceToken(); setInterval(updateClock, 1000);

        function updateClock() {
            const now = new Date();
            const timeString = now.toLocaleTimeString('en-US', { hour12: true, hour: '2-digit', minute: '2-digit', second: '2-digit'});
            const dateString = now.toLocaleDateString(currentLang === 'ar' ? 'ar-EG' : 'en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'});
            clockDiv.innerHTML = `${dateString} | ${timeString}`;
        }

        async function fetchEmployeeStatus() {
            clearMessage();
            const identifier = identifierInput.value.trim();
            if (identifier.length < 4) { updateDashboard(null, 'initial'); return; }
            try {
                const response = await fetch(`/api/employee-status?identifier=${identifier}`);
                if (!response.ok) throw new Error();
                const result = await response.json();
                updateDashboard(result, result.status);
            } catch (error) { console.error("Error fetching status:", error); updateDashboard(null, 'error'); }
        }
        
        async function recordAttendance(type) {
            showMessage(translations[currentLang]['processing'], 'info');
            const identifier = identifierInput.value.trim(); let success = false;
            try {
                const notes = lateReasonSelect.value;
                const deviceToken = getOrGenerateDeviceToken();
                const location = await getLocation();
                const fingerprint = await getCanvasFingerprint();
                const payload = { identifier, fingerprint, location, type, notes, token: deviceToken };
                const response = await fetch('/api/check-in', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
                const result = await response.json();
                showMessage(result.message, response.ok ? 'success' : 'error');
                if (response.ok) { success = true; }
            } catch (error) { showMessage(error.message || 'حدث خطأ فني.', 'error'); }
            finally { if (success) { await fetchEmployeeStatus(); } }
        }

        function updateDashboard(data, state) {
            dashboard.classList.remove('visible'); todaysLog.classList.add('hidden');
            checkInButton.classList.remove('visible'); checkOutButton.classList.remove('visible');
            lateReasonGroup.classList.add('hidden');
            switch (state) {
                case 'found':
                    dashboard.classList.add('visible');
                    welcomeMessage.textContent = `${translations[currentLang]['welcome']} ${data.employee_name}`;
                    jobTitleDisplay.textContent = data.job_title || '';
                    monthlyAttendanceStat.textContent = data.stats.monthly_attendance;
                    const lastCheckIn = data.todays_log.filter(log => log.type === 'Check-In').pop();
                    const lastCheckOut = data.todays_log.filter(log => log.type === 'Check-Out').pop();
                    if (lastCheckIn && (!lastCheckOut || new Date(`1970-01-01T${lastCheckOut.check_time}`) < new Date(`1970-01-01T${lastCheckIn.check_time}`))) {
                        currentStatus.innerHTML = translations[currentLang]['status-in'];
                    } else { currentStatus.innerHTML = translations[currentLang]['status-out']; }
                    if (data.next_action === 'Check-In') { checkInButton.classList.add('visible'); if (data.is_late) { lateReasonGroup.classList.remove('hidden'); } }
                    else if (data.next_action === 'Check-Out') { checkOutButton.classList.add('visible'); }
                    if (data.todays_log && data.todays_log.length > 0) {
                        todaysLog.classList.remove('hidden');
                        todaysLogList.innerHTML = '';
                        data.todays_log.sort((a, b) => b.id - a.id).forEach(log => {
                            const li = document.createElement('li');
                            const typeText = translations[currentLang][log.type === 'Check-In' ? 'log-in' : 'log-out'];
                            li.innerHTML = `<div class="log-type">${log.type === 'Check-In' ? '✅' : '❌'} ${typeText}</div><div class="log-time">${log.check_time}</div>`;
                            todaysLogList.appendChild(li);
                        });
                    }
                    break;
                case 'not_found':
                    dashboard.classList.add('visible');
                    welcomeMessage.textContent = translations[currentLang]['not-found-name'];
                    currentStatus.textContent = translations[currentLang]['not-found-status'];
                    jobTitleDisplay.textContent = ''; monthlyAttendanceStat.textContent = '0';
                    break;
                case 'error': showMessage(translations[currentLang]['server-error'], 'error'); break;
                case 'initial': default: break;
            }
        }
        function showMessage(msg, type) { clearTimeout(messageTimer); messageDiv.textContent = msg; messageDiv.className = `msg-${type} visible`; messageTimer = setTimeout(clearMessage, 5000); }
        function clearMessage() { messageDiv.classList.remove('visible'); }
        function getLocation() { return new Promise((resolve, reject) => { if (!navigator.geolocation) return reject(new Error("Geolocation not supported.")); navigator.geolocation.getCurrentPosition(pos => resolve({ lat: pos.coords.latitude, lon: pos.coords.longitude }), () => reject(new Error("Failed to get location.")), { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }); }); }
        function getCanvasFingerprint() { return new Promise((resolve) => { const canvas = document.createElement('canvas'); const ctx = canvas.getContext('2d'); const txt = 'abcdefghijklmnopqrstuvwxyz0123456789'; ctx.textBaseline = "top"; ctx.font = "14px 'Arial'"; ctx.textBaseline = "alphabetic"; ctx.fillStyle = "#f60"; ctx.fillRect(125, 1, 62, 20); ctx.fillStyle = "#069"; ctx.fillText(txt, 2, 15); ctx.fillStyle = "rgba(102, 204, 0, 0.7)"; ctx.fillText(txt, 4, 17); const dataUrl = canvas.toDataURL(); let hash = 0; for (let i = 0; i < dataUrl.length; i++) { const char = dataUrl.charCodeAt(i); hash = ((hash << 5) - hash) + char; hash = hash & hash; } resolve(hash.toString()); }); }
        function generateUUID() { return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c => (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)); }
        function getOrGenerateDeviceToken() { let token = localStorage.getItem(DEVICE_TOKEN_KEY); if (!token) { token = generateUUID(); localStorage.setItem(DEVICE_TOKEN_KEY, token); } return token; }
        function debounce(func, delay) { let timeout; return function(...args) { clearTimeout(timeout); timeout = setTimeout(() => func.apply(this, args), delay); }; }
    
    });