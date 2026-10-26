(() => {
  const form = document.getElementById('usage-controls');
  if (!form) return;
  const period = document.getElementById('usage-period');
  const from = document.getElementById('usage-from');
  const to = document.getElementById('usage-to');
  const chart = document.getElementById('usage-chart');
  const error = document.getElementById('usage-error');
  const forecast = JSON.parse(document.getElementById('usage-forecast').textContent);
  const dayMs = 86400000;
  const factors = [[1, 1], [.85, .95], [.65, 1.1], [1, 1], [.7, .9], [.95, 1.05], [.8, 1.2]];
  const iso = date => date.toISOString().slice(0, 10);
  const parse = value => new Date(`${value}T00:00:00Z`);
  const today = new Date();
  from.value = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
  to.value = from.value;

  function setBounds() {
    const date = parse(from.value);
    if (!Number.isFinite(date.getTime())) return;
    if (period.value === 'daily') to.value = from.value;
    if (period.value === 'monthly') {
      from.value = iso(new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), 1)));
      to.value = iso(new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth() + 1, 0)));
    }
    if (period.value === 'yearly') {
      from.value = `${date.getUTCFullYear()}-01-01`;
      to.value = `${date.getUTCFullYear()}-12-31`;
    }
    to.disabled = period.value !== 'custom';
  }

  function render() {
    error.hidden = true;
    if (!form.reportValidity()) return;
    const start = parse(from.value), end = parse(to.value);
    const days = Math.round((end - start) / dayMs) + 1;
    if (!Number.isFinite(days) || days < 1 || days > 3660) {
      error.textContent = 'Choose an end date on or after the start date, within a ten-year range.';
      error.hidden = false;
      return;
    }
    const groups = new Map();
    for (let day = new Date(start); day <= end; day = new Date(day.getTime() + dayMs)) {
      const [solarFactor, homeFactor] = factors[day.getUTCDay()];
      for (const slot of forecast) {
        const hourly = period.value === 'daily';
        const monthly = period.value === 'yearly' || days > 62;
        const key = hourly ? Math.floor(slot.hour / 3) : monthly ? iso(day).slice(0, 7) : iso(day);
        if (!groups.has(key)) {
          const label = hourly ? `${String(key * 3).padStart(2, '0')}:00` : monthly ? iso(day).slice(0, 7) : iso(day).slice(5);
          groups.set(key, {label, solar: 0, home: 0});
        }
        const row = groups.get(key);
        row.solar += slot.solar_kw * .5 * solarFactor;
        row.home += slot.home_kw * .5 * homeFactor;
      }
    }
    const rows = [...groups.values()];
    const max = Math.max(1, ...rows.flatMap(row => [row.solar, row.home]));
    chart.replaceChildren();
    for (const row of rows) {
      const group = document.createElement('div');
      group.className = 'weekly-day';
      group.setAttribute('role', 'img');
      group.setAttribute('aria-label', `${row.label}: solar ${row.solar.toFixed(1)} kWh; home ${row.home.toFixed(1)} kWh`);
      const pair = document.createElement('div');
      pair.className = 'weekly-pair';
      for (const [type, value] of [['solar', row.solar], ['home', row.home]]) {
        const bar = document.createElement('span');
        bar.className = `weekly-${type}`;
        bar.style.height = `${value / max * 100}%`;
        const number = document.createElement('b');
        number.textContent = value.toFixed(1);
        bar.append(number);
        pair.append(bar);
      }
      const label = document.createElement('span');
      label.textContent = row.label;
      group.append(pair, label);
      chart.append(group);
    }
    const bucket = period.value === 'daily' ? '3-hour totals' : period.value === 'yearly' || days > 62 ? 'Monthly totals' : 'Daily totals';
    document.getElementById('usage-caption').textContent = `${from.value} to ${to.value} · ${bucket} · kWh`;
    const solar = rows.reduce((sum, row) => sum + row.solar, 0);
    const home = rows.reduce((sum, row) => sum + row.home, 0);
    document.getElementById('usage-summary').textContent = `Selected period: ${solar.toFixed(1)} kWh solar generated · ${home.toFixed(1)} kWh home usage.`;
  }
  period.addEventListener('change', () => { setBounds(); render(); });
  from.addEventListener('change', () => { setBounds(); render(); });
  to.addEventListener('change', render);
  form.addEventListener('submit', event => { event.preventDefault(); setBounds(); render(); });
  setBounds();
  render();
})();
