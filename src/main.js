import { createApp } from 'vue';
import { createPinia } from 'pinia';
import { MotionPlugin } from '@vueuse/motion';
import vue3GoogleLogin from 'vue3-google-login';
import App from './App.vue';
import router from './router';
import './styles/index.css';
import { initializeTheme } from './utils/theme';

initializeTheme();

const app = createApp(App);
const pinia = createPinia();
const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';

app.use(pinia);
app.use(router);
app.use(MotionPlugin);
app.use(vue3GoogleLogin, {
  clientId: googleClientId,
});

app.mount('#root');
