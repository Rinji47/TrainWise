document.addEventListener('DOMContentLoaded', () => {
  if (!window.jQuery || !jQuery.fn || !jQuery.fn.DataTable) {
    return;
  }

  const selector = '.dashboard-container table.admin-table, .dashboard-container table.history-table, .dashboard-container table.js-datatable';
  const tables = document.querySelectorAll(selector);

  tables.forEach((table) => {
    if (table.dataset.datatableInit === 'true') {
      return;
    }

    const headerCells = table.querySelectorAll('thead th');
    const columnCount = headerCells.length;
    const visibleCount = Math.max(1, parseInt(table.dataset.dtVisible || '4', 10));

    const visibleTargets = [];
    const hiddenTargets = [];

    for (let i = 0; i < columnCount; i += 1) {
      if (i < visibleCount) {
        visibleTargets.push(i);
      } else {
        hiddenTargets.push(i);
      }
    }

    const paging = table.dataset.dtPaging !== 'false';
    const lengthChange = table.dataset.dtLength !== 'false';
    const searching = table.dataset.dtSearch !== 'false';

    jQuery(table).DataTable({
      pageLength: 10,
      lengthMenu: [5, 10, 25, 50],
      paging,
      lengthChange,
      searching,
      ordering: true,
      responsive: {
        details: {
          type: 'inline',
          target: 'tr'
        }
      },
      autoWidth: false,
      columnDefs: [
        { targets: visibleTargets, className: 'all' },
        { targets: hiddenTargets, className: 'none' }
      ],
      language: {
        search: 'Search:',
        lengthMenu: 'Show _MENU_',
        info: 'Showing _START_ to _END_ of _TOTAL_',
        infoEmpty: 'Showing 0 to 0 of 0',
        emptyTable: 'No data available',
        paginate: {
          previous: 'Prev',
          next: 'Next'
        }
      }
    });

    table.dataset.datatableInit = 'true';
  });
});
