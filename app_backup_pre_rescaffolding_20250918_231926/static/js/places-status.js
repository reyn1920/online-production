/**
 * Places Status Dashboard
 * Displays clinic groups with provider status indicators
 */const CLINIC_GROUPS = [
  { name: "Geocoding", ids: ["opencage", "nominatim_osm"] },
  { name: "Vet Clinics", ids: ["overpass_main", "overpass_kumi", "overpass_fr", "foursquare", "google_places", "yelp"] },
  { name: "Hospitals/Clinics", ids: ["overpass_main", "overpass_kumi", "overpass_fr", "foursquare", "google_places", "yelp"] },
];//For each provider id, pull status from/integrations registry
function dotClass(status) {
  if (status === "green") return "dot green";
  if (status === "red") return "dot red";
  return "dot purple";//default/needs key or disabled
}

class PlacesStatusDashboard {
  constructor() {
    this.providers = new Map();
    this.refreshInterval = null;
  }

  async init() {
    await this.fetchProviders();
    this.render();
    this.startAutoRefresh();
  }

  async fetchProviders() {
    try {
      const response = await fetch("/places/providers");
      const data = await response.json();//Store providers in a map for quick lookup
      this.providers.clear();
      data.providers.forEach(provider => {
        this.providers.set(provider.id, provider);
      });
    } catch (error) {
      console.error('Failed to fetch providers:', error);
    }
  }

  getProviderStatus(providerId) {
    const provider = this.providers.get(providerId);
    return provider ? provider.status : 'purple';
  }

  getProviderName(providerId) {
    const provider = this.providers.get(providerId);
    return provider ? provider.name : providerId;
  }

  renderClinicGroup(group) {
    const groupDiv = document.createElement('div');
    groupDiv.className = 'clinic-group';
    
    const header = document.createElement('h3');
    header.textContent = group.name;
    header.className = 'clinic-group-header';
    groupDiv.appendChild(header);

    const providersList = document.createElement('div');
    providersList.className = 'providers-list';

    group.ids.forEach(providerId => {
      const status = this.getProviderStatus(providerId);
      const name = this.getProviderName(providerId);
      
      const providerItem = document.createElement('div');
      providerItem.className = 'provider-item';
      
      const statusDot = document.createElement('span');
      statusDot.className = dotClass(status);
      
      const providerName = document.createElement('span');
      providerName.textContent = name;
      providerName.className = 'provider-name';
      
      const statusText = document.createElement('span');
      statusText.textContent = status.toUpperCase();
      statusText.className = `status-text status-${status}`;
      
      providerItem.appendChild(statusDot);
      providerItem.appendChild(providerName);
      providerItem.appendChild(statusText);
      
      providersList.appendChild(providerItem);
    });

    groupDiv.appendChild(providersList);
    return groupDiv;
  }

  render() {
    const container = document.getElementById('places-status-container');
    if (!container) {
      console.error('Places status container not found');
      return;
    }

    container.innerHTML = '';
    
    const title = document.createElement('h2');
    title.textContent = 'Places & Clinic Services Status';
    title.className = 'places-status-title';
    container.appendChild(title);

    const legend = document.createElement('div');
    legend.className = 'status-legend';
    legend.innerHTML = `
      <div class="status-legend-item">
        <span class="dot green"></span>
        <span>Working</span>
      </div>
      <div class="status-legend-item">
        <span class="dot purple"></span>
        <span>Needs Key/Disabled</span>
      </div>
      <div class="status-legend-item">
        <span class="dot red"></span>
        <span>Not Working</span>
      </div>
    `;
    container.appendChild(legend);

    const groupsContainer = document.createElement('div');
    groupsContainer.className = 'clinic-groups-container';
    
    CLINIC_GROUPS.forEach(group => {
      const groupElement = this.renderClinicGroup(group);
      groupsContainer.appendChild(groupElement);
    });

    container.appendChild(groupsContainer);//Add last updated timestamp
    const timestamp = document.createElement('div');
    timestamp.className = 'last-updated';
    timestamp.textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
    container.appendChild(timestamp);
  }

  startAutoRefresh(intervalMs = 30000) {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }
    
    this.refreshInterval = setInterval(async () => {
      await this.fetchProviders();
      this.render();
    }, intervalMs);
  }

  stopAutoRefresh() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
      this.refreshInterval = null;
    }
  }

  async refresh() {
    await this.fetchProviders();
    this.render();
  }

  getGroupSummary(groupName) {
    const group = CLINIC_GROUPS.find(g => g.name === groupName);
    if (!group) return null;

    const summary = {
      total: group.ids.length,
      green: 0,
      purple: 0,
      red: 0
    };

    group.ids.forEach(id => {
      const status = this.getProviderStatus(id);
      summary[status]++;
    });

    return summary;
  }

  getAllGroupsSummary() {
    return CLINIC_GROUPS.map(group => ({
      name: group.name,
      ...this.getGroupSummary(group.name)
    }));
  }
}//Global instance
let placesStatusDashboard = null;//Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  placesStatusDashboard = new PlacesStatusDashboard();
});//Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { PlacesStatusDashboard, CLINIC_GROUPS, dotClass };
}//Global functions for manual control
window.refreshPlacesStatus = async () => {
  if (placesStatusDashboard) {
    await placesStatusDashboard.refresh();
  }
};

window.initPlacesStatus = async () => {
  if (placesStatusDashboard) {
    await placesStatusDashboard.init();
  }
};