(() => {
  const root = document.getElementById('live-appliances');
  if (!root) return;
  const forecast = JSON.parse(document.getElementById('day-forecast').textContent);
  const dailySolar = forecast.reduce((sum, slot) => sum + Math.max(0, slot.solar_kw-slot.home_kw)*.5, 0);
  const taskFromRow = row => ({
    row, check: row.querySelector('input[type=checkbox]'), slider: row.querySelector('input[type=range]'),
    power: Number(row.dataset.power), duration: Number(row.dataset.duration),
    initial: row.querySelector('input[type=range]').value
  });
  let tasks = [...root.querySelectorAll('.live-appliance')].map(taskFromRow);
  let nextCustomId = 0;
  const customForm = document.getElementById('add-appliance-form');
  const status = document.getElementById('custom-appliance-status');
  const rowTemplate = root.querySelector('.live-appliance').cloneNode(true);
  customForm.addEventListener('submit', event => {
    event.preventDefault();
    const nameInput = customForm.elements.namedItem('name');
    const name = nameInput.value.trim();
    nameInput.setCustomValidity(name ? '' : 'Enter an appliance name.');
    if (!customForm.reportValidity()) return;
    const power = Number(customForm.elements.namedItem('power').value) / 1000;
    const duration = Number(customForm.elements.namedItem('duration').value);
    const row = rowTemplate.cloneNode(true);
    row.dataset.power = power;
    row.dataset.duration = duration;
    row.querySelector('strong').textContent = name;
    row.querySelector('.live-appliance-heading > span').textContent = `${(power * duration).toFixed(1)} kWh · ${duration} h`;
    const checkbox = row.querySelector('input[type=checkbox]');
    checkbox.checked = checkbox.defaultChecked = true;
    const slider = row.querySelector('input[type=range]');
    slider.id = `start-custom-${++nextCustomId}`;
    slider.max = 24 - duration;
    slider.value = 8;
    slider.setAttribute('aria-label', `${name} start time`);
    row.querySelector('.live-appliance-timing label').htmlFor = slider.id;
    const remove = document.createElement('button');
    remove.type = 'button';
    remove.className = 'remove-appliance';
    remove.textContent = 'Remove';
    remove.setAttribute('aria-label', `Remove ${name}`);
    remove.addEventListener('click', () => {
      tasks = tasks.filter(task => task.row !== row);
      row.remove();
      update();
      status.textContent = `${name} removed.`;
      customForm.closest('details').querySelector('summary').focus();
    });
    row.querySelector('.live-appliance-heading').append(remove);
    root.append(row);
    tasks.push(taskFromRow(row));
    update();
    status.textContent = `${name} added. Adjust its start time below.`;
    customForm.reset();
    customForm.closest('details').open = false;
    slider.focus();
  });
  customForm.elements.namedItem('name').addEventListener('input', event => event.target.setCustomValidity(''));
  const clock = h => {
    const minutes = Math.round(h*60), hours = Math.floor(minutes/60);
    return `${hours%12 || 12}:${String(minutes%60).padStart(2,'0')} ${hours>=12 && hours<24?'PM':'AM'}${hours===24?' (+1 day)':''}`;
  };
  function update() {
    const solar = tasks.map(() => 0);
    let total = 0, fromSolar = 0;
    for (let i=0;i<48;i++) {
      const active = tasks.map((t,index) => ({t,index})).filter(({t}) => t.check.checked && i/2>=Number(t.slider.value) && i/2<Number(t.slider.value)+t.duration);
      const demand = active.reduce((sum,{t}) => sum+t.power,0);
      const available = Math.max(0,forecast[i].solar_kw-forecast[i].home_kw);
      const used = Math.min(available,demand)*.5;
      total += demand*.5;
      fromSolar += used;
      for (const {t,index} of active) solar[index] += demand ? used*t.power/demand : 0;
    }
    const percent = total ? 100*fromSolar/total : 0;
    document.getElementById('budget-available').textContent = `${dailySolar.toFixed(1)} kWh`;
    document.getElementById('budget-used').textContent = `${fromSolar.toFixed(1)} kWh`;
    document.getElementById('budget-remaining').textContent = `${Math.max(0, dailySolar-fromSolar).toFixed(1)} kWh`;
    document.getElementById('live-solar-percent').textContent = `${Math.round(percent)}%`;
    document.getElementById('live-energy-total').textContent = `${total.toFixed(1)} kWh total`;
    document.getElementById('live-energy-split').textContent = `${fromSolar.toFixed(1)} solar · ${(total-fromSolar).toFixed(1)} grid (kWh)`;
    document.getElementById('live-solar-fill').style.width = `${percent}%`;
    tasks.forEach((t,index) => {
      t.slider.disabled = !t.check.checked;
      t.row.classList.toggle('is-off',!t.check.checked);
      t.row.querySelector('.live-start').textContent = clock(Number(t.slider.value));
      t.row.querySelector('.live-end').textContent = `Ends ${clock(Number(t.slider.value)+t.duration)}`;
      t.row.querySelector('.live-task-solar').textContent = t.check.checked ? `${Math.round(100*solar[index]/(t.power*t.duration))}% solar` : 'Not selected';
    });
  }
  root.addEventListener('input',update);
  document.getElementById('reset-day').addEventListener('click',() => { tasks.forEach(t => {t.slider.value=t.initial; t.check.checked=t.check.defaultChecked;}); update(); });
  update();
})();
