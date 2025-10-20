// Main interactive script for the Jeopardy UI
document.addEventListener('DOMContentLoaded', function() {
    try {
    const modal = document.getElementById('modal')
    const modalContent = document.getElementById('modalContent')
    const modalCategory = document.getElementById('modalCategory')
    const modalQuestion = document.getElementById('modalQuestion')
    const answerInput = document.getElementById('answerInput')
    const scoreEl = document.getElementById('score')
    const timeEl = document.getElementById('time')
    const closeBtn = document.getElementById('closeModal');
    if (closeBtn) {
        closeBtn.addEventListener('click', hideModal);
    }
    let current = null // {category, points}
    const submitBtn = document.getElementById('submitAnswer');
    if (submitBtn) {
        submitBtn.addEventListener('click', submitAnswer);
    }
    if (answerInput && !answerInput.listenerAdded) {
        answerInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') submitAnswer()
        })
        answerInput.listenerAdded = true
    }

    function showModal() {
        // try to use classes, but also set inline styles as fallback so it appears
        try {
            modal.classList.remove('hidden')
            modal.classList.add('flex')
            modal.style.display = 'flex'
        } catch (e) {
            modal.style.display = 'flex'
        }
        // animate in (use inline fallback)
        try {
            requestAnimationFrame(() => {
                modalContent.classList.remove('scale-95', 'opacity-0')
                modalContent.classList.add('scale-100', 'opacity-100')
            })
        } catch (e) {
            modalContent.style.transform = 'scale(1)'
            modalContent.style.opacity = '1'
        }
        answerInput.focus()
    }

    function hideModal() {
        try {
            modalContent.classList.add('scale-95', 'opacity-0')
            modalContent.classList.remove('scale-100', 'opacity-100')
        } catch (e) {
            modalContent.style.transform = 'scale(0.95)'
            modalContent.style.opacity = '0'
        }
        // remove flex after animation to restore hidden block state
        setTimeout(() => {
            try { modal.classList.remove('flex'); modal.classList.add('hidden') } catch (e) {}
            modal.style.display = 'none'
        }, 220)
        answerInput.value = ''
        current = null
    }

    document.querySelectorAll('.question').forEach(btn => {
        btn.addEventListener('click', () => {
            if (btn.disabled) return
            // check time left before opening
            fetch('/time_left').then(r => r.json()).then(tdata => {
                if (tdata.time_left <= 0) {
                    showToast('Time is up — no more questions', 1800)
                    return
                }
                const category = btn.getAttribute('data-category')
                const points = btn.getAttribute('data-points')
                current = {category, points}

                if (window.questions && window.questions[category] && window.questions[category][points]) {
                    modalQuestion.innerText = window.questions[category][points].question
                } else {
                    modalQuestion.innerText = `${points} points question`
                }
                // prefer button data-question attribute if present
                const btnQuestion = btn.getAttribute('data-question')
                if (btnQuestion && btnQuestion.trim().length) {
                    modalQuestion.innerText = btnQuestion
                }
                modalCategory.innerText = `${category} — ${points}`
                showModal()
                // disable the button to prevent re-click locally; server will also block cross-client
                btn.disabled = true
                btn.classList.add('opacity-50', 'cursor-not-allowed')
            }).catch(() => {
                // if time check fails, allow opening but rely on server-side checks
                const category = btn.getAttribute('data-category')
                const points = btn.getAttribute('data-points')
                current = {category, points}
                const btnQuestion = btn.getAttribute('data-question')
                if (btnQuestion && btnQuestion.trim().length) {
                    modalQuestion.innerText = btnQuestion
                } else if (window.questions && window.questions[category] && window.questions[category][points]) {
                    modalQuestion.innerText = window.questions[category][points].question
                } else {
                    modalQuestion.innerText = `${points} points question`
                }
                modalCategory.innerText = `${category} — ${points}`
                showModal()
                btn.disabled = true
                btn.classList.add('opacity-50', 'cursor-not-allowed')
            })
        })
    })

    //document.getElementById('closeModal').addEventListener('click', hideModal);
    //document.getElementById('submitAnswer').addEventListener('click', submitAnswer)
    //answerInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') submitAnswer() })

    // Toast helpers
    const toast = document.getElementById('toast')
    const toastInner = document.getElementById('toastInner')
    const toastMessage = document.getElementById('toastMessage')

    function showToast(message, timeout = 1500) {
        toastMessage.innerText = message
        toast.classList.remove('hidden')
        // animate in
        requestAnimationFrame(() => {
            toastInner.classList.remove('translate-y-6', 'opacity-0')
            toastInner.classList.add('translate-y-0', 'opacity-100')
        })
        // hide after timeout
        setTimeout(() => hideToast(), timeout)
    }

    function hideToast() {
        toastInner.classList.add('translate-y-6', 'opacity-0')
        toastInner.classList.remove('translate-y-0', 'opacity-100')
        setTimeout(() => toast.classList.add('hidden'), 200)
    }

    const HOLD_MS = 1500 // how long to hold the modal visible after showing toast

    function submitAnswer() {
        if (!current) return
        // capture current into a local immutable context so async callbacks
        // don't fail if `current` is cleared by hideModal() before the delayed handlers run
        const ctx = { category: current.category, points: current.points }
        const answer = answerInput.value.trim()
        fetch('/check_answer', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({category: ctx.category, points: ctx.points, answer})
        }).then(r => r.json()).then(data => {
            if (data.status === 'time_up') {
                showToast('Time is up — no more answers accepted', 2000)
                // disable input and submit
                answerInput.disabled = true
                document.getElementById('submitAnswer').disabled = true
                setTimeout(() => hideModal(), 1200)
                return
            }
            if (data.status === 'already_answered') {
                showToast('Already answered', 1200)
                // close after a short hold
                setTimeout(() => hideModal(), Math.min(HOLD_MS, 700))
                return
            }

            if (data.result === 'correct') {
                scoreEl.innerText = data.score
                showToast('✅ Correct!', 1300)
            } else {
                showToast('❌ Incorrect', 1300)
            }
            // hold the modal visible briefly so the player can see the toast and result, then close
            setTimeout(() => {
                // mark the tile as disabled permanently in the DOM to reflect answered state
                try {
                    document.querySelectorAll(`button.question[data-category="${ctx.category}"][data-points="${ctx.points}"]`).forEach(b => { b.disabled = true; b.classList.add('opacity-50','cursor-not-allowed') })
                } catch (e) {
                    // defensive: if DOM selection fails, ignore and continue
                    console.warn('Failed to mark button disabled', e)
                }
                hideModal()
            }, HOLD_MS)
        }).catch(err => {
            console.error('submit error', err)
            showToast('Error submitting', 1000)
            setTimeout(() => hideModal(), 800)
        })
    }

    // Player name is display-only now (no save button)

    // Poll time left
    function updateTime() {
        fetch('/time_left').then(r => r.json()).then(data => {
            const t = data.time_left
            const mm = String(Math.floor(t/60)).padStart(2, '0')
            const ss = String(t % 60).padStart(2, '0')
            timeEl.innerText = `${mm}:${ss}`
            // animate timeBar
            const total = window.GAME_DURATION || 600
            const bar = document.getElementById('timeBar')
            if (bar) {
                const pct = Math.max(0, Math.min(1, t / total))
                bar.style.width = `${pct * 100}%`
            }

            if (t <= 0) {
                // show end game modal
                showEndGame()
            }
        }).catch(()=>{})
    }
    updateTime()
    setInterval(updateTime, 1000)

    // Theme toggle
    const themeToggle = document.getElementById('themeToggle')
    if (themeToggle) {
        themeToggle.addEventListener('change', (e) => {
            if (e.target.checked) document.body.classList.add('cyber')
            else document.body.classList.remove('cyber')
        })
    }

    function showEndGame() {
        const modal = document.getElementById('endGameModal')
        const final = document.getElementById('finalScore')
        fetch('/end_game', {method:'POST'}).then(r=>r.json()).then(data=>{
            final.innerText = data.final_score || 0
            try { modal.classList.remove('hidden'); modal.classList.add('flex') } catch(e){ modal.style.display='flex'}
        }).catch(()=>{})
    }

    const closeEndGame = document.getElementById('closeEndGame')
    if (closeEndGame) closeEndGame.addEventListener('click', () => { document.getElementById('endGameModal').style.display='none' })

    // When the game ends due to time running out, close the tab automatically.
    // Some browsers restrict window.close() for tabs not opened via script; in that case
    // we fallback to showing the end-game modal and leaving it to the user to close the tab.
    function tryCloseTab() {
        try {
            // attempt to close the window/tab
            window.open('', '_self')
            window.close()
        } catch (e) {
            // no-op: some browsers prevent programmatic close; just leave modal visible
            console.warn('Unable to close tab programmatically', e)
        }
    }

    // Replace showEndGame to redirect to /login after showing final score
    function showEndGame() {
        const modal = document.getElementById('endGameModal')
        const final = document.getElementById('finalScore')
        fetch('/end_game', {method:'POST'}).then(r=>r.json()).then(data=>{
            final.innerText = data.final_score || 0
            try { modal.classList.remove('hidden'); modal.classList.add('flex') } catch(e){ modal.style.display='flex'}
            // give user a short moment to see the score then redirect to login
            setTimeout(() => {
                // use replace so back button doesn't return to the finished game
                try {
                    location.replace('/login')
                } catch (e) {
                    // fallback to assigning href
                    location.href = '/login'
                }
            }, 1200)
        }).catch(()=>{})
    }

    // end try for DOMContentLoaded
    } catch (err) {
        showDebugError(err)
    }

    // global error handler to catch runtime errors and display in overlay
    window.addEventListener('error', function(ev) {
        showDebugError(ev.error || ev.message || String(ev))
    })

    // helper to display debug overlay (creates element if necessary)
    function showDebugError(err) {
        let overlay = document.getElementById('debugOverlay')
        if (!overlay) {
            overlay = document.createElement('div')
            overlay.id = 'debugOverlay'
            overlay.style.position = 'fixed'
            overlay.style.left = '8px'
            overlay.style.bottom = '8px'
            overlay.style.padding = '8px 12px'
            overlay.style.background = 'rgba(220,30,30,0.95)'
            overlay.style.color = 'white'
            overlay.style.zIndex = '99999'
            overlay.style.maxWidth = '60vw'
            overlay.style.fontFamily = 'monospace'
            overlay.style.fontSize = '12px'
            overlay.style.borderRadius = '6px'
            document.body.appendChild(overlay)
        }
        overlay.textContent = 'JS ERROR: ' + (err && err.stack ? err.stack : String(err))
        overlay.style.display = 'block'
    }

})
