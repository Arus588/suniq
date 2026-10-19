(() => {
  const button = document.getElementById('choose-gmail');
  const accounts = document.getElementById('gmail-accounts');
  if (!button || !accounts) return;
  button.addEventListener('click', () => {
    accounts.hidden = false;
    button.hidden = true;
    accounts.querySelector('button').focus();
  });
})();
