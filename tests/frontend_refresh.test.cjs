const assert = require('node:assert/strict');
const {readFileSync} = require('node:fs');
const {join} = require('node:path');
const {test} = require('node:test');
const {runInNewContext} = require('node:vm');

function harness() {
  let Panel, push, interval, timeout;
  const data = {rules: [], alerts: [], runtime: {}, history: [], settings: {}};
  const context = {
    HTMLElement: class {
      attachShadow() { this.shadowRoot = {activeElement: null}; }
      toggleAttribute() {}
    },
    customElements: {get() {}, define(_name, type) { Panel = type; }},
    setInterval(fn) { interval = fn; }, clearInterval() {},
    setTimeout(fn) { timeout = fn; }, clearTimeout() {},
    Date, Intl, navigator: {language: 'de'},
  };
  runInNewContext(readFileSync(join(__dirname,
    '../custom_components/nodarion_pager/frontend/nodarion-pager-panel.js'), 'utf8'), context);
  const panel = new Panel();
  let renders = 0;
  panel.renderLoading = () => {};
  panel.render = () => { renders++; };
  panel._hass = {
    callApi: async () => data,
    connection: {subscribeMessage: async fn => { push = fn; return () => {}; }},
  };
  panel._loaded = true;
  panel.connectedCallback();
  return {panel, load: () => panel.load(), push: value => push(value),
    poll: () => interval(), delayed: () => timeout(), renders: () => renders};
}

test('live updates keep the settings DOM, scroll position and unsaved values intact', async () => {
  const h = harness();
  await h.load();
  h.panel._view = 'settings';
  const form = h.panel.shadowRoot;
  form.scrollTop = 280;
  form.draft = {name: 'Ungespeichert', checked: true, color: '#abcdef'};
  const before = h.renders();
  h.push({runtime: {room: {last_value: 42}}});
  assert.equal(h.renders(), before);
  assert.equal(h.panel.shadowRoot, form);
  assert.equal(form.scrollTop, 280);
  assert.equal(form.draft.name, 'Ungespeichert');
  assert.equal(h.panel._data.runtime.room.last_value, 42);
  h.panel._view = 'dashboard';
  h.push({runtime: {}});
  assert.equal(h.renders(), before + 1);
});

test('a queued HA render rechecks the active view before replacing its DOM', async () => {
  const h = harness();
  await h.load();
  h.panel.hass = h.panel._hass;
  h.panel._view = 'settings';
  const before = h.renders();
  h.delayed();
  assert.equal(h.renders(), before);
});

test('an in-flight runtime request cannot redraw settings after navigation', async () => {
  const h = harness();
  await h.load();
  let resolve;
  h.panel._hass.callApi = () => new Promise(done => { resolve = done; });
  const request = h.poll();
  h.panel._view = 'settings';
  const before = h.renders();
  resolve({runtime: {updated: true}});
  await request;
  assert.equal(h.renders(), before);
  assert.equal(h.panel._data.runtime.updated, true);
});
