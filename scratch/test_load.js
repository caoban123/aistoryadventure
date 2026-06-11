// Mock DOM environment for Node.js testing
const fs = require('fs');
const path = require('path');

const mockElement = (id) => ({
  id: id || '',
  classList: {
    add: () => {},
    remove: () => {},
    contains: () => false,
    toggle: () => {}
  },
  addEventListener: () => {},
  setAttribute: () => {},
  removeAttribute: () => {},
  style: {},
  querySelectorAll: () => [],
  querySelector: () => null,
  dataset: {},
  appendChild: () => {},
  removeChild: () => {},
  value: '',
  textContent: '',
  innerHTML: ''
});

global.window = {
  API_BASE: '/api',
  ALL_PAGES: [],
  location: { href: 'http://localhost/' }
};
global.document = {
  getElementById: (id) => mockElement(id),
  querySelectorAll: (selector) => [],
  querySelector: (selector) => mockElement(),
  createElement: (tag) => mockElement(),
  addEventListener: () => {}, // Mock document.addEventListener
  body: {
    appendChild: () => {},
    removeChild: () => {}
  },
  documentElement: {
    scrollLeft: 0,
    scrollTop: 0,
    clientLeft: 0,
    clientTop: 0
  }
};
global.localStorage = {
  getItem: () => null,
  setItem: () => {}
};
global.fetch = () => Promise.resolve({
  ok: true,
  headers: { get: () => 'application/json' },
  json: () => Promise.resolve({})
});

// Run the script
try {
  const code = fs.readFileSync(path.join(__dirname, '../frontend/rpg_app.js'), 'utf8');
  // Evaluate the code
  eval(code);
  console.log("SUCCESS: rpg_app.js loaded without runtime errors!");
} catch (e) {
  console.error("FAILURE: Error when loading rpg_app.js:");
  console.error(e);
}
