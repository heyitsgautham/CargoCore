// Node 25+ ships its own localStorage and sessionStorage globals, which shadow jsdom's
// and are undefined unless Node gets a storage file. Point both back at jsdom's storage.
for (const name of ['localStorage', 'sessionStorage']) {
  if (typeof globalThis[name]?.clear !== 'function' && globalThis.jsdom) {
    Object.defineProperty(globalThis, name, {
      value: globalThis.jsdom.window[name],
      configurable: true,
      writable: true,
    })
  }
}
