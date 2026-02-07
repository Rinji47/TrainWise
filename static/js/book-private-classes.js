let selectedClassId = null
let selectedClassName = null

function filterClasses() {
  const trainer = document.getElementById("trainerFilter").value
  const date = document.getElementById("dateFilter").value
  const capacity = document.getElementById("capacityFilter").value

  const params = new URLSearchParams()
  if (trainer) params.append("trainer", trainer)
  if (date) params.append("date", date)
  if (capacity) params.append("capacity", capacity)

  if (params.toString()) {
    window.location.search = params.toString()
  }
}

function resetFilters() {
  document.getElementById("trainerFilter").value = ""
  document.getElementById("dateFilter").value = ""
  document.getElementById("capacityFilter").value = ""
  window.location.search = ""
}

function bookClass(classId, className) {
  selectedClassId = classId
  selectedClassName = className
  const modal = document.getElementById("bookingModal")
  const bookingDetails = document.getElementById("bookingDetails")

  const classCard = document.querySelector(`[data-class-id="${classId}"]`)
  const trainerText = classCard.querySelector("strong").parentElement.textContent
  const dateTimeText = classCard.querySelectorAll("p")[1].textContent
  const capacityText = classCard.querySelectorAll("p")[2].textContent

  bookingDetails.innerHTML = `
    <div class="booking-details-content">
      <p><strong>Class:</strong> ${selectedClassName}</p>
      <p>${dateTimeText}</p>
      <p>${trainerText}</p>
      <p>${capacityText}</p>
      <p style="color: var(--success); font-weight: 600;">Booking confirmation will be sent to your email</p>
    </div>
  `
  modal.style.display = "flex"
}

function closeBookingModal() {
  document.getElementById("bookingModal").style.display = "none"
}

function confirmBooking() {
  if (selectedClassId) {
    const form = document.querySelector(`form[data-class-id="${selectedClassId}"]`)
    if (form) form.submit()
  }
}

window.addEventListener("click", (e) => {
  const modal = document.getElementById("bookingModal")
  if (e.target === modal) closeBookingModal()
})
