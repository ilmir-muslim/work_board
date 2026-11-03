// static/js/developer.js

document.addEventListener('DOMContentLoaded', function () {
    initializeTimerDisplays();
    initLiveStats();

    // Запрашиваем права на уведомления для Pomodoro
    if ("Notification" in window && Notification.permission === "default") {
        Notification.requestPermission();
    }

    // Восстанавливаем фильтры из памяти
    const savedTaskFilter = localStorage.getItem('savedTaskFilter');
    if (savedTaskFilter && document.getElementById(`filter-${savedTaskFilter}`)) {
        if (typeof filterTasks === 'function') filterTasks(savedTaskFilter);
    }

    const savedProjectFilter = localStorage.getItem('savedProjectFilter');
    if (savedProjectFilter && document.getElementById(`filter-${savedProjectFilter}`)) {
        if (typeof filterProjects === 'function') filterProjects(savedProjectFilter);
    }
});

function initializeTimerDisplays() {
    document.querySelectorAll('.current-time').forEach(el => {
        const initial = el.getAttribute('data-initial-seconds');
        const seconds = initial ? parseFloat(initial) : 0;
        el.textContent = formatTimeColon(seconds); // Формат ЧЧ:ММ:СС
        el.setAttribute('data-seconds', seconds);
    });
    updateProjectTotals();
}

// ---------------------------------------------------------------
//  Базовые утилиты и работа со ставкой
// ---------------------------------------------------------------
function openRateModal() {
    document.getElementById('rateModal').style.display = 'flex';
}

function closeRateModal() {
    document.getElementById('rateModal').style.display = 'none';
}

function updateRate() {
    const rate = document.getElementById('newRate').value;
    fetch('/users/profile/rate/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'default_hourly_rate=' + rate
    }).then(res => {
        if (res.ok) location.reload();
    });
}

// ---------------------------------------------------------------
//  Проекты
// ---------------------------------------------------------------
function createProject() {
    const name = document.getElementById('newProjectName').value.trim();
    if (!name) return;
    fetch('/developers/api/projects/create/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
        body: JSON.stringify({ name: name })
    }).then(response => {
        if (response.ok) location.reload();
    });
}

function deleteProject() {
    if (!confirm('Удалить проект и все его задачи?')) return;
    fetch(`/developers/api/projects/${currentProjectId}/delete/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken }
    }).then(response => {
        if (response.ok) window.location.href = '/developers/projects/';
    });
}

function editProjectName() {
    const titleElement = document.getElementById('projectName');
    if (!titleElement) return;
    const currentName = titleElement.textContent.replace(/^📋\s*/, '').trim();
    const newName = prompt('Новое название проекта:', currentName);
    if (newName) {
        fetch(`/developers/api/projects/${currentProjectId}/update/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
            body: JSON.stringify({ name: newName })
        }).then(response => {
            if (response.ok) location.reload();
        });
    }
}

function addProjectPayment() {
    const amountStr = prompt('Введите сумму поступившей оплаты (₽):\n(Введенная сумма прибавится к уже оплаченной)');
    if (!amountStr) return;

    const amount = parseFloat(amountStr.replace(',', '.'));

    if (isNaN(amount) || amount <= 0) {
        alert('Пожалуйста, введите корректную сумму.');
        return;
    }

    fetch(`/developers/api/projects/${currentProjectId}/update/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
        body: JSON.stringify({ add_payment: amount })
    }).then(response => {
        if (response.ok) {
            location.reload();
        } else {
            alert('Ошибка при сохранении оплаты');
        }
    }).catch(() => alert('Ошибка сети'));
}

function editProjectRate() {
    const currentRate = document.querySelector('.project-rate').textContent.trim();
    const newRate = prompt('Новая ставка (₽/час):', currentRate);
    if (newRate) {
        fetch(`/developers/api/projects/${currentProjectId}/update/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
            body: JSON.stringify({ hourly_rate: newRate })
        }).then(response => {
            if (response.ok) location.reload();
        });
    }
}

// ---------------------------------------------------------------
//  Задачи (общие)
// ---------------------------------------------------------------
async function addTimerTask() {
    const title = document.getElementById('newTimerTaskTitle').value.trim();
    if (!title) return;
    await fetch('/developers/api/tasks/create/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
        body: JSON.stringify({
            title: title,
            project_id: currentProjectId
        })
    });
    location.reload();
}

async function addProjectTask() {
    const title = document.getElementById('newTaskTitle').value.trim();
    if (!title) return;
    const priority = document.getElementById('newTaskPriority').value;
    let dueDate = document.getElementById('newTaskDueDate').value || null;
    await fetch('/developers/api/tasks/create/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
        body: JSON.stringify({
            title: title,
            project_id: currentProjectId,
            priority: priority,
            due_date: dueDate
        })
    });
    location.reload();
}

async function addDailyTask() {
    const title = document.getElementById('newTaskTitle').value.trim();
    if (!title) return;
    const priority = document.getElementById('newTaskPriority').value;
    let dueDate = document.getElementById('newTaskDueDate').value || null;
    await fetch('/developers/api/tasks/create/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
        body: JSON.stringify({
            title: title,
            project_id: null,
            priority: priority,
            due_date: dueDate
        })
    });
    location.reload();
}

async function deleteTask(taskId) {
    if (!confirm('Удалить задачу?')) return;
    await fetch(`/developers/api/tasks/${taskId}/delete/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken }
    });
    location.reload();
}

async function toggleTaskCompletion(taskId, checked) {
    await fetch(`/developers/api/tasks/${taskId}/update/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
        body: JSON.stringify({ is_completed: checked })
    });

    const card = document.querySelector(`.task-item[data-task-id="${taskId}"]`);
    if (card) {
        if (checked) {
            card.classList.add('completed');
        } else {
            card.classList.remove('completed');
        }
        card.dataset.completed = checked.toString();
    }

    const allTaskCards = document.querySelectorAll('#tasksList .task-item');
    const completedCount = Array.from(allTaskCards).filter(
        item => item.dataset.completed === 'true'
    ).length;

    const counterElement = document.getElementById('completedTasksCount');
    if (counterElement) {
        counterElement.textContent = completedCount;
    }
}

// ---------------------------------------------------------------
//  Редактирование Времени (с форматом ЧЧ:ММ:СС)
// ---------------------------------------------------------------
async function editTaskTime(taskId, element) {
    const seconds = parseFloat(element.getAttribute('data-seconds') || element.getAttribute('data-initial-seconds') || 0);
    const defaultTime = formatTimeColon(seconds);
    const newTimeStr = prompt('Корректировка времени задачи\nВведите новое время в формате ЧЧ:ММ:СС :', defaultTime);

    if (!newTimeStr || newTimeStr === defaultTime) return;
    const parts = newTimeStr.split(':');
    if (parts.length !== 3) {
        alert('Неверный формат! Пожалуйста, используйте формат ЧЧ:ММ:СС');
        return;
    }

    const h = parseInt(parts[0], 10) || 0;
    const m = parseInt(parts[1], 10) || 0;
    const s = parseInt(parts[2], 10) || 0;
    const totalSeconds = (h * 3600) + (m * 60) + s;

    try {
        const response = await fetch(`/developers/api/tasks/${taskId}/update/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
            body: JSON.stringify({ total_time: totalSeconds })
        });
        if (response.ok) { location.reload(); } else { alert('Ошибка при сохранении времени'); }
    } catch (e) { alert('Ошибка сети при сохранении'); }
}

async function editDailySessionTime(element) {
    const defaultTime = formatTimeColon(dailySeconds);
    const newTimeStr = prompt('Корректировка времени за СЕГОДНЯ\nВведите новое время в формате ЧЧ:ММ:СС :', defaultTime);

    if (!newTimeStr || newTimeStr === defaultTime) return;
    const parts = newTimeStr.split(':');
    if (parts.length !== 3) {
        alert('Неверный формат! Пожалуйста, используйте формат ЧЧ:ММ:СС');
        return;
    }

    const h = parseInt(parts[0], 10) || 0;
    const m = parseInt(parts[1], 10) || 0;
    const s = parseInt(parts[2], 10) || 0;
    const totalSeconds = (h * 3600) + (m * 60) + s;

    try {
        const response = await fetch(`/developers/api/daily-session/update/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
            body: JSON.stringify({ total_time: totalSeconds })
        });
        if (response.ok) {
            if (typeof refreshLiveStatsNow === 'function') { refreshLiveStatsNow(); } else { location.reload(); }
        } else { alert('Ошибка при сохранении дневного времени'); }
    } catch (e) { alert('Ошибка сети при сохранении'); }
}

// ---------------------------------------------------------------
//  Таймер (с динамическими кнопками старт/пауза)
// ---------------------------------------------------------------
function formatTime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    return `${hours}ч ${minutes}м ${secs}с`;
}

function formatTimeColon(seconds) {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

function renderTimerButton(isRunning) {
    if (isRunning) {
        return `<button onclick="pauseTimer(this.closest('[data-task-id]').dataset.taskId)" class="btn btn-warning timer-action">⏸ Пауза</button>`;
    } else {
        return `<button onclick="startTimer(this.closest('[data-task-id]').dataset.taskId)" class="btn btn-primary timer-action">▶ Старт</button>`;
    }
}

function updateTimerButton(taskId, isRunning) {
    const container = document.querySelector(`.timer-btn-container[data-task-id="${taskId}"]`);
    if (container) {
        container.innerHTML = renderTimerButton(isRunning);
    }
}

function updateProjectTotals() {
    let totalSeconds = 0;
    document.querySelectorAll('.current-time').forEach(el => {
        const sec = parseFloat(el.getAttribute('data-seconds')) || 0;
        totalSeconds += sec;
    });

    const totalEl = document.getElementById('projectTotalTime');
    if (totalEl) {
        totalEl.textContent = formatTimeColon(totalSeconds);
    }

    const rateEl = document.querySelector('.project-rate');
    if (rateEl) {
        const rateText = rateEl.textContent.trim();
        const rateMatch = rateText.match(/[\d.]+/);
        const rate = rateMatch ? parseFloat(rateMatch[0]) : 0;

        // Пересчет Заработанного
        const earned = (totalSeconds * rate / 3600);
        const earnedEl = document.getElementById('earnedAmount');
        if (earnedEl) {
            earnedEl.textContent = `${earned.toFixed(2)} ₽`;
        }

        // Пересчет Осталось к оплате
        const leftToPayEl = document.getElementById('remainingAmount');
        if (leftToPayEl) {
            const paidEl = document.getElementById('paidAmount');
            const paidText = paidEl ? paidEl.textContent : '0';
            const paid = parseFloat(paidText.replace(',', '.')) || 0;

            const remaining = Math.max(0, earned - paid);
            leftToPayEl.textContent = `${remaining.toFixed(2)} ₽`;

            if (remaining <= 0 && earned > 0) {
                leftToPayEl.style.color = '#10b981'; // Оплачено (зеленый)
            } else {
                leftToPayEl.style.color = '#ffd966'; // Долг (желтый)
            }
        }
    }
}

function updateLiveTimers() {
    document.querySelectorAll('.timer-task-card[data-task-id]').forEach(card => {
        const taskId = card.dataset.taskId;
        fetch(`/developers/api/task-current-time/${taskId}/`)
            .then(r => r.json())
            .then(data => {
                const timeEl = card.querySelector('.current-time');
                if (timeEl) {
                    timeEl.textContent = formatTimeColon(data.total_time);
                    timeEl.setAttribute('data-seconds', data.total_time);
                }
                if (data.is_timer_running) {
                    card.classList.add('active');
                } else {
                    card.classList.remove('active');
                }
                updateTimerButton(taskId, data.is_timer_running);
                updateProjectTotals();
            });
    });
}

async function startTimer(taskId) {
    updateTimerButton(taskId, true);
    try {
        await fetch(`/developers/api/timer/start/${taskId}/`, {
            method: 'POST',
            headers: { 'X-CSRFToken': csrfToken }
        });
        if (typeof updateLiveTimers === 'function') updateLiveTimers();
        if (typeof refreshLiveStatsNow === 'function') refreshLiveStatsNow();
    } catch (e) {
        updateTimerButton(taskId, false);
    }
}

async function pauseTimer(taskId) {
    updateTimerButton(taskId, false);
    try {
        await fetch(`/developers/api/timer/pause/${taskId}/`, {
            method: 'POST',
            headers: { 'X-CSRFToken': csrfToken }
        });
        if (typeof updateLiveTimers === 'function') updateLiveTimers();
        if (typeof refreshLiveStatsNow === 'function') refreshLiveStatsNow();
    } catch (e) {
        updateTimerButton(taskId, true);
    }
}

async function stopAllTimers() {
    await fetch('/developers/api/timer/stop-all/', {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken }
    });
    location.reload();
}

// ---------------------------------------------------------------
//  Подзадачи
// ---------------------------------------------------------------
async function addSubTask(taskId, input) {
    const title = input.value.trim();
    if (!title) return;
    await fetch(`/developers/api/tasks/${taskId}/subtasks/create/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
        body: JSON.stringify({ title: title })
    });
    location.reload();
}

async function editSubTask(subtaskId, element) {
    const newTitle = prompt('Новое название:', element.textContent.trim());
    if (newTitle) {
        await fetch(`/developers/api/subtasks/${subtaskId}/update/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
            body: JSON.stringify({ title: newTitle })
        });
        location.reload();
    }
}

async function deleteSubTask(taskId, subtaskId) {
    if (!confirm('Удалить подзадачу?')) return;
    await fetch(`/developers/api/subtasks/${subtaskId}/delete/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken }
    });
    location.reload();
}

async function toggleSubTaskCompletion(taskId, subtaskId, checked) {
    await fetch(`/developers/api/subtasks/${subtaskId}/update/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
        body: JSON.stringify({ is_completed: checked })
    });
    location.reload();
}

// ---------------------------------------------------------------
//  Статические комментарии (с перезагрузкой)
// ---------------------------------------------------------------
async function addTaskComment(taskId, textarea) {
    const content = textarea.value.trim();
    if (!content) return;
    await fetch(`/developers/api/tasks/${taskId}/comments/create/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
        body: JSON.stringify({ content: content })
    });
    location.reload();
}

async function deleteTaskComment(taskId, commentId) {
    if (!confirm('Удалить комментарий?')) return;
    await fetch(`/developers/api/task-comments/${commentId}/delete/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken }
    });
    location.reload();
}

async function addSubTaskComment(subtaskId, textarea) {
    const content = textarea.value.trim();
    if (!content) return;
    await fetch(`/developers/api/subtasks/${subtaskId}/comments/create/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
        body: JSON.stringify({ content: content })
    });
    location.reload();
}

async function deleteSubTaskComment(subtaskId, commentId) {
    if (!confirm('Удалить комментарий?')) return;
    await fetch(`/developers/api/subtask-comments/${commentId}/delete/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken }
    });
    location.reload();
}

// ---------------------------------------------------------------
//  Динамические комментарии (без перезагрузки, для вкладки таймера)
// ---------------------------------------------------------------

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

function toggleCommentsBlock(button, taskId) {
    const block = button.nextElementSibling;
    if (block.style.display === 'none' || !block.style.display) {
        block.style.display = 'block';
        button.textContent = '💬 Скрыть комментарии';
    } else {
        block.style.display = 'none';
        const count = block.querySelector('.comments-list').children.length;
        button.textContent = `💬 Комментарии (${count})`;
    }
}

async function addTaskCommentDynamic(taskId, textarea) {
    const content = textarea.value.trim();
    if (!content) return;

    try {
        const response = await fetch(`/developers/api/tasks/${taskId}/comments/create/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
            body: JSON.stringify({ content: content })
        });
        if (!response.ok) throw new Error('Ошибка сервера');
        const comment = await response.json();

        const commentDiv = document.createElement('div');
        commentDiv.className = 'comment-item';
        commentDiv.setAttribute('data-comment-id', comment.id);
        commentDiv.style.cssText =
            'background:#f9fafb; padding:0.5rem; border-radius:0.5rem; margin-bottom:0.3rem;';

        const now = new Date();
        const dateStr =
            now.toLocaleDateString('ru-RU') +
            ' ' +
            now.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });

        commentDiv.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <span style="flex:1;">${escapeHtml(content)}</span>
                <button onclick="deleteTaskCommentDynamic(${taskId}, ${comment.id})"
                        class="btn btn-sm btn-danger" style="margin-left:0.5rem;">🗑️</button>
            </div>
            <div style="font-size:0.75rem; color:#64748b; margin-top:0.2rem;">${dateStr}</div>
        `;

        const list = document.querySelector(`.comments-list[data-task-id="${taskId}"]`);
        if (list) {
            list.appendChild(commentDiv);
        }

        textarea.value = '';

        const toggleBtn = document.querySelector(
            `.timer-task-card[data-task-id="${taskId}"] button[onclick*="toggleCommentsBlock"]`
        );
        if (toggleBtn) {
            const block = document.querySelector(`.comments-block[data-task-id="${taskId}"]`);
            if (block && block.style.display !== 'none') {
                toggleBtn.textContent = '💬 Скрыть комментарии';
            } else {
                const count = list ? list.children.length : 0;
                toggleBtn.textContent = `💬 Комментарии (${count})`;
            }
        }
    } catch (error) {
        console.error('Ошибка добавления комментария:', error);
        alert('Не удалось добавить комментарий');
    }
}

async function deleteTaskCommentDynamic(taskId, commentId) {
    if (!confirm('Удалить комментарий?')) return;
    try {
        const response = await fetch(`/developers/api/task-comments/${commentId}/delete/`, {
            method: 'POST',
            headers: { 'X-CSRFToken': csrfToken }
        });
        if (!response.ok) throw new Error('Ошибка сервера');

        const commentEl = document.querySelector(`.comment-item[data-comment-id="${commentId}"]`);
        if (commentEl) {
            commentEl.remove();
        }

        const list = document.querySelector(`.comments-list[data-task-id="${taskId}"]`);
        const count = list ? list.children.length : 0;
        const toggleBtn = document.querySelector(
            `.timer-task-card[data-task-id="${taskId}"] button[onclick*="toggleCommentsBlock"]`
        );
        if (toggleBtn) {
            const block = document.querySelector(`.comments-block[data-task-id="${taskId}"]`);
            if (block && block.style.display !== 'none') {
                toggleBtn.textContent = '💬 Скрыть комментарии';
            } else {
                toggleBtn.textContent = `💬 Комментарии (${count})`;
            }
        }
    } catch (error) {
        console.error('Ошибка удаления комментария:', error);
        alert('Не удалось удалить комментарий');
    }
}

// ---------------------------------------------------------------
//  Редактирование задач (модальное окно)
// ---------------------------------------------------------------
function openEditTaskModal(taskId) {
    const taskEl = document.querySelector(`.task-item[data-task-id="${taskId}"]`);
    const title = taskEl.querySelector('.task-text').textContent.trim();
    document.getElementById('editTaskId').value = taskId;
    document.getElementById('editTaskTitle').value = title;
    document.getElementById('editTaskModal').style.display = 'flex';
}

function closeEditTaskModal() {
    document.getElementById('editTaskModal').style.display = 'none';
}

async function saveTaskEdit(event) {
    event.preventDefault();
    const taskId = document.getElementById('editTaskId').value;
    const title = document.getElementById('editTaskTitle').value.trim();
    const priority = document.getElementById('editTaskPriority').value;
    const dueDate = document.getElementById('editTaskDueDate').value || null;
    await fetch(`/developers/api/tasks/${taskId}/update/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
        body: JSON.stringify({ title, priority, due_date: dueDate })
    });
    location.reload();
}

// ---------------------------------------------------------------
//  Отчёты и экспорт
// ---------------------------------------------------------------
function generateDailyReport() {
    window.location.href = `/developers/projects/${currentProjectId}/report/`;
}

function exportToTxt() {
    window.location.href = `/developers/projects/${currentProjectId}/export/txt/`;
}

function copyToClipboard() {
    const reportText = document.getElementById('reportContent')?.innerText || '';
    navigator.clipboard.writeText(reportText).then(() => alert('Скопировано в буфер обмена'));
}

function exportTaskReport() {
    window.location.href = `/developers/projects/${currentProjectId}/report/tasks/`;
}

function copyTaskReport() {
    const reportText = document.getElementById('reportContent')?.innerText || '';
    navigator.clipboard.writeText(reportText).then(() => alert('Скопировано в буфер обмена'));
}

function copySingleTaskToClipboard(taskId) {
    const taskEl = document.querySelector(`.task-item[data-task-id="${taskId}"]`);
    const title = taskEl.querySelector('.task-text').textContent.trim();
    navigator.clipboard.writeText(title).then(() => alert('Скопировано'));
}

// ---------------------------------------------------------------
//  Недельные отчёты (дейлики)
// ---------------------------------------------------------------
function generateCurrentWeekReport() {
    window.location.href = '/developers/reports/current-week/';
}

function generatePreviousWeekReport() {
    window.location.href = '/developers/reports/previous-week/';
}

function transferUncompletedTasksFromPreviousWeek() {
    if (!confirm('Перенести незавершённые задачи с прошлой недели?')) return;
    fetch('/developers/api/tasks/transfer-previous-week/', {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken }
    }).then(res => {
        if (res.ok) location.reload();
    });
}

// ---------------------------------------------------------------
//  Вспомогательные функции
// ---------------------------------------------------------------
function openEditTimerTaskModal(taskId) {
    alert('Редактирование задачи таймера будет здесь.');
}

// ---------------------------------------------------------------
//  Фильтры и вкладки
// ---------------------------------------------------------------
function filterProjectTasks(filter) {
    document.querySelectorAll('#projectTasksList .task-item').forEach(item => {
        const completed = item.dataset.completed === 'true';
        item.style.display =
            filter === 'all' || (filter === 'active' && !completed) || (filter === 'completed' && completed)
                ? ''
                : 'none';
    });
    document.querySelectorAll('#projectTasksList .filter-btn').forEach(b => b.classList.remove('active'));
    document.getElementById(`filter-${filter}`).classList.add('active');
}

function filterTasks(filter) {
    document.querySelectorAll('#tasksList .task-item, #tasks-container .task-item').forEach(item => {
        // Учитываем, что Python может вернуть строку 'True' или 'true'
        const completed = item.dataset.completed.toLowerCase() === 'true';
        item.style.display =
            filter === 'all' || (filter === 'active' && !completed) || (filter === 'completed' && completed)
                ? ''
                : 'none';
    });

    // Обновляем кнопки только для задач (не трогаем фильтры проектов)
    document.querySelectorAll('.filter-btn').forEach(b => {
        if (b.id && b.id.startsWith('filter-') && !b.id.startsWith('filter-proj-')) {
            b.classList.remove('active');
        }
    });
    const activeBtn = document.getElementById(`filter-${filter}`);
    if (activeBtn) activeBtn.classList.add('active');

    // Сохраняем выбор в память браузера
    localStorage.setItem('savedTaskFilter', filter);
}

function filterProjects(filterType) {
    const projects = document.querySelectorAll('.project-item');

    projects.forEach(project => {
        const status = project.getAttribute('data-payment-status');
        let shouldShow = false;

        if (filterType === 'all') {
            shouldShow = true;
        } else if (filterType === 'unpaid') {
            shouldShow = (status === 'unpaid' || status === 'partial');
        } else if (filterType === 'paid') {
            shouldShow = (status === 'paid');
        }

        project.style.display = shouldShow ? 'flex' : 'none';
    });

    document.querySelectorAll('[id^="filter-proj-"]').forEach(btn => btn.classList.remove('active'));
    const activeBtn = document.getElementById(`filter-proj-${filterType}`);
    if (activeBtn) activeBtn.classList.add('active');

    localStorage.setItem('savedProjectFilter', filterType);
}

function switchTab(tabName) {
    document.getElementById('timer-tab').style.display = tabName === 'timer' ? 'block' : 'none';
    document.getElementById('tasks-tab').style.display = tabName === 'tasks' ? 'block' : 'none';
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById(`tab-${tabName}`).classList.add('active');
}

// ---------------------------------------------------------------
//  Живое обновление статистики и Pomodoro
// ---------------------------------------------------------------
let dailySeconds = 0;
let isDailyTimerRunning = false;
let dailyTimerInterval = null;
let statsUpdateInterval = null;
let earningsUpdateInterval = null;

function formatSecondsShort(sec) {
    return sec + ' сек';
}

function renderWeekBars(data) {
    const container = document.getElementById('weekBars');
    if (!container || !data.week_stats) return;
    const max = data.max_week_seconds || 1;
    container.innerHTML = data.week_stats.map(day => {
        const percent = (day.total_seconds / max) * 100;
        const [y, m, d] = day.date.split('-');
        const dayStr = d.padStart(2, '0') + '.' + m.padStart(2, '0');
        return `
            <div class="day-bar">
                <div class="day-label" style="white-space:nowrap;">${dayStr}</div>
                <div class="bar-bg">
                    <div class="bar-fill" style="width: ${percent}%;"></div>
                </div>
                <div class="day-value">${day.total_seconds}с</div>
            </div>
        `;
    }).join('');
}

function applyDailyStats(data) {
    dailySeconds = data.current_daily_seconds;
    isDailyTimerRunning = data.is_daily_timer_running;
    document.getElementById('todayTime').textContent = formatTimeColon(dailySeconds);
    renderWeekBars(data);
    const weekTotalEl = document.getElementById('weekTotal');
    if (weekTotalEl) weekTotalEl.textContent = `Всего за неделю: ${formatTimeColon(data.week_total)}`;

    if (isDailyTimerRunning && !dailyTimerInterval) {
        startLocalDailyTicker();
    } else if (!isDailyTimerRunning && dailyTimerInterval) {
        stopLocalDailyTicker();
    }
}

function showRestNotification() {
    const title = "WorkBoard 🍅";
    const options = {
        body: "Прошло 25 минут! Пора сделать небольшой перерыв.",
        icon: "/media/ico_png.png"
    };

    if (!("Notification" in window)) return;

    if (Notification.permission === "granted") {
        new Notification(title, options);
    } else if (Notification.permission !== "denied") {
        Notification.requestPermission().then(permission => {
            if (permission === "granted") {
                new Notification(title, options);
            }
        });
    }
}

function startLocalDailyTicker() {
    if (dailyTimerInterval) return;
    dailyTimerInterval = setInterval(() => {
        dailySeconds++;
        document.getElementById('todayTime').textContent = formatTimeColon(dailySeconds);

        let start = localStorage.getItem('pomodoroStart');
        if (!start) {
            start = Date.now();
            localStorage.setItem('pomodoroStart', start);
            localStorage.setItem('pomodoroNotified', 'false');
        }

        const elapsed = Math.floor((Date.now() - start) / 1000);
        const notified = localStorage.getItem('pomodoroNotified') === 'true';

        if (elapsed >= 25 * 60 && !notified) {
            showRestNotification();
            localStorage.setItem('pomodoroNotified', 'true');
        }
    }, 1000);
}

function stopLocalDailyTicker() {
    clearInterval(dailyTimerInterval);
    dailyTimerInterval = null;

    localStorage.removeItem('pomodoroStart');
    localStorage.removeItem('pomodoroNotified');
}

async function fetchDailyStats() {
    try {
        const response = await fetch('/developers/api/daily-stats-widget/');
        if (!response.ok) return;
        const data = await response.json();
        applyDailyStats(data);
    } catch (e) {
        console.error('Ошибка получения дневной статистики', e);
    }
}

async function fetchEarnings() {
    try {
        const response = await fetch('/developers/api/earnings-widget/');
        if (!response.ok) return;
        const data = await response.json();
        const totalEl = document.getElementById('totalEarned');
        const avgEl = document.getElementById('avgMonthly');
        const monthsEl = document.getElementById('monthsSince');
        if (totalEl) totalEl.textContent = data.total_earned.toFixed(2) + ' ₽';
        if (avgEl) avgEl.textContent = data.average_monthly.toFixed(2) + ' ₽';
        if (monthsEl) monthsEl.textContent = data.months_since;
    } catch (e) {
        console.error('Ошибка получения заработка', e);
    }
}

function initLiveStats() {
    fetchDailyStats();
    fetchEarnings();
    statsUpdateInterval = setInterval(fetchDailyStats, 30000);
    earningsUpdateInterval = setInterval(fetchEarnings, 30000);
}

function refreshLiveStatsNow() {
    fetchDailyStats();
    fetchEarnings();
}