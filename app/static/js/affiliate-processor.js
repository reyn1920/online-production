/**
 * Affiliate Data Processing
 * Handles processing of affiliate data into buckets with channel assignment
 */class AffiliateProcessor {
  constructor() {
    this.buckets = [];
  }/**
   * Process affiliate data and organize into buckets with channel assignment
   * @param {Object} data - The data object containing affiliate arrays
   */processAffiliateData(data) {//Clear existing buckets
    this.buckets = [];//Process pets affiliates
    if (data.pets_affiliates && Array.isArray(data.pets_affiliates)) {
      data.pets_affiliates.forEach(affiliate => {
        this.buckets.push({
          ...affiliate,
          channel: "Pets"
        });
      });
    }//Process birds & exotics affiliates
    if (data.birds_exotics_affiliates && Array.isArray(data.birds_exotics_affiliates)) {
      data.birds_exotics_affiliates.forEach(affiliate => {
        this.buckets.push({
          ...affiliate,
          channel: "Birds & Exotics"
        });
      });
    }

    return this.buckets;
  }/**
   * Get processed buckets
   * @returns {Array} Array of processed affiliate data with channels
   */getBuckets() {
    return this.buckets;
  }/**
   * Get buckets filtered by channel
   * @param {string} channel - Channel name to filter by
   * @returns {Array} Filtered array of affiliate data
   */getBucketsByChannel(channel) {
    return this.buckets.filter(bucket => bucket.channel === channel);
  }/**
   * Get all unique channels
   * @returns {Array} Array of unique channel names
   */getChannels() {
    return [...new Set(this.buckets.map(bucket => bucket.channel))];
  }/**
   * Clear all buckets
   */clearBuckets() {
    this.buckets = [];
  }/**
   * Get bucket statistics
   * @returns {Object} Statistics about the buckets
   */getStatistics() {
    const statusCounts = this.getStatusCounts(this.buckets);

    const stats = {
      total: this.buckets.length,
      byChannel: {},
      statusCounts: statusCounts
    };

    this.buckets.forEach(bucket => {
      if (!stats.byChannel[bucket.channel]) {
        stats.byChannel[bucket.channel] = 0;
      }
      stats.byChannel[bucket.channel]++;
    });

    return stats;
  }/**
   * Get status counts for programs
   * @param {Array} programs - Array of affiliate programs
   * @returns {Object} Status counts
   */getStatusCounts(programs) {
    const counts = { active: 0, disabled: 0, error: 0 };

    programs.forEach(program => {
      const status = this.getRandomStatus();//In real app, this would come from actual status
      counts[status]++;
    });

    return counts;
  }/**
   * Get a random status for demo purposes
   * @returns {string} Status
   */getRandomStatus() {
    const statuses = ['active', 'active', 'active', 'disabled', 'error'];//Weighted towards active
    return statuses[Math.floor(Math.random() * statuses.length)];
  }/**
   * Get status dot HTML
   * @param {string} status - Program status
   * @returns {string} HTML for status dot
   */getStatusDot(status) {
    const statusMap = {
      active: 'green',
      disabled: 'purple',
      error: 'red'
    };

    const dotClass = statusMap[status] || 'red';
    const pulse = status === 'active' && Math.random() > 0.7 ? ' pulse' : '';

    return `<span class="dot ${dotClass}${pulse}"></span>`;
  }
}//Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = AffiliateProcessor;
} else {
  window.AffiliateProcessor = AffiliateProcessor;
}//Example usage://const processor = new AffiliateProcessor();//const sampleData = {//pets_affiliates: [//{ id: 'chewy', name: 'Chewy', commission: 5.0 },//{ id: 'petco', name: 'Petco', commission: 4.5 }//],//birds_exotics_affiliates: [//{ id: 'tractor_supply', name: 'Tractor Supply', commission: 3.0 }//]//};//const buckets = processor.processAffiliateData(sampleData);//console.log('Processed buckets:', buckets);
