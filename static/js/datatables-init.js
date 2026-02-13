const escapeRegex = (value) => value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

const normalizeCellText = (value) => {
  if (value === null || value === undefined) {
    return '';
  }

  const text = String(value);
  return text.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
};

const populateFilterOptions = (select, dataTable) => {
  const columnIndex = parseInt(select.dataset.dtColumn || '', 10);
  if (Number.isNaN(columnIndex)) {
    return;
  }

  const columnData = dataTable.column(columnIndex).data().toArray();
  const uniqueValues = new Set();

  columnData.forEach((value) => {
    const normalized = normalizeCellText(value);
    if (normalized) {
      uniqueValues.add(normalized);
    }
  });

  const existingValues = new Set([...select.options].map((option) => option.value));

  Array.from(uniqueValues)
    .sort((a, b) => a.localeCompare(b))
    .forEach((value) => {
      if (existingValues.has(value)) {
        return;
      }

      const option = document.createElement('option');
      option.value = value;
      option.textContent = value;
      select.appendChild(option);
    });
};

const bindTableFilters = (table, dataTable) => {
  const tableId = table.getAttribute('id');
  if (!tableId) {
    return;
  }

  const filterGroups = document.querySelectorAll(`[data-dt-target="${tableId}"]`);
  if (!filterGroups.length) {
    return;
  }

  filterGroups.forEach((group) => {
    const selects = group.querySelectorAll('[data-dt-filter]');

    selects.forEach((select) => {
      if (select.dataset.dtAutofill === 'true') {
        populateFilterOptions(select, dataTable);
      }

      select.addEventListener('change', () => {
        const columnIndex = parseInt(select.dataset.dtColumn || '', 10);
        if (Number.isNaN(columnIndex)) {
          return;
        }

        const value = select.value;
        if (!value) {
          dataTable.column(columnIndex).search('', true, false).draw();
          return;
        }

        dataTable
          .column(columnIndex)
          .search(`^${escapeRegex(value)}$`, true, false)
          .draw();
      });
    });
  });
};

document.addEventListener('DOMContentLoaded', () => {
  if (!window.jQuery || !jQuery.fn || !jQuery.fn.DataTable) {
    return;
  }

  const selector = 'table.admin-table, table.history-table, table.js-datatable';
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

    const dataTable = jQuery(table).DataTable({
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

    bindTableFilters(table, dataTable);

    table.dataset.datatableInit = 'true';
  });
});
