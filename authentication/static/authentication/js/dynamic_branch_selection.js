document.addEventListener('DOMContentLoaded', function () {
  function loadBranches() {
    const companySelect = document.getElementById('id_company');
    const branchSelect = document.getElementById('id_branch');
    const companyId = companySelect.value;

    while (branchSelect.options.length > 1) {
      branchSelect.remove(1);
    }

    if (companyId) {
      const xhr = new XMLHttpRequest();
      xhr.open('GET', `/admin/authentication/user/load_branches/?company_id=${companyId}`, true);
      xhr.setRequestHeader('Content-Type', 'application/json');
      xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');

      xhr.onload = function () {
        if (xhr.status === 200) {
          const data = JSON.parse(xhr.responseText);

          data.forEach(function (branch) {
            const option = document.createElement('option');
            option.value = branch.id;
            option.textContent = branch.branch_name;
            branchSelect.appendChild(option);
          });

          // If there's a previously selected branch value, try to restore it
          const savedBranchId = branchSelect.getAttribute('data-saved-value');
          if (savedBranchId) {
            branchSelect.value = savedBranchId;
          }
        } else {
          console.error('Request failed.  Returned status of ' + xhr.status);
        }
      };

      xhr.onerror = function () {
        console.error('Request failed. Network error.');
      };

      xhr.send();
    }
  }


  const companySelect = document.getElementById('id_company');
  const branchSelect = document.getElementById('id_branch');

  // Save the initial branch value if it exists (for edit forms)
  if (branchSelect && branchSelect.value) {
    branchSelect.setAttribute('data-saved-value', branchSelect.value);
  }

  if (companySelect) {
    companySelect.addEventListener('change', loadBranches);

    // Load branches on page load if company is already selected
    if (companySelect.value) {
      loadBranches();
    }
  }

  console.log('Vanilla JS dynamic branch selection loaded');
  console.log('Company field present:', !!companySelect);
  console.log('Branch field present:', !!branchSelect);
  if (companySelect) console.log('Initial company value:', companySelect.value);
});