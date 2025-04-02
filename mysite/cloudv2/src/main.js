import { createApp } from 'vue'
import { library } from '@fortawesome/fontawesome-svg-core'
import { fas } from '@fortawesome/free-solid-svg-icons'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import App from './App.vue'
import router from './router'
import PrimeVue from 'primevue/config'
import Aura from '@primevue/themes/aura'
import Material from '@primevue/themes/material'
import Lara from '@primevue/themes/lara'
import Nora from '@primevue/themes/nora'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Menubar from 'primevue/menubar'
import 'primevue/resources/themes/saga-blue/theme.css'; // Choose your preferred theme
import 'primevue/resources/primevue.min.css'; 
import 'primeicons/primeicons.css'; 
import 'primeflex/primeflex.css'; // If PrimeFlex is needed

import '@fortawesome/fontawesome-svg-core'
import '@fortawesome/free-brands-svg-icons'
import '@fortawesome/free-regular-svg-icons'
import '@fortawesome/free-solid-svg-icons'

library.add(fas)

const app = createApp(App)

app.use(PrimeVue)

app.use(router)


app.component('DataTable', DataTable)
app.component('Column', Column)
app.component('Menubar', Menubar)
app.component('fa', FontAwesomeIcon)

app.mount('#app')
