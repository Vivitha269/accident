const axios = require('axios');

/**
 * OSRM Service for routing (free tier: http://router.project-osrm.org)
 */
class OSRMService {
  constructor() {
    this.baseURL = process.env.OSRM_SERVER || 'http://router.project-osrm.org/route/v1/driving';
  }

  async getRoute(fromLat, fromLng, toLat, toLng) {
    try {
      const url = `${this.baseURL}/${fromLng},${fromLat};${toLng},${toLat}?overview=false&alternatives=false`;
      const response = await axios.get(url);
      return response.data.routes[0];
    } catch (error) {
      console.error('OSRM error:', error.message);
      return null;
    }
  }

  async getDistance(lat1, lng1, lat2, lng2) {
    const route = await this.getRoute(lat1, lng1, lat2, lng2);
    return route ? route.distance : 0;
  }
}

module.exports = { osrmService: new OSRMService() };
