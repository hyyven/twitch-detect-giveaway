const container = document.getElementById('container');

async function updateData()
{
	try
	{
		const response = await fetch('/api/data');
		const resData = await response.json();
		const data = resData.channels;
		const cooldownMax = resData.cooldown;
		const currentChannels = new Set(Object.keys(data));

		for (const [channel, info] of Object.entries(data))
		{
			let card = document.getElementById(`card-${channel}`);
			if (!card)
			{
				card = document.createElement('div');
				card.id = `card-${channel}`;
				card.className = 'card';
				card.innerHTML = `
					<div>
						<span id="status-${channel}" class="status"></span>
						<strong>${channel}</strong>
					</div>
					<div class="stats">
						<span id="cooldown-${channel}">-</span>
						<span id="msg-count-${channel}">0 msg</span>
					</div>
					<div id="history-${channel}" class="history"></div>
				`;
				container.appendChild(card);
			}
			const statusEl = document.getElementById(`status-${channel}`);
			statusEl.className = info.is_connected ? 'status online' : 'status offline';
			const cooldownEl = document.getElementById(`cooldown-${channel}`);
			const elapsed = (Date.now() / 1000) - info.last_notif_time;
			const remaining = cooldownMax - elapsed;
			if (info.last_notif_time === 0 || remaining <= 0)
			{
				cooldownEl.textContent = 'cd: ready';
				cooldownEl.style.color = '#4caf50';
			}
			else
			{
				cooldownEl.textContent = `cd: ${Math.round(remaining)}s`;
				cooldownEl.style.color = '#f44336';
			}
			const countEl = document.getElementById(`msg-count-${channel}`);
			countEl.textContent = `${info.message_history.length} msg`;
			const historyEl = document.getElementById(`history-${channel}`);
			const oldLen = parseInt(historyEl.dataset.len || "0", 10);
			if (info.message_history.length !== oldLen)
			{
				historyEl.innerHTML = info.message_history
					.map(msg => `<div class="history-item">${msg}</div>`)
					.join('');
				historyEl.dataset.len = info.message_history.length;
			}
		}

		for (const child of Array.from(container.children))
		{
			const chName = child.id.replace('card-', '');
			if (!currentChannels.has(chName))
			{
				child.remove();
			}
		}
	}
	catch (error)
	{
		console.error("dashboard fetch error: ", error);
	}
}

setInterval(updateData, 500);
updateData();
