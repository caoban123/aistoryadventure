(function () {
  const isLocal = !window.location.hostname.endsWith("aistoryadventure.xyz");
  window.AI_STORY_CONFIG = {
    API_BASE: isLocal ? "http://127.0.0.1:8002" : "https://api.aistoryadventure.xyz",
  };
})();