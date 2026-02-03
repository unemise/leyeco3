document.addEventListener('DOMContentLoaded', function() {
  // Default map centered on Philippines
  const DEFAULT_CENTER = [12.8797, 121.7740];
  const DEFAULT_ZOOM = 7;

  // Auto-zoom behavior when we have markers:
  // - avoid TOO ZOOMED OUT (min)
  // - avoid TOO ZOOMED IN / too tight on coordinates (max)
  const MIN_AUTO_ZOOM = 10;
  const MAX_AUTO_ZOOM = 25;

  // Remember last view (frontend-only UX improvement)
  const VIEW_KEY = 'leyeco.mapView.v1';
  function loadSavedView() {
    try {
      const raw = localStorage.getItem(VIEW_KEY);
      if (!raw) return null;
      const v = JSON.parse(raw);
      if (!v || !Array.isArray(v.center) || typeof v.zoom !== 'number') return null;
      if (typeof v.center[0] !== 'number' || typeof v.center[1] !== 'number') return null;
      return v;
    } catch {
      return null;
    }
  }
  function saveView(map) {
    try {
      const c = map.getCenter();
      localStorage.setItem(VIEW_KEY, JSON.stringify({ center: [c.lat, c.lng], zoom: map.getZoom() }));
    } catch {
      // ignore (private mode / disabled storage)
    }
  }

  const saved = loadSavedView();
  const map = L.map('map').setView(saved?.center || DEFAULT_CENTER, saved?.zoom || DEFAULT_ZOOM);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors'
  }).addTo(map);

  // Rotation wrapper to allow visual rotation (tiles & overlays) without rotating controls
  const mapContainer = document.getElementById('map');
  const mapPane = map.getPane('mapPane');
  const rotateWrap = document.createElement('div');
  rotateWrap.className = 'rotate-wrapper';
  mapContainer.insertBefore(rotateWrap, mapPane);
  rotateWrap.appendChild(mapPane);
  let rotation = 0;
  function setMapRotation(deg) {
    rotation = ((deg % 360) + 360) % 360;
    rotateWrap.style.transform = `rotate(${rotation}deg)`;
  }
  function rotateBy(delta) { setMapRotation(rotation + delta); }

  // Rotate control: left/right/reset and slider
  const RotateControl = L.Control.extend({
    options: { position: 'topleft' },
    onAdd: function() {
      const container = L.DomUtil.create('div', 'leaflet-bar rotate-control');
      container.innerHTML = `
        <button id="rot-left" title="Rotate left 15°">◀</button>
        <input id="rot-range" type="range" min="0" max="360" step="1" value="0" style="width:80px; vertical-align:middle;">
        <button id="rot-right" title="Rotate right 15°">▶</button>
        <button id="rot-reset" title="Reset rotation">↺</button>
      `;
      L.DomEvent.disableClickPropagation(container);
      setTimeout(() => {
        const left = container.querySelector('#rot-left');
        const right = container.querySelector('#rot-right');
        const reset = container.querySelector('#rot-reset');
        const range = container.querySelector('#rot-range');
        left.addEventListener('click', () => { rotateBy(-15); range.value = rotation; });
        right.addEventListener('click', () => { rotateBy(15); range.value = rotation; });
        reset.addEventListener('click', () => { setMapRotation(0); range.value = rotation; });
        range.addEventListener('input', (e) => setMapRotation(parseInt(e.target.value, 10)));
      }, 0);
      return container;
    }
  });
  map.addControl(new RotateControl());

  const postsLayer = L.layerGroup();
  const latlongLayer = L.layerGroup();
  const bounds = L.latLngBounds();

  const overlays = {
    'Posts (canonical)': postsLayer,
    'LatLongData (raw)': latlongLayer
  };
  L.control.layers(null, overlays, { collapsed: false }).addTo(map);

  // Helper to add markers to a layer
  const STATUS_COLORS = {
    // You can tweak these to match your branding
    active: '#dc2626',       // red-600
    maintenance: '#ef4444',  // red-500
    inactive: '#991b1b',     // red-800
  };

  function normalizeStatus(status) {
    const s = String(status || '').trim().toLowerCase();
    if (s === 'active' || s === 'maintenance' || s === 'inactive') return s;
    return 'inactive';
  }

  function createPostIcon(p) {
    const s = normalizeStatus(p.status);
    const color = STATUS_COLORS[s] || STATUS_COLORS.inactive;
    const id = p.id ?? '';
    return L.divIcon({
      className: 'custom-pin',
      html: `
        <div class="pin-wrap">
          <div class="pin-label">ID ${id}</div>
          <svg class="pin-svg" viewBox="0 0 24 36" aria-hidden="true">
            <!-- pin body -->
            <path d="M12 35c7-10 10-15.2 10-20.2C22 7.7 17.5 3 12 3S2 7.7 2 14.8C2 19.8 5 25 12 35z" fill="${color}"></path>
            <!-- white ring + center highlight -->
            <circle class="pin-ring" cx="12" cy="14" r="6.2" fill="none"></circle>
            <circle class="pin-center" cx="12" cy="14" r="2.1"></circle>
          </svg>
        </div>
      `,
      iconSize: [18, 28],
      iconAnchor: [9, 28],     // bottom-center of pin
      popupAnchor: [0, -24],
    });
  }

  function addPostMarker(layer, p) {
    const lat = parseFloat(p.lat);
    const lng = parseFloat(p.lng);
    if (Number.isNaN(lat) || Number.isNaN(lng)) return;
    const marker = L.marker([lat, lng], { title: p.name || `Post ${p.id}`, icon: createPostIcon(p) })
      .bindPopup(`<strong>${p.name || 'Post ' + p.id}</strong><br>Status: ${p.status || 'N/A'}<br>Coordinates: ${lat.toFixed(6)}, ${lng.toFixed(6)}<br>ID: ${p.id}`);
    marker.bindTooltip(`ID: ${p.id}`, { permanent: false, direction: 'top' });
    marker.addTo(layer);
    bounds.extend([lat, lng]);
    return marker;
  }

  function addLatLongMarker(layer, r) {
    const lat = parseFloat(r.lat);
    const lng = parseFloat(r.lng);
    if (Number.isNaN(lat) || Number.isNaN(lng)) return;
    // Keep raw layer visually lighter than canonical posts
    const circle = L.circleMarker([lat, lng], { radius: 5, color: '#0ea5e9', weight: 2, fillColor: '#0ea5e9', fillOpacity: 0.18 })
      .bindPopup(`<strong>Raw: ${r.post_id}</strong><br>Coordinates: ${lat.toFixed(6)}, ${lng.toFixed(6)}`);
    circle.addTo(layer);
    bounds.extend([lat, lng]);
    return circle;
  }

  // Load canonical posts (filtered to PH)
  fetch('/api/posts?in_ph=1')
    .then(r => r.json())
    .then(posts => {
      posts.forEach(p => addPostMarker(postsLayer, p));
      // Add postsLayer to map by default
      postsLayer.addTo(map);
      // Fit map if we added markers
      // Only auto-fit if the user doesn't have a saved view yet
      if (!saved && !bounds.isEmpty()) {
        // A bit more padding so it doesn't feel "too focused on coordinates"
        map.fitBounds(bounds.pad(0.18), { maxZoom: MAX_AUTO_ZOOM });
        if (map.getZoom() < MIN_AUTO_ZOOM) map.setZoom(MIN_AUTO_ZOOM);
      }
    })
    .catch(err => console.error('Failed to load posts', err));

  // Load raw latlongdata layer
  fetch('/api/latlongdata')
    .then(r => r.json())
    .then(rows => {
      if (!rows || rows.length === 0) return;
      rows.forEach(r => addLatLongMarker(latlongLayer, r));
      // Do not add latlongLayer by default; user can toggle it on via control
    })
    .catch(err => console.error('Failed to load latlongdata', err));

  // Scale pins based on zoom (small when zoomed out, bigger when zoomed in)
  const mapElForScale = document.getElementById('map');
  function updatePinScale() {
    if (!mapElForScale) return;
    const z = map.getZoom();
    // Tuned for zoom 6..18. Clamp keeps it clean.
    const scale = Math.max(0.55, Math.min(1.25, 0.55 + (z - 6) * 0.06));
    mapElForScale.style.setProperty('--pin-scale', String(scale));
  }
  updatePinScale();
  map.on('zoomend', updatePinScale);

  // Persist view when user navigates/zooms (so next open matches what they last used)
  map.on('moveend', () => saveView(map));
  map.on('zoomend', () => saveView(map));

});
