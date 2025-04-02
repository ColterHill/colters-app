<template>
  <div class="home-container">
    <!-- Logo Section -->
    <header class="header">
      <img src="@/assets/ccc-logo.png" alt="Colter Codes Logo" class="logo">
      <h1>Colter Codes Development Consulting</h1>
      <p>Specializing in Django Python Projects and Salesforce Consulting</p>
    </header>

    <!-- Services Section -->
    <section class="services">
      <h2>Our Services</h2>
      <div class="service-grid">
        <div class="service-card">
          <h3>Django & Python Development</h3>
          <p>Expert backend development with Django and Python. Whether you need API integrations, custom web applications, or complex data-driven solutions, we can help.</p>
        </div>

        <div class="service-card">
          <h3>Salesforce Consulting</h3>
          <p>Maximize your business potential with Salesforce. We offer consulting for Salesforce setup, customization, and optimization to improve workflow and boost productivity.</p>
        </div>
      </div>
    </section>

    <!-- Contact Section -->
    <section class="contact">
      <h2>Get In Touch</h2>
      <p>If you're looking for expert help with Django Python development or Salesforce consulting, we'd love to hear from you!</p>
      <router-link to="/contact" class="contact-button">Contact Us</router-link>
    </section>
  </div>
</template>

<script>
export default {
  name: 'HomePage',
};
</script>

<style scoped>
/* General styling */
.home-container {
  text-align: center;
  padding: 20px;
  font-family: 'Roboto', sans-serif;
  background-color: #f4f5f7; /* Light gray Starfield color for the background */
}

/* Header styling */
.header {
  background-color: #304c7a; /* Deep Starfield blue for the header */
  color: #f4f5f7; /* Light gray text for contrast */
  padding: 40px 20px;
  border-radius: 10px;
  margin-bottom: 30px;
}

.header .logo {
  max-width: 200px;
  margin-bottom: 20px;
}

.header h1 {
  font-size: 32px;
  margin-bottom: 10px;
}

.header p {
  font-size: 18px;
}

/* Services section */
.services {
  padding: 40px 20px;
  background-color: #f4f5f7; /* Light background */
}

.services h2 {
  font-size: 28px;
  margin-bottom: 20px;
  color: #304c7a; /* Dark blue for headings */
}

.service-grid {
  display: flex;
  gap: 20px;
  justify-content: center;
}

.service-card {
  background-color: #c72138; /* Bold red background for service cards */
  padding: 20px;
  border-radius: 10px;
  width: 300px;
  box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  color: #f4f5f7; /* Light text for contrast */
}

.service-card:hover {
  transform: translateY(-5px);
  box-shadow: 0px 8px 16px rgba(0, 0, 0, 0.2);
}

.service-card h3 {
  color: #d7a64b; /* Golden highlight for headings */
  font-size: 22px;
  margin-bottom: 10px;
}

.service-card p {
  color: #f4f5f7;
  font-size: 16px;
}

/* Contact Section */
.contact {
  padding: 40px 20px;
  background-color: #304c7a; /* Deep blue background for the contact section */
  color: #f4f5f7;
  border-radius: 10px;
}

.contact h2 {
  font-size: 28px;
  margin-bottom: 20px;
}

.contact p {
  font-size: 18px;
  margin-bottom: 20px;
}

.contact-button {
  background-color: #e06236; /* Starfield orange for the button */
  color: white;
  padding: 12px 20px;
  border-radius: 5px;
  text-decoration: none;
  font-size: 18px;
  transition: background-color 0.3s ease;
}

.contact-button:hover {
  background-color: #d7a64b; /* Golden hover for button */
}

/* Media Queries for responsiveness */
@media (max-width: 768px) {
  .service-grid {
    flex-direction: column;
  }

  .service-card {
    width: 100%;
    margin-bottom: 20px;
  }
}
</style>