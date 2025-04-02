<template>
  <div class="side-navbar">
    <nav>
        <img src="@/assets/ccc-logo.png" alt="logo">
        <ul>
            <li><router-link to="/">Home</router-link></li>
            <li><router-link to="/about">About</router-link></li>
            <li><router-link to="/marketingcalls">Marketing Calls</router-link></li>
        </ul>
    </nav>
  </div>
</template>

<script>
export default {
    
}
</script>


<style scoped>
.side-navbar {
  background-color: #304c7a;
  color: white;
  padding: 15px;
  border-radius: 15px;
  box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1); /* Soft shadow for depth */
  transition: all 0.3s ease; /* Smooth transition for hover effects */
}

.side-navbar:hover {
  transform: translateY(-5px); /* Slight hover effect for the navbar */
}

nav {
  display: flex;
  align-items: center; /* Centers items vertically */
  justify-content: space-between; /* Space out the logo and links */
}

nav img {
  max-height: 80px; /* Slightly smaller, for a cleaner look */
  max-width: 80px;
  border-radius: 50%; /* Circular logo */
}

.side-navbar nav ul {
  list-style-type: none;
  display: flex;
  gap: 20px; /* Better spacing between items */
  margin: 0;
}

.side-navbar nav ul li {
  margin: 0;
}

.side-navbar nav ul li a {
  color: white;
  text-decoration: none;
  font-size: 16px;
  font-family: 'Roboto', sans-serif; /* Modern font */
  padding: 10px 15px;
  border-radius: 30px;
  transition: all 0.3s ease; /* Smooth hover transition */
}

.side-navbar nav ul li a:hover {
  background-color: #d7a64b;
  color: white;
  box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1); /* Soft shadow for hover */
  transform: translateY(-2px); /* Slight movement on hover */
}

@media (max-width: 768px) {
  .side-navbar nav ul {
    flex-direction: column;
    gap: 10px;
  }

  .side-navbar nav ul li a {
    font-size: 14px;
    padding: 8px 12px;
  }
}
</style>