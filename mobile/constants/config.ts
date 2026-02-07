import Constants from "expo-constants";

const ENV = {
  dev: {
    apiUrl: "http://192.168.1.164:8000/api/v1",
  },
  staging: {
    apiUrl: "https://staging-api.alice.example.com/api/v1",
  },
  prod: {
    apiUrl: "https://api.alice.example.com/api/v1",
  },
};

const getEnvVars = () => {
  // Hier kann man später auf Constants.expoConfig?.extra oder process.env zugreifen
  // Für jetzt nutzen wir dev
  return ENV.dev;
};

export default getEnvVars();
