<template>
  <div class="map-container"
       @dragover.prevent="onDragOver"
       @dragleave="onDragLeave"
       @drop.prevent="onDrop"
       :class="{ 'drag-over': isDragging }">

    <!-- Zone de drop pour import -->
    <div v-if="isDragging" class="drop-zone">
      <div class="drop-zone-content">
        <svg class="drop-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12"/>
        </svg>
        <span class="drop-text">Glissez votre fichier GeoJSON ici</span>
      </div>
    </div>

    <!-- Barre d'outils principale - UI moderne et claire -->
    <div class="toolbar-main">
      <!-- Logo et titre -->
      <div class="toolbar-brand">
        <span class="brand-icon">🗺️</span>
        <span class="brand-title">SIG Web</span>
      </div>

      <!-- Sélecteur de projet -->
      <div class="toolbar-section toolbar-section-project">
        <span class="section-label">Projet</span>
        <div class="project-selector">
          <button @click="toggleProjectPanel" class="project-btn" :class="{ active: showProjectPanel }">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/>
            </svg>
            <span class="project-name">{{ mapStore.currentProject?.name || 'Sélectionner...' }}</span>
            <svg class="chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="6 9 12 15 18 9"/>
            </svg>
          </button>
        </div>
      </div>

      <!-- Groupe: Navigation et dessin -->
      <div class="toolbar-section">
        <span class="section-label">Outils</span>
        <div class="tool-buttons">
          <button
            @click="setToolMode('navigation')"
            :class="{ active: toolMode === 'navigation' }"
            class="tool-btn"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M5 9l7-7 7 7M12 2v20"/>
            </svg>
            <span class="tool-label">Naviguer</span>
          </button>
          <button
            @click="setToolMode('marker')"
            :class="{ active: toolMode === 'marker' }"
            class="tool-btn"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 1118 0z"/>
              <circle cx="12" cy="10" r="3"/>
            </svg>
            <span class="tool-label">Point</span>
          </button>
          <button
            @click="setToolMode('polyline')"
            :class="{ active: toolMode === 'polyline' }"
            class="tool-btn"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3,17 9,11 13,15 21,7"/>
            </svg>
            <span class="tool-label">Ligne</span>
          </button>
          <button
            @click="setToolMode('polygon')"
            :class="{ active: toolMode === 'polygon' }"
            class="tool-btn"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="12,2 22,8.5 22,15.5 12,22 2,15.5 2,8.5"/>
            </svg>
            <span class="tool-label">Zone</span>
          </button>
          <button
            @click="setToolMode('series')"
            :class="{ active: toolMode === 'series' }"
            class="tool-btn"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="8" cy="8" r="2"/><circle cx="16" cy="8" r="2"/>
              <circle cx="8" cy="16" r="2"/><circle cx="16" cy="16" r="2"/>
            </svg>
            <span class="tool-label">Série</span>
          </button>
        </div>
      </div>

      <!-- Groupe: Mesures -->
      <div class="toolbar-section">
        <span class="section-label">Mesures</span>
        <div class="tool-buttons">
          <button
            @click="setToolMode('measureDistance')"
            :class="{ active: toolMode === 'measureDistance' }"
            class="tool-btn"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M2 12h20M6 8v8M18 8v8M10 10v4M14 10v4"/>
            </svg>
            <span class="tool-label">Distance</span>
          </button>
          <button
            @click="setToolMode('measureArea')"
            :class="{ active: toolMode === 'measureArea' }"
            class="tool-btn"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="18" height="18" rx="2"/>
              <path d="M3 9h18M9 3v18"/>
            </svg>
            <span class="tool-label">Surface</span>
          </button>
          <button
            v-if="measurePoints.length > 0"
            @click="clearMeasure"
            class="tool-btn tool-btn-clear"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
            </svg>
            <span class="tool-label">Effacer</span>
          </button>
        </div>
      </div>

      <!-- Groupe: Édition -->
      <div class="toolbar-section">
        <span class="section-label">Édition</span>
        <div class="tool-buttons">
          <button
            @click="setToolMode('edit')"
            :class="{ active: toolMode === 'edit' }"
            class="tool-btn"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
            <span class="tool-label">Retouche</span>
          </button>
        </div>
      </div>

      <!-- Groupe: Fond de carte -->
      <div class="toolbar-section toolbar-section-map">
        <span class="section-label">Fond de carte</span>
        <div class="map-controls">
          <select v-model="selectedBaseLayer" @change="changeBaseLayer" class="base-layer-select">
            <optgroup label="IGN France (recommandé)">
              <option value="ign_plan">Plan IGN</option>
              <option value="ign_ortho">Photos aériennes</option>
              <option value="ign_cadastre">Cadastre parcellaire</option>
              <option value="ign_carte">Carte topographique</option>
              <option value="ign_ortho_histo">Photos 1950-65</option>
            </optgroup>
            <optgroup label="Cartes internationales">
              <option value="osm">OpenStreetMap</option>
              <option value="osm_france">OSM France</option>
              <option value="satellite">Satellite mondial</option>
              <option value="topo">Relief/Topo</option>
            </optgroup>
          </select>
          <label class="cadastre-overlay" title="Superposer les parcelles cadastrales">
            <input type="checkbox" v-model="showCadastre" @change="toggleCadastre">
            <span class="overlay-label">+ Cadastre</span>
          </label>
        </div>
      </div>

      <!-- Groupe: Actions -->
      <div class="toolbar-section">
        <span class="section-label">Actions</span>
        <div class="tool-buttons">
          <button @click="zoomToData" class="tool-btn" title="Centrer sur vos données">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <circle cx="12" cy="12" r="3"/>
              <path d="M12 2v4M12 18v4M2 12h4M18 12h4"/>
            </svg>
            <span class="tool-label">Centrer</span>
          </button>
          <button @click="toggleLayerPanel" :class="{ active: showLayerPanel }" class="tool-btn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="12,2 2,7 12,12 22,7"/>
              <polyline points="2,17 12,22 22,17"/>
              <polyline points="2,12 12,17 22,12"/>
            </svg>
            <span class="tool-label">Couches</span>
          </button>
          <button @click="toggleStatsPanel" :class="{ active: showStatsPanel }" class="tool-btn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 20V10M12 20V4M6 20v-6"/>
            </svg>
            <span class="tool-label">Stats</span>
          </button>
          <button @click="togglePerimeterPanel" :class="{ active: showPerimeterPanel }" class="tool-btn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="18" height="18" rx="2" stroke-dasharray="4 2"/>
              <path d="M9 12h6M12 9v6"/>
            </svg>
            <span class="tool-label">Zones</span>
          </button>
          <button @click="exportData" class="tool-btn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/>
            </svg>
            <span class="tool-label">Export</span>
          </button>
          <button @click="showHelp = true" class="tool-btn tool-btn-help">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3M12 17h.01"/>
            </svg>
            <span class="tool-label">Aide</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Barre de mesure améliorée -->
    <div v-if="(toolMode === 'measureDistance' || toolMode === 'measureArea') && measurePoints.length > 0" class="measure-bar">
      <div class="measure-result">
        <span class="measure-icon">
          <svg v-if="toolMode === 'measureDistance'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M2 12h20M6 8v8M18 8v8"/>
          </svg>
          <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2"/>
          </svg>
        </span>
        <span v-if="toolMode === 'measureDistance'" class="measure-value">
          {{ formatDistance(totalDistance) }}
        </span>
        <span v-else-if="measurePoints.length >= 3" class="measure-value">
          {{ formatArea(totalArea) }}
        </span>
      </div>
      <div class="measure-hint">
        <span v-if="toolMode === 'measureDistance'">
          Cliquez pour ajouter des points • Échap pour terminer
        </span>
        <span v-else>
          Cliquez pour tracer la zone à mesurer
        </span>
      </div>
    </div>

    <!-- Indicateur de mode actif (flottant en bas) -->
    <div v-if="toolMode && toolMode !== 'navigation'" class="mode-indicator">
      <div class="mode-content">
        <span class="mode-icon-wrapper" :style="{ backgroundColor: getModeColor(toolMode) }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path :d="getModeIconPath(toolMode)"/>
          </svg>
        </span>
        <div class="mode-info">
          <span class="mode-title">{{ getModeLabel(toolMode) }}</span>
          <span class="mode-hint">{{ getModeHint(toolMode) }}</span>
        </div>
      </div>
      <button @click="setToolMode('navigation')" class="mode-cancel" title="Annuler (Échap)">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M18 6L6 18M6 6l12 12"/>
        </svg>
      </button>
    </div>

    <!-- Panneau des couches amélioré -->
    <div v-if="showLayerPanel" class="layer-panel">
      <div class="panel-header">
        <svg class="panel-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polygon points="12,2 2,7 12,12 22,7"/>
          <polyline points="2,17 12,22 22,17"/>
          <polyline points="2,12 12,17 22,12"/>
        </svg>
        <h3>Mes couches</h3>
        <button @click="showLayerPanel = false" class="panel-close">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 6L6 18M6 6l12 12"/>
          </svg>
        </button>
      </div>
      <div class="panel-body">
        <div v-if="mapStore.layers.length > 0" class="layers-list">
          <div v-for="layer in mapStore.layers" :key="layer.id" class="layer-item" :class="{ 'layer-hidden': !layer.visible }">
            <div class="layer-visibility">
              <input
                type="checkbox"
                :id="'layer-' + layer.id"
                :checked="layer.visible"
                @change="toggleLayer(layer)"
                class="layer-checkbox"
              >
              <label :for="'layer-' + layer.id" class="layer-toggle">
                <svg v-if="layer.visible" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                  <circle cx="12" cy="12" r="3"/>
                </svg>
                <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24M1 1l22 22"/>
                </svg>
              </label>
            </div>
            <span v-if="layer.icon" class="layer-icon-mdi" :style="{ color: layer.color }">
              <i :class="'mdi ' + layer.icon"></i>
            </span>
            <span v-else class="layer-color" :style="{ backgroundColor: layer.color }"></span>
            <span class="layer-name">{{ layer.name }}</span>
            <span class="layer-badge">{{ layer.data?.features?.length || 0 }}</span>
          </div>
        </div>
        <div v-else class="layers-empty">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <polygon points="12,2 2,7 12,12 22,7"/>
            <polyline points="2,17 12,22 22,17"/>
            <polyline points="2,12 12,17 22,12"/>
          </svg>
          <p>Aucune couche</p>
          <span>Importez un fichier GeoJSON ou créez des éléments</span>
        </div>
      </div>
      <div class="panel-footer">
        <button @click="triggerImport" class="btn-secondary">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12"/>
          </svg>
          Importer GeoJSON
        </button>
      </div>
    </div>

    <!-- Panneau de sélection de projet -->
    <div v-if="showProjectPanel" class="project-panel">
      <div class="panel-header">
        <svg class="panel-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/>
        </svg>
        <h3>Mes projets</h3>
        <button @click="showProjectPanel = false" class="panel-close">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 6L6 18M6 6l12 12"/>
          </svg>
        </button>
      </div>
      <div class="panel-body">
        <div v-if="mapStore.projects.length > 0" class="projects-list">
          <div
            v-for="project in mapStore.projects"
            :key="project.id"
            class="project-item"
            :class="{ 'project-active': mapStore.currentProject?.id === project.id }"
            @click="selectProject(project)"
          >
            <div class="project-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/>
              </svg>
            </div>
            <div class="project-info">
              <span class="project-item-name">{{ project.name }}</span>
              <span class="project-desc">{{ project.description || 'Aucune description' }}</span>
            </div>
            <div v-if="mapStore.currentProject?.id === project.id" class="project-check">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
            </div>
          </div>
        </div>
        <div v-else class="projects-empty">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/>
          </svg>
          <p>Aucun projet disponible</p>
          <span>Les projets sont gérés depuis GéoClic Data</span>
        </div>
      </div>
      <div class="panel-footer">
        <button @click="mapStore.loadProjects(); showToast('Projets actualisés', 'info')" class="btn-secondary">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="23 4 23 10 17 10"/>
            <polyline points="1 20 1 14 7 14"/>
            <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/>
          </svg>
          Actualiser
        </button>
      </div>
    </div>

    <!-- Panneau des périmètres/zones -->
    <div v-if="showPerimeterPanel" class="perimeter-panel">
      <div class="panel-header">
        <svg class="panel-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="3" width="18" height="18" rx="2" stroke-dasharray="4 2"/>
        </svg>
        <h3>Zones</h3>
        <button @click="showPerimeterPanel = false" class="panel-close">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 6L6 18M6 6l12 12"/>
          </svg>
        </button>
      </div>
      <div class="panel-body">
        <!-- Zones API (base de données) - Vue hiérarchique -->
        <div class="api-zones-section">
          <div class="section-header">
            <div class="section-title-row">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="section-icon">
                <circle cx="12" cy="12" r="10"/>
                <path d="M2 12h20M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z"/>
              </svg>
              <span class="section-title">Zones</span>
              <span class="section-count">({{ mapStore.apiZones.length }})</span>
            </div>
            <label class="toggle-switch" title="Afficher/masquer toutes les zones">
              <input type="checkbox" v-model="mapStore.apiZonesVisible" />
              <span class="toggle-slider"></span>
            </label>
          </div>

          <!-- Filtres par niveau -->
          <div class="level-filters">
            <button
              class="level-filter-btn"
              :class="{ active: mapStore.apiZonesLevelFilter === null }"
              @click="mapStore.setApiZonesLevelFilter(null)"
            >
              Tous
            </button>
            <button
              class="level-filter-btn level-1"
              :class="{ active: mapStore.apiZonesLevelFilter === 1 }"
              @click="mapStore.setApiZonesLevelFilter(1)"
              title="Communes"
            >
              <span class="level-icon">🏛️</span>
              <span class="level-count">{{ mapStore.apiZonesByLevel[1]?.length || 0 }}</span>
            </button>
            <button
              class="level-filter-btn level-2"
              :class="{ active: mapStore.apiZonesLevelFilter === 2 }"
              @click="mapStore.setApiZonesLevelFilter(2)"
              title="Quartiers"
            >
              <span class="level-icon">🏘️</span>
              <span class="level-count">{{ mapStore.apiZonesByLevel[2]?.length || 0 }}</span>
            </button>
            <button
              class="level-filter-btn level-3"
              :class="{ active: mapStore.apiZonesLevelFilter === 3 }"
              @click="mapStore.setApiZonesLevelFilter(3)"
              title="Secteurs"
            >
              <span class="level-icon">📍</span>
              <span class="level-count">{{ mapStore.apiZonesByLevel[3]?.length || 0 }}</span>
            </button>
          </div>

          <div v-if="mapStore.apiZonesLoading" class="loading-indicator">
            <svg class="spinner" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
            </svg>
            <span>Chargement...</span>
          </div>

          <!-- Liste hiérarchique des zones -->
          <div v-else-if="mapStore.apiZonesTree.length > 0" class="api-zones-list hierarchical">
            <template v-for="zone in mapStore.apiZonesTree" :key="zone.id">
              <!-- Zone de niveau 1 (Commune) -->
              <div
                class="api-zone-item level-1"
                :class="{ 'zone-hidden': !zone.visible }"
                v-if="!mapStore.apiZonesLevelFilter || mapStore.apiZonesLevelFilter === 1"
              >
                <button
                  v-if="zone.children && zone.children.length > 0"
                  class="expand-btn"
                  @click="mapStore.toggleZoneExpanded(zone.id)"
                >
                  {{ zone.expanded ? '▼' : '▶' }}
                </button>
                <span v-else class="expand-placeholder"></span>
                <div class="zone-color" :style="{ backgroundColor: zone.color }"></div>
                <div class="zone-info">
                  <span class="zone-name">{{ zone.name }}</span>
                  <span class="zone-level-badge level-1">Commune</span>
                </div>
                <input
                  type="checkbox"
                  :checked="zone.visible"
                  @change="mapStore.toggleApiZoneVisibility(zone.id)"
                  class="zone-checkbox"
                />
              </div>

              <!-- Enfants niveau 2 (Quartiers) -->
              <template v-if="zone.expanded && zone.children">
                <template v-for="child in zone.children" :key="child.id">
                  <div
                    class="api-zone-item level-2"
                    :class="{ 'zone-hidden': !child.visible }"
                    v-if="!mapStore.apiZonesLevelFilter || mapStore.apiZonesLevelFilter === 2"
                  >
                    <button
                      v-if="child.children && child.children.length > 0"
                      class="expand-btn"
                      @click="mapStore.toggleZoneExpanded(child.id)"
                    >
                      {{ child.expanded ? '▼' : '▶' }}
                    </button>
                    <span v-else class="expand-placeholder"></span>
                    <div class="zone-color" :style="{ backgroundColor: child.color }"></div>
                    <div class="zone-info">
                      <span class="zone-name">{{ child.name }}</span>
                      <span class="zone-level-badge level-2">Quartier</span>
                    </div>
                    <input
                      type="checkbox"
                      :checked="child.visible"
                      @change="mapStore.toggleApiZoneVisibility(child.id)"
                      class="zone-checkbox"
                    />
                  </div>

                  <!-- Enfants niveau 3 (Secteurs) -->
                  <template v-if="child.expanded && child.children">
                    <div
                      v-for="subChild in child.children"
                      :key="subChild.id"
                      class="api-zone-item level-3"
                      :class="{ 'zone-hidden': !subChild.visible }"
                      v-show="!mapStore.apiZonesLevelFilter || mapStore.apiZonesLevelFilter === 3"
                    >
                      <span class="expand-placeholder"></span>
                      <div class="zone-color" :style="{ backgroundColor: subChild.color }"></div>
                      <div class="zone-info">
                        <span class="zone-name">{{ subChild.name }}</span>
                        <span class="zone-level-badge level-3">Secteur</span>
                      </div>
                      <input
                        type="checkbox"
                        :checked="subChild.visible"
                        @change="mapStore.toggleApiZoneVisibility(subChild.id)"
                        class="zone-checkbox"
                      />
                    </div>
                  </template>
                </template>
              </template>
            </template>

            <!-- Zones orphelines (sans parent) de niveau 2 ou 3 -->
            <template v-for="zone in mapStore.apiZones.filter(z => !z.parent_id && z.level > 1)" :key="'orphan-' + zone.id">
              <div
                class="api-zone-item"
                :class="[`level-${zone.level}`, { 'zone-hidden': !zone.visible }]"
                v-if="!mapStore.apiZonesLevelFilter || mapStore.apiZonesLevelFilter === zone.level"
              >
                <span class="expand-placeholder"></span>
                <div class="zone-color" :style="{ backgroundColor: zone.color }"></div>
                <div class="zone-info">
                  <span class="zone-name">{{ zone.name }}</span>
                  <span class="zone-level-badge" :class="`level-${zone.level}`">
                    {{ zone.level === 2 ? 'Quartier' : 'Secteur' }}
                  </span>
                </div>
                <input
                  type="checkbox"
                  :checked="zone.visible"
                  @change="mapStore.toggleApiZoneVisibility(zone.id)"
                  class="zone-checkbox"
                />
              </div>
            </template>
          </div>

          <div v-else class="api-zones-empty">
            <span>Aucune zone définie</span>
            <a href="/admin/#/zones" target="_blank" class="link-admin">Gérer dans Admin</a>
          </div>

          <div class="api-zones-actions">
            <button @click="mapStore.loadApiZones()" class="btn-refresh" title="Actualiser les zones">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="23 4 23 10 17 10"/>
                <polyline points="1 20 1 14 7 14"/>
                <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/>
              </svg>
            </button>
          </div>
        </div>

        <div class="section-divider"></div>

        <!-- Zones locales (session) -->
        <div class="local-zones-section">
          <div class="section-header">
            <div class="section-title-row">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="section-icon">
                <rect x="3" y="3" width="18" height="18" rx="2" stroke-dasharray="4 2"/>
              </svg>
              <span class="section-title">Zones locales</span>
              <span class="section-count">({{ perimeters.length }})</span>
            </div>
          </div>

        <!-- Mode dessin actif -->
        <div v-if="isDrawingPerimeter" class="perimeter-drawing-mode">
          <div class="drawing-info">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M12 16v-4M12 8h.01"/>
            </svg>
            <span>Cliquez sur la carte pour tracer les coins de la zone. Échap pour terminer.</span>
          </div>
          <div class="drawing-stats">
            <strong>{{ perimeterPoints.length }}</strong> points
          </div>
          <div class="drawing-actions">
            <button @click="cancelPerimeterDrawing" class="btn-secondary">Annuler</button>
            <button @click="finishPerimeter" :disabled="perimeterPoints.length < 3" class="btn-primary">
              Créer la zone
            </button>
          </div>
        </div>

        <!-- Liste des zones -->
        <div v-else>
          <div v-if="perimeters.length > 0" class="perimeters-list">
            <div
              v-for="perimeter in perimeters"
              :key="perimeter.id"
              class="perimeter-item"
              :class="{ 'perimeter-active': perimeter.active }"
            >
              <div class="perimeter-color" :style="{ backgroundColor: perimeter.color }"></div>
              <div class="perimeter-info" @click="togglePerimeterActive(perimeter)">
                <span class="perimeter-name">{{ perimeter.name }}</span>
                <span class="perimeter-status">{{ perimeter.active ? 'Actif' : 'Inactif' }}</span>
              </div>
              <div class="perimeter-actions">
                <button @click="renamePerimeter(perimeter)" class="perimeter-action-btn" title="Renommer">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
                    <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
                  </svg>
                </button>
                <button @click="deletePerimeter(perimeter)" class="perimeter-action-btn perimeter-action-delete" title="Supprimer">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>
          <div v-else class="perimeters-empty perimeters-empty-small">
            <p>Aucune zone locale</p>
          </div>
        </div>
        </div><!-- Fin local-zones-section -->
      </div>
      <div v-if="!isDrawingPerimeter" class="panel-footer">
        <button @click="startDrawingPerimeter" class="btn-primary btn-full">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 5v14M5 12h14"/>
          </svg>
          Nouvelle zone locale
        </button>
      </div>
    </div>

    <!-- Panneau statistiques -->
    <div v-if="showStatsPanel" class="stats-panel">
      <div class="panel-header">
        <svg class="panel-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M18 20V10M12 20V4M6 20v-6"/>
        </svg>
        <h3>Statistiques</h3>
        <button @click="showStatsPanel = false" class="panel-close">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 6L6 18M6 6l12 12"/>
          </svg>
        </button>
      </div>
      <div class="panel-body">
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon stat-icon-blue">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="12,2 2,7 12,12 22,7"/>
                <polyline points="2,17 12,22 22,17"/>
              </svg>
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ totalLayers }}</span>
              <span class="stat-label">Couches</span>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon stat-icon-green">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 1118 0z"/>
                <circle cx="12" cy="10" r="3"/>
              </svg>
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ totalPoints }}</span>
              <span class="stat-label">Points</span>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon stat-icon-orange">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3,17 9,11 13,15 21,7"/>
              </svg>
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ totalLines }}</span>
              <span class="stat-label">Lignes</span>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon stat-icon-purple">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="12,2 22,8.5 22,15.5 12,22 2,15.5 2,8.5"/>
              </svg>
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ totalPolygons }}</span>
              <span class="stat-label">Zones</span>
            </div>
          </div>
        </div>
        <div v-if="totalFeatures > 0" class="stats-summary">
          <strong>{{ totalFeatures }}</strong> éléments au total
        </div>
        <div v-else class="stats-empty">
          Aucune donnée à afficher
        </div>
      </div>
    </div>

    <!-- Carte Leaflet -->
    <div ref="mapContainer" class="leaflet-map"></div>

    <!-- Panneau de propriétés -->
    <div v-if="mapStore.selectedFeature" class="feature-panel">
      <div class="panel-header panel-header-primary">
        <svg class="panel-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <path d="M12 16v-4M12 8h.01"/>
        </svg>
        <h3>{{ mapStore.selectedFeature.properties?.name || 'Élément sélectionné' }}</h3>
        <button @click="mapStore.selectFeature(null)" class="panel-close">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 6L6 18M6 6l12 12"/>
          </svg>
        </button>
      </div>
      <div class="panel-body">
        <div v-if="mapStore.selectedFeature.geometry" class="feature-type-badge">
          {{ getGeometryLabel(mapStore.selectedFeature.geometry.type) }}
        </div>
        <div class="feature-properties">
          <div class="feature-property" v-for="prop in getDisplayProperties(mapStore.selectedFeature.properties)" :key="prop.key">
            <span class="property-key">{{ prop.label }}</span>
            <span class="property-value">{{ prop.value }}</span>
          </div>
          <div v-if="getDisplayProperties(mapStore.selectedFeature.properties).length === 0" class="no-properties">
            Aucune propriété définie
          </div>
        </div>
        <!-- Photos -->
        <div v-if="mapStore.selectedFeature.properties?.photos?.length" class="feature-photos">
          <h4 class="photos-title">Photos</h4>
          <div class="photos-grid">
            <a
              v-for="photo in mapStore.selectedFeature.properties.photos"
              :key="photo.id"
              :href="photo.url"
              target="_blank"
              class="photo-thumb"
            >
              <img :src="photo.thumbnail_url || photo.url" :alt="photo.filename" />
            </a>
          </div>
        </div>
      </div>
      <div class="panel-footer feature-actions">
        <button @click="zoomToFeature" class="btn-secondary">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <circle cx="12" cy="12" r="3"/>
          </svg>
          Centrer
        </button>
        <button @click="editFeature" class="btn-primary">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
            <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
          </svg>
          Modifier
        </button>
        <button @click="deleteFeature" class="btn-danger">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
          </svg>
          Supprimer
        </button>
      </div>
    </div>

    <!-- Aide contextuelle -->
    <div v-if="showHelp" class="help-modal" @click.self="showHelp = false">
      <div class="help-content">
        <div class="help-header">
          <h2>Guide rapide - SIG Web</h2>
          <button @click="showHelp = false" class="panel-close">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="help-body">
          <div class="help-section">
            <h3>Navigation</h3>
            <ul>
              <li><strong>Se déplacer</strong> : Cliquez-glissez sur la carte</li>
              <li><strong>Zoomer</strong> : Molette ou boutons +/-</li>
              <li><strong>Centrer</strong> : Cliquez sur le bouton "Centrer"</li>
            </ul>
          </div>
          <div class="help-section">
            <h3>Création d'éléments</h3>
            <ul>
              <li><strong>Point</strong> : Sélectionnez l'outil puis cliquez sur la carte</li>
              <li><strong>Ligne</strong> : Cliquez pour ajouter des points, Échap pour terminer</li>
              <li><strong>Zone</strong> : Tracez le contour, Échap pour fermer</li>
              <li><strong>Série</strong> : Ajoutez plusieurs points rapidement</li>
            </ul>
          </div>
          <div class="help-section">
            <h3>Mesures</h3>
            <ul>
              <li><strong>Distance</strong> : Cliquez pour tracer, Échap pour finir</li>
              <li><strong>Surface</strong> : Dessinez une zone fermée</li>
            </ul>
          </div>
          <div class="help-section">
            <h3>Import/Export</h3>
            <ul>
              <li><strong>Importer</strong> : Glissez-déposez un fichier GeoJSON sur la carte</li>
              <li><strong>Exporter</strong> : Cliquez sur "Export" pour télécharger vos données</li>
            </ul>
          </div>
          <div class="help-section">
            <h3>Raccourcis clavier</h3>
            <ul>
              <li><kbd>Échap</kbd> : Annuler l'outil actuel</li>
              <li><kbd>Suppr</kbd> : Supprimer l'élément sélectionné</li>
            </ul>
          </div>
        </div>
        <div class="help-footer">
          <button @click="showHelp = false" class="btn-primary">Compris !</button>
        </div>
      </div>
    </div>

    <!-- Modal d'édition des propriétés -->
    <div v-if="showEditModal" class="edit-modal" @click.self="showEditModal = false">
      <div class="edit-content">
        <div class="edit-header">
          <h2>Modifier les propriétés</h2>
          <button @click="showEditModal = false" class="panel-close">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="edit-body">
          <!-- Propriétés existantes -->
          <div class="edit-properties">
            <div v-for="(value, key) in editingProperties" :key="key" class="edit-property">
              <label class="property-label">{{ formatPropertyKey(String(key)) }}</label>
              <div class="property-input-group">
                <input
                  type="text"
                  v-model="editingProperties[key]"
                  class="property-input"
                  :placeholder="String(key)"
                >
                <button @click="removeProperty(String(key))" class="remove-property-btn" title="Supprimer cette propriété">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M18 6L6 18M6 6l12 12"/>
                  </svg>
                </button>
              </div>
            </div>
            <div v-if="Object.keys(editingProperties).length === 0" class="no-properties-edit">
              Aucune propriété. Ajoutez-en une ci-dessous.
            </div>
          </div>

          <!-- Ajouter une nouvelle propriété -->
          <div class="add-property-section">
            <h4>Ajouter une propriété</h4>
            <div class="add-property-form">
              <input
                type="text"
                v-model="newPropertyKey"
                class="property-input"
                placeholder="Nom de la propriété"
                @keyup.enter="addProperty"
              >
              <input
                type="text"
                v-model="newPropertyValue"
                class="property-input"
                placeholder="Valeur"
                @keyup.enter="addProperty"
              >
              <button @click="addProperty" class="btn-add-property">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 5v14M5 12h14"/>
                </svg>
                Ajouter
              </button>
            </div>
          </div>
        </div>
        <div class="edit-footer">
          <button @click="showEditModal = false" class="btn-secondary">Annuler</button>
          <button @click="saveFeatureProperties" class="btn-primary">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z"/>
              <polyline points="17 21 17 13 7 13 7 21"/>
              <polyline points="7 3 7 8 15 8"/>
            </svg>
            Enregistrer
          </button>
        </div>
      </div>
    </div>

    <!-- Chargement -->
    <div v-if="mapStore.loading" class="loading-overlay">
      <div class="loading-spinner"></div>
      <span>Chargement en cours...</span>
    </div>

    <!-- Notification toast -->
    <div v-if="toastMessage" class="toast" :class="toastType">
      <svg v-if="toastType === 'success'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/>
        <polyline points="22 4 12 14.01 9 11.01"/>
      </svg>
      <svg v-else-if="toastType === 'error'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <path d="M15 9l-6 6M9 9l6 6"/>
      </svg>
      <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <path d="M12 16v-4M12 8h.01"/>
      </svg>
      <span>{{ toastMessage }}</span>
    </div>

    <!-- Coordonnées curseur -->
    <div class="coordinates-display">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <path d="M2 12h20M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z"/>
      </svg>
      <span>{{ cursorCoords.lat.toFixed(5) }}, {{ cursorCoords.lng.toFixed(5) }}</span>
    </div>

    <!-- Input file caché pour import -->
    <input type="file" ref="fileInput" @change="onFileSelected" accept=".geojson,.json" style="display: none">
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed, onUnmounted } from 'vue'
import { useMapStore } from '../stores/map'
import L from 'leaflet'
import 'leaflet-draw'

// Patch Leaflet : protéger contre le bug _map=null sur les marqueurs DivIcon
// Quand un marqueur est supprimé pendant une animation de zoom, Leaflet peut
// encore appeler _animateZoom/_updatePosition sur le marqueur orphelin → crash
const _origAnimateZoom = L.Marker.prototype._animateZoom
if (_origAnimateZoom) {
  L.Marker.prototype._animateZoom = function (opt: any) {
    if (!this._map) return
    _origAnimateZoom.call(this, opt)
  }
}
const _origUpdatePosition = (L.Marker.prototype as any)._updatePosition
if (_origUpdatePosition) {
  ;(L.Marker.prototype as any)._updatePosition = function () {
    if (!this._map) return
    _origUpdatePosition.call(this)
  }
}
// Idem pour Tooltip/Popup (DivOverlay) qui peuvent aussi avoir _map=null
if ((L as any).DivOverlay?.prototype?._updatePosition) {
  const _origDivOverlayUpdate = (L as any).DivOverlay.prototype._updatePosition
  ;(L as any).DivOverlay.prototype._updatePosition = function () {
    if (!this._map) return
    _origDivOverlayUpdate.call(this)
  }
}

const mapStore = useMapStore()

// Refs
const mapContainer = ref<HTMLElement | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const map = ref<L.Map | null>(null)
const toolMode = ref<string>('navigation')
const selectedBaseLayer = ref('ign_plan')
const showCadastre = ref(false)
const showLayerPanel = ref(false)
const showStatsPanel = ref(false)
const showProjectPanel = ref(false)
const showPerimeterPanel = ref(false)
const showHelp = ref(false)

// Périmètres/zones
interface Perimeter {
  id: string
  name: string
  bounds: L.LatLngBounds | null
  polygon: L.Polygon | null
  active: boolean
  color: string
}
const perimeters = ref<Perimeter[]>([])
const currentPerimeter = ref<Perimeter | null>(null)
const isDrawingPerimeter = ref(false)
const perimeterPoints = ref<L.LatLng[]>([])
const layerGroups = ref<Map<string, L.LayerGroup>>(new Map())
const drawnItems = ref<L.FeatureGroup | null>(null)
const currentDrawHandler = ref<any>(null)
const cadastreLayer = ref<L.TileLayer | null>(null)

// Drag & drop
const isDragging = ref(false)

// Toast notifications
const toastMessage = ref('')
const toastType = ref<'success' | 'error' | 'info'>('info')
let toastTimeout: number | null = null

// Mesure
const measurePoints = ref<L.LatLng[]>([])
const measureLayer = ref<L.LayerGroup | null>(null)
const totalDistance = ref(0)
const totalArea = ref(0)

// Curseur
const cursorCoords = ref({ lat: 46.603354, lng: 1.888334 })

// Saisie en série
const seriesPoints = ref<L.LatLng[]>([])

// Édition de propriétés
const showEditModal = ref(false)
const editingProperties = ref<Record<string, string>>({})
const newPropertyKey = ref('')
const newPropertyValue = ref('')

// Statistiques computées
const totalLayers = computed(() => mapStore.layers.length)
const totalFeatures = computed(() => {
  return mapStore.layers.reduce((sum, layer) => sum + (layer.data?.features?.length || 0), 0)
})
const totalPoints = computed(() => {
  return mapStore.layers.reduce((sum, layer) => {
    const features = layer.data?.features || []
    return sum + features.filter((f: any) => f.geometry?.type === 'Point' || f.geometry?.type === 'MultiPoint').length
  }, 0)
})
const totalLines = computed(() => {
  return mapStore.layers.reduce((sum, layer) => {
    const features = layer.data?.features || []
    return sum + features.filter((f: any) => f.geometry?.type === 'LineString' || f.geometry?.type === 'MultiLineString').length
  }, 0)
})
const totalPolygons = computed(() => {
  return mapStore.layers.reduce((sum, layer) => {
    const features = layer.data?.features || []
    return sum + features.filter((f: any) => f.geometry?.type === 'Polygon' || f.geometry?.type === 'MultiPolygon').length
  }, 0)
})

// URLs des fonds de carte IGN Géoplateforme (gratuits)
const baseLayers: Record<string, () => L.TileLayer> = {
  // IGN France
  ign_plan: () => L.tileLayer(
    'https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2&STYLE=normal&FORMAT=image/png&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}',
    { attribution: '© IGN - Géoportail', maxZoom: 19 }
  ),
  ign_ortho: () => L.tileLayer(
    'https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=ORTHOIMAGERY.ORTHOPHOTOS&STYLE=normal&FORMAT=image/jpeg&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}',
    { attribution: '© IGN - Géoportail', maxZoom: 20 }
  ),
  ign_cadastre: () => L.tileLayer(
    'https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=CADASTRALPARCELS.PARCELLAIRE_EXPRESS&STYLE=PCI%20vecteur&FORMAT=image/png&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}',
    { attribution: '© IGN - Géoportail', maxZoom: 20 }
  ),
  ign_carte: () => L.tileLayer(
    'https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=GEOGRAPHICALGRIDSYSTEMS.MAPS&STYLE=normal&FORMAT=image/jpeg&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}',
    { attribution: '© IGN - Géoportail', maxZoom: 18 }
  ),
  ign_ortho_histo: () => L.tileLayer(
    'https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=ORTHOIMAGERY.ORTHOPHOTOS.1950-1965&STYLE=normal&FORMAT=image/png&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}',
    { attribution: '© IGN - Géoportail', maxZoom: 18 }
  ),
  // International
  osm: () => L.tileLayer(
    'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    { attribution: '© OpenStreetMap contributors', maxZoom: 19 }
  ),
  osm_france: () => L.tileLayer(
    'https://{s}.tile.openstreetmap.fr/osmfr/{z}/{x}/{y}.png',
    { attribution: '© OpenStreetMap France', maxZoom: 20 }
  ),
  satellite: () => L.tileLayer(
    'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    { attribution: '© Esri', maxZoom: 19 }
  ),
  topo: () => L.tileLayer(
    'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
    { attribution: '© OpenTopoMap', maxZoom: 17 }
  )
}

let currentBaseLayer: L.TileLayer | null = null

// Initialisation
onMounted(async () => {
  initMap()
  mapStore.loadProjects()

  // Charger les zones API et zoomer dessus
  await mapStore.loadApiZones()
  const bounds = mapStore.getApiZonesBounds()
  if (bounds && map.value) {
    map.value.fitBounds(bounds, { padding: [50, 50], maxZoom: 14 })
  }

  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
  if (map.value) {
    map.value.remove()
  }
})

function initMap() {
  if (!mapContainer.value) return

  // Créer la carte avec zoom étendu
  map.value = L.map(mapContainer.value, {
    center: [46.603354, 1.888334], // Centre de la France
    zoom: 6,
    zoomControl: false,
    maxZoom: 20,
    minZoom: 3
  })

  // Contrôle de zoom
  L.control.zoom({ position: 'topright' }).addTo(map.value)

  // Fond de carte initial
  currentBaseLayer = baseLayers[selectedBaseLayer.value]()
  currentBaseLayer.addTo(map.value)

  // Échelle
  L.control.scale({ imperial: false, position: 'bottomleft' }).addTo(map.value)

  // Couche pour les éléments dessinés
  drawnItems.value = new L.FeatureGroup()
  map.value.addLayer(drawnItems.value)

  // Couche pour les mesures
  measureLayer.value = new L.LayerGroup()
  map.value.addLayer(measureLayer.value)

  // Événements
  map.value.on('mousemove', onMouseMove)
  map.value.on('click', onMapClick)
  map.value.on('dblclick', onMapDoubleClick)

  // Événement de création
  map.value.on(L.Draw.Event.CREATED, onDrawCreated)
}

function onMouseMove(e: L.LeafletMouseEvent) {
  cursorCoords.value = { lat: e.latlng.lat, lng: e.latlng.lng }

  // Mise à jour de la mesure en temps réel
  if ((toolMode.value === 'measureDistance' || toolMode.value === 'measureArea') && measurePoints.value.length > 0) {
    updateMeasurePreview(e.latlng)
  }
}

function onMapClick(e: L.LeafletMouseEvent) {
  if (isDrawingPerimeter.value) {
    addPerimeterPoint(e.latlng)
  } else if (toolMode.value === 'measureDistance' || toolMode.value === 'measureArea') {
    addMeasurePoint(e.latlng)
  } else if (toolMode.value === 'series') {
    addSeriesPoint(e.latlng)
  }
}

function onMapDoubleClick(e: L.LeafletMouseEvent) {
  if (isDrawingPerimeter.value) {
    finishPerimeter()
    return
  }
  if (toolMode.value === 'measureDistance') {
    finishMeasure()
  }
}

function onDrawCreated(e: any) {
  const layer = e.layer
  drawnItems.value?.addLayer(layer)

  const geojson = layer.toGeoJSON()
  console.log('Feature created:', geojson)

  // TODO: Sauvegarder vers l'API
  // mapStore.saveFeature(geojson)
}

// Gestion des modes d'outils
function setToolMode(mode: string) {
  // Annuler le mode précédent
  cancelCurrentMode()

  toolMode.value = mode

  if (!map.value) return

  // Gérer le zoom double-clic selon le mode
  if (mode === 'measureDistance' || mode === 'measureArea') {
    map.value.doubleClickZoom.disable()
  } else {
    map.value.doubleClickZoom.enable()
  }

  // Activer le nouveau mode
  switch (mode) {
    case 'marker':
      currentDrawHandler.value = new L.Draw.Marker(map.value, {})
      currentDrawHandler.value.enable()
      break
    case 'polyline':
      currentDrawHandler.value = new L.Draw.Polyline(map.value, {
        shapeOptions: { color: '#3498db', weight: 3 }
      })
      currentDrawHandler.value.enable()
      break
    case 'polygon':
      currentDrawHandler.value = new L.Draw.Polygon(map.value, {
        shapeOptions: { color: '#3498db', weight: 2, fillOpacity: 0.3 }
      })
      currentDrawHandler.value.enable()
      break
    case 'measureDistance':
    case 'measureArea':
      clearMeasure()
      break
    case 'edit':
      // Mode édition de sommets
      if (drawnItems.value && drawnItems.value.getLayers().length > 0) {
        // Activer l'édition sur les couches existantes
        drawnItems.value.eachLayer((layer: any) => {
          if (layer.editing) {
            layer.editing.enable()
          }
        })
      }
      break
    case 'series':
      seriesPoints.value = []
      break
  }
}

function cancelCurrentMode() {
  if (currentDrawHandler.value) {
    currentDrawHandler.value.disable()
    currentDrawHandler.value = null
  }

  // Désactiver l'édition
  if (drawnItems.value) {
    drawnItems.value.eachLayer((layer: any) => {
      if (layer.editing) {
        layer.editing.disable()
      }
    })
  }
}

// Mesures
function addMeasurePoint(latlng: L.LatLng) {
  measurePoints.value.push(latlng)
  updateMeasureDisplay()
}

function updateMeasurePreview(latlng: L.LatLng) {
  if (!measureLayer.value || measurePoints.value.length === 0) return

  // Calculer la distance/surface avec le point de prévisualisation
  const previewPoints = [...measurePoints.value, latlng]

  if (toolMode.value === 'measureDistance') {
    totalDistance.value = calculateDistance(previewPoints)
  } else if (toolMode.value === 'measureArea' && previewPoints.length >= 3) {
    totalArea.value = calculateArea(previewPoints)
  }

  updateMeasureDisplay(latlng)
}

function updateMeasureDisplay(previewPoint?: L.LatLng) {
  if (!measureLayer.value || !map.value) return

  measureLayer.value.clearLayers()

  const points = previewPoint ? [...measurePoints.value, previewPoint] : measurePoints.value

  if (points.length === 0) return

  // Marqueurs pour chaque point
  points.forEach((p, i) => {
    const isPreview = previewPoint && i === points.length - 1
    L.circleMarker(p, {
      radius: isPreview ? 4 : 6,
      fillColor: isPreview ? '#e74c3c' : '#3498db',
      color: '#fff',
      weight: 2,
      fillOpacity: 1
    }).addTo(measureLayer.value!)
  })

  // Ligne ou polygone
  if (toolMode.value === 'measureDistance' && points.length >= 2) {
    L.polyline(points, {
      color: '#3498db',
      weight: 3,
      dashArray: '5, 10'
    }).addTo(measureLayer.value!)

    totalDistance.value = calculateDistance(points)
  } else if (toolMode.value === 'measureArea' && points.length >= 3) {
    L.polygon(points, {
      color: '#9b59b6',
      weight: 2,
      fillOpacity: 0.2,
      dashArray: '5, 10'
    }).addTo(measureLayer.value!)

    totalArea.value = calculateArea(points)
  }
}

function finishMeasure() {
  // La mesure est terminée, on garde l'affichage
  updateMeasureDisplay()
}

function clearMeasure() {
  measurePoints.value = []
  totalDistance.value = 0
  totalArea.value = 0
  measureLayer.value?.clearLayers()
}

function calculateDistance(points: L.LatLng[]): number {
  let total = 0
  for (let i = 0; i < points.length - 1; i++) {
    total += points[i].distanceTo(points[i + 1])
  }
  return total
}

function calculateArea(points: L.LatLng[]): number {
  // Algorithme du lacet (Shoelace formula) pour calculer l'aire
  // Conversion approximative en m² pour les petites surfaces
  if (points.length < 3) return 0

  const R = 6378137 // Rayon de la Terre en mètres
  let area = 0

  const toRad = (deg: number) => deg * Math.PI / 180

  for (let i = 0; i < points.length; i++) {
    const j = (i + 1) % points.length
    const xi = toRad(points[i].lng) * R * Math.cos(toRad(points[i].lat))
    const yi = toRad(points[i].lat) * R
    const xj = toRad(points[j].lng) * R * Math.cos(toRad(points[j].lat))
    const yj = toRad(points[j].lat) * R

    area += xi * yj - xj * yi
  }

  return Math.abs(area / 2)
}

function formatDistance(meters: number): string {
  if (meters < 1000) {
    return `${meters.toFixed(1)} m`
  }
  return `${(meters / 1000).toFixed(2)} km`
}

function formatArea(sqMeters: number): string {
  if (sqMeters < 10000) {
    return `${sqMeters.toFixed(1)} m²`
  }
  return `${(sqMeters / 10000).toFixed(2)} ha`
}

// Saisie en série
function addSeriesPoint(latlng: L.LatLng) {
  seriesPoints.value.push(latlng)

  // Ajouter un marqueur
  if (drawnItems.value) {
    const marker = L.marker(latlng)
    drawnItems.value.addLayer(marker)
  }

  // TODO: Ouvrir une modal pour les attributs du point
  console.log('Point série ajouté:', latlng)
}

// Gestion des fonds de carte
function changeBaseLayer() {
  if (!map.value) return

  // Supprimer l'ancien
  if (currentBaseLayer) {
    map.value.removeLayer(currentBaseLayer)
  }

  // Ajouter le nouveau
  currentBaseLayer = baseLayers[selectedBaseLayer.value]()
  currentBaseLayer.addTo(map.value)

  // Remettre le cadastre par-dessus si actif
  if (showCadastre.value && cadastreLayer.value) {
    cadastreLayer.value.bringToFront()
  }
}

function toggleCadastre() {
  if (!map.value) return

  if (showCadastre.value) {
    if (!cadastreLayer.value) {
      cadastreLayer.value = L.tileLayer(
        'https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=CADASTRALPARCELS.PARCELLAIRE_EXPRESS&STYLE=PCI%20vecteur&FORMAT=image/png&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}',
        { attribution: '© IGN - Cadastre', maxZoom: 20, opacity: 0.7 }
      )
    }
    cadastreLayer.value.addTo(map.value)
  } else {
    if (cadastreLayer.value) {
      map.value.removeLayer(cadastreLayer.value)
    }
  }
}

// Gestion des couches
function toggleLayer(layer: any) {
  mapStore.toggleLayerVisibility(layer.id)
}

function toggleLayerPanel() {
  showLayerPanel.value = !showLayerPanel.value
}

// Actions sur les features
function zoomToData() {
  if (!map.value) return

  try {
    const allBounds: L.LatLngBounds[] = []

    mapStore.visibleLayers.forEach(layer => {
      if (layer.data?.features?.length) {
        const geoJsonLayer = L.geoJSON(layer.data)
        const bounds = geoJsonLayer.getBounds()
        if (bounds.isValid()) {
          allBounds.push(bounds)
        }
      }
    })

    if (allBounds.length > 0) {
      const combinedBounds = allBounds.reduce((acc, bounds) => acc.extend(bounds))
      map.value.fitBounds(combinedBounds, { padding: [50, 50] })
    }
  } catch (e) {
    console.warn('zoomToData error:', e)
  }
}

function zoomToFeature() {
  if (!map.value || !mapStore.selectedFeature) return

  try {
    const layer = L.geoJSON(mapStore.selectedFeature)
    const bounds = layer.getBounds()
    if (bounds.isValid()) {
      map.value.fitBounds(bounds, { padding: [100, 100], maxZoom: 18 })
    }
  } catch (e) {
    console.warn('zoomToFeature error:', e)
  }
}

function editFeature() {
  if (!mapStore.selectedFeature) return
  // Copier les propriétés pour l'édition
  editingProperties.value = { ...mapStore.selectedFeature.properties } as Record<string, string>
  newPropertyKey.value = ''
  newPropertyValue.value = ''
  showEditModal.value = true
}

function saveFeatureProperties() {
  if (!mapStore.selectedFeature) return

  // Mettre à jour les propriétés de la feature
  mapStore.selectedFeature.properties = { ...editingProperties.value }

  // TODO: Sauvegarder via API
  // await api.updateFeature(mapStore.selectedFeature.properties.id, editingProperties.value)

  showEditModal.value = false
  showToast('Propriétés enregistrées', 'success')
}

function addProperty() {
  if (!newPropertyKey.value.trim()) {
    showToast('Le nom de la propriété est requis', 'error')
    return
  }
  editingProperties.value[newPropertyKey.value.trim()] = newPropertyValue.value
  newPropertyKey.value = ''
  newPropertyValue.value = ''
}

function removeProperty(key: string) {
  delete editingProperties.value[key]
}

function deleteFeature() {
  if (!mapStore.selectedFeature) return
  if (confirm('Voulez-vous vraiment supprimer cet élément ?')) {
    // TODO: Supprimer via API
    console.log('Delete feature:', mapStore.selectedFeature)
    mapStore.selectFeature(null)
  }
}

function exportData() {
  const geojson: GeoJSON.FeatureCollection = {
    type: 'FeatureCollection',
    features: []
  }

  mapStore.visibleLayers.forEach(layer => {
    if (layer.data?.features) {
      geojson.features.push(...layer.data.features)
    }
  })

  // Ajouter les métadonnées
  const exportData = {
    ...geojson,
    metadata: {
      exported_at: new Date().toISOString(),
      source: 'GéoClic SIG Web',
      version: '14.0',
      feature_count: geojson.features.length
    }
  }

  const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `geoclic_export_${new Date().toISOString().slice(0, 10)}.geojson`
  a.click()
  URL.revokeObjectURL(url)
}

// Helpers
function getModeLabel(mode: string): string {
  const labels: Record<string, string> = {
    marker: 'Ajout de point',
    polyline: 'Tracé de ligne',
    polygon: 'Création de zone',
    series: 'Saisie en série',
    measureDistance: 'Mesure de distance',
    measureArea: 'Mesure de surface',
    edit: 'Mode retouche'
  }
  return labels[mode] || 'Navigation'
}

function getModeHint(mode: string): string {
  const hints: Record<string, string> = {
    marker: 'Cliquez sur la carte pour placer un point',
    polyline: 'Cliquez pour tracer, Échap pour terminer',
    polygon: 'Dessinez le contour, Échap pour fermer',
    series: 'Cliquez pour ajouter des points rapidement',
    measureDistance: 'Cliquez pour mesurer, Échap pour finir',
    measureArea: 'Tracez une zone pour calculer la surface',
    edit: 'Cliquez sur un élément pour modifier ses sommets'
  }
  return hints[mode] || ''
}

function getModeColor(mode: string): string {
  const colors: Record<string, string> = {
    marker: '#27ae60',
    polyline: '#3498db',
    polygon: '#9b59b6',
    series: '#e67e22',
    measureDistance: '#1abc9c',
    measureArea: '#1abc9c',
    edit: '#e74c3c'
  }
  return colors[mode] || '#3498db'
}

function getModeIconPath(mode: string): string {
  const paths: Record<string, string> = {
    marker: 'M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 1118 0z',
    polyline: 'M3,17 9,11 13,15 21,7',
    polygon: 'M12,2 22,8.5 22,15.5 12,22 2,15.5 2,8.5z',
    series: 'M8,8 L8,8 M16,8 L16,8 M8,16 L8,16 M16,16 L16,16',
    measureDistance: 'M2 12h20M6 8v8M18 8v8',
    measureArea: 'M3,3 21,3 21,21 3,21z M3,9 21,9 M9,3 9,21',
    edit: 'M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7 M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z'
  }
  return paths[mode] || ''
}

function getGeometryLabel(type: string): string {
  const labels: Record<string, string> = {
    Point: 'Point',
    LineString: 'Ligne',
    Polygon: 'Polygone',
    MultiPoint: 'Multi-points',
    MultiLineString: 'Multi-lignes',
    MultiPolygon: 'Multi-polygones'
  }
  return labels[type] || type
}

// Propriétés à afficher dans le panneau détail avec labels français
const PROPERTY_LABELS: Record<string, string> = {
  name: 'Nom',
  categorie: 'Catégorie',
  type: 'Type',
  condition_state: 'État',
  point_status: 'Statut',
  comment: 'Commentaire',
}

// Propriétés internes à masquer
const HIDDEN_PROPERTIES = new Set(['id', 'color_value', 'icon_name', 'sync_status', 'lexique_code', 'photos', '_category_icon', '_category_color'])

function getDisplayProperties(properties: Record<string, any> | null): { key: string; label: string; value: string }[] {
  if (!properties) return []
  return Object.entries(properties)
    .filter(([key, value]) => !HIDDEN_PROPERTIES.has(key) && value != null && value !== '')
    .map(([key, value]) => ({
      key,
      label: PROPERTY_LABELS[key] || formatPropertyKey(key),
      value: String(value),
    }))
}

function formatPropertyKey(key: string): string {
  // Convertit snake_case ou camelCase en texte lisible
  return key
    .replace(/_/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/^./, str => str.toUpperCase())
}

// Toast notifications
function showToast(message: string, type: 'success' | 'error' | 'info' = 'info') {
  if (toastTimeout) {
    clearTimeout(toastTimeout)
  }
  toastMessage.value = message
  toastType.value = type
  toastTimeout = window.setTimeout(() => {
    toastMessage.value = ''
  }, 3000)
}

// Panneau stats
function toggleStatsPanel() {
  showStatsPanel.value = !showStatsPanel.value
  if (showStatsPanel.value) {
    showLayerPanel.value = false
    showProjectPanel.value = false
  }
}

function toggleProjectPanel() {
  showProjectPanel.value = !showProjectPanel.value
  if (showProjectPanel.value) {
    showLayerPanel.value = false
    showStatsPanel.value = false
  }
}

function selectProject(project: any) {
  mapStore.selectProject(project)
  showProjectPanel.value = false
  showToast(`Projet "${project.name}" chargé`, 'success')
}

// Périmètres
function togglePerimeterPanel() {
  showPerimeterPanel.value = !showPerimeterPanel.value
  if (showPerimeterPanel.value) {
    showLayerPanel.value = false
    showStatsPanel.value = false
    showProjectPanel.value = false
  }
}

function startDrawingPerimeter() {
  isDrawingPerimeter.value = true
  perimeterPoints.value = []
  setToolMode('navigation')
  // Désactiver le zoom double-clic pendant le dessin
  if (map.value) {
    map.value.doubleClickZoom.disable()
  }
  showToast('Cliquez sur la carte pour définir les coins de la zone. Échap pour terminer.', 'info')
}

function addPerimeterPoint(latlng: L.LatLng) {
  if (!isDrawingPerimeter.value) return

  perimeterPoints.value.push(latlng)

  // Afficher le polygone en cours de dessin
  updatePerimeterPreview()
}

function updatePerimeterPreview() {
  if (!map.value || perimeterPoints.value.length < 2) return

  // Supprimer l'ancien preview
  map.value.eachLayer((layer: any) => {
    if (layer._perimeterPreview) {
      map.value?.removeLayer(layer)
    }
  })

  // Dessiner le nouveau
  const preview = L.polygon(perimeterPoints.value, {
    color: '#e67e22',
    weight: 2,
    fillOpacity: 0.1,
    dashArray: '5, 10'
  }) as any
  preview._perimeterPreview = true
  preview.addTo(map.value)
}

function finishPerimeter() {
  if (perimeterPoints.value.length < 3) {
    showToast('Minimum 3 points requis pour créer une zone', 'error')
    return
  }

  // Créer le périmètre
  const id = `perimeter_${Date.now()}`
  const polygon = L.polygon(perimeterPoints.value, {
    color: '#e67e22',
    weight: 2,
    fillOpacity: 0.15
  })

  const newPerimeter: Perimeter = {
    id,
    name: `Zone ${perimeters.value.length + 1}`,
    bounds: polygon.getBounds(),
    polygon: polygon,
    active: false,
    color: '#e67e22'
  }

  perimeters.value.push(newPerimeter)

  // Nettoyer
  cancelPerimeterDrawing()

  // Ajouter le polygone à la carte
  if (map.value) {
    polygon.addTo(map.value)
    polygon.bindTooltip(newPerimeter.name)
  }

  showToast('Zone créée avec succès', 'success')
}

function cancelPerimeterDrawing() {
  isDrawingPerimeter.value = false
  perimeterPoints.value = []

  // Supprimer le preview et réactiver le zoom double-clic
  if (map.value) {
    map.value.eachLayer((layer: any) => {
      if (layer._perimeterPreview) {
        map.value?.removeLayer(layer)
      }
    })
    map.value.doubleClickZoom.enable()
  }
}

function togglePerimeterActive(perimeter: Perimeter) {
  perimeter.active = !perimeter.active

  if (perimeter.active) {
    // Désactiver les autres
    perimeters.value.forEach(p => {
      if (p.id !== perimeter.id) p.active = false
    })
    currentPerimeter.value = perimeter

    // Zoomer sur la zone
    if (map.value && perimeter.bounds) {
      map.value.fitBounds(perimeter.bounds, { padding: [50, 50] })
    }

    showToast(`Filtrage par "${perimeter.name}" activé`, 'info')
  } else {
    currentPerimeter.value = null
    showToast('Filtrage désactivé', 'info')
  }
}

function deletePerimeter(perimeter: Perimeter) {
  if (!confirm(`Supprimer la zone "${perimeter.name}" ?`)) return

  // Retirer de la carte
  if (map.value && perimeter.polygon) {
    map.value.removeLayer(perimeter.polygon)
  }

  // Retirer du tableau
  perimeters.value = perimeters.value.filter(p => p.id !== perimeter.id)

  if (currentPerimeter.value?.id === perimeter.id) {
    currentPerimeter.value = null
  }

  showToast('Zone supprimée', 'success')
}

function renamePerimeter(perimeter: Perimeter) {
  const newName = prompt('Nouveau nom de la zone:', perimeter.name)
  if (newName && newName.trim()) {
    perimeter.name = newName.trim()
    if (perimeter.polygon) {
      perimeter.polygon.unbindTooltip()
      perimeter.polygon.bindTooltip(newName.trim())
    }
  }
}

// Drag & drop pour import GeoJSON
function onDragOver(e: DragEvent) {
  isDragging.value = true
}

function onDragLeave(e: DragEvent) {
  isDragging.value = false
}

function onDrop(e: DragEvent) {
  isDragging.value = false
  const files = e.dataTransfer?.files
  if (files && files.length > 0) {
    handleFile(files[0])
  }
}

function triggerImport() {
  fileInput.value?.click()
}

function onFileSelected(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files && input.files.length > 0) {
    handleFile(input.files[0])
    input.value = '' // Reset pour permettre re-import du même fichier
  }
}

function handleFile(file: File) {
  if (!file.name.endsWith('.geojson') && !file.name.endsWith('.json')) {
    showToast('Format non supporté. Utilisez un fichier GeoJSON.', 'error')
    return
  }

  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const geojson = JSON.parse(e.target?.result as string)
      if (geojson.type === 'FeatureCollection' || geojson.type === 'Feature') {
        importGeoJSON(geojson, file.name)
        showToast(`Import réussi: ${file.name}`, 'success')
      } else {
        showToast('Le fichier ne contient pas de données GeoJSON valides.', 'error')
      }
    } catch (err) {
      showToast('Erreur de lecture du fichier GeoJSON.', 'error')
    }
  }
  reader.readAsText(file)
}

function importGeoJSON(geojson: any, filename: string) {
  const features = geojson.type === 'FeatureCollection' ? geojson.features : [geojson]
  const layerName = filename.replace(/\.(geo)?json$/i, '')

  // Créer une nouvelle couche
  const newLayer = {
    id: `import_${Date.now()}`,
    name: layerName,
    visible: true,
    color: getRandomColor(),
    data: {
      type: 'FeatureCollection' as const,
      features: features
    }
  }

  mapStore.addLayer(newLayer)

  // Zoomer sur les données importées
  if (map.value && features.length > 0) {
    const geoJsonLayer = L.geoJSON(newLayer.data)
    map.value.fitBounds(geoJsonLayer.getBounds(), { padding: [50, 50] })
  }
}

function getRandomColor(): string {
  const colors = ['#3498db', '#e74c3c', '#2ecc71', '#9b59b6', '#f39c12', '#1abc9c', '#34495e', '#e67e22']
  return colors[Math.floor(Math.random() * colors.length)]
}

// Raccourcis clavier
function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    if (showHelp.value) {
      showHelp.value = false
    } else if (toolMode.value !== 'navigation') {
      setToolMode('navigation')
    }
  } else if (e.key === 'Delete' && mapStore.selectedFeature) {
    deleteFeature()
  }
}

// Supprimer proprement un LayerGroup de la carte
// IMPORTANT: NE PAS appeler clearLayers() avant map.removeLayer() !
// Leaflet a besoin des layers dans le groupe pour les désabonner
// de l'événement zoomanim lors du onRemove(). Si on clear avant,
// les marqueurs restent abonnés avec _map=null → crash _animateZoom.
function removeLayerGroupFromMap(group: L.LayerGroup, mapInstance: L.Map) {
  try {
    mapInstance.removeLayer(group)
  } catch (_) { /* ignore removal errors */ }
}

// Créer un LayerGroup Leaflet à partir d'une couche du store
function createLeafletLayerGroup(layer: { data: GeoJSON.FeatureCollection | null; color: string; icon?: string; id: string }) {
  const group = L.layerGroup()
  if (!layer.data) return group

  L.geoJSON(layer.data, {
    style: () => ({
      color: layer.color,
      weight: 2,
      fillOpacity: 0.3
    }),
    pointToLayer: (feature, latlng) => {
      const iconName = feature.properties?._category_icon || layer.icon || 'mdi-map-marker'
      const iconColor = feature.properties?._category_color || layer.color || '#3498db'
      return L.marker(latlng, {
        icon: L.divIcon({
          className: 'sig-marker',
          html: `<div class="sig-marker-pin" style="background-color: ${iconColor}"><i class="mdi ${iconName}"></i></div>`,
          iconSize: [32, 32],
          iconAnchor: [16, 32],
          tooltipAnchor: [0, -32],
        })
      })
    },
    onEachFeature: (feature, featureLayer) => {
      featureLayer.on('click', () => {
        mapStore.selectFeature(feature)
      })

      if (feature.properties?.name) {
        featureLayer.bindTooltip(feature.properties.name)
      }
    }
  }).addTo(group)

  return group
}

// Watch pour les changements de couches
// Fingerprint = identité + visibilité + nombre de features (détecte les changements de données)
watch(
  () => mapStore.layers.map(l => `${l.id}:${l.visible}:${l.data?.features?.length || 0}`).join(','),
  () => {
    if (!map.value) return

    const m = map.value

    // Si la carte est en pleine animation de zoom, attendre la fin
    if ((m as any)._animatingZoom) {
      m.once('zoomend', () => renderLayers())
      return
    }
    renderLayers()
  }
)

function renderLayers() {
  if (!map.value) return

  // Supprimer les couches existantes de la carte (Leaflet gère le cleanup des events)
  layerGroups.value.forEach((group) => {
    removeLayerGroupFromMap(group, map.value!)
  })
  layerGroups.value.clear()

  // Ajouter les couches visibles
  mapStore.layers.forEach(layer => {
    if (!layer.visible || !layer.data) return

    const group = createLeafletLayerGroup(layer)
    group.addTo(map.value!)
    layerGroups.value.set(layer.id, group)
  })
}

// Couche pour les zones API
const apiZonesLayerGroup = ref<L.LayerGroup | null>(null)

// Watch pour les zones API
watch(
  () => [mapStore.apiZonesVisible, mapStore.visibleApiZones],
  () => {
    if (!map.value) return

    // Supprimer la couche existante
    if (apiZonesLayerGroup.value) {
      removeLayerGroupFromMap(apiZonesLayerGroup.value, map.value)
    }

    // Afficher les zones si visible globalement
    if (!mapStore.apiZonesVisible) return

    const zonesGeoJSON = mapStore.getApiZonesGeoJSON()
    if (zonesGeoJSON.features.length === 0) return

    apiZonesLayerGroup.value = L.layerGroup()

    L.geoJSON(zonesGeoJSON, {
      style: (feature) => ({
        color: feature?.properties?.color || '#3498db',
        weight: 2,
        fillOpacity: 0.15,
        dashArray: '5, 5'
      }),
      onEachFeature: (feature, layer) => {
        if (feature.properties?.name) {
          layer.bindTooltip(feature.properties.name, {
            permanent: false,
            direction: 'center',
            className: 'zone-tooltip'
          })
        }
      }
    }).addTo(apiZonesLayerGroup.value)

    apiZonesLayerGroup.value.addTo(map.value)
  },
  { deep: true }
)
</script>

<style scoped>
/* ============================================
   Variables et base
   ============================================ */
.map-container {
  position: relative;
  width: 100%;
  height: 100%;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.leaflet-map {
  width: 100%;
  height: 100%;
}

/* ============================================
   Drop zone pour import
   ============================================ */
.map-container.drag-over::before {
  content: '';
  position: absolute;
  inset: 0;
  background: rgba(52, 152, 219, 0.1);
  border: 3px dashed #3498db;
  z-index: 1500;
  pointer-events: none;
}

.drop-zone {
  position: absolute;
  inset: 0;
  background: rgba(52, 152, 219, 0.15);
  z-index: 1500;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.drop-zone-content {
  background: white;
  padding: 40px 60px;
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.2);
  text-align: center;
}

.drop-icon {
  width: 48px;
  height: 48px;
  color: #3498db;
  margin-bottom: 16px;
}

.drop-text {
  font-size: 1.1rem;
  color: #2c3e50;
  font-weight: 500;
}

/* ============================================
   Toolbar principal - Design moderne
   ============================================ */
.toolbar-main {
  position: absolute;
  top: 8px;
  left: 12px;
  right: 60px;
  z-index: 1000;
  display: flex;
  align-items: stretch;
  gap: 2px;
  background: white;
  padding: 4px;
  border-radius: 10px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
  flex-wrap: wrap;
}

.toolbar-brand {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
  border-radius: 6px;
  color: white;
}

.brand-icon {
  font-size: 1.3rem;
}

.brand-title {
  font-weight: 600;
  font-size: 0.95rem;
  letter-spacing: -0.3px;
}

.toolbar-section {
  display: flex;
  flex-direction: column;
  padding: 2px 8px;
  border-left: 1px solid #f0f0f0;
}

.toolbar-section:first-of-type {
  border-left: none;
}

.section-label {
  font-size: 0.65rem;
  text-transform: uppercase;
  color: #95a5a6;
  font-weight: 600;
  letter-spacing: 0.5px;
  margin-bottom: 2px;
}

.tool-buttons {
  display: flex;
  gap: 4px;
}

.tool-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1px;
  padding: 4px 8px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
  min-width: 48px;
}

.tool-btn svg {
  width: 20px;
  height: 20px;
  color: #5d6d7e;
  transition: color 0.15s ease;
}

.tool-label {
  font-size: 0.7rem;
  color: #7f8c8d;
  font-weight: 500;
  transition: color 0.15s ease;
}

.tool-btn:hover {
  background: #f8f9fa;
}

.tool-btn:hover svg {
  color: #3498db;
}

.tool-btn:hover .tool-label {
  color: #3498db;
}

.tool-btn.active {
  background: #ebf5fb;
}

.tool-btn.active svg {
  color: #3498db;
}

.tool-btn.active .tool-label {
  color: #3498db;
  font-weight: 600;
}

.tool-btn-clear svg {
  color: #e74c3c;
}

.tool-btn-clear .tool-label {
  color: #e74c3c;
}

.tool-btn-help {
  opacity: 0.7;
}

.tool-btn-help:hover {
  opacity: 1;
}

/* Sélecteur fond de carte */
.toolbar-section-map {
  flex-direction: column;
  gap: 2px;
}

.map-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.base-layer-select {
  padding: 4px 8px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 0.8rem;
  color: #2c3e50;
  background: white;
  cursor: pointer;
  min-width: 120px;
}

.base-layer-select:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.15);
}

.cadastre-overlay {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  font-size: 0.75rem;
}

.cadastre-overlay input {
  width: 14px;
  height: 14px;
  cursor: pointer;
  accent-color: #3498db;
}

.overlay-label {
  color: #7f8c8d;
  font-weight: 500;
}

/* ============================================
   Barre de mesure
   ============================================ */
.measure-bar {
  position: absolute;
  top: 80px;
  left: 12px;
  z-index: 1000;
  background: linear-gradient(135deg, #1abc9c 0%, #16a085 100%);
  color: white;
  padding: 12px 20px;
  border-radius: 10px;
  box-shadow: 0 4px 15px rgba(26, 188, 156, 0.3);
  display: flex;
  align-items: center;
  gap: 16px;
}

.measure-result {
  display: flex;
  align-items: center;
  gap: 10px;
}

.measure-icon svg {
  width: 24px;
  height: 24px;
}

.measure-value {
  font-size: 1.4rem;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.measure-hint {
  font-size: 0.8rem;
  opacity: 0.85;
  border-left: 1px solid rgba(255,255,255,0.3);
  padding-left: 16px;
}

/* ============================================
   Indicateur de mode
   ============================================ */
.mode-indicator {
  position: absolute;
  bottom: 50px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
  background: white;
  padding: 10px 16px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  display: flex;
  align-items: center;
  gap: 12px;
}

.mode-content {
  display: flex;
  align-items: center;
  gap: 10px;
}

.mode-icon-wrapper {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.mode-icon-wrapper svg {
  width: 20px;
  height: 20px;
  color: white;
}

.mode-info {
  display: flex;
  flex-direction: column;
}

.mode-title {
  font-weight: 600;
  font-size: 0.9rem;
  color: #2c3e50;
}

.mode-hint {
  font-size: 0.75rem;
  color: #7f8c8d;
}

.mode-cancel {
  width: 32px;
  height: 32px;
  border: none;
  background: #f8f9fa;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}

.mode-cancel svg {
  width: 16px;
  height: 16px;
  color: #7f8c8d;
}

.mode-cancel:hover {
  background: #fee;
}

.mode-cancel:hover svg {
  color: #e74c3c;
}

/* ============================================
   Sélecteur de projet dans toolbar
   ============================================ */
.toolbar-section-project {
  min-width: 160px;
}

.project-selector {
  width: 100%;
}

.project-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  width: 100%;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.project-btn:hover {
  border-color: #3498db;
}

.project-btn.active {
  border-color: #3498db;
  background: #ebf5fb;
}

.project-btn svg:first-child {
  width: 18px;
  height: 18px;
  color: #3498db;
  flex-shrink: 0;
}

.project-name {
  flex: 1;
  font-size: 0.85rem;
  font-weight: 500;
  color: #2c3e50;
  text-align: left;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chevron {
  width: 14px;
  height: 14px;
  color: #7f8c8d;
  flex-shrink: 0;
  transition: transform 0.2s ease;
}

.project-btn.active .chevron {
  transform: rotate(180deg);
}

/* ============================================
   Panneaux latéraux (couches, stats, propriétés, projets, périmètres)
   ============================================ */
.layer-panel,
.stats-panel,
.project-panel,
.perimeter-panel,
.feature-panel {
  position: absolute;
  width: 280px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 25px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  max-height: calc(100% - 120px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.layer-panel {
  left: 12px;
  top: 80px;
}

.stats-panel {
  left: 12px;
  top: 80px;
}

.project-panel {
  left: 12px;
  top: 80px;
  width: 320px;
}

.feature-panel {
  right: 12px;
  top: 80px;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  background: #f8f9fa;
  border-bottom: 1px solid #eee;
}

.panel-header-primary {
  background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
  color: white;
}

.panel-header-primary .panel-close svg {
  color: white;
}

.panel-icon {
  width: 20px;
  height: 20px;
  color: #5d6d7e;
}

.panel-header-primary .panel-icon {
  color: white;
}

.panel-header h3 {
  flex: 1;
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
  color: #2c3e50;
}

.panel-header-primary h3 {
  color: white;
}

.panel-close {
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s ease;
}

.panel-close svg {
  width: 16px;
  height: 16px;
  color: #7f8c8d;
}

.panel-close:hover {
  background: rgba(0,0,0,0.05);
}

.panel-body {
  flex: 1;
  padding: 12px;
  overflow-y: auto;
}

.panel-footer {
  padding: 12px;
  border-top: 1px solid #eee;
  background: #fafafa;
}

/* Couches */
.layers-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.layer-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  transition: background 0.15s ease;
}

.layer-item:hover {
  background: #f8f9fa;
}

.layer-item.layer-hidden {
  opacity: 0.5;
}

.layer-visibility {
  flex-shrink: 0;
}

.layer-checkbox {
  display: none;
}

.layer-toggle {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s ease;
}

.layer-toggle svg {
  width: 16px;
  height: 16px;
  color: #7f8c8d;
}

.layer-checkbox:checked + .layer-toggle {
  background: #ebf5fb;
}

.layer-checkbox:checked + .layer-toggle svg {
  color: #3498db;
}

.layer-color {
  width: 14px;
  height: 14px;
  border-radius: 4px;
  flex-shrink: 0;
}

.layer-icon-mdi {
  flex-shrink: 0;
  font-size: 18px;
  width: 22px;
  text-align: center;
}

.layer-name {
  flex: 1;
  font-size: 0.85rem;
  color: #2c3e50;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.layer-badge {
  font-size: 0.75rem;
  color: #7f8c8d;
  background: #f0f0f0;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
}

.layers-empty {
  text-align: center;
  padding: 30px 20px;
  color: #95a5a6;
}

.layers-empty svg {
  width: 48px;
  height: 48px;
  margin-bottom: 12px;
  opacity: 0.4;
}

.layers-empty p {
  margin: 0 0 4px;
  font-weight: 500;
  color: #7f8c8d;
}

.layers-empty span {
  font-size: 0.8rem;
}

/* Projects list */
.projects-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.project-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.15s ease;
  border: 2px solid transparent;
}

.project-item:hover {
  background: #f8f9fa;
}

.project-item.project-active {
  background: #ebf5fb;
  border-color: #3498db;
}

.project-icon {
  width: 40px;
  height: 40px;
  background: #f0f0f0;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.project-icon svg {
  width: 20px;
  height: 20px;
  color: #7f8c8d;
}

.project-item.project-active .project-icon {
  background: #3498db;
}

.project-item.project-active .project-icon svg {
  color: white;
}

.project-info {
  flex: 1;
  min-width: 0;
}

.project-item-name {
  display: block;
  font-size: 0.9rem;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 2px;
}

.project-desc {
  display: block;
  font-size: 0.75rem;
  color: #95a5a6;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.project-check {
  width: 24px;
  height: 24px;
  background: #27ae60;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.project-check svg {
  width: 14px;
  height: 14px;
  color: white;
}

.projects-empty {
  text-align: center;
  padding: 30px 20px;
  color: #95a5a6;
}

.projects-empty svg {
  width: 48px;
  height: 48px;
  margin-bottom: 12px;
  opacity: 0.4;
}

.projects-empty p {
  margin: 0 0 4px;
  font-weight: 500;
  color: #7f8c8d;
}

.projects-empty span {
  font-size: 0.8rem;
}

/* Perimeters/Zones */
.perimeter-panel {
  left: 12px;
  top: 80px;
  width: 320px;
  max-height: calc(100vh - 120px);
  overflow-y: auto;
}

.perimeter-drawing-mode {
  background: #fff8e1;
  border: 1px solid #f9a825;
  border-radius: 10px;
  padding: 16px;
}

.drawing-info {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  margin-bottom: 12px;
}

.drawing-info svg {
  width: 20px;
  height: 20px;
  color: #f9a825;
  flex-shrink: 0;
  margin-top: 2px;
}

.drawing-info span {
  font-size: 0.85rem;
  color: #5d4037;
  line-height: 1.4;
}

.drawing-stats {
  text-align: center;
  padding: 10px;
  background: rgba(249, 168, 37, 0.1);
  border-radius: 6px;
  margin-bottom: 12px;
  font-size: 0.9rem;
  color: #5d4037;
}

.drawing-actions {
  display: flex;
  gap: 8px;
}

.drawing-actions button {
  flex: 1;
}

.perimeters-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.perimeter-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  border: 2px solid transparent;
  transition: all 0.15s ease;
}

.perimeter-item:hover {
  background: #f8f9fa;
}

.perimeter-item.perimeter-active {
  background: #fff3e0;
  border-color: #e67e22;
}

.perimeter-color {
  width: 12px;
  height: 12px;
  border-radius: 4px;
  flex-shrink: 0;
}

.perimeter-info {
  flex: 1;
  cursor: pointer;
  min-width: 0;
}

.perimeter-name {
  display: block;
  font-size: 0.9rem;
  font-weight: 500;
  color: #2c3e50;
}

.perimeter-status {
  display: block;
  font-size: 0.75rem;
  color: #95a5a6;
}

.perimeter-item.perimeter-active .perimeter-status {
  color: #e67e22;
  font-weight: 500;
}

.perimeter-actions {
  display: flex;
  gap: 4px;
}

.perimeter-action-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}

.perimeter-action-btn svg {
  width: 14px;
  height: 14px;
  color: #95a5a6;
}

.perimeter-action-btn:hover {
  background: #f0f0f0;
}

.perimeter-action-btn:hover svg {
  color: #3498db;
}

.perimeter-action-delete:hover {
  background: #fee;
}

.perimeter-action-delete:hover svg {
  color: #e74c3c;
}

.perimeters-empty {
  text-align: center;
  padding: 30px 20px;
  color: #95a5a6;
}

.perimeters-empty svg {
  width: 48px;
  height: 48px;
  margin-bottom: 12px;
  opacity: 0.4;
}

.perimeters-empty p {
  margin: 0 0 4px;
  font-weight: 500;
  color: #7f8c8d;
}

.perimeters-empty span {
  font-size: 0.8rem;
}

.perimeters-empty-small {
  padding: 15px;
}

.perimeters-empty-small p {
  margin: 0;
  font-size: 0.85rem;
}

/* API Zones Section */
.api-zones-section,
.local-zones-section {
  margin-bottom: 8px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid #eee;
}

.section-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-icon {
  width: 16px;
  height: 16px;
  color: #3498db;
}

.section-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: #2c3e50;
}

.section-count {
  font-size: 0.75rem;
  color: #95a5a6;
}

.section-divider {
  height: 1px;
  background: #eee;
  margin: 16px 0;
}

/* Toggle Switch */
.toggle-switch {
  position: relative;
  display: inline-block;
  width: 36px;
  height: 20px;
  cursor: pointer;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  border-radius: 20px;
  transition: 0.3s;
}

.toggle-slider::before {
  position: absolute;
  content: "";
  height: 14px;
  width: 14px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  border-radius: 50%;
  transition: 0.3s;
}

.toggle-switch input:checked + .toggle-slider {
  background-color: #3498db;
}

.toggle-switch input:checked + .toggle-slider::before {
  transform: translateX(16px);
}

/* API Zones List */
.api-zones-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 200px;
  overflow-y: auto;
}

.api-zone-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 6px;
  transition: all 0.15s ease;
}

.api-zone-item:hover {
  background: #f8f9fa;
}

.api-zone-item.zone-hidden {
  opacity: 0.5;
}

.zone-color {
  width: 10px;
  height: 10px;
  border-radius: 3px;
  flex-shrink: 0;
}

.zone-info {
  flex: 1;
  min-width: 0;
}

.zone-name {
  display: block;
  font-size: 0.85rem;
  font-weight: 500;
  color: #2c3e50;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.zone-type {
  display: block;
  font-size: 0.7rem;
  color: #95a5a6;
  text-transform: capitalize;
}

.zone-checkbox {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: #3498db;
}

/* Filtres par niveau */
.level-filters {
  display: flex;
  gap: 6px;
  padding: 8px 10px;
  border-bottom: 1px solid #eee;
  margin-bottom: 8px;
}

.level-filter-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  background: white;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.15s ease;
}

.level-filter-btn:hover {
  background: #f5f5f5;
}

.level-filter-btn.active {
  border-color: #3498db;
  background: #e3f2fd;
  color: #3498db;
}

.level-filter-btn.level-1.active {
  border-color: #22c55e;
  background: #dcfce7;
  color: #16a34a;
}

.level-filter-btn.level-2.active {
  border-color: #3b82f6;
  background: #dbeafe;
  color: #2563eb;
}

.level-filter-btn.level-3.active {
  border-color: #f97316;
  background: #ffedd5;
  color: #ea580c;
}

.level-icon {
  font-size: 0.9rem;
}

.level-count {
  font-weight: 600;
}

/* Vue hiérarchique */
.api-zones-list.hierarchical {
  max-height: 300px;
}

.api-zone-item.level-1 {
  font-weight: 500;
}

.api-zone-item.level-2 {
  padding-left: 24px;
}

.api-zone-item.level-3 {
  padding-left: 44px;
}

.expand-btn {
  width: 16px;
  height: 16px;
  padding: 0;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 0.65rem;
  color: #666;
  flex-shrink: 0;
}

.expand-btn:hover {
  color: #333;
}

.expand-placeholder {
  width: 16px;
  flex-shrink: 0;
}

/* Badges de niveau */
.zone-level-badge {
  display: inline-block;
  font-size: 0.6rem;
  padding: 1px 5px;
  border-radius: 8px;
  margin-left: 6px;
  font-weight: 500;
}

.zone-level-badge.level-1 {
  background: #dcfce7;
  color: #16a34a;
}

.zone-level-badge.level-2 {
  background: #dbeafe;
  color: #2563eb;
}

.zone-level-badge.level-3 {
  background: #ffedd5;
  color: #ea580c;
}

.api-zones-empty {
  text-align: center;
  padding: 15px;
  color: #95a5a6;
  font-size: 0.85rem;
}

.link-admin {
  display: block;
  margin-top: 8px;
  color: #3498db;
  text-decoration: none;
  font-size: 0.8rem;
}

.link-admin:hover {
  text-decoration: underline;
}

.api-zones-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}

.btn-refresh {
  width: 28px;
  height: 28px;
  border: none;
  background: #f8f9fa;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}

.btn-refresh svg {
  width: 14px;
  height: 14px;
  color: #95a5a6;
}

.btn-refresh:hover {
  background: #e8f4fc;
}

.btn-refresh:hover svg {
  color: #3498db;
}

.loading-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 15px;
  color: #95a5a6;
  font-size: 0.85rem;
}

.spinner {
  width: 18px;
  height: 18px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  100% { transform: rotate(360deg); }
}

/* Zone tooltip */
:deep(.zone-tooltip) {
  background: rgba(44, 62, 80, 0.9);
  border: none;
  border-radius: 4px;
  color: white;
  font-size: 0.8rem;
  padding: 4px 8px;
}

.btn-full {
  width: 100%;
}

/* Stats */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  background: #f8f9fa;
  border-radius: 10px;
}

.stat-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon svg {
  width: 20px;
  height: 20px;
  color: white;
}

.stat-icon-blue { background: linear-gradient(135deg, #3498db, #2980b9); }
.stat-icon-green { background: linear-gradient(135deg, #2ecc71, #27ae60); }
.stat-icon-orange { background: linear-gradient(135deg, #f39c12, #e67e22); }
.stat-icon-purple { background: linear-gradient(135deg, #9b59b6, #8e44ad); }

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 1.4rem;
  font-weight: 700;
  color: #2c3e50;
  line-height: 1;
}

.stat-label {
  font-size: 0.75rem;
  color: #95a5a6;
  font-weight: 500;
}

.stats-summary {
  margin-top: 16px;
  padding: 12px;
  background: #ebf5fb;
  border-radius: 8px;
  text-align: center;
  font-size: 0.85rem;
  color: #2980b9;
}

.stats-empty {
  text-align: center;
  padding: 20px;
  color: #95a5a6;
  font-size: 0.85rem;
}

/* Feature panel */
.feature-type-badge {
  display: inline-block;
  padding: 6px 12px;
  background: #f0f0f0;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 500;
  color: #5d6d7e;
  margin-bottom: 12px;
}

.feature-properties {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.feature-property {
  display: flex;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
  font-size: 0.85rem;
}

.property-key {
  color: #7f8c8d;
  font-weight: 500;
}

.property-value {
  color: #2c3e50;
  font-weight: 500;
  text-align: right;
  max-width: 60%;
  word-break: break-word;
}

.no-properties {
  text-align: center;
  padding: 20px;
  color: #95a5a6;
  font-size: 0.85rem;
}

.feature-photos {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e0e0e0;
}

.photos-title {
  font-size: 0.85rem;
  color: #7f8c8d;
  margin: 0 0 8px 0;
  font-weight: 500;
}

.photos-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;
}

.photo-thumb {
  display: block;
  border-radius: 6px;
  overflow: hidden;
  aspect-ratio: 1;
  border: 1px solid #e0e0e0;
}

.photo-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.photo-thumb:hover {
  border-color: #3498db;
  box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2);
}

.feature-actions {
  display: flex;
  gap: 8px;
}

/* Boutons */
.btn-primary,
.btn-secondary,
.btn-danger {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 16px;
  border: none;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-primary {
  background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
  color: white;
}

.btn-primary:hover {
  box-shadow: 0 4px 12px rgba(52, 152, 219, 0.3);
  transform: translateY(-1px);
}

.btn-secondary {
  background: white;
  border: 1px solid #e0e0e0;
  color: #5d6d7e;
}

.btn-secondary:hover {
  background: #f8f9fa;
  border-color: #ccc;
}

.btn-danger {
  background: white;
  border: 1px solid #e74c3c;
  color: #e74c3c;
}

.btn-danger:hover {
  background: #fee;
}

.btn-primary svg,
.btn-secondary svg,
.btn-danger svg {
  width: 16px;
  height: 16px;
}

/* Panel footer avec bouton pleine largeur */
.panel-footer .btn-secondary {
  width: 100%;
}

/* ============================================
   Modal d'aide
   ============================================ */
.help-modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 20px;
}

.help-content {
  background: white;
  border-radius: 16px;
  max-width: 500px;
  width: 100%;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.help-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #eee;
}

.help-header h2 {
  margin: 0;
  font-size: 1.2rem;
  color: #2c3e50;
}

.help-body {
  flex: 1;
  padding: 20px 24px;
  overflow-y: auto;
}

.help-section {
  margin-bottom: 20px;
}

.help-section:last-child {
  margin-bottom: 0;
}

.help-section h3 {
  font-size: 0.9rem;
  color: #3498db;
  margin: 0 0 10px;
  font-weight: 600;
}

.help-section ul {
  margin: 0;
  padding: 0;
  list-style: none;
}

.help-section li {
  padding: 6px 0;
  font-size: 0.85rem;
  color: #5d6d7e;
  line-height: 1.5;
}

.help-section li strong {
  color: #2c3e50;
}

.help-section kbd {
  display: inline-block;
  padding: 2px 6px;
  background: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.8rem;
  font-family: monospace;
}

.help-footer {
  padding: 16px 24px;
  border-top: 1px solid #eee;
  display: flex;
  justify-content: flex-end;
}

/* ============================================
   Modal d'édition des propriétés
   ============================================ */
.edit-modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 20px;
}

.edit-content {
  background: white;
  border-radius: 16px;
  max-width: 500px;
  width: 100%;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.edit-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #eee;
}

.edit-header h2 {
  margin: 0;
  font-size: 1.2rem;
  color: #2c3e50;
}

.edit-body {
  flex: 1;
  padding: 20px 24px;
  overflow-y: auto;
}

.edit-properties {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 24px;
}

.edit-property {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.property-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: #5d6d7e;
  text-transform: capitalize;
}

.property-input-group {
  display: flex;
  gap: 8px;
}

.property-input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 0.9rem;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.property-input:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.15);
}

.remove-property-btn {
  width: 40px;
  height: 40px;
  border: 1px solid #e0e0e0;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.remove-property-btn svg {
  width: 16px;
  height: 16px;
  color: #95a5a6;
}

.remove-property-btn:hover {
  background: #fee;
  border-color: #e74c3c;
}

.remove-property-btn:hover svg {
  color: #e74c3c;
}

.no-properties-edit {
  padding: 30px 20px;
  text-align: center;
  color: #95a5a6;
  background: #f8f9fa;
  border-radius: 10px;
  font-size: 0.9rem;
}

.add-property-section {
  padding-top: 16px;
  border-top: 1px solid #eee;
}

.add-property-section h4 {
  margin: 0 0 12px;
  font-size: 0.9rem;
  font-weight: 600;
  color: #2c3e50;
}

.add-property-form {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.add-property-form .property-input {
  flex: 1;
  min-width: 140px;
}

.btn-add-property {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  background: #ebf5fb;
  border: 1px solid #3498db;
  color: #3498db;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-add-property svg {
  width: 16px;
  height: 16px;
}

.btn-add-property:hover {
  background: #3498db;
  color: white;
}

.edit-footer {
  padding: 16px 24px;
  border-top: 1px solid #eee;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* ============================================
   Toast notifications
   ============================================ */
.toast {
  position: fixed;
  bottom: 80px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 3000;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 24px;
  border-radius: 10px;
  font-size: 0.9rem;
  font-weight: 500;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  animation: toast-in 0.3s ease;
}

@keyframes toast-in {
  from {
    opacity: 0;
    transform: translate(-50%, 20px);
  }
  to {
    opacity: 1;
    transform: translate(-50%, 0);
  }
}

.toast svg {
  width: 20px;
  height: 20px;
}

.toast.success {
  background: #d4edda;
  color: #155724;
}

.toast.error {
  background: #f8d7da;
  color: #721c24;
}

.toast.info {
  background: #d1ecf1;
  color: #0c5460;
}

/* ============================================
   Chargement
   ============================================ */
.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #f0f0f0;
  border-top-color: #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-overlay span {
  font-size: 0.95rem;
  color: #5d6d7e;
  font-weight: 500;
}

/* ============================================
   Coordonnées
   ============================================ */
.coordinates-display {
  position: absolute;
  bottom: 12px;
  right: 12px;
  z-index: 1000;
  background: rgba(44, 62, 80, 0.9);
  color: white;
  padding: 8px 14px;
  border-radius: 8px;
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', monospace;
  font-size: 0.8rem;
  display: flex;
  align-items: center;
  gap: 8px;
}

.coordinates-display svg {
  width: 14px;
  height: 14px;
  opacity: 0.7;
}

/* ============================================
   Responsive
   ============================================ */
@media (max-width: 900px) {
  .toolbar-main {
    right: 12px;
    flex-wrap: wrap;
  }

  .toolbar-brand {
    display: none;
  }

  .tool-btn {
    min-width: 44px;
    padding: 6px 8px;
  }

  .tool-label {
    display: none;
  }
}

@media (max-width: 600px) {
  .toolbar-main {
    top: 8px;
    left: 8px;
    right: 8px;
    padding: 4px;
    gap: 0;
  }

  .toolbar-section {
    padding: 4px 8px;
  }

  .section-label {
    display: none;
  }

  .base-layer-select {
    min-width: 100px;
    font-size: 0.75rem;
  }

  .cadastre-overlay {
    display: none;
  }

  .layer-panel,
  .stats-panel,
  .feature-panel {
    width: calc(100% - 16px);
    left: 8px;
    right: 8px;
    max-height: 50vh;
  }

  .feature-panel {
    bottom: 60px;
    top: auto;
  }

  .mode-indicator {
    bottom: 70px;
    width: calc(100% - 40px);
    justify-content: space-between;
  }

  .measure-bar {
    top: auto;
    bottom: 130px;
    left: 8px;
    right: 8px;
    flex-direction: column;
    align-items: flex-start;
  }

  .measure-hint {
    border-left: none;
    padding-left: 0;
    margin-top: 4px;
  }
}
</style>

<!-- CSS non-scoped pour les marqueurs Leaflet DivIcon (créés hors du scope Vue) -->
<style>
.sig-marker {
  background: none !important;
  border: none !important;
}

.sig-marker-pin {
  width: 32px;
  height: 32px;
  border-radius: 50% 50% 50% 0;
  transform: rotate(-45deg);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.35);
  border: 2px solid #fff;
}

.sig-marker-pin .mdi {
  transform: rotate(45deg);
  color: #fff;
  font-size: 16px;
}
</style>
