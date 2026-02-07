// Edit class
function editClass(classId) {
  window.location.href = `/trainer/classes/${classId}/edit/`
}

// Delete class with confirmation
function deleteClass(classId) {
  if (confirm("Are you sure you want to delete this class?")) {
    // Create form and submit for DELETE
    const form = document.createElement("form")
    form.method = "POST"
    form.action = `/trainer/classes/${classId}/delete/`

    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]")
    if (csrfToken) {
      form.appendChild(csrfToken.cloneNode(true))
    }

    document.body.appendChild(form)
    form.submit()
  }
}

// Close modal
function closeModal(modalId) {
  document.getElementById(modalId).style.display = "none"
}

// Filter classes
document.getElementById("classFilter")?.addEventListener("keyup", function () {
  const searchTerm = this.value.toLowerCase()
  const tableRows = document.querySelectorAll("#classesTableBody tr")

  tableRows.forEach((row) => {
    const text = row.textContent.toLowerCase()
    row.style.display = text.includes(searchTerm) ? "" : "none"
  })
})

// Modal click outside to close
window.onclick = (event) => {
  const modal = document.getElementById("createClassModal")
  if (event.target === modal) {
    modal.style.display = "none"
  }
}
