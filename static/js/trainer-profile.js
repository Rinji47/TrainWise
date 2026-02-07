// Form submission handlers for profile update
document.addEventListener("DOMContentLoaded", () => {
  const profileForm = document.querySelector('form[action*="update-trainer-profile"]')
  const passwordForm = document.querySelector('form[action*="change-password"]')

  if (profileForm) {
    profileForm.addEventListener("submit", function (e) {
      // Add any client-side validation here
      const fullName = this.querySelector('input[name="full_name"]').value
      const specialization = this.querySelector('input[name="specialization"]').value

      if (!fullName || !specialization) {
        e.preventDefault()
        alert("Please fill in all required fields")
      }
    })
  }

  if (passwordForm) {
    passwordForm.addEventListener("submit", function (e) {
      const newPassword = this.querySelector('input[name="new_password"]').value
      const confirmPassword = this.querySelector('input[name="confirm_password"]').value

      if (newPassword !== confirmPassword) {
        e.preventDefault()
        alert("Passwords do not match")
      }

      if (newPassword.length < 6) {
        e.preventDefault()
        alert("Password must be at least 6 characters")
      }
    })
  }
})
