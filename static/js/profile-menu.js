(() => {
 document.querySelectorAll('.profile-menu').forEach(menu => {
  menu.addEventListener('mouseenter',() => { menu.open=true; });
  menu.addEventListener('mouseleave',() => { if (!menu.contains(document.activeElement)) menu.open=false; });
  menu.addEventListener('keydown',event => { if (event.key==='Escape') {menu.open=false;menu.querySelector('summary').focus();} });
  document.addEventListener('click',event => {if (!menu.contains(event.target)) menu.open=false;});
 });
})();
