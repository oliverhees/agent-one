import Constants from "expo-constants";

const ENV = {
  dev: {
    apiUrl: "http://192.168.1.164:8000/api/v1",
  },
  staging: {
    apiUrl: "http://89.167.90.18:8000/api/v1",
  },
  prod: {
    apiUrl: "http://89.167.90.18:8000/api/v1",
  },
};

const getEnvVars = () => {
  if (__DEV__) {
    return ENV.dev;
  }
  return ENV.prod;
};

export default getEnvVars();
