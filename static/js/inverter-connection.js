(() => {
  const form = document.getElementById('inverter-setup');
  const panel = document.getElementById('connection-progress');
  const bar = document.getElementById('connection-bar');
  const status = document.getElementById('connection-status');
  const percent = document.getElementById('connection-percent');
  if (!form || !panel) return;
  let busy = false;
  const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
  function update(value, message) {
    bar.value = value;
    percent.textContent = `${value}%`;
    status.textContent = message;
  }
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (busy) return;
    busy = true;
    const data = new FormData(form);
    const button = form.querySelector('button[type="submit"]');
    button.disabled = true;
    form.hidden = true;
    panel.hidden = false;
    panel.setAttribute('aria-busy', 'true');
    update(10, 'Preparing your workspace...');
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 15000);
      let response;
      try {
        response = await fetch(form.action, {
          method: 'POST', body: data, credentials: 'same-origin', signal: controller.signal
        });
      } finally {
        clearTimeout(timeout);
      }
      if (response.status === 400) {
        update(0, 'Select a provider and enter your inverter model and serial number.');
        panel.setAttribute('aria-busy', 'false');
        form.hidden = false;
        button.disabled = false;
        busy = false;
        return;
      }
      if (!response.ok) throw new Error('Unable to save inverter');
      const destination = new URL(response.url);
      if (!['/demo','/planner'].includes(destination.pathname)) {
        window.location.assign(destination.href);
        return;
      }
      // This walkthrough simulates a connection, not a provider API request.
      await pause(500);
      update(40, 'Setting up your inverter...');
      await pause(650);
      update(75, 'Loading energy overview...');
      await pause(650);
      update(100, 'Your workspace is ready.');
      panel.setAttribute('aria-busy', 'false');
      await pause(350);
      window.location.assign(destination.href);
    } catch (error) {
      panel.setAttribute('aria-busy', 'false');
      update(0, 'Connection could not be completed. Check your connection and try again.');
      form.hidden = false;
      button.disabled = false;
      busy = false;
    }
  });
})();
