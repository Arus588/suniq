(() => {
 const select=document.getElementById('run-appliance');
 if (!select) return;
 select.addEventListener('change',()=>{
  const data=select.selectedOptions[0].dataset;
  for(const key of ['power','duration','earliest']) document.getElementById('run-'+key).value=data[key];
  document.getElementById('run-start').value=data.start;
 });
})();
