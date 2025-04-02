<template>
  <div class="main">
    <h1>Marketing calls</h1>
    <DataTable :value="items" paginator :rows="25" :rowsPerPageOptions="[5, 10, 20, 50]" tableStyle="min-width: 50rem">
        <Column field="account_name" header="Account Name" sortable ></Column>
        <Column field="call_date" header="Call Date"></Column>
        <Column field="salesforce_account_id" header="Salesforce Account ID"></Column>
        <Column field="campaign_code" header="Campaing Code" sortable ></Column>
        <Column field="phone_source" header="Phone Source"></Column>
        <Column field="number_called_name" header="Number Called"></Column>
        <Column field="keyword" header="Keyword"></Column>
    </DataTable>
  </div>
</template>

<script>
import fetcher from "../fetcher"

export default {
    name: 'MarketingCalls',
    data() {
        return {
            items: [],
            callLogs: []
        }
    },
    created() {
        this.getItems2();
    },
    methods: {
        async getItems2() {
            this.items = [];
            this.items = await fetcher('http://localhost:8000/api/MarketingTracker/')
        }
    }
}
</script>

<style scoped>
/* Main container styling */
.main {
  text-align: center;
  padding: 20px;
}

h1 {
  font-family: 'Roboto', sans-serif;
  color: #304c7a;
  font-weight: 500;
  margin-bottom: 20px;
}

/* DataTable Styling */
.modern-table {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); /* Add shadow for depth */
}

/* Header Styling */
.p-datatable-thead > tr > th {
  background-color: #304c7a; /* Darker blue header background */
  color: #fff; /* White text for contrast */
  font-weight: bold;
  font-family: 'Roboto', sans-serif;
  font-size: 16px;
  padding: 12px 10px;
  text-align: left;
}

/* Table Body Styling */
.p-datatable-tbody > tr > td {
  font-family: 'Roboto', sans-serif;
  color: #333; /* Darker text for better readability */
  padding: 12px 10px;
  border-bottom: 1px solid #ddd; /* Light border between rows */
  background-color: #fff; /* White background for rows */
}

.p-datatable-tbody > tr:hover {
  background-color: #f4f5f7; /* Light background on hover */
  cursor: pointer;
  transition: background-color 0.3s ease; /* Smooth transition on hover */
}

/* General Table Container Styling */
.p-datatable-table-container {
  border-radius: 12px;
  overflow-x: auto;
}

/* Mobile Responsiveness */
@media (max-width: 768px) {
  .modern-table {
    font-size: 14px; /* Smaller font on mobile */
  }
  .p-datatable-tbody > tr > td, 
  .p-datatable-thead > tr > th {
    padding: 8px; /* Less padding for smaller screens */
  }
}
</style>