import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.skdev.playroom',
  appName: 'Mirth',
  webDir: 'dist',
  server: {
    // For local dev, uncomment and set your machine's local IP:
    // url: 'http://192.168.x.x:5173',
    // cleartext: true,
  },
  android: {
    // Allow mixed content for development
    allowMixedContent: false,
  },
};

export default config;
