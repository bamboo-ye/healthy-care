import {defineConfig} from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig({plugins:[react()],build:{rollupOptions:{input:{user:'index.html',research:'research/index.html'}}},server:{proxy:{'/v1':'http://127.0.0.1:8781'}}});
