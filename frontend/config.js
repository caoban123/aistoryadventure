(function () {
  const isLocal = !window.location.hostname.endsWith("aistoryadventure.xyz");
  window.AI_STORY_CONFIG = {
    API_BASE: isLocal ? "http://172.27.117.104:8002" : "https://api.aistoryadventure.xyz",
    BYPASS_FIREBASE: isLocal && localStorage.getItem("use_firebase_local") !== "true",
  };
})();