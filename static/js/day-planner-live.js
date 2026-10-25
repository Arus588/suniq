(() => {
  const root = document.getElementById('live-appliances');
  if (!root) return;
  const forecast = JSON.parse(document.getElementById('day-forecast').textContent);
  const dailySolar = forecast.reduce((sum, slot) => sum + Math.max(0, slot.solar_kw-slot.home_kw)*.5, 0);
  const tasks = [...root.querySelectorAll('.live-appliance')].map(row => ({
    row, check: row.querySelector('input[type=checkbox]'), slider: row.querySelector('input[type=range]'),
    power: Number(row.dataset.power), duration: Number(row.dataset.duration),
    initial: row.querySelector('input[type=range]').value
  }));
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
