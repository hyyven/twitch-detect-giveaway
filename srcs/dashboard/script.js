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
				const headerDiv = document.createElement('div');
				const statusSpan = document.createElement('span');
				statusSpan.id = `status-${channel}`;
				statusSpan.className = 'status';
				const channelStrong = document.createElement('strong');
				channelStrong.textContent = channel;
				headerDiv.appendChild(statusSpan);
				headerDiv.appendChild(channelStrong);

				const statsDiv = document.createElement('div');
				statsDiv.className = 'stats';
				const cooldownSpan = document.createElement('span');
				cooldownSpan.id = `cooldown-${channel}`;
				cooldownSpan.textContent = '-';
				const msgCountSpan = document.createElement('span');
				msgCountSpan.id = `msg-count-${channel}`;
				msgCountSpan.textContent = '0 msg';
				statsDiv.appendChild(cooldownSpan);
				statsDiv.appendChild(msgCountSpan);

				const historyDiv = document.createElement('div');
				historyDiv.id = `history-${channel}`;
				historyDiv.className = 'history';

				card.appendChild(headerDiv);
				card.appendChild(statsDiv);
				card.appendChild(historyDiv);
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
				historyEl.replaceChildren();
				for (const msg of info.message_history)
				{
					const item = document.createElement('div');
					item.className = 'history-item';
					item.textContent = msg;
					historyEl.appendChild(item);
				}
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

setInterval(updateData, 2000);
updateData();
