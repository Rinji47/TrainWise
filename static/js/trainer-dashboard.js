// Mark attendance for a class
function markAttendance(classId) {
  window.location.href = `/trainer/attendance/${classId}/mark/`
}

// Edit attendance record
function editAttendance(attendanceId) {
  window.location.href = `/trainer/attendance/${attendanceId}/edit/`
}

// Submit attendance bulk
function submitBulkAttendance(classId) {
  const form = document.querySelector(`form[data-class="${classId}"]`)
  if (form) {
    form.submit()
  } else {
    alert("Form not found")
  }
}

// Helper to get CSRF token
function getCookie(name) {
  let cookieValue = null
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";")
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim()
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
        break
      }
    }
  }
  return cookieValue
}

// Load trainer dashboard
document.addEventListener("DOMContentLoaded", () => {
  // No console log for now
})
