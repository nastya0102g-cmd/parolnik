/* static/js/script.js */
document.addEventListener('DOMContentLoaded', function(){
    // Acknowledge info
    const ackBtn = document.getElementById('acknowledgeBtn');
    if(ackBtn){
        if(localStorage.getItem('infoViewed') === 'true'){
            ackBtn.textContent='Ознакомлено ✓';
            ackBtn.disabled=true;
            ackBtn.style.background='#00C851';
        }
        ackBtn.addEventListener('click', function(){
            localStorage.setItem('infoViewed','true');
            ackBtn.textContent='Ознакомлено ✓';
            ackBtn.disabled=true;
            ackBtn.style.background='#00C851';
            showNotification('Статус сохранён', 'success');
        });
    }

    // Password check with real-time validation
    const pwdInput = document.getElementById('pwdInput');
    const pwdBtn = document.getElementById('pwdCheckBtn');

    if(pwdInput && pwdBtn){
        // Real-time password strength indicator
        pwdInput.addEventListener('input', function(){
            const password = this.value;
            updatePasswordStrength(password);

            // Enable/disable check button based on input
            pwdBtn.disabled = password.length === 0;
        });

        // Manual check button
        pwdBtn.addEventListener('click', function(){
            const password = pwdInput.value;
            updatePasswordStrength(password);
            showNotification('Пароль проверен', 'info');
        });

        // Enter key support
        pwdInput.addEventListener('keypress', function(e){
            if(e.key === 'Enter' && this.value.length > 0){
                pwdBtn.click();
            }
        });
    }

    // Password strength calculation function
    function updatePasswordStrength(password){
        let score = 0;
        const requirements = {
            length: password.length >= 8,
            upper: /[A-Z]/.test(password),
            lower: /[a-z]/.test(password),
            digit: /[0-9]/.test(password),
            special: /[^A-Za-z0-9]/.test(password)
        };

        // Calculate score
        Object.values(requirements).forEach(req => {
            if(req) score++;
        });

        const pct = Math.round(score/5*100);
        const prog = document.querySelector('.progress');
        const pwdLabel = document.getElementById('pwdLabel');

        if(prog){
            prog.style.width = pct + '%';

            // Update progress bar color and label
            if(score <= 2){
                prog.style.background = 'var(--red)';
                if(pwdLabel) pwdLabel.textContent='Слабый пароль';
                localStorage.setItem('passwordChecked','false');
            } else if(score === 3){
                prog.style.background = '#f1c40f';
                if(pwdLabel) pwdLabel.textContent='Средний пароль';
                localStorage.setItem('passwordChecked','false');
            } else {
                prog.style.background = 'var(--green)';
                if(pwdLabel) pwdLabel.textContent='Надёжный пароль';
                localStorage.setItem('passwordChecked','true');
            }
        }

        // Update requirements display if exists
        updatePasswordRequirements(requirements);
    }

    // Password requirements display
    function updatePasswordRequirements(requirements){
        const reqElements = {
            length: document.getElementById('req-length'),
            upper: document.getElementById('req-upper'),
            lower: document.getElementById('req-lower'),
            digit: document.getElementById('req-digit'),
            special: document.getElementById('req-special')
        };

        for(const [key, element] of Object.entries(reqElements)){
            if(element){
                if(requirements[key]){
                    element.style.color = 'var(--green)';
                    element.innerHTML = '✓ ' + element.textContent.replace(/[✓✗] /, '');
                } else {
                    element.style.color = 'var(--red)';
                    element.innerHTML = '✗ ' + element.textContent.replace(/[✓✗] /, '');
                }
            }
        }
    }

    // Trainer (mini-game): one question at a time, random order
    const quizEl = document.getElementById('quiz-container');
    if(quizEl){
        const pool = [
            {q:'Выберите самый надёжный пароль', opts:['123456','qwerty','M#9k!2zL@7pT'], correct:2},
            {q:'Выберите самый лёгкий пароль', opts:['P@ssw0rd123','admin','S!lverM00n!'], correct:1},
            {q:'Какой пароль самый надёжный?', opts:['1q2w3e','K@9b*L3!nV','password'], correct:1},
            {q:'Выберите ненадёжный пароль', opts:['LetMeIn','H#2rL!xT7z','Dr@gon$5'], correct:0},
            {q:'Выберите надёжный пароль', opts:['Qwerty','123456789','B$7k@L9#tM'], correct:2},
            {q:'Какой пароль слабый?', opts:['G@laxy$4P','sunshine','N0va!xT#3'], correct:1},
            {q:'Выберите надёжный пароль', opts:['Football1','Z@p!rK#7qP','111111'], correct:1},
            {q:'Какой пароль небезопасный?', opts:['AaBbCc','Strong#Pass9!','MyCat123'], correct:0},
            {q:'Выберите сильный пароль', opts:['X#9tR$8v!','welcome','Password1'], correct:0},
            {q:'Выберите слабый пароль', opts:['R@nd0mP@ss','monkey','Star$5Sky'], correct:1}
        ];

        let questions = [...pool].sort(()=>Math.random()-0.5);
        let idx = 0;
        let score = 0;
        const qText = document.getElementById('question');
        const answers = document.getElementById('answers');
        const feedback = document.getElementById('feedback');
        const nextBtn = document.getElementById('nextBtn');
        const resultEl = document.getElementById('result');

        function showQuestion(){
            if(idx >= questions.length){
                // Game completed
                resultEl.textContent = 'Итог: ' + score + ' / ' + questions.length;
                resultEl.style.fontWeight = 'bold';
                resultEl.style.fontSize = '1.2em';

                if(score >= 8){
                    resultEl.style.color = 'var(--green)';
                    resultEl.innerHTML += ' 🎉 Отлично!';
                } else if(score >= 5){
                    resultEl.style.color = '#f1c40f';
                    resultEl.innerHTML += ' 👍 Хорошо';
                } else {
                    resultEl.style.color = 'var(--red)';
                    resultEl.innerHTML += ' 😔 Попробуйте ещё раз';
                }

                localStorage.setItem('trainerPassed', score >= 8 ? 'true' : 'false');
                localStorage.setItem('trainerScore', score);
                answers.innerHTML='';
                qText.textContent='Тренажёр завершён';
                nextBtn.style.display='none';
                return;
            }

            const cur = questions[idx];
            qText.textContent = (idx+1) + '. ' + cur.q;
            answers.innerHTML='';
            feedback.textContent='';
            feedback.style.color='';
            nextBtn.style.display='none';

            cur.opts.forEach((opt,i)=>{
                const b = document.createElement('button');
                b.className='btn secondary';
                b.textContent = opt;
                b.style.margin = '5px';
                b.style.width = '100%';
                b.style.textAlign = 'left';
                b.style.padding = '10px';

                b.addEventListener('click', ()=>{
                    const isCorrect = i === cur.correct;

                    if(isCorrect){
                        feedback.textContent='Верно! ✅';
                        feedback.style.color='var(--green)';
                        b.style.background = 'var(--green)';
                        b.style.color = 'white';
                        score++;
                    } else {
                        feedback.textContent='Неверно! ❌';
                        feedback.style.color='var(--red)';
                        b.style.background = 'var(--red)';
                        b.style.color = 'white';

                        // Highlight correct answer
                        const correctBtn = answers.children[cur.correct];
                        correctBtn.style.background = 'var(--green)';
                        correctBtn.style.color = 'white';
                    }

                    Array.from(answers.querySelectorAll('button')).forEach(x=>{
                        x.disabled=true;
                        x.style.cursor='not-allowed';
                    });

                    nextBtn.style.display='block';
                });
                answers.appendChild(b);
            });
        }

        nextBtn.addEventListener('click', ()=>{
            idx++;
            showQuestion();
        });

        showQuestion();
    }

    // Profile statuses with enhanced display
    function updateProfileStatuses(){
        const ackStatus = document.getElementById('ackStatus');
        if(ackStatus){
            const v = localStorage.getItem('infoViewed') === 'true';
            ackStatus.textContent = v ? '✅ Завершено' : '❌ Не завершено';
            ackStatus.style.fontWeight = v ? 'bold' : 'normal';
        }

        const trainerStatus = document.getElementById('trainerStatus');
        if(trainerStatus){
            const t = localStorage.getItem('trainerPassed') === 'true';
            const score = localStorage.getItem('trainerScore') || '0';
            trainerStatus.textContent = t ? `✅ Завершено (${score}/10)` : '❌ Не завершено';
            trainerStatus.style.fontWeight = t ? 'bold' : 'normal';
        }

        const pwdStatus = document.getElementById('pwdStatus');
        if(pwdStatus){
            const p = localStorage.getItem('passwordChecked') === 'true';
            pwdStatus.textContent = p ? '✅ Завершено' : '❌ Не завершено';
            pwdStatus.style.fontWeight = p ? 'bold' : 'normal';
        }
    }

    // Initialize profile statuses
    updateProfileStatuses();

    // Notification system
    function showNotification(message, type = 'info') {
        // Remove existing notification
        const existingNotification = document.querySelector('.notification');
        if(existingNotification){
            existingNotification.remove();
        }

        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;

        // Add styles
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 5px;
            color: white;
            font-weight: bold;
            z-index: 1000;
            animation: slideIn 0.3s ease-out;
            max-width: 300px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        `;

        switch(type){
            case 'success':
                notification.style.background = 'var(--green)';
                break;
            case 'error':
                notification.style.background = 'var(--red)';
                break;
            case 'warning':
                notification.style.background = '#f1c40f';
                break;
            default:
                notification.style.background = '#3498db';
        }

        document.body.appendChild(notification);

        // Auto remove after 3 seconds
        setTimeout(() => {
            if(notification.parentNode){
                notification.style.animation = 'slideOut 0.3s ease-in';
                setTimeout(() => notification.remove(), 300);
            }
        }, 3000);
    }

    // Add CSS animations for notifications
    if(!document.querySelector('#notification-styles')){
        const style = document.createElement('style');
        style.id = 'notification-styles';
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideOut {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
        `;
        document.head.appendChild(style);
    }

    // Password generator helper (optional feature)
    const generatePwdBtn = document.getElementById('generatePwdBtn');
    if(generatePwdBtn && pwdInput){
        generatePwdBtn.addEventListener('click', function(){
            const generatedPassword = generateStrongPassword();
            pwdInput.value = generatedPassword;
            updatePasswordStrength(generatedPassword);
            showNotification('Пароль сгенерирован!', 'success');
        });
    }

    function generateStrongPassword(){
        const chars = {
            upper: 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
            lower: 'abcdefghijklmnopqrstuvwxyz',
            digits: '0123456789',
            special: '!@#$%^&*()_+-=[]{}|;:,.<>?'
        };

        let password = '';
        // Ensure at least one of each type
        password += chars.upper[Math.floor(Math.random() * chars.upper.length)];
        password += chars.lower[Math.floor(Math.random() * chars.lower.length)];
        password += chars.digits[Math.floor(Math.random() * chars.digits.length)];
        password += chars.special[Math.floor(Math.random() * chars.special.length)];

        // Fill remaining characters randomly
        const allChars = chars.upper + chars.lower + chars.digits + chars.special;
        for(let i = password.length; i < 12; i++){
            password += allChars[Math.floor(Math.random() * allChars.length)];
        }

        // Shuffle the password
        return password.split('').sort(() => 0.5 - Math.random()).join('');
    }

    // Clear all progress button
    const clearProgressBtn = document.getElementById('clearProgressBtn');
    if(clearProgressBtn){
        clearProgressBtn.addEventListener('click', function(){
            if(confirm('Вы уверены, что хотите сбросить весь прогресс? Это действие нельзя отменить.')){
                localStorage.removeItem('infoViewed');
                localStorage.removeItem('trainerPassed');
                localStorage.removeItem('trainerScore');
                localStorage.removeItem('passwordChecked');
                updateProfileStatuses();
                showNotification('Прогресс сброшен', 'info');
            }
        });
    }

    // Auto-save progress every 30 seconds
    setInterval(updateProfileStatuses, 30000);
});