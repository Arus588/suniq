(() => {
  const appliance = document.getElementById('appliance');
  if (!appliance) return;
  appliance.addEventListener('change', () => {
    const option = appliance.selectedOptions[0];
    document.getElementById('power').value = option.dataset.power;
    document.getElementById('duration').value = option.dataset.duration;
  });
})();
